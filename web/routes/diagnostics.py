"""
Stagebox Diagnostics Routes

Health check, WiFi diagnostics, Ethernet config, ECO mode.
Health check is Pro-only; WiFi scan, Ethernet, ECO are available in both editions.
"""

import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from flask import Blueprint, jsonify, request

from web.edition import is_pro
from web.services import device_manager, is_building_active

bp = Blueprint('diagnostics', __name__)


def _rpc_call(ip, method, params=None, timeout=5):
    """Direct HTTP RPC call to a Shelly device (fallback when core not available)."""
    try:
        resp = requests.post(
            f'http://{ip}/rpc',
            json={'id': 1, 'method': method, 'params': params or {}},
            timeout=timeout
        )
        if resp.status_code == 200:
            data = resp.json()
            if 'result' in data:
                return data['result']
            if 'error' in data:
                return {'_error': data['error'].get('message', 'RPC error')}
        return {'_error': f'HTTP {resp.status_code}'}
    except requests.exceptions.Timeout:
        return {'_error': 'Timeout'}
    except Exception as e:
        return {'_error': str(e)}


def _rpc(ip, method, params=None, timeout=5):
    """RPC call using core RpcClient if available, else fallback to HTTP."""
    from web.services import core_modules

    if core_modules.CORE_AVAILABLE and core_modules.RpcClient:
        try:
            rpc = core_modules.RpcClient(ip, timeout_s=float(timeout))
            return rpc.call(method, params or {})
        except Exception as e:
            return {'_error': str(e)}
    return _rpc_call(ip, method, params, timeout)


def _has_error(result):
    return isinstance(result, dict) and '_error' in result


# =========================================================================
# Health Check (Pro only)
# =========================================================================

@bp.route('/api/diagnostics/health-check', methods=['POST'])
def health_check():
    """Run a health check on all (or selected) devices.

    Collects: uptime, RAM, filesystem, temperature, WiFi RSSI,
    firmware version, eco_mode status.
    """
    if not is_pro():
        return jsonify({'success': False, 'error': 'Pro edition required'}), 403

    if not is_building_active():
        return jsonify({'success': False, 'error': 'No building active'}), 400

    device_manager.load_devices()
    devices = device_manager.devices

    data = request.get_json() or {}
    selected_macs = data.get('devices', [])

    if selected_macs:
        devices = [d for d in devices if d.get('id', '').upper() in
                   [m.upper() for m in selected_macs]]

    if not devices:
        return jsonify({'success': True, 'results': [], 'summary': {}})

    results = []

    def check_one(device):
        ip = device.get('ip')
        mac = device.get('id', '')
        name = device.get('friendly_name') or device.get('room', '') or ip or mac
        model = device.get('model', '')

        if not ip:
            return {'mac': mac, 'name': name, 'model': model, 'offline': True}

        entry = {
            'mac': mac,
            'ip': ip,
            'name': name,
            'model': model,
            'offline': False,
        }

        # Sys.GetStatus → uptime, RAM, FS, WiFi RSSI
        sys_status = _rpc(ip, 'Sys.GetStatus', timeout=5)
        if _has_error(sys_status):
            entry['offline'] = True
            entry['error'] = sys_status['_error']
            return entry

        entry['uptime'] = sys_status.get('uptime', 0)
        entry['ram_free'] = sys_status.get('ram_free', 0)
        entry['ram_size'] = sys_status.get('ram_size', 0)
        entry['fs_free'] = sys_status.get('fs_free', 0)
        entry['fs_size'] = sys_status.get('fs_size', 0)

        # Available updates
        entry['available_updates'] = sys_status.get('available_updates', {})

        # Wifi.GetStatus → RSSI, SSID, IP (separate call required,
        # Sys.GetStatus does NOT include wifi info)
        wifi_status = _rpc(ip, 'Wifi.GetStatus', timeout=3)
        if not _has_error(wifi_status):
            entry['wifi_rssi'] = wifi_status.get('rssi')
            entry['wifi_ssid'] = wifi_status.get('ssid', '')
            entry['wifi_ip'] = wifi_status.get('sta_ip', '')

        # Temperature: Shelly Gen2+ exposes device temp via component status,
        # NOT via Sys.GetStatus. Try Switch → Cover → Light in order.
        temp_c = None

        # First check Sys.GetStatus.temperature (some sensor devices)
        sys_temp = sys_status.get('temperature', {})
        if isinstance(sys_temp, dict) and sys_temp.get('tC') is not None:
            temp_c = sys_temp['tC']

        # Then try component statuses (where relay/dimmer devices report temp)
        if temp_c is None:
            for method in ('Switch.GetStatus', 'Cover.GetStatus', 'Light.GetStatus'):
                comp_status = _rpc(ip, method, {'id': 0}, timeout=2)
                if not _has_error(comp_status):
                    comp_temp = comp_status.get('temperature', {})
                    if isinstance(comp_temp, dict) and comp_temp.get('tC') is not None:
                        temp_c = comp_temp['tC']
                        break

        entry['temp_c'] = temp_c

        # Sys.GetConfig → eco_mode
        sys_config = _rpc(ip, 'Sys.GetConfig', timeout=3)
        if not _has_error(sys_config):
            device_cfg = sys_config.get('device', {})
            entry['eco_mode'] = device_cfg.get('eco_mode', False)
            entry['timezone'] = sys_config.get('location', {}).get('tz', '')

        # Eth.GetStatus (optional – only Pro devices)
        eth_status = _rpc(ip, 'Eth.GetStatus', timeout=2)
        if not _has_error(eth_status):
            entry['eth_ip'] = eth_status.get('ip')

        return entry

    # Parallel execution
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(check_one, d): d for d in devices}
        for future in as_completed(futures):
            try:
                results.append(future.result())
            except Exception:
                pass

    # Sort by IP for consistent display
    results.sort(key=lambda r: r.get('ip', ''))

    # Build summary
    total = len(results)
    online = sum(1 for r in results if not r.get('offline'))
    offline = total - online
    weak_wifi = sum(1 for r in results
                    if r.get('wifi_rssi') is not None and r['wifi_rssi'] < -70)
    hot = sum(1 for r in results
              if r.get('temp_c') is not None and r['temp_c'] > 85)
    has_update = sum(1 for r in results
                     if r.get('available_updates', {}).get('stable'))

    summary = {
        'total': total,
        'online': online,
        'offline': offline,
        'weak_wifi': weak_wifi,
        'hot_devices': hot,
        'updates_available': has_update,
    }

    return jsonify({'success': True, 'results': results, 'summary': summary})


# =========================================================================
# WiFi Scan (both editions)
# =========================================================================

@bp.route('/api/diagnostics/wifi-scan/<device_id>', methods=['POST'])
def wifi_scan(device_id):
    """Run Wifi.Scan on a specific device.

    Returns visible networks with RSSI, channel, security.
    """
    if not is_building_active():
        return jsonify({'success': False, 'error': 'No building active'}), 400

    device = device_manager.get_device(device_id)
    if not device:
        return jsonify({'success': False, 'error': 'Device not found'}), 404

    ip = device.get('ip')
    if not ip:
        return jsonify({'success': False, 'error': 'Device has no IP'}), 400

    result = _rpc(ip, 'Wifi.Scan', timeout=10)
    if _has_error(result):
        return jsonify({'success': False, 'error': result['_error']}), 500

    # result.results is the scan list
    networks = result.get('results', []) if isinstance(result, dict) else []

    # Sort by RSSI (strongest first)
    networks.sort(key=lambda n: n.get('rssi', -100), reverse=True)

    # Also get current WiFi config to highlight connected network
    wifi_status = _rpc(ip, 'Wifi.GetStatus', timeout=3)
    connected_ssid = ''
    if not _has_error(wifi_status):
        connected_ssid = wifi_status.get('ssid', '')

    return jsonify({
        'success': True,
        'networks': networks,
        'connected_ssid': connected_ssid,
        'device_ip': ip,
        'device_name': device.get('friendly_name', ip),
    })


# =========================================================================
# Network Config: Ethernet + ECO Mode (both editions)
# =========================================================================

@bp.route('/api/diagnostics/device/<device_id>/network', methods=['GET'])
def get_device_network(device_id):
    """Get Ethernet and ECO mode config for a device."""
    if not is_building_active():
        return jsonify({'success': False, 'error': 'No building active'}), 400

    device = device_manager.get_device(device_id)
    if not device:
        return jsonify({'success': False, 'error': 'Device not found'}), 404

    ip = device.get('ip')
    if not ip:
        return jsonify({'success': False, 'error': 'Device has no IP'}), 400

    result = {'success': True, 'has_ethernet': False, 'eco_mode': None}

    # Sys.GetConfig for eco_mode
    sys_config = _rpc(ip, 'Sys.GetConfig', timeout=5)
    if not _has_error(sys_config):
        result['eco_mode'] = sys_config.get('device', {}).get('eco_mode', False)

    # Eth.GetConfig (only available on Pro devices with Ethernet)
    eth_config = _rpc(ip, 'Eth.GetConfig', timeout=3)
    if not _has_error(eth_config):
        result['has_ethernet'] = True
        result['ethernet'] = {
            'enable': eth_config.get('enable', False),
            'ipv4mode': eth_config.get('ipv4mode', 'dhcp'),
            'ip': eth_config.get('ip'),
            'netmask': eth_config.get('netmask'),
            'gw': eth_config.get('gw'),
            'nameserver': eth_config.get('nameserver'),
        }

    return jsonify(result)


@bp.route('/api/diagnostics/device/<device_id>/network', methods=['PUT'])
def set_device_network(device_id):
    """Update Ethernet and/or ECO mode config."""
    if not is_building_active():
        return jsonify({'success': False, 'error': 'No building active'}), 400

    device = device_manager.get_device(device_id)
    if not device:
        return jsonify({'success': False, 'error': 'Device not found'}), 404

    ip = device.get('ip')
    if not ip:
        return jsonify({'success': False, 'error': 'Device has no IP'}), 400

    data = request.get_json() or {}
    results = {}

    # ECO mode
    if 'eco_mode' in data:
        res = _rpc(ip, 'Sys.SetConfig', {
            'config': {'device': {'eco_mode': bool(data['eco_mode'])}}
        })
        if _has_error(res):
            results['eco_mode'] = f"failed: {res['_error']}"
        else:
            results['eco_mode'] = 'updated'

    # Ethernet config
    if 'ethernet' in data:
        eth_data = data['ethernet']
        eth_config = {}
        if 'enable' in eth_data:
            eth_config['enable'] = bool(eth_data['enable'])
        if 'ipv4mode' in eth_data:
            eth_config['ipv4mode'] = eth_data['ipv4mode']
        if eth_data.get('ipv4mode') == 'static':
            for field in ('ip', 'netmask', 'gw', 'nameserver'):
                if field in eth_data and eth_data[field]:
                    eth_config[field] = eth_data[field]

        if eth_config:
            res = _rpc(ip, 'Eth.SetConfig', {'config': eth_config})
            if _has_error(res):
                results['ethernet'] = f"failed: {res['_error']}"
            else:
                results['ethernet'] = 'updated'
                if isinstance(res, dict) and res.get('restart_required'):
                    results['restart_required'] = True

    return jsonify({'success': True, 'results': results})


# =========================================================================
# Pro Ethernet — Scan & Switch
# =========================================================================

@bp.route('/api/pro-ethernet/scan', methods=['POST'])
def pro_ethernet_scan():
    """Scan all known devices for Ethernet link status.

    Returns devices that have an Ethernet cable plugged in and
    are currently running on WiFi (candidates for switching).
    """
    if not is_building_active():
        return jsonify({'success': False, 'error': 'No building active'}), 400

    device_manager.load_devices()
    devices = device_manager.devices

    if not devices:
        return jsonify({'success': True, 'devices': [], 'count': 0})

    candidates = []
    # Collect MACs that need ip_state.json correction
    state_corrections = []

    def check_eth(device):
        ip = device.get('ip')
        mac = device.get('id', '')
        name = device.get('friendly_name') or device.get('room', '') or ip or mac
        model = device.get('model', '')
        iface_stored = device.get('interface', 'wifi')

        if not ip:
            return None

        # Check Ethernet link status
        eth_status = _rpc(ip, 'Eth.GetStatus', timeout=3)
        if _has_error(eth_status):
            # Device has no Ethernet port → skip
            return None

        # Detect active Ethernet: either 'link' field is true,
        # or device has an Ethernet IP (some Pro models omit 'link')
        eth_ip = eth_status.get('ip', '')
        has_link = eth_status.get('link', False)

        if not has_link and not eth_ip:
            # No cable plugged in and no IP → skip
            return None

        # Determine ACTUAL interface state by checking WiFi
        wifi_status = _rpc(ip, 'Wifi.GetStatus', timeout=3)
        wifi_active = (not _has_error(wifi_status) and
                       bool(wifi_status.get('ssid')) and
                       wifi_status.get('rssi') is not None)

        # Real state: if Ethernet has IP and WiFi is not connected → running on Ethernet
        actually_ethernet = bool(eth_ip) and not wifi_active

        # Flag for ip_state.json correction if stored state differs
        if actually_ethernet and iface_stored != 'ethernet':
            state_corrections.append(mac)
        elif not actually_ethernet and iface_stored == 'ethernet':
            state_corrections.append(mac)

        return {
            'mac': mac,
            'ip': ip,
            'name': name,
            'model': model,
            'eth_link': True,
            'already_ethernet': actually_ethernet,
            'eth_ip': eth_ip,
            'wifi_active': wifi_active,
        }

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(check_eth, d): d for d in devices}
        for future in as_completed(futures):
            try:
                result = future.result()
                if result:
                    candidates.append(result)
            except Exception:
                pass

    # Auto-correct ip_state.json for devices where stored state != actual
    for mac in state_corrections:
        mac_upper = mac.upper().replace(':', '').replace('-', '')
        dev = device_manager.get_device(mac_upper)
        if dev:
            actual = 'ethernet' if any(
                c['mac'] == mac and c['already_ethernet'] for c in candidates
            ) else 'wifi'
            device_manager.update_device(mac_upper, {
                'interface': actual,
                'wifi_disabled': actual == 'ethernet',
            })

    # Sort by IP
    candidates.sort(key=lambda c: c.get('ip', ''))

    return jsonify({
        'success': True,
        'devices': candidates,
        'count': len(candidates),
    })


@bp.route('/api/pro-ethernet/switch', methods=['POST'])
def pro_ethernet_switch():
    """Switch selected Pro devices from WiFi to Ethernet.

    Safe 2-reboot strategy:
    Phase 1: Configure Ethernet (static IP = current WiFi IP), reboot
    Phase 2: Verify Ethernet works, then disable WiFi, reboot
    Phase 3: Final verification
    """
    import time

    if not is_building_active():
        return jsonify({'success': False, 'error': 'No building active'}), 400

    data = request.get_json() or {}
    mac_list = data.get('devices', [])

    if not mac_list:
        return jsonify({'success': False, 'error': 'No devices selected'}), 400

    # Load network config from building settings
    from web import config as app_config
    cfg = app_config.load_config()
    network = cfg.get('stage2', {}).get('network', {})
    gateway = network.get('gateway', '')
    if not gateway:
        # Auto-derive from pool_start
        pool_start = network.get('pool_start', '')
        if pool_start:
            gateway = '.'.join(pool_start.split('.')[:3]) + '.1'
    netmask = '255.255.255.0'
    nameserver = gateway

    if not gateway:
        return jsonify({'success': False, 'error': 'No gateway configured in building settings'}), 400

    device_manager.load_devices()
    results = []

    for mac in mac_list:
        mac_upper = mac.upper().replace(':', '').replace('-', '')
        device = device_manager.get_device(mac_upper)

        if not device:
            results.append({'mac': mac, 'status': 'error', 'phase': 'init',
                            'error': 'Device not found'})
            continue

        ip = device.get('ip')
        name = device.get('friendly_name') or ip or mac

        if not ip:
            results.append({'mac': mac, 'name': name, 'status': 'error',
                            'phase': 'init', 'error': 'No IP'})
            continue

        entry = {'mac': mac_upper, 'ip': ip, 'name': name, 'status': 'ok', 'phase': 'done'}

        # --- Phase 1: Configure Ethernet + Reboot #1 ---
        eth_cfg = _rpc(ip, 'Eth.SetConfig', {
            'config': {
                'enable': True,
                'ipv4mode': 'static',
                'ip': ip,
                'netmask': netmask,
                'gw': gateway,
                'nameserver': nameserver,
            }
        }, timeout=5)

        if _has_error(eth_cfg):
            entry['status'] = 'error'
            entry['phase'] = 'eth_config'
            entry['error'] = eth_cfg['_error']
            results.append(entry)
            continue

        # Reboot #1
        _rpc(ip, 'Shelly.Reboot', timeout=3)
        time.sleep(12)  # Wait for reboot

        # Wait for device to come back
        came_back = False
        for _ in range(15):
            test = _rpc(ip, 'Shelly.GetDeviceInfo', timeout=2)
            if not _has_error(test):
                came_back = True
                break
            time.sleep(2)

        if not came_back:
            entry['status'] = 'error'
            entry['phase'] = 'reboot1_timeout'
            entry['error'] = 'Device did not come back after first reboot'
            results.append(entry)
            continue

        # --- Phase 2: Verify Ethernet, then disable WiFi ---
        eth_status = _rpc(ip, 'Eth.GetStatus', timeout=3)
        eth_ok = (not _has_error(eth_status) and
                  eth_status.get('ip') == ip)

        if not eth_ok:
            # Rollback: disable Ethernet again
            _rpc(ip, 'Eth.SetConfig', {'config': {'enable': False}}, timeout=3)
            entry['status'] = 'error'
            entry['phase'] = 'eth_verify'
            entry['error'] = 'Ethernet did not get expected IP — rolled back'
            results.append(entry)
            continue

        # Ethernet verified — disable WiFi STA (primary + fallback)
        wifi_off = _rpc(ip, 'Wifi.SetConfig', {
            'config': {
                'sta': {'enable': False},
                'sta1': {'enable': False},
            }
        }, timeout=5)

        if _has_error(wifi_off):
            entry['status'] = 'error'
            entry['phase'] = 'wifi_disable'
            entry['error'] = wifi_off['_error']
            results.append(entry)
            continue

        # Reboot #2
        _rpc(ip, 'Shelly.Reboot', timeout=3)
        time.sleep(12)

        # --- Phase 3: Final verification ---
        final_ok = False
        for _ in range(15):
            test = _rpc(ip, 'Shelly.GetDeviceInfo', timeout=2)
            if not _has_error(test):
                final_ok = True
                break
            time.sleep(2)

        if not final_ok:
            entry['status'] = 'error'
            entry['phase'] = 'reboot2_timeout'
            entry['error'] = 'Device unreachable after WiFi disabled'
            results.append(entry)
            continue

        # Success — update ip_state.json
        device_manager.update_device(mac_upper, {
            'interface': 'ethernet',
            'wifi_disabled': True,
            'eth_switched_at': time.strftime('%Y-%m-%dT%H:%M:%SZ'),
        })

        entry['status'] = 'ok'
        entry['phase'] = 'done'
        results.append(entry)

    ok_count = sum(1 for r in results if r['status'] == 'ok')
    fail_count = len(results) - ok_count

    return jsonify({
        'success': True,
        'results': results,
        'switched': ok_count,
        'failed': fail_count,
    })


@bp.route('/api/pro-ethernet/revert', methods=['POST'])
def pro_ethernet_revert():
    """Revert selected devices from Ethernet back to WiFi.

    Phase 1: Re-enable WiFi STA + STA1, reboot
    Phase 2: Verify WiFi connected, disable Ethernet static, reboot
    Phase 3: Final verification
    """
    import time

    if not is_building_active():
        return jsonify({'success': False, 'error': 'No building active'}), 400

    data = request.get_json() or {}
    mac_list = data.get('devices', [])

    if not mac_list:
        return jsonify({'success': False, 'error': 'No devices selected'}), 400

    device_manager.load_devices()
    results = []

    for mac in mac_list:
        mac_upper = mac.upper().replace(':', '').replace('-', '')
        device = device_manager.get_device(mac_upper)

        if not device:
            results.append({'mac': mac, 'status': 'error', 'phase': 'init',
                            'error': 'Device not found'})
            continue

        ip = device.get('ip')
        name = device.get('friendly_name') or ip or mac

        if not ip:
            results.append({'mac': mac, 'name': name, 'status': 'error',
                            'phase': 'init', 'error': 'No IP'})
            continue

        entry = {'mac': mac_upper, 'ip': ip, 'name': name, 'status': 'ok', 'phase': 'done'}

        # --- Phase 1: Re-enable WiFi STA + STA1, reboot ---
        wifi_on = _rpc(ip, 'Wifi.SetConfig', {
            'config': {
                'sta': {'enable': True},
                'sta1': {'enable': True},
            }
        }, timeout=5)

        if _has_error(wifi_on):
            entry['status'] = 'error'
            entry['phase'] = 'wifi_enable'
            entry['error'] = wifi_on['_error']
            results.append(entry)
            continue

        # Reboot #1
        _rpc(ip, 'Shelly.Reboot', timeout=3)
        time.sleep(12)

        # Wait for device to come back
        came_back = False
        for _ in range(15):
            test = _rpc(ip, 'Shelly.GetDeviceInfo', timeout=2)
            if not _has_error(test):
                came_back = True
                break
            time.sleep(2)

        if not came_back:
            entry['status'] = 'error'
            entry['phase'] = 'reboot1_timeout'
            entry['error'] = 'Device did not come back after first reboot'
            results.append(entry)
            continue

        # --- Phase 2: Verify WiFi connected ---
        wifi_status = _rpc(ip, 'Wifi.GetStatus', timeout=3)
        wifi_ok = (not _has_error(wifi_status) and
                   wifi_status.get('ssid') and
                   wifi_status.get('rssi') is not None)

        if not wifi_ok:
            # Rollback: re-disable WiFi (leave Ethernet)
            _rpc(ip, 'Wifi.SetConfig', {
                'config': {'sta': {'enable': False}, 'sta1': {'enable': False}}
            }, timeout=3)
            entry['status'] = 'error'
            entry['phase'] = 'wifi_verify'
            entry['error'] = 'WiFi did not connect — rolled back'
            results.append(entry)
            continue

        # WiFi verified — disable Ethernet static, revert to DHCP
        _rpc(ip, 'Eth.SetConfig', {
            'config': {
                'enable': True,
                'ipv4mode': 'dhcp',
            }
        }, timeout=5)

        # Reboot #2
        _rpc(ip, 'Shelly.Reboot', timeout=3)
        time.sleep(12)

        # --- Phase 3: Final verification ---
        final_ok = False
        for _ in range(15):
            test = _rpc(ip, 'Shelly.GetDeviceInfo', timeout=2)
            if not _has_error(test):
                final_ok = True
                break
            time.sleep(2)

        if not final_ok:
            entry['status'] = 'error'
            entry['phase'] = 'reboot2_timeout'
            entry['error'] = 'Device unreachable after Ethernet reverted'
            results.append(entry)
            continue

        # Success — update ip_state.json
        device_manager.update_device(mac_upper, {
            'interface': 'wifi',
            'wifi_disabled': False,
            'eth_switched_at': '',
        })

        entry['status'] = 'ok'
        entry['phase'] = 'done'
        results.append(entry)

    ok_count = sum(1 for r in results if r['status'] == 'ok')
    fail_count = len(results) - ok_count

    return jsonify({
        'success': True,
        'results': results,
        'reverted': ok_count,
        'failed': fail_count,
    })
