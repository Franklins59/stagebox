"""
Stagebox Schedules Routes

Manage Shelly schedules - create templates, deploy to devices, check status.
Available in both editions.
"""

import json
import re
import time
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from flask import Blueprint, jsonify, request

from web import config
from web.services import device_manager, get_active_building

bp = Blueprint('schedules', __name__)

# Component-to-method mapping for schedule actions
COMPONENT_METHODS = {
    'switch': {
        'label': 'Switch',
        'methods': [
            {'method': 'Switch.Set', 'label': 'Set', 'params': [
                {'name': 'on', 'type': 'bool', 'label': 'On'}
            ]},
            {'method': 'Switch.Toggle', 'label': 'Toggle', 'params': []}
        ]
    },
    'cover': {
        'label': 'Cover',
        'methods': [
            {'method': 'Cover.Open', 'label': 'Open', 'params': []},
            {'method': 'Cover.Close', 'label': 'Close', 'params': []},
            {'method': 'Cover.Stop', 'label': 'Stop', 'params': []},
            {'method': 'Cover.GoToPosition', 'label': 'Go to position', 'params': [
                {'name': 'pos', 'type': 'int', 'label': 'Position (0-100)', 'min': 0, 'max': 100}
            ]}
        ]
    },
    'light': {
        'label': 'Light',
        'methods': [
            {'method': 'Light.Set', 'label': 'Set', 'params': [
                {'name': 'on', 'type': 'bool', 'label': 'On'},
                {'name': 'brightness', 'type': 'int', 'label': 'Brightness (0-100)',
                 'min': 0, 'max': 100, 'optional': True}
            ]},
            {'method': 'Light.Toggle', 'label': 'Toggle', 'params': []}
        ]
    },
    'input': {
        'label': 'Input',
        'i4_only': True,
        'methods': [
            {'method': 'Input.Trigger', 'label': 'Trigger', 'params': [
                {'name': 'event_type', 'type': 'select', 'label': 'Event type',
                 'options': [
                     {'value': 'single_push', 'label': 'Single push'},
                     {'value': 'double_push', 'label': 'Double push'},
                     {'value': 'triple_push', 'label': 'Triple push'},
                     {'value': 'long_push', 'label': 'Long push'}
                 ]}
            ]}
        ]
    }
}


def get_schedules_dir():
    """Get the schedules directory for the active building."""
    active = get_active_building()
    if not active:
        return None
    return config.DATA_DIR / 'schedules' if config.DATA_DIR else None


# ===========================================================================
# Schedule Template CRUD
# ===========================================================================

@bp.route('/api/schedules/templates', methods=['GET'])
def list_templates():
    """List saved schedule templates from data/schedules/."""
    schedules_dir = get_schedules_dir()

    if not schedules_dir:
        return jsonify({'success': False, 'error': 'No building active'})

    templates = []

    if schedules_dir.exists():
        for f in sorted(schedules_dir.glob('*.json')):
            try:
                data = json.loads(f.read_text(encoding='utf-8'))
                templates.append({
                    'filename': f.name,
                    'name': data.get('name', f.stem),
                    'description': data.get('description', ''),
                    'mode': data.get('mode', 'basic'),
                    'timespec': data.get('schedule', {}).get('timespec', ''),
                    'enable': data.get('schedule', {}).get('enable', True),
                    'calls_count': len(data.get('schedule', {}).get('calls', [])),
                    'required_components': data.get('required_components', []),
                    'created': data.get('created', '')
                })
            except Exception:
                pass

    return jsonify({'success': True, 'templates': templates})


@bp.route('/api/schedules/templates/<filename>', methods=['GET'])
def get_template(filename):
    """Get a single schedule template by filename."""
    schedules_dir = get_schedules_dir()

    if not schedules_dir:
        return jsonify({'success': False, 'error': 'No building active'})

    if not re.match(r'^[a-zA-Z0-9_.-]+\.json$', filename):
        return jsonify({'success': False, 'error': 'Invalid filename'}), 400

    filepath = schedules_dir / filename
    if not filepath.exists():
        return jsonify({'success': False, 'error': 'Template not found'}), 404

    try:
        data = json.loads(filepath.read_text(encoding='utf-8'))
        return jsonify({'success': True, 'template': data, 'filename': filename})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/schedules/templates', methods=['POST'])
def save_template():
    """Save a schedule template to data/schedules/."""
    schedules_dir = get_schedules_dir()

    if not schedules_dir:
        return jsonify({'success': False, 'error': 'No building active'})

    data = request.get_json() or {}
    name = data.get('name', '').strip()
    if not name:
        return jsonify({'success': False, 'error': 'Name is required'}), 400

    # Build template structure
    template = {
        'name': name,
        'description': data.get('description', ''),
        'mode': data.get('mode', 'basic'),
        'required_components': data.get('required_components', []),
        'ref_device': data.get('ref_device'),
        'created': data.get('created', datetime.now().isoformat()),
        'schedule': {
            'enable': data.get('enable', True),
            'timespec': data.get('timespec', ''),
            'calls': data.get('calls', [])
        }
    }

    # Generate safe filename
    safe_name = re.sub(r'[^a-zA-Z0-9_-]', '_', name)[:50]
    filename = data.get('filename', f'{safe_name}.json')

    if not re.match(r'^[a-zA-Z0-9_.-]+\.json$', filename):
        filename = f'{safe_name}.json'

    schedules_dir.mkdir(parents=True, exist_ok=True)
    filepath = schedules_dir / filename

    try:
        filepath.write_text(json.dumps(template, indent=2), encoding='utf-8')
        return jsonify({'success': True, 'filename': filename})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/schedules/templates/delete', methods=['POST'])
def delete_template():
    """Delete a schedule template from data/schedules/."""
    schedules_dir = get_schedules_dir()

    if not schedules_dir:
        return jsonify({'success': False, 'error': 'No building active'})

    data = request.get_json() or {}
    filename = data.get('filename', '')

    if not re.match(r'^[a-zA-Z0-9_.-]+\.json$', filename):
        return jsonify({'success': False, 'error': 'Invalid filename'}), 400

    filepath = schedules_dir / filename
    if not filepath.exists():
        return jsonify({'success': False, 'error': 'Template not found'}), 404

    try:
        filepath.unlink()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ===========================================================================
# Device Component Discovery
# ===========================================================================

@bp.route('/api/schedules/components/<device_id>', methods=['GET'])
def get_device_components(device_id):
    """Get available components from a device for schedule action building.

    Queries Shelly.GetConfig and returns components that can be used
    in schedule calls (Switch, Cover, Light, etc.).
    """
    device = device_manager.get_device(device_id)
    if not device:
        return jsonify({'success': False, 'error': 'Device not found'}), 404

    ip = device.get('ip')
    if not ip:
        return jsonify({'success': False, 'error': 'No IP'}), 400

    try:
        resp = requests.get(f'http://{ip}/rpc/Shelly.GetConfig', timeout=5)
        if resp.status_code != 200:
            return jsonify({'success': False, 'error': f'GetConfig failed: {resp.status_code}'})

        cfg = resp.json()
        components = []

        # Detect component types present
        found_types = set()
        for key in cfg:
            match = re.match(r'^(switch|cover|light|input):(\d+)$', key)
            if match:
                found_types.add(match.group(1))

        # Device is I4 if it has inputs but no switch/cover/light
        is_i4 = 'input' in found_types and not found_types.intersection({'switch', 'cover', 'light'})

        # Detect components from config keys
        for key in cfg:
            # Match patterns like "switch:0", "cover:0", "light:0", "input:0"
            match = re.match(r'^(switch|cover|light|input):(\d+)$', key)
            if match:
                comp_type = match.group(1)
                comp_id = int(match.group(2))
                comp_name = cfg[key].get('name', '') or f'{comp_type.capitalize()}:{comp_id}'

                if comp_type in COMPONENT_METHODS:
                    comp_def = COMPONENT_METHODS[comp_type]

                    # Skip I4-only components on non-I4 devices
                    if comp_def.get('i4_only') and not is_i4:
                        continue

                    components.append({
                        'type': comp_type,
                        'id': comp_id,
                        'name': comp_name,
                        'label': f'{comp_def["label"]}:{comp_id} - {comp_name}',
                        'methods': comp_def['methods']
                    })

        return jsonify({'success': True, 'components': components})

    except requests.exceptions.Timeout:
        return jsonify({'success': False, 'error': 'Device timeout'}), 504
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ===========================================================================
# Deploy Schedule to Devices
# ===========================================================================

@bp.route('/api/schedules/deploy', methods=['POST'])
def deploy_schedule():
    """Deploy a schedule template to multiple devices via Schedule.Create."""
    data = request.get_json() or {}
    filename = data.get('filename')
    device_macs = data.get('devices', [])

    if not filename:
        return jsonify({'success': False, 'error': 'No template specified'})

    if not device_macs:
        return jsonify({'success': False, 'error': 'No devices specified'})

    # Load template
    schedules_dir = get_schedules_dir()
    if not schedules_dir:
        return jsonify({'success': False, 'error': 'No building active'})

    filepath = schedules_dir / filename
    if not filepath.exists():
        return jsonify({'success': False, 'error': 'Template not found'})

    try:
        template = json.loads(filepath.read_text(encoding='utf-8'))
    except Exception as e:
        return jsonify({'success': False, 'error': f'Failed to read template: {e}'})

    schedule_data = template.get('schedule', {})
    required_components = template.get('required_components', [])

    # Validate: Shelly requires at least one call
    if not schedule_data.get('calls'):
        return jsonify({'success': False, 'error': 'Template has no actions. Edit and add at least one action.'})

    # Validate timespec format
    timespec = schedule_data.get('timespec', '')
    if not timespec:
        return jsonify({'success': False, 'error': 'Template has no timespec.'})

    if timespec.startswith('@'):
        # Solar format: @sunrise/@sunset with optional offset like +5m, -1h30m
        if not re.match(r'^@(sunrise|sunset)([+-][\dh.m]+)?\s+', timespec):
            return jsonify({'success': False, 'error': f'Invalid solar timespec: {timespec}. Expected: @sunrise or @sunset with optional +Xm/-Xh offset'})
    else:
        parts = timespec.split()
        if len(parts) != 6:
            return jsonify({'success': False, 'error': f'Invalid timespec: {timespec}. Must have 6 fields: sec min hour day month weekday'})
        if any('@' in p for p in parts):
            return jsonify({'success': False, 'error': f'Invalid timespec: {timespec}. Use @sunrise/@sunset at the start, not inside cron fields.'})

    results = []

    def deploy_to_device(mac):
        device = device_manager.get_device(mac)
        if not device:
            return {'device': mac, 'success': False, 'error': 'Device not found'}

        ip = device.get('ip')
        if not ip:
            return {'device': mac, 'success': False, 'error': 'No IP'}

        try:
            # Check compatibility: verify each call's component:id exists on target
            calls = schedule_data.get('calls', [])
            if calls:
                cfg_resp = requests.get(f'http://{ip}/rpc/Shelly.GetConfig', timeout=5)
                if cfg_resp.status_code == 200:
                    cfg = cfg_resp.json()

                    # Build set of available component:id pairs
                    available = set()  # e.g. {'switch:0', 'switch:1', 'cover:0', 'input:0'}
                    cfg_types = set()
                    for key in cfg:
                        match = re.match(r'^(switch|cover|light|input):(\d+)$', key)
                        if match:
                            available.add(key)
                            cfg_types.add(match.group(1))

                    # Check each call's target component exists
                    for call in calls:
                        method = call.get('method', '')
                        comp_type = method.split('.')[0].lower()  # 'Switch.Set' -> 'switch'
                        comp_id = call.get('params', {}).get('id', 0)
                        comp_key = f'{comp_type}:{comp_id}'

                        if comp_key not in available:
                            return {
                                'device': mac, 'ip': ip, 'success': False,
                                'error': f'Incompatible: {comp_key} not found on device'
                            }

                        # Input.Trigger only works on I4 devices
                        if method == 'Input.Trigger':
                            is_i4 = 'input' in cfg_types and not cfg_types.intersection({'switch', 'cover', 'light'})
                            if not is_i4:
                                return {
                                    'device': mac, 'ip': ip, 'success': False,
                                    'error': 'Input.Trigger only supported on I4 devices'
                                }

            # Create schedule via RPC
            resp = requests.post(
                f'http://{ip}/rpc/Schedule.Create',
                json=schedule_data,
                timeout=5
            )

            if resp.status_code != 200:
                error = resp.text[:100]
                return {'device': mac, 'ip': ip, 'success': False, 'error': error}

            result = resp.json()
            sched_id = result.get('id', '?')
            return {
                'device': mac, 'ip': ip, 'success': True,
                'message': f'Schedule ID {sched_id}'
            }

        except requests.exceptions.Timeout:
            return {'device': mac, 'ip': ip, 'success': False, 'error': 'Timeout'}
        except Exception as e:
            return {'device': mac, 'ip': ip, 'success': False, 'error': str(e)}

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(deploy_to_device, mac): mac for mac in device_macs}
        for future in as_completed(futures):
            results.append(future.result())

    return jsonify({'success': True, 'results': results})


# ===========================================================================
# Schedule Status (List from devices)
# ===========================================================================

@bp.route('/api/schedules/status', methods=['POST'])
def schedule_status():
    """List schedules from multiple devices via Schedule.List."""
    data = request.get_json() or {}
    device_macs = data.get('devices', [])

    if not device_macs:
        return jsonify({'success': False, 'error': 'No devices specified'})

    results = []

    def get_status(mac):
        device = device_manager.get_device(mac)
        if not device:
            return {'device': mac, 'success': False, 'error': 'Device not found'}

        ip = device.get('ip')
        if not ip:
            return {'device': mac, 'success': False, 'error': 'No IP'}

        try:
            resp = requests.post(
                f'http://{ip}/rpc/Schedule.List',
                json={},
                timeout=5
            )
            if resp.status_code != 200:
                return {'device': mac, 'ip': ip, 'success': False, 'error': 'Schedule.List failed'}

            jobs = resp.json().get('jobs', [])
            schedules = []
            for job in jobs:
                calls_summary = []
                for c in job.get('calls', []):
                    calls_summary.append(c.get('method', '?'))
                schedules.append({
                    'id': job.get('id'),
                    'enable': job.get('enable', False),
                    'timespec': job.get('timespec', ''),
                    'calls': calls_summary
                })

            return {
                'device': mac, 'ip': ip, 'success': True,
                'schedules': schedules
            }

        except requests.exceptions.Timeout:
            return {'device': mac, 'ip': ip, 'success': False, 'error': 'Timeout'}
        except Exception as e:
            return {'device': mac, 'ip': ip, 'success': False, 'error': str(e)}

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(get_status, mac): mac for mac in device_macs}
        for future in as_completed(futures):
            results.append(future.result())

    return jsonify({'success': True, 'results': results})


# ===========================================================================
# Update Schedule (Enable/Disable)
# ===========================================================================

@bp.route('/api/schedules/update', methods=['POST'])
def update_schedule():
    """Enable or disable a single schedule on a device via Schedule.Update."""
    data = request.get_json() or {}
    device_mac = data.get('device')
    schedule_id = data.get('schedule_id')
    enable = data.get('enable')

    if not device_mac:
        return jsonify({'success': False, 'error': 'No device specified'})

    if schedule_id is None:
        return jsonify({'success': False, 'error': 'No schedule_id specified'})

    device = device_manager.get_device(device_mac)
    if not device:
        return jsonify({'success': False, 'error': 'Device not found'})

    ip = device.get('ip')
    if not ip:
        return jsonify({'success': False, 'error': 'No IP'})

    try:
        resp = requests.post(
            f'http://{ip}/rpc/Schedule.Update',
            json={'id': int(schedule_id), 'enable': bool(enable)},
            timeout=5
        )
        if resp.status_code == 200:
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': resp.text[:100]})
    except requests.exceptions.Timeout:
        return jsonify({'success': False, 'error': 'Timeout'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


# ===========================================================================
# Delete Schedules from Devices
# ===========================================================================

@bp.route('/api/schedules/delete', methods=['POST'])
def delete_schedules():
    """Delete schedules from multiple devices.

    Supports delete_all=true to remove all schedules,
    or schedule_id to delete a specific one.
    """
    data = request.get_json() or {}
    device_macs = data.get('devices', [])
    delete_all = data.get('delete_all', False)
    schedule_id = data.get('schedule_id')

    if not device_macs:
        return jsonify({'success': False, 'error': 'No devices specified'})

    results = []

    def delete_from_device(mac):
        device = device_manager.get_device(mac)
        if not device:
            return {'device': mac, 'success': False, 'error': 'Device not found'}

        ip = device.get('ip')
        if not ip:
            return {'device': mac, 'success': False, 'error': 'No IP'}

        try:
            if delete_all:
                # Delete all schedules
                resp = requests.post(
                    f'http://{ip}/rpc/Schedule.DeleteAll',
                    json={},
                    timeout=5
                )
                if resp.status_code == 200:
                    return {'device': mac, 'ip': ip, 'success': True, 'message': 'All deleted'}
                else:
                    return {'device': mac, 'ip': ip, 'success': False, 'error': resp.text[:100]}

            elif schedule_id is not None:
                # Delete specific schedule
                resp = requests.post(
                    f'http://{ip}/rpc/Schedule.Delete',
                    json={'id': int(schedule_id)},
                    timeout=5
                )
                if resp.status_code == 200:
                    return {'device': mac, 'ip': ip, 'success': True, 'message': f'ID {schedule_id} deleted'}
                else:
                    return {'device': mac, 'ip': ip, 'success': False, 'error': resp.text[:100]}

            else:
                return {'device': mac, 'ip': ip, 'success': False, 'error': 'No target specified'}

        except requests.exceptions.Timeout:
            return {'device': mac, 'ip': ip, 'success': False, 'error': 'Timeout'}
        except Exception as e:
            return {'device': mac, 'ip': ip, 'success': False, 'error': str(e)}

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(delete_from_device, mac): mac for mac in device_macs}
        for future in as_completed(futures):
            results.append(future.result())

    return jsonify({'success': True, 'results': results})
