"""
Stagebox Provisioning Routes

Stage 1-4 provisioning operations.
Available in both editions.
"""

import json
import threading
import time
import ipaddress
from flask import Blueprint, jsonify, request

import yaml

from web import config
from web.services import device_manager, is_building_active
from web.services.job_queue import job_queue
from web.services import core_modules  # Import module, not values

bp = Blueprint('provisioning', __name__)

# Stage 1 worker state
stage1_worker_thread = None
stage1_stop_event = threading.Event()
stage1_last_heartbeat = 0.0
stage1_lock = threading.Lock()


# ===========================================================================
# Stage 1 - AP Provisioning
# ===========================================================================

def _load_stage1_config():
    """Load Stage 1 configuration."""
    if not config.CONFIG_FILE or not config.CONFIG_FILE.exists():
        return {}
    
    try:
        with open(config.CONFIG_FILE, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f) or {}
        
        stage1 = config_data.get('stage1', {}) or {}
        
        wifi_profiles = []
        if config.SECRETS_FILE and config.SECRETS_FILE.exists():
            with open(config.SECRETS_FILE, 'r', encoding='utf-8') as f:
                secrets_data = yaml.safe_load(f) or {}
            wifi_profiles = secrets_data.get('wifi_profiles', []) or []
        
        return {
            'wifi_profiles': wifi_profiles,
            'shelly_ip': stage1.get('shelly_ip', '192.168.33.1'),
            'options': stage1.get('options', {}),
            'log': stage1.get('logging', {}),
            'enabled': stage1.get('enabled', True),
        }
    except Exception as e:
        print(f"Error loading Stage 1 config: {e}")
        return {}


def _write_stage1_status(status):
    """Write Stage 1 status to file."""
    try:
        with open(config.STAGE1_STATUS_FILE, 'w', encoding='utf-8') as f:
            json.dump(status, f)
    except Exception as e:
        print(f"Error writing Stage 1 status: {e}")


def _read_stage1_status():
    """Read Stage 1 status from file."""
    try:
        if config.STAGE1_STATUS_FILE.exists():
            with open(config.STAGE1_STATUS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error reading Stage 1 status: {e}")
    return {}


def _stage1_worker():
    """Stage 1 worker thread."""
    global stage1_last_heartbeat
    
    try:
        from core.provision.stage1_ap_core import provision_once, wifi_disconnect
    except ImportError as e:
        _write_stage1_status({
            'running': False,
            'error': f'Failed to import stage1_ap_core: {e}',
            'stopped_at': time.time()
        })
        return
    
    s1_config = _load_stage1_config()
    if not s1_config.get('wifi_profiles'):
        _write_stage1_status({
            'running': False,
            'error': 'No WiFi profiles configured',
            'stopped_at': time.time()
        })
        return
    
    devices_processed = []
    errors = []
    
    _write_stage1_status({
        'running': True,
        'started_at': time.time(),
        'state': 'scanning',
        'devices_processed': devices_processed,
        'errors': errors,
        'current_device': None
    })
    
    while not stage1_stop_event.is_set():
        with stage1_lock:
            time_since_heartbeat = time.time() - stage1_last_heartbeat
        
        if time_since_heartbeat > config.STAGE1_HEARTBEAT_TIMEOUT:
            _write_stage1_status({
                'running': False,
                'stopped_at': time.time(),
                'reason': 'heartbeat_timeout',
                'devices_processed': devices_processed,
                'errors': errors
            })
            try:
                wifi_disconnect()
            except:
                pass
            return
        
        try:
            summary = provision_once(s1_config, dry_run=False, logfile=None, iface_hint=None, quiet=True)
            
            if summary.get('ok'):
                device_info = {
                    'mac': summary.get('mac'),
                    'model': summary.get('model'),
                    'fw': summary.get('fw'),
                    'ssid': summary.get('ssid'),
                    'timestamp': time.time()
                }
                devices_processed.append(device_info)
                _write_stage1_status({
                    'running': True,
                    'state': 'device_done',
                    'last_device': device_info,
                    'devices_processed': devices_processed,
                    'errors': errors,
                    'current_device': None
                })
                time.sleep(2)
                # Reset to scanning state after showing success
                _write_stage1_status({
                    'running': True,
                    'state': 'scanning',
                    'devices_processed': devices_processed,
                    'errors': errors,
                    'current_device': None
                })
            else:
                reason = summary.get('reason', 'unknown')
                if reason in ('no_shelly_found', 'no_connectable_ap'):
                    _write_stage1_status({
                        'running': True,
                        'state': 'waiting',
                        'message': 'Waiting for Shelly AP...',
                        'devices_processed': devices_processed,
                        'errors': errors,
                        'current_device': None
                    })
                    for _ in range(50):
                        if stage1_stop_event.is_set():
                            break
                        time.sleep(0.1)
                else:
                    errors.append({'reason': reason, 'timestamp': time.time()})
                    
        except Exception as e:
            errors.append({'error': str(e), 'timestamp': time.time()})
            time.sleep(2)
    
    try:
        wifi_disconnect()
    except:
        pass
    
    _write_stage1_status({
        'running': False,
        'stopped_at': time.time(),
        'reason': 'user_stopped',
        'devices_processed': devices_processed,
        'errors': errors
    })


@bp.route('/api/stage1/start', methods=['POST'])
def stage1_start():
    """Start Stage 1 provisioning worker."""
    global stage1_worker_thread, stage1_last_heartbeat
    
    if not is_building_active():
        return jsonify({'success': False, 'error': 'No building active'}), 400
    
    with stage1_lock:
        if stage1_worker_thread and stage1_worker_thread.is_alive():
            return jsonify({'success': False, 'error': 'Stage 1 already running'}), 400
        
        stage1_stop_event.clear()
        stage1_last_heartbeat = time.time()
        stage1_worker_thread = threading.Thread(target=_stage1_worker, daemon=True)
        stage1_worker_thread.start()
    
    return jsonify({'success': True, 'message': 'Stage 1 started'})


@bp.route('/api/stage1/stop', methods=['POST'])
def stage1_stop():
    """Stop Stage 1 provisioning worker."""
    with stage1_lock:
        if not stage1_worker_thread or not stage1_worker_thread.is_alive():
            return jsonify({'success': False, 'error': 'Stage 1 not running'}), 400
        stage1_stop_event.set()
    
    stage1_worker_thread.join(timeout=10)
    return jsonify({'success': True, 'message': 'Stage 1 stopped'})


@bp.route('/api/stage1/status', methods=['GET'])
def stage1_status():
    """Get Stage 1 status."""
    status = _read_stage1_status()
    with stage1_lock:
        status['thread_alive'] = stage1_worker_thread and stage1_worker_thread.is_alive()
    return jsonify({'success': True, 'status': status})


@bp.route('/api/stage1/heartbeat', methods=['POST'])
def stage1_heartbeat():
    """Send heartbeat to keep Stage 1 worker alive."""
    global stage1_last_heartbeat
    with stage1_lock:
        stage1_last_heartbeat = time.time()
        running = stage1_worker_thread and stage1_worker_thread.is_alive()
    return jsonify({'success': True, 'running': running})


# ===========================================================================
# Stage 2 - Scan & Adopt
# ===========================================================================

@bp.route('/api/stage2/scan', methods=['POST'])
def stage2_scan():
    """Scan network for new Shelly devices."""
    if not core_modules.STAGE2_AVAILABLE:
        return jsonify({'success': False, 'error': 'Stage 2 not available'}), 500
    
    cfg = config.load_config()
    network_cfg = cfg.get('stage2', {}).get('network', {})
    
    dhcp_start = network_cfg.get('dhcp_scan_start', '192.168.50.150')
    dhcp_end = network_cfg.get('dhcp_scan_end', '192.168.50.249')
    
    found_devices = []
    
    # Load existing state to check for known devices
    existing_macs = set()
    if device_manager.state and device_manager.state.devices:
        existing_macs = set(device_manager.state.devices.keys())
    
    try:
        start_ip = ipaddress.IPv4Address(dhcp_start)
        end_ip = ipaddress.IPv4Address(dhcp_end)
        
        import requests
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        def check_device(ip):
            try:
                resp = requests.post(
                    f'http://{ip}/rpc',
                    json={'id': 1, 'method': 'Shelly.GetDeviceInfo'},
                    timeout=1
                )
                if resp.status_code == 200:
                    data = resp.json()
                    if 'result' in data:
                        info = data['result']
                        mac = info.get('mac', '').upper().replace(':', '')
                        return {
                            'ip': str(ip),
                            'mac': mac,
                            'model': info.get('model', info.get('app', 'Unknown')),
                            'name': info.get('name', ''),
                            'fw_version': info.get('ver', ''),
                            'existing': mac in existing_macs
                        }
            except:
                pass
            return None
        
        ips_to_scan = [str(ipaddress.IPv4Address(i)) for i in range(int(start_ip), int(end_ip) + 1)]
        
        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = {executor.submit(check_device, ip): ip for ip in ips_to_scan}
            for future in as_completed(futures):
                result = future.result()
                if result:
                    found_devices.append(result)
        
        return jsonify({
            'success': True,
            'devices': found_devices,
            'scanned_range': f'{dhcp_start} - {dhcp_end}'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/stage2/adopt', methods=['POST'])
def stage2_adopt():
    """Adopt discovered devices into the pool."""
    if not core_modules.STAGE2_AVAILABLE or not core_modules.CORE_AVAILABLE:
        return jsonify({'success': False, 'error': 'Stage 2 not available'}), 500
    
    if not is_building_active():
        return jsonify({'success': False, 'error': 'No building active'}), 400
    
    data = request.get_json() or {}
    devices_to_adopt = data.get('devices', [])
    
    if not devices_to_adopt:
        return jsonify({'success': False, 'error': 'No devices to adopt'}), 400
    
    # Check device limit (currently unlimited for all editions)
    from web.edition import get_device_limit
    device_limit = get_device_limit()
    
    if device_limit > 0:  # 0 = unlimited
        current_count = len(device_manager.devices) if device_manager.devices else 0
        new_devices = len([d for d in devices_to_adopt if not d.get('existing', False)])
        
        if current_count + new_devices > device_limit:
            return jsonify({
                'success': False,
                'error': f'Device limit reached ({current_count}/{device_limit}).',
                'device_limit': device_limit,
                'current_count': current_count
            }), 400
    
    # Create job for progress tracking
    job_id = job_queue.create_job('stage2', len(devices_to_adopt))
    
    # Run adoption in background thread
    def run_adoption():
        import time
        cfg = config.load_config()
        secrets = config.load_secrets()
        stage2_cfg = cfg.get('stage2', {})
        network_cfg = stage2_cfg.get('network', {})
        
        # Build options for stage2_configure_device_by_ip
        options = {
            'network': network_cfg,
            'wifi_profiles': secrets.get('wifi_profiles', []),
            'model_mapping': config.load_model_mapping(),
            'hostname': stage2_cfg.get('naming', {}),
            'dry_run': False,
        }
        
        state_file = str(config.STATE_FILE)
        state_bak = state_file + ".bak"
        
        results = []
        for i, dev in enumerate(devices_to_adopt):
            ip = dev.get('ip')
            mac = dev.get('mac', '')
            was_reset = dev.get('was_reset', False)
            
            print(f"[Stage2] Processing device {i+1}/{len(devices_to_adopt)}: {mac} @ {ip}")
            job_queue.update_job(job_id, current=i, current_device=f"{mac} @ {ip}")
            
            try:
                # Reload state to avoid IP collisions
                state = core_modules.load_state(state_file)
                state_path_attr = getattr(state, 'path', 'NOT SET')
                print(f"[Stage2] Loaded state with {len(state.devices)} devices, path={state_path_attr}")
                print(f"[Stage2] State file we expect: {state_file}")
                print(f"[Stage2] Devices in state: {list(state.devices.keys())}")
                
                # If device was reset, clear stage_completed
                if was_reset and mac:
                    mac_normalized = mac.upper().replace(':', '').replace('-', '')
                    if mac_normalized in state.devices:
                        old_stage = state.devices[mac_normalized].get('stage_completed', 0)
                        state.devices[mac_normalized]['stage_completed'] = 0
                        state.devices[mac_normalized]['_reset_from_stage'] = old_stage
                        state.devices[mac_normalized]['_reset_ts'] = time.strftime('%Y-%m-%dT%H:%M:%SZ')
                        core_modules.save_state_atomic_with_bak(state, state_file, state_bak)
                        state = core_modules.load_state(state_file)
                
                rpc = core_modules.RpcClient(ip, timeout_s=network_cfg.get('rpc_timeout_s', 0.5))
                result = core_modules.stage2_configure_device_by_ip(
                    rpc_client=rpc,
                    state=state,
                    target_ip=ip,
                    options=options,
                )
                
                print(f"[Stage2] Result for {mac}: ok={result.ok}, ip={result.ip}, errors={result.errors}")
                
                # Note: Core function already saves state internally, no need to save again
                
                results.append({
                    'mac': mac,
                    'ip': ip,
                    'status': 'ok' if result.ok else 'error',
                    'new_ip': result.ip if result.ok else None,
                    'was_reset': was_reset,
                    'message': '' if result.ok else str(result.errors),
                })
                job_queue.update_job(job_id, result={
                    'mac': mac,
                    'status': 'ok' if result.ok else 'error',
                    'new_ip': result.ip if result.ok else None,
                })
                
            except Exception as e:
                results.append({
                    'mac': mac,
                    'ip': ip,
                    'status': 'error',
                    'message': str(e),
                })
                job_queue.update_job(job_id, result={
                    'mac': mac,
                    'status': 'error',
                    'message': str(e),
                })
        
        # Complete job
        adopted = sum(1 for r in results if r['status'] == 'ok')
        failed = len(results) - adopted
        job_queue.complete_job(job_id, {
            'adopted': adopted,
            'failed': failed,
            'results': results,
        })
        
        # Reload devices
        device_manager.load_devices()
    
    # Start background thread
    import threading
    thread = threading.Thread(target=run_adoption, daemon=True)
    thread.start()
    
    return jsonify({
        'success': True,
        'job_id': job_id,
        'message': f'Adopting {len(devices_to_adopt)} devices...'
    })


# ===========================================================================
# Stage 3 - OTA & Friendly Names
# ===========================================================================

@bp.route('/api/stage3/run', methods=['POST'])
def stage3_run():
    """Run Stage 3 (OTA updates and friendly names).
    
    Friendly name logic:
    1. If Shelly has a name set -> use it as friendly_name
    2. If no Shelly name but model_map has entry -> use model_map name and set on Shelly
    3. If neither -> use technical model name (hw_model or app)
    """
    import requests
    
    if not core_modules.STAGE3_AVAILABLE:
        return jsonify({'success': False, 'error': 'Stage 3 not available'}), 500
    
    if not is_building_active():
        return jsonify({'success': False, 'error': 'No building active'}), 400
    
    data = request.get_json() or {}
    device_macs = data.get('devices', []) or data.get('macs', [])
    ota_enabled = data.get('ota_enabled', True)
    
    cfg = config.load_config()
    stage3_cfg = cfg.get('stage3', {})
    
    # Load model mapping for fallback names
    model_map = config.load_model_mapping()
    
    try:
        # Configure Stage 3 - OTA only, we handle friendly names ourselves
        s3_config = core_modules.Stage3Config(
            enabled=True,
            ip_state_file=str(config.DATA_DIR / 'ip_state.json'),
            ota=core_modules.Stage3OtaConfig(
                enabled=ota_enabled,
                mode=stage3_cfg.get('ota', {}).get('mode', 'check_and_update'),
                timeout_s=float(stage3_cfg.get('ota', {}).get('timeout', 20)),
            ),
            friendly=core_modules.Stage3FriendlyConfig(
                enabled=False,  # We handle this ourselves
                field_name='friendly_name',
                backfill=False,
            ),
        )
        
        # Load current state
        device_manager.load_devices()
        state_dict = {
            'version': device_manager.state.version if device_manager.state else 1,
            'devices': dict(device_manager.state.devices) if device_manager.state else {}
        }
        
        # Build only_ips filter if specific MACs provided
        only_ips = None
        if device_macs:
            only_ips = [
                device_manager.state.devices[m].get('ip')
                for m in device_macs
                if device_manager.state.devices.get(m, {}).get('ip')
            ]
        
        # Run stage 3 (OTA only)
        summary = core_modules.run_stage3_on_state_dict(
            state=state_dict,
            config=s3_config,
            only_ips=only_ips if only_ips else None,
            dry_run=False,
            concurrency=8,
        )
        
        # Process results and handle friendly names
        details = []
        ok_count = 0
        failed_count = 0
        
        for mac, result in summary.devices.items():
            mac_upper = mac.upper().replace(':', '').replace('-', '')
            
            # Find device in state
            device = None
            state_mac_key = None
            for state_mac in state_dict.get('devices', {}).keys():
                state_mac_norm = state_mac.upper().replace(':', '').replace('-', '')
                if state_mac_norm == mac_upper:
                    device = state_dict['devices'][state_mac]
                    state_mac_key = state_mac
                    break
            
            friendly_status = 'skipped'
            
            if device and result.ok:
                ip = device.get('ip')
                hw_model = device.get('hw_model') or device.get('model', '')
                
                # Try to get/set friendly name
                if ip:
                    try:
                        # Get current device info from Shelly
                        resp = requests.get(f'http://{ip}/rpc/Shelly.GetDeviceInfo', timeout=5)
                        if resp.status_code == 200:
                            info = resp.json()
                            shelly_name = (info.get('name') or '').strip()
                            
                            if shelly_name:
                                # Shelly has a name - use it
                                device['friendly_name'] = shelly_name
                                friendly_status = 'from_shelly'
                            else:
                                # No name on Shelly - check model map
                                display_name = model_map.get(hw_model, '')
                                
                                if display_name:
                                    # Set name from model map
                                    device['friendly_name'] = display_name
                                    # Also set on Shelly
                                    try:
                                        requests.post(
                                            f'http://{ip}/rpc/Sys.SetConfig',
                                            json={'config': {'device': {'name': display_name}}},
                                            timeout=5
                                        )
                                        friendly_status = 'from_model_map'
                                    except:
                                        friendly_status = 'from_model_map_local_only'
                                else:
                                    # Use technical name (app or model)
                                    tech_name = (info.get('app') or '') or hw_model
                                    if tech_name:
                                        device['friendly_name'] = tech_name
                                        friendly_status = 'technical_name'
                                    else:
                                        friendly_status = 'no_name_available'
                    except requests.exceptions.RequestException as e:
                        friendly_status = 'connection_error'
                
                # Update stage_completed
                device['stage_completed'] = 3
                ok_count += 1
            else:
                failed_count += 1
            
            details.append({
                'mac': mac,
                'status': 'ok' if result.ok else 'error',
                'ota_status': getattr(result, 'ota_status', None),
                'friendly_status': friendly_status,
                'friendly_name': device.get('friendly_name') if device else None,
                'message': getattr(result, 'message', ''),
            })
        
        # Save updated state
        device_manager.state.devices = state_dict.get('devices', {})
        device_manager.save_state()
        device_manager.load_devices()
        
        return jsonify({
            'success': summary.ok,
            'processed': len(summary.devices),
            'updated': ok_count,
            'failed': failed_count,
            'details': details
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ===========================================================================
# Stage 4 - Profile Configuration
# ===========================================================================

@bp.route('/api/stage4/run', methods=['POST'])
def stage4_run():
    """Run Stage 4 (profile configuration)."""
    if not core_modules.STAGE4_AVAILABLE:
        return jsonify({'success': False, 'error': 'Stage 4 not available'}), 500
    
    if not is_building_active():
        return jsonify({'success': False, 'error': 'No building active'}), 400
    
    data = request.get_json() or {}
    device_macs = data.get('devices', []) or data.get('macs', [])  # Accept both
    force = data.get('force', False)
    
    print(f"[Stage4] Received MACs: {device_macs}")  # Debug
    
    try:
        # Load profiles
        profiles_dir = config.DATA_DIR / 'profiles'
        profiles = core_modules.load_all_profiles(profiles_dir)
        
        if not profiles:
            return jsonify({'success': False, 'error': 'No profiles found'}), 400
        
        # Load current state
        device_manager.load_devices()
        state_dict = {
            'version': device_manager.state.version if device_manager.state else 1,
            'devices': dict(device_manager.state.devices) if device_manager.state else {}
        }
        
        # Run stage 4
        results, skipped = core_modules.run_stage4_on_state(
            state=state_dict,
            profiles=profiles,
            only_macs=device_macs if device_macs else None,
            dry_run=False,
            force=force,
        )
        
        # Process results and update stage_completed
        details = []
        ok_count = 0
        failed_count = 0
        
        for mac, result in results.items():
            details.append({
                'mac': mac,
                'status': 'ok' if result.ok else 'error',
                'profile': getattr(result, 'profile_name', None),
                'message': str(result.errors) if result.errors else '',
            })
            
            if result.ok:
                ok_count += 1
                # Update stage_completed to 4
                mac_upper = mac.upper().replace(':', '').replace('-', '')
                for state_mac in state_dict.get('devices', {}).keys():
                    state_mac_norm = state_mac.upper().replace(':', '').replace('-', '')
                    if state_mac_norm == mac_upper:
                        state_dict['devices'][state_mac]['stage_completed'] = 4
                        break
            else:
                failed_count += 1
        
        # Save updated state
        device_manager.state.devices = state_dict.get('devices', {})
        device_manager.save_state()
        device_manager.load_devices()
        
        return jsonify({
            'success': True,
            'processed': len(results),
            'configured': ok_count,
            'failed': failed_count,
            'skipped': len(skipped),
            'details': details
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


# ===========================================================================
# Job Progress
# ===========================================================================

@bp.route('/api/stage/progress/<job_id>', methods=['GET'])
def get_stage_progress(job_id):
    """Get progress of a running stage job."""
    job = job_queue.get_job(job_id)
    if not job:
        return jsonify({'success': False, 'error': 'Job not found'}), 404
    
    # Return job fields directly for frontend compatibility
    return jsonify({
        'success': True,
        'status': job.get('status', 'unknown'),
        'current': job.get('current', 0),
        'total': job.get('total', 0),
        'current_device': job.get('current_device'),
        'results': job.get('results', []),
    })
