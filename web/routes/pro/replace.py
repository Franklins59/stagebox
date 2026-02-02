"""
Stagebox Device Replacement Routes (Pro Only)

Replace defective devices with new ones, preserving configuration.
"""

import json
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests
import yaml
from flask import Blueprint, jsonify, request

from web import config
from web.services import device_manager, is_building_active
from web.routes.pro.admin import require_admin, require_pro
from web.services.core_modules import (
    CORE_AVAILABLE, STAGE2_AVAILABLE,
    RpcClient, stage2_configure_device_by_ip,
    load_state, save_state_atomic_with_bak
)

bp = Blueprint('replace', __name__)


def _load_model_mapping() -> dict:
    """Load model mapping from shelly_model_map.yaml."""
    if not config.DATA_DIR:
        return {}
    
    map_path = config.DATA_DIR / 'shelly_model_map.yaml'
    if not map_path.exists():
        return {}
    
    try:
        with open(map_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    except:
        return {}


@bp.route('/api/replace/devices', methods=['GET'])
@require_pro
def get_replaceable_devices():
    """Get list of OFFLINE devices that can be replaced (from ip_state.json)."""
    if not is_building_active():
        return jsonify({'success': False, 'error': 'No building active'}), 400
    
    if not config.STATE_FILE or not config.STATE_FILE.exists():
        return jsonify({'success': False, 'error': 'ip_state.json not found'}), 404
    
    try:
        with open(config.STATE_FILE, 'r', encoding='utf-8') as f:
            state_data = json.load(f)
        
        # Load model mapping for normalized names
        model_map = _load_model_mapping()
        
        # Get all devices
        all_devices = state_data.get('devices', {})
        
        def check_online(ip):
            """Check if device is online."""
            try:
                response = requests.get(f'http://{ip}/rpc/Shelly.GetDeviceInfo', timeout=2)
                return response.status_code == 200
            except:
                return False
        
        # Parallel ping to find offline devices
        online_status = {}
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = {
                executor.submit(check_online, dev.get('ip')): mac
                for mac, dev in all_devices.items() if dev.get('ip')
            }
            for future in as_completed(futures):
                mac = futures[future]
                online_status[mac] = future.result()
        
        # Only include OFFLINE devices
        devices = []
        for mac, dev in all_devices.items():
            if online_status.get(mac, False):
                continue  # Skip online devices
            
            # Normalize model name using model map
            hw_model = dev.get('hw_model', '')
            model_from_state = dev.get('model', '')
            
            # Try mapping hw_model first, then model
            normalized_model = (
                model_map.get(hw_model) or 
                model_map.get(model_from_state) or 
                model_from_state or 
                hw_model
            )
            
            devices.append({
                'mac': mac,
                'ip': dev.get('ip'),
                'name': dev.get('friendly_name') or dev.get('hostname'),
                'model': normalized_model,
                'hw_model': hw_model
            })
        
        # Sort by IP
        devices.sort(key=lambda d: tuple(int(x) for x in d.get('ip', '0.0.0.0').split('.')))
        
        return jsonify({'success': True, 'devices': devices})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/replace/scan-dhcp', methods=['POST'])
@require_pro
def scan_dhcp_for_new_device():
    """Scan DHCP range for new devices not yet in ip_state."""
    if not is_building_active():
        return jsonify({'success': False, 'error': 'No building active'}), 400
    
    try:
        cfg = config.load_config()
    except Exception as e:
        return jsonify({'success': False, 'error': f'Cannot read config: {e}'}), 500
    
    # Get DHCP scan range
    stage2 = cfg.get('stage2', {})
    network = stage2.get('network', {})
    
    dhcp_start = network.get('dhcp_scan_start')
    dhcp_end = network.get('dhcp_scan_end')
    
    if not dhcp_start or not dhcp_end:
        return jsonify({'success': False, 'error': 'DHCP scan range not configured'}), 400
    
    # Load model mapping
    model_map = _load_model_mapping()
    
    # Load existing devices to exclude
    existing_macs = set()
    if config.STATE_FILE and config.STATE_FILE.exists():
        try:
            with open(config.STATE_FILE, 'r', encoding='utf-8') as f:
                state_data = json.load(f)
                existing_macs = set(state_data.get('devices', {}).keys())
        except:
            pass
    
    # Parse IP range
    start_parts = dhcp_start.split('.')
    end_parts = dhcp_end.split('.')
    start_num = int(start_parts[3])
    end_num = int(end_parts[3])
    subnet = '.'.join(start_parts[:3])
    
    def check_device(ip):
        """Check if IP has a Shelly device."""
        try:
            response = requests.get(f'http://{ip}/rpc/Shelly.GetDeviceInfo', timeout=2)
            if response.status_code == 200:
                info = response.json()
                hw_model = info.get('model', '')
                # Normalize model name using model map
                normalized_model = model_map.get(hw_model, info.get('app') or hw_model)
                return {
                    'ip': ip,
                    'mac': info.get('mac', '').upper().replace(':', ''),
                    'model': normalized_model,
                    'hw_model': hw_model,
                    'name': info.get('name'),
                    'fw': info.get('ver')
                }
        except:
            pass
        return None
    
    # Parallel scan
    devices = []
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = {}
        for i in range(start_num, end_num + 1):
            ip = f"{subnet}.{i}"
            futures[executor.submit(check_device, ip)] = ip
        
        for future in as_completed(futures):
            result = future.result()
            if result:
                # Only include devices NOT already in ip_state
                if result['mac'] not in existing_macs:
                    devices.append(result)
    
    # Sort by IP
    devices.sort(key=lambda d: tuple(int(x) for x in d.get('ip', '0.0.0.0').split('.')))
    
    return jsonify({
        'success': True,
        'devices': devices,
        'scanned_range': f'{dhcp_start} - {dhcp_end}'
    })


def _extract_snapshot_json_from_zip(zip_path: Path) -> dict:
    """Extract the JSON snapshot data from a ZIP bundle."""
    try:
        with zipfile.ZipFile(zip_path, 'r') as zf:
            for name in zf.namelist():
                if name.endswith('.json') and 'shelly_snapshot' in name:
                    with zf.open(name) as f:
                        return json.load(f)
    except:
        pass
    return {}


@bp.route('/api/replace/snapshot-config/<mac>', methods=['GET'])
@require_pro
def get_snapshot_config_for_device(mac):
    """Get device config from latest snapshot ZIP bundle."""
    if not is_building_active():
        return jsonify({'success': False, 'error': 'No building active'}), 400
    
    snapshots_dir = config.DATA_DIR / 'snapshots'
    if not snapshots_dir.exists():
        return jsonify({'success': False, 'error': 'No snapshots directory'}), 404
    
    # Find newest ZIP bundle
    zip_files = sorted(snapshots_dir.glob('snapshot_*.zip'), reverse=True)
    if not zip_files:
        return jsonify({'success': False, 'error': 'No snapshot available'}), 404
    
    try:
        snapshot = _extract_snapshot_json_from_zip(zip_files[0])
        if not snapshot:
            return jsonify({'success': False, 'error': 'Cannot read snapshot'}), 500
        
        # Find device by MAC
        mac_upper = mac.upper().replace(':', '').replace('-', '')
        for dev in snapshot.get('devices', []):
            dev_mac = dev.get('device_info', {}).get('mac', '').upper().replace(':', '')
            if dev_mac == mac_upper:
                # Extract relevant config info
                config_info = {
                    'found': True,
                    'snapshot_timestamp': snapshot.get('snapshot_timestamp'),
                    'config': {}
                }
                
                dev_config = dev.get('config', {})
                
                # Input settings
                inputs = []
                for i in range(4):
                    key = f'input:{i}'
                    if key in dev_config:
                        inp = dev_config[key]
                        inputs.append(f"input:{i} type={inp.get('type')}, invert={inp.get('invert')}")
                if inputs:
                    config_info['config']['inputs'] = inputs
                
                # Switch settings
                switches = []
                for i in range(4):
                    key = f'switch:{i}'
                    if key in dev_config:
                        sw = dev_config[key]
                        switches.append(f"switch:{i} in_mode={sw.get('in_mode')}, initial={sw.get('initial_state')}")
                if switches:
                    config_info['config']['switches'] = switches
                
                # Cover settings
                covers = []
                for i in range(2):
                    key = f'cover:{i}'
                    if key in dev_config:
                        cov = dev_config[key]
                        covers.append(f"cover:{i} in_mode={cov.get('in_mode')}, swap={cov.get('swap_inputs')}")
                if covers:
                    config_info['config']['covers'] = covers
                
                # Scripts - include code
                scripts = dev.get('scripts', [])
                if scripts:
                    config_info['config']['scripts'] = []
                    for s in scripts:
                        script_info = {'name': s.get('name', 'unknown')}
                        if s.get('code'):
                            script_info['code'] = s.get('code')
                        config_info['config']['scripts'].append(script_info)
                
                # KVS - include full values
                kvs = dev.get('kvs', {})
                if kvs:
                    config_info['config']['kvs'] = kvs
                
                # Webhooks - include full details
                webhooks = dev.get('webhooks', {}).get('hooks', [])
                if webhooks:
                    config_info['config']['webhooks'] = webhooks
                
                return jsonify({'success': True, **config_info})
        
        return jsonify({'success': True, 'found': False})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


def _run_stage2_for_device_http(current_ip: str, target_ip: str) -> dict:
    """
    Fallback: Run Stage 2 via direct HTTP requests when core module not available.
    Configures WiFi with static IP on the device.
    """
    try:
        cfg = config.load_config()
        secrets = config.load_secrets()
        network_cfg = cfg.get('stage2', {}).get('network', {})
        wifi_profiles = secrets.get('wifi_profiles', [])
        
        if not wifi_profiles:
            return {'success': False, 'error': 'No WiFi profiles configured'}
        
        wifi = wifi_profiles[0]
        
        # Build static IP config
        static_cfg = {
            'enable': True,
            'ipv4mode': 'static',
            'ip': target_ip,
            'netmask': network_cfg.get('netmask', '255.255.255.0'),
            'gw': network_cfg.get('gateway'),
            'nameserver': network_cfg.get('nameserver', network_cfg.get('gateway'))
        }
        
        # Apply WiFi config with static IP
        resp = requests.post(
            f'http://{current_ip}/rpc/WiFi.SetConfig',
            json={
                'config': {
                    'sta': {
                        'ssid': wifi.get('ssid'),
                        'pass': wifi.get('password'),
                        **static_cfg
                    }
                }
            },
            timeout=10
        )
        
        if resp.status_code != 200:
            return {'success': False, 'error': f'WiFi config failed: {resp.status_code}'}
        
        # Reboot device to apply changes
        try:
            requests.post(f'http://{current_ip}/rpc/Shelly.Reboot', json={}, timeout=5)
        except:
            pass  # Device may not respond during reboot
        
        return {
            'success': True,
            'new_ip': target_ip,
            'message': f'Static IP {target_ip} configured via HTTP fallback, device rebooting'
        }
        
    except Exception as e:
        return {'success': False, 'error': str(e)}


def _run_stage2_for_device(current_ip: str, target_ip: str, mac: str) -> dict:
    """Run Stage 2 (network config) for a single device using core module or HTTP fallback."""
    
    # Try core module first
    if not STAGE2_AVAILABLE or not CORE_AVAILABLE or RpcClient is None:
        # Fallback to HTTP method
        return _run_stage2_for_device_http(current_ip, target_ip)
    
    try:
        cfg = config.load_config()
        secrets = config.load_secrets()
        stage2_cfg = cfg.get('stage2', {})
        network_cfg = stage2_cfg.get('network', {})
        
        # Build options for stage2_configure_device_by_ip
        options = {
            'network': network_cfg,
            'wifi_profiles': secrets.get('wifi_profiles', []),
            'model_mapping': _load_model_mapping(),
            'hostname': stage2_cfg.get('naming', {}),
            'dry_run': False,
        }
        
        # Load current state
        state = load_state(str(config.STATE_FILE))
        
        # Create RPC client for current (DHCP) IP
        rpc = RpcClient(current_ip, timeout_s=network_cfg.get('rpc_timeout_s', 2.0))
        
        # Run stage 2 configure
        result = stage2_configure_device_by_ip(
            rpc_client=rpc,
            state=state,
            target_ip=current_ip,  # Current IP where device is now
            options=options,
        )
        
        # Save state after configuration
        save_state_atomic_with_bak(state, str(config.STATE_FILE), str(config.STATE_FILE) + ".bak")
        
        if result.ok:
            return {
                'success': True,
                'new_ip': result.ip,
                'message': f'Static IP {result.ip} configured, device rebooting'
            }
        else:
            return {
                'success': False,
                'error': str(result.errors) if result.errors else 'Stage 2 failed'
            }
        
    except Exception as e:
        return {'success': False, 'error': str(e)}


@bp.route('/api/replace/execute', methods=['POST'])
@require_pro
def execute_replace_device():
    """Execute device replacement: update ip_state.json and run Stage 2."""
    if not is_building_active():
        return jsonify({'success': False, 'error': 'No building active'}), 400
    
    data = request.get_json() or {}
    old_mac = data.get('old_mac', '').upper().replace(':', '').replace('-', '')
    new_mac = data.get('new_mac', '').upper().replace(':', '').replace('-', '')
    new_ip = data.get('new_ip')
    
    if not old_mac or not new_mac or not new_ip:
        return jsonify({'success': False, 'error': 'Missing old_mac, new_mac, or new_ip'}), 400
    
    if not config.STATE_FILE or not config.STATE_FILE.exists():
        return jsonify({'success': False, 'error': 'ip_state.json not found'}), 404
    
    try:
        # Load ip_state.json
        with open(config.STATE_FILE, 'r', encoding='utf-8') as f:
            state_data = json.load(f)
        
        devices = state_data.get('devices', {})
        
        if old_mac not in devices:
            return jsonify({'success': False, 'error': f'Old MAC {old_mac} not found in ip_state.json'}), 404
        
        if new_mac in devices:
            return jsonify({'success': False, 'error': f'New MAC {new_mac} already exists in ip_state.json'}), 400
        
        # Get old device data
        old_device = devices[old_mac].copy()
        target_ip = old_device.get('ip')
        
        # Create new device entry with same IP but new MAC
        # Reset stage_completed to 1 (as if just came from Stage 1)
        new_device = old_device.copy()
        new_device['id'] = new_mac
        new_device['replaced_from'] = old_mac
        new_device['replaced_at'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
        new_device['stage_completed'] = 1  # Reset to Stage 1, so Stage 2 will set it to 2
        
        # Remove old entry, add new entry
        del devices[old_mac]
        devices[new_mac] = new_device
        
        # Save updated ip_state.json BEFORE running stage2
        with open(config.STATE_FILE, 'w', encoding='utf-8') as f:
            json.dump(state_data, f, indent=2)
        
        # Reload device manager to pick up changes
        device_manager.load_devices()
        
        # Run Stage 2 on the new device to assign static IP
        stage2_result = _run_stage2_for_device(new_ip, target_ip, new_mac)
        
        # If Stage 2 succeeded, update stage_completed to 2
        if stage2_result.get('success'):
            with open(config.STATE_FILE, 'r', encoding='utf-8') as f:
                state_data = json.load(f)
            if new_mac in state_data.get('devices', {}):
                state_data['devices'][new_mac]['stage_completed'] = 2
                with open(config.STATE_FILE, 'w', encoding='utf-8') as f:
                    json.dump(state_data, f, indent=2)
        
        # Reload devices after stage2
        device_manager.load_devices()
        
        return jsonify({
            'success': True,
            'old_mac': old_mac,
            'new_mac': new_mac,
            'target_ip': target_ip,
            'stage2_result': stage2_result,
            'device_name': old_device.get('friendly_name') or old_device.get('hostname')
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
