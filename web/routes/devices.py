"""
Stagebox Device Routes

Device CRUD operations, KVS, webhooks, settings.
Available in both editions.
"""

import json
from flask import Blueprint, jsonify, request, Response

from web import config
from web.edition import is_pro, get_device_limit
from web.services import device_manager, is_building_active, get_active_building
from web.utils import escape_csv

bp = Blueprint('devices', __name__)


@bp.route('/api/devices', methods=['GET'])
def get_devices():
    """Get all devices."""
    if not is_building_active():
        return jsonify({'success': False, 'error': 'No building active'}), 400
    
    device_manager.load_devices()
    
    devices = device_manager.devices
    device_limit = get_device_limit()
    
    response = {
        'success': True,
        'devices': devices,
        'count': len(devices),
    }
    
    if device_limit > 0 and len(devices) > device_limit:
        response['warning'] = f'Device limit exceeded ({len(devices)}/{device_limit})'
        response['device_limit'] = device_limit
    
    return jsonify(response)


@bp.route('/api/devices/<device_id>', methods=['GET'])
def get_device(device_id):
    """Get single device details."""
    device = device_manager.get_device(device_id)
    if device:
        return jsonify({'success': True, 'device': device})
    return jsonify({'success': False, 'error': 'Device not found'}), 404


@bp.route('/api/devices/<device_id>', methods=['DELETE'])
def delete_device(device_id):
    """Remove a device from ip_state.json.
    
    This only removes the device from Stagebox tracking,
    it does not affect the actual Shelly device.
    """
    # Ensure devices are loaded
    device_manager.load_devices()
    
    device = device_manager.get_device(device_id)
    if not device:
        return jsonify({'success': False, 'error': 'Device not found'}), 404
    
    if device_manager.delete_device(device_id):
        return jsonify({'success': True, 'message': 'Device removed'})
    return jsonify({'success': False, 'error': 'Failed to remove device'}), 500


@bp.route('/api/devices/<device_id>', methods=['PUT'])
def update_device_route(device_id):
    """Update device metadata."""
    data = request.get_json()
    if device_manager.update_device(device_id, data):
        return jsonify({'success': True, 'message': 'Device updated'})
    return jsonify({'success': False, 'error': 'Update failed'}), 400


@bp.route('/api/devices/<device_id>/config', methods=['PUT'])
def update_device_config(device_id):
    """Update device config via RPC.
    
    When updating labels (room, location), also updates the Shelly device.name
    in the format: {ip_short} {room} {location}
    Example: "50.41 Wohnzimmer SS Türe"
    """
    from web.services import core_modules
    
    device = device_manager.get_device(device_id)
    if not device:
        return jsonify({'success': False, 'error': 'Device not found'}), 404
    
    ip = device.get('ip')
    if not ip:
        return jsonify({'success': False, 'error': 'Device has no IP'}), 400
    
    if not core_modules.CORE_AVAILABLE or not core_modules.RpcClient:
        return jsonify({'success': False, 'error': 'Core not available'}), 500
    
    data = request.get_json() or {}
    
    try:
        rpc = core_modules.RpcClient(ip, timeout_s=5.0)
        
        # Set Shelly device.name from friendly_name (sanitized for HomeAssistant)
        shelly_name = None
        if 'shelly_label' in data:
            # Direct label override (already sanitized by caller)
            shelly_name = data['shelly_label']
        elif 'friendly_name' in data:
            # Sanitize friendly_name for HA compatibility
            friendly_name = data.get('friendly_name', '')
            if friendly_name:
                shelly_name = sanitize_ha_name(friendly_name)
        
        if shelly_name:
            rpc.call('Sys.SetConfig', {
                'config': {
                    'device': {'name': shelly_name}
                }
            })
        
        return jsonify({'success': True, 'message': 'Config updated', 'shelly_name': shelly_name})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


def sanitize_ha_name(name):
    """Sanitize name for HomeAssistant compatibility."""
    import re
    # Replace common problematic chars
    name = name.replace('ä', 'ae').replace('ö', 'oe').replace('ü', 'ue')
    name = name.replace('Ä', 'Ae').replace('Ö', 'Oe').replace('Ü', 'Ue')
    name = name.replace('ß', 'ss')
    # Remove any remaining non-ASCII
    name = re.sub(r'[^\x00-\x7F]+', '', name)
    return name.strip()


@bp.route('/api/devices/<device_id>/settings', methods=['GET'])
def get_device_settings(device_id):
    """Get device component settings (Switch, Cover, Input, Light/Dimmer)."""
    from web.services import core_modules
    
    device = device_manager.get_device(device_id)
    if not device:
        return jsonify({'success': False, 'error': 'Device not found'}), 404
    
    ip = device.get('ip')
    if not ip:
        return jsonify({'success': False, 'error': 'Device has no IP'}), 400
    
    if not core_modules.CORE_AVAILABLE or not core_modules.RpcClient:
        return jsonify({'success': False, 'error': 'Core not available'}), 500
    
    try:
        rpc = core_modules.RpcClient(ip, timeout_s=5.0)
        
        # Get device info to determine type
        device_info = rpc.call('Shelly.GetDeviceInfo')
        shelly_profile = device_info.get('profile')  # 'switch' or 'cover' for 2PM
        
        result = {
            'success': True,
            'device_type': shelly_profile or 'switch',
            'switch': None,
            'cover': None,
            'light': None,
            'inputs': [],
            'input_mode_source': 'input',  # 'input' or 'switch' - where to read/write input mode
        }
        
        # Try to get Switch config
        try:
            switch_config = rpc.call('Switch.GetConfig', {'id': 0})
            result['switch'] = {
                'name': switch_config.get('name', ''),
                'initial_state': switch_config.get('initial_state', 'off'),
                'auto_on': switch_config.get('auto_on', False),
                'auto_on_delay': switch_config.get('auto_on_delay', 60),
                'auto_off': switch_config.get('auto_off', False),
                'auto_off_delay': switch_config.get('auto_off_delay', 60),
                'in_mode': switch_config.get('in_mode', 'momentary'),
                # Protections (may not exist on all devices)
                'power_limit': switch_config.get('power_limit'),
                'voltage_limit': switch_config.get('voltage_limit'),
                'undervoltage_limit': switch_config.get('undervoltage_limit'),
                'current_limit': switch_config.get('current_limit'),
            }
            # If device has switch component, input mode is controlled via switch.in_mode
            result['input_mode_source'] = 'switch'
        except:
            pass  # Device might not have Switch component
        
        # Try to get Cover config
        try:
            cover_config = rpc.call('Cover.GetConfig', {'id': 0})
            obstruction = cover_config.get('obstruction_detection', {})
            slat = cover_config.get('slat_control', {})
            result['cover'] = {
                'name': cover_config.get('name', ''),
                'maxtime_open': cover_config.get('maxtime_open', 60),
                'maxtime_close': cover_config.get('maxtime_close', 60),
                'swap_inputs': cover_config.get('swap_inputs', False),
                'invert_directions': cover_config.get('invert_directions', False),
                'initial_state': cover_config.get('initial_state', 'stopped'),
                # Obstruction detection
                'obstruction_enable': obstruction.get('enable', False),
                'obstruction_direction': obstruction.get('direction', 'both'),
                'obstruction_action': obstruction.get('action', 'stop'),
                'obstruction_power_thr': obstruction.get('power_thr', -1),
                # Slat control (Venetian blinds)
                'slat_enable': slat.get('enable', False) if slat else False,
                'slat_open_time': slat.get('open_time', 1.5) if slat else 1.5,
                'slat_close_time': slat.get('close_time', 1.5) if slat else 1.5,
                'slat_step': slat.get('step', 5) if slat else 5,
                # Protections (may not exist on all devices)
                'power_limit': cover_config.get('power_limit'),
                'voltage_limit': cover_config.get('voltage_limit'),
                'undervoltage_limit': cover_config.get('undervoltage_limit'),
                'current_limit': cover_config.get('current_limit'),
            }
            # Also get Cover status for calibration info
            try:
                cover_status = rpc.call('Cover.GetStatus', {'id': 0})
                result['cover']['pos_control'] = cover_status.get('pos_control', False)
                result['cover']['current_pos'] = cover_status.get('current_pos')
                result['cover']['state'] = cover_status.get('state', 'stopped')
            except:
                result['cover']['pos_control'] = None
                result['cover']['current_pos'] = None
                result['cover']['state'] = None
        except:
            pass  # Device might not have Cover component
        
        # Try to get Light/Dimmer config
        try:
            light_config = rpc.call('Light.GetConfig', {'id': 0})
            result['light'] = {
                'name': light_config.get('name', ''),
                'initial_state': light_config.get('initial_state', 'off'),
                'auto_on': light_config.get('auto_on', False),
                'auto_on_delay': light_config.get('auto_on_delay', 60),
                'auto_off': light_config.get('auto_off', False),
                'auto_off_delay': light_config.get('auto_off_delay', 60),
                'default_brightness': light_config.get('default', {}).get('brightness', 100),
                'night_mode_enable': light_config.get('night_mode', {}).get('enable', False),
                'night_mode_brightness': light_config.get('night_mode', {}).get('brightness', 50),
                'night_mode_active_between': light_config.get('night_mode', {}).get('active_between', []),
                'min_brightness_on_toggle': light_config.get('min_brightness_on_toggle', 0),
                'transition_duration': light_config.get('transition_duration', 0),
                'button_fade_rate': light_config.get('button_fade_rate', 3),
                # Input mode (dim/follow/flip/activate)
                'in_mode': light_config.get('in_mode', 'dim'),
                # Range map (min/max brightness)
                'range_map': light_config.get('range_map', [0, 100]),
                # Protections
                'current_limit': light_config.get('current_limit'),
                'power_limit': light_config.get('power_limit'),
                'voltage_limit': light_config.get('voltage_limit'),
                'undervoltage_limit': light_config.get('undervoltage_limit'),
            }
            # Get Light status for calibration info
            try:
                light_status = rpc.call('Light.GetStatus', {'id': 0})
                result['light']['calibrating'] = light_status.get('calibrating', False)
                result['light']['calib_progress'] = light_status.get('calib_progress')
            except:
                result['light']['calibrating'] = None
            # Dimmer: in_mode is controlled via Light component, not Switch
            result['input_mode_source'] = 'light'
        except:
            pass  # Device might not have Light component
        
        # Try to get Input configs (up to 4 inputs)
        for input_id in range(4):
            try:
                input_config = rpc.call('Input.GetConfig', {'id': input_id})
                result['inputs'].append({
                    'id': input_id,
                    'name': input_config.get('name', ''),
                    'type': input_config.get('type', 'button'),
                    'invert': input_config.get('invert', False),
                })
            except:
                break  # No more inputs
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/devices/<device_id>/settings', methods=['PUT'])
def update_device_settings(device_id):
    """Update device component settings (Switch, Cover, Input, Light/Dimmer)."""
    from web.services import core_modules
    
    device = device_manager.get_device(device_id)
    if not device:
        return jsonify({'success': False, 'error': 'Device not found'}), 404
    
    ip = device.get('ip')
    if not ip:
        return jsonify({'success': False, 'error': 'Device has no IP'}), 400
    
    if not core_modules.CORE_AVAILABLE or not core_modules.RpcClient:
        return jsonify({'success': False, 'error': 'Core not available'}), 500
    
    data = request.get_json() or {}
    
    try:
        rpc = core_modules.RpcClient(ip, timeout_s=5.0)
        results = {'switch': None, 'cover': None, 'light': None, 'inputs': []}
        
        # Check if we need to change in_mode (for Minis)
        # For Minis, Input.type and Switch.in_mode must be in sync!
        # We need to set Input.type FIRST, then Switch.in_mode
        in_mode_to_set = None
        input_type_to_set = None
        input_mode_source = data.get('inputModeSource', 'input')
        
        if 'inputs' in data and data['inputs']:
            if input_mode_source == 'switch':
                for input_data in data['inputs']:
                    if 'type' in input_data:
                        # Map UI type to both Input.type and Switch.in_mode
                        if input_data['type'] == 'switch':
                            input_type_to_set = 'switch'
                            in_mode_to_set = 'follow'
                        else:  # button
                            input_type_to_set = 'button'
                            in_mode_to_set = 'momentary'
                        break
        
        # For Minis: Set Input.type FIRST to unlock Switch.SetConfig
        if input_type_to_set and input_mode_source == 'switch':
            try:
                resp = rpc.call('Input.SetConfig', {'id': 0, 'config': {'type': input_type_to_set}})
                results['inputs'].append(f'input:0 type set to {input_type_to_set}')
                if isinstance(resp, dict) and resp.get('restart_required'):
                    results['restart_required'] = True
            except Exception as e:
                results['inputs'].append(f'input:0 type failed: {str(e)}')
        
        # Update Switch settings (WITHOUT in_mode yet - that comes after)
        # For Minis (input_mode_source == 'switch'), skip initial_state as it's not supported
        if 'switch' in data and data['switch']:
            switch_data = data['switch']
            switch_config = {}
            
            # Switch name (sanitized for HA compatibility)
            if 'name' in switch_data:
                switch_config['name'] = sanitize_ha_name(switch_data['name'])
            # initial_state is not supported on Minis - only send for other devices
            if 'initial_state' in switch_data and input_mode_source != 'switch':
                switch_config['initial_state'] = switch_data['initial_state']
            if 'auto_on' in switch_data:
                switch_config['auto_on'] = switch_data['auto_on']
            if 'auto_on_delay' in switch_data:
                switch_config['auto_on_delay'] = float(switch_data['auto_on_delay'])
            if 'auto_off' in switch_data:
                switch_config['auto_off'] = switch_data['auto_off']
            if 'auto_off_delay' in switch_data:
                switch_config['auto_off_delay'] = float(switch_data['auto_off_delay'])
            # Protections
            if 'power_limit' in switch_data and switch_data['power_limit'] is not None:
                switch_config['power_limit'] = int(switch_data['power_limit'])
            if 'voltage_limit' in switch_data and switch_data['voltage_limit'] is not None:
                switch_config['voltage_limit'] = int(switch_data['voltage_limit'])
            if 'undervoltage_limit' in switch_data and switch_data['undervoltage_limit'] is not None:
                switch_config['undervoltage_limit'] = int(switch_data['undervoltage_limit'])
            if 'current_limit' in switch_data and switch_data['current_limit'] is not None:
                switch_config['current_limit'] = float(switch_data['current_limit'])
            
            if switch_config:
                try:
                    resp = rpc.call('Switch.SetConfig', {'id': 0, 'config': switch_config})
                    results['switch'] = 'updated'
                    if isinstance(resp, dict) and resp.get('restart_required'):
                        results['restart_required'] = True
                except Exception as e:
                    results['switch'] = f'failed: {str(e)}'
        
        # Now set in_mode separately if needed (for Minis)
        if in_mode_to_set and input_mode_source == 'switch':
            try:
                rpc.call('Switch.SetConfig', {'id': 0, 'config': {'in_mode': in_mode_to_set}})
                results['inputs'].append(f'switch in_mode set to {in_mode_to_set}')
            except Exception as e:
                results['inputs'].append(f'switch in_mode failed: {str(e)}')
        
        # Update Cover settings
        if 'cover' in data and data['cover']:
            cover_data = data['cover']
            cover_config = {}
            
            # Cover name (sanitized for HA compatibility)
            if 'name' in cover_data:
                cover_config['name'] = sanitize_ha_name(cover_data['name'])
            if 'maxtime_open' in cover_data:
                cover_config['maxtime_open'] = float(cover_data['maxtime_open'])
            if 'maxtime_close' in cover_data:
                cover_config['maxtime_close'] = float(cover_data['maxtime_close'])
            if 'swap_inputs' in cover_data:
                cover_config['swap_inputs'] = cover_data['swap_inputs']
            if 'invert_directions' in cover_data:
                cover_config['invert_directions'] = cover_data['invert_directions']
            if 'initial_state' in cover_data:
                cover_config['initial_state'] = cover_data['initial_state']
            
            # Obstruction detection
            obstruction_keys = ['obstruction_enable', 'obstruction_direction', 'obstruction_action', 'obstruction_power_thr']
            if any(k in cover_data for k in obstruction_keys):
                obstruction = {}
                if 'obstruction_enable' in cover_data:
                    obstruction['enable'] = cover_data['obstruction_enable']
                if 'obstruction_direction' in cover_data:
                    obstruction['direction'] = cover_data['obstruction_direction']
                if 'obstruction_action' in cover_data:
                    obstruction['action'] = cover_data['obstruction_action']
                if 'obstruction_power_thr' in cover_data:
                    obstruction['power_thr'] = float(cover_data['obstruction_power_thr'])
                cover_config['obstruction_detection'] = obstruction
            
            # Slat control (Venetian blinds)
            slat_keys = ['slat_enable', 'slat_open_time', 'slat_close_time', 'slat_step']
            if any(k in cover_data for k in slat_keys):
                slat = {}
                if 'slat_enable' in cover_data:
                    slat['enable'] = cover_data['slat_enable']
                if 'slat_open_time' in cover_data:
                    slat['open_time'] = float(cover_data['slat_open_time'])
                if 'slat_close_time' in cover_data:
                    slat['close_time'] = float(cover_data['slat_close_time'])
                if 'slat_step' in cover_data:
                    slat['step'] = int(cover_data['slat_step'])
                cover_config['slat_control'] = slat
            # Protections
            if 'power_limit' in cover_data and cover_data['power_limit'] is not None:
                cover_config['power_limit'] = int(cover_data['power_limit'])
            if 'voltage_limit' in cover_data and cover_data['voltage_limit'] is not None:
                cover_config['voltage_limit'] = int(cover_data['voltage_limit'])
            if 'undervoltage_limit' in cover_data and cover_data['undervoltage_limit'] is not None:
                cover_config['undervoltage_limit'] = int(cover_data['undervoltage_limit'])
            if 'current_limit' in cover_data and cover_data['current_limit'] is not None:
                cover_config['current_limit'] = float(cover_data['current_limit'])
            
            if cover_config:
                try:
                    resp = rpc.call('Cover.SetConfig', {'id': 0, 'config': cover_config})
                    results['cover'] = 'updated'
                    if isinstance(resp, dict) and resp.get('restart_required'):
                        results['restart_required'] = True
                except Exception as e:
                    results['cover'] = f'failed: {str(e)}'
        
        # Update Light/Dimmer settings
        if 'light' in data and data['light']:
            light_data = data['light']
            light_config = {}
            
            # Light name (sanitized for HA compatibility)
            if 'name' in light_data:
                light_config['name'] = sanitize_ha_name(light_data['name'])
            if 'initial_state' in light_data:
                light_config['initial_state'] = light_data['initial_state']
            if 'auto_on' in light_data:
                light_config['auto_on'] = light_data['auto_on']
            if 'auto_on_delay' in light_data:
                light_config['auto_on_delay'] = float(light_data['auto_on_delay'])
            if 'auto_off' in light_data:
                light_config['auto_off'] = light_data['auto_off']
            if 'auto_off_delay' in light_data:
                light_config['auto_off_delay'] = float(light_data['auto_off_delay'])
            if 'default_brightness' in light_data:
                light_config['default'] = {'brightness': int(light_data['default_brightness'])}
            if 'night_mode_enable' in light_data or 'night_mode_brightness' in light_data:
                night_mode = {
                    'enable': light_data.get('night_mode_enable', False),
                    'brightness': int(light_data.get('night_mode_brightness', 50))
                }
                # Active time range (list of two time strings, e.g. ["22:00", "06:00"])
                active_between = light_data.get('night_mode_active_between')
                if active_between and isinstance(active_between, list) and len(active_between) == 2:
                    night_mode['active_between'] = active_between
                light_config['night_mode'] = night_mode
            if 'min_brightness_on_toggle' in light_data:
                light_config['min_brightness_on_toggle'] = int(light_data['min_brightness_on_toggle'])
            if 'transition_duration' in light_data:
                light_config['transition_duration'] = float(light_data['transition_duration'])
            if 'button_fade_rate' in light_data:
                light_config['button_fade_rate'] = int(light_data['button_fade_rate'])
            if 'in_mode' in light_data:
                light_config['in_mode'] = light_data['in_mode']
            if 'range_map' in light_data and isinstance(light_data['range_map'], list) and len(light_data['range_map']) == 2:
                light_config['range_map'] = [int(light_data['range_map'][0]), int(light_data['range_map'][1])]
            if 'current_limit' in light_data and light_data['current_limit'] is not None:
                light_config['current_limit'] = float(light_data['current_limit'])
            if 'power_limit' in light_data and light_data['power_limit'] is not None:
                light_config['power_limit'] = int(light_data['power_limit'])
            if 'voltage_limit' in light_data and light_data['voltage_limit'] is not None:
                light_config['voltage_limit'] = int(light_data['voltage_limit'])
            if 'undervoltage_limit' in light_data and light_data['undervoltage_limit'] is not None:
                light_config['undervoltage_limit'] = int(light_data['undervoltage_limit'])
            
            if light_config:
                # Sync Input.type with Light.in_mode if in_mode is being changed
                # Valid combinations: button → dim/flip/activate, switch → follow/flip
                if 'in_mode' in light_config:
                    new_in_mode = light_config['in_mode']
                    required_input_type = None
                    if new_in_mode in ('dim', 'activate'):
                        required_input_type = 'button'
                    elif new_in_mode == 'follow':
                        required_input_type = 'switch'
                    # 'flip' is compatible with both, no change needed
                    
                    if required_input_type:
                        try:
                            # Read current Input.type to check if change is needed
                            current_input = rpc.call('Input.GetConfig', {'id': 0})
                            if current_input.get('type') != required_input_type:
                                rpc.call('Input.SetConfig', {'id': 0, 'config': {'type': required_input_type}})
                                results['inputs'].append(f'input:0 type synced to {required_input_type}')
                        except Exception as e:
                            results['inputs'].append(f'input:0 type sync failed: {str(e)}')
                
                try:
                    resp = rpc.call('Light.SetConfig', {'id': 0, 'config': light_config})
                    results['light'] = 'updated'
                    if isinstance(resp, dict) and resp.get('restart_required'):
                        results['restart_required'] = True
                except Exception as e:
                    results['light'] = f'failed: {str(e)}'
        
        # Update Input settings
        if 'inputs' in data and data['inputs']:
            input_mode_source = data.get('inputModeSource', 'input')
            
            for input_data in data['inputs']:
                input_id = input_data.get('id')
                if input_id is None:
                    continue
                
                mode_source = input_data.get('modeSource', input_mode_source)
                
                # Handle input name (sanitized for HA compatibility)
                if 'name' in input_data:
                    try:
                        sanitized_name = sanitize_ha_name(input_data['name'])
                        rpc.call('Input.SetConfig', {'id': input_id, 'config': {'name': sanitized_name}})
                        results['inputs'].append(f'input:{input_id} name updated')
                    except Exception as e:
                        results['inputs'].append(f'input:{input_id} name failed: {str(e)}')
                
                # Handle input type change for I4 (not Minis - those use in_mode above)
                if 'type' in input_data and mode_source == 'input':
                    try:
                        resp = rpc.call('Input.SetConfig', {'id': input_id, 'config': {'type': input_data['type']}})
                        results['inputs'].append(f'input:{input_id} type updated')
                        if isinstance(resp, dict) and resp.get('restart_required'):
                            results['restart_required'] = True
                    except Exception as e:
                        results['inputs'].append(f'input:{input_id} type failed: {str(e)}')
                
                # Handle invert change (works on all devices)
                if 'invert' in input_data:
                    try:
                        rpc.call('Input.SetConfig', {'id': input_id, 'config': {'invert': input_data['invert']}})
                        results['inputs'].append(f'input:{input_id} invert updated')
                    except Exception as e:
                        results['inputs'].append(f'input:{input_id} invert failed: {str(e)}')
        
        return jsonify({
            'success': True,
            'message': 'Settings updated',
            'results': results,
            'restart_required': results.get('restart_required', False)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/devices/<device_id>/convert-profile', methods=['POST'])
def convert_device_profile(device_id):
    """
    Convert device between switch and cover profile.
    
    WARNING: This triggers a device reboot!
    
    Body: {profile: "switch" | "cover"}
    """
    import time
    from web.services import core_modules
    
    device = device_manager.get_device(device_id)
    if not device:
        return jsonify({'success': False, 'error': 'Device not found'}), 404
    
    ip = device.get('ip')
    if not ip:
        return jsonify({'success': False, 'error': 'Device has no IP'}), 400
    
    if not core_modules.CORE_AVAILABLE or not core_modules.RpcClient:
        return jsonify({'success': False, 'error': 'Core not available'}), 500
    
    data = request.get_json() or {}
    target_profile = data.get('profile')
    
    if target_profile not in ('switch', 'cover'):
        return jsonify({'success': False, 'error': 'Invalid profile. Use "switch" or "cover"'}), 400
    
    try:
        rpc = core_modules.RpcClient(ip, timeout_s=5.0)
        
        # Get current profile
        device_info = rpc.call('Shelly.GetDeviceInfo')
        current_profile = device_info.get('profile')
        
        if current_profile is None:
            return jsonify({
                'success': False, 
                'error': 'Device does not support profiles (not a 2PM/2-channel device)'
            }), 400
        
        if current_profile == target_profile:
            return jsonify({
                'success': True, 
                'message': f'Device already in {target_profile} mode',
                'changed': False
            })
        
        # Set new profile (this triggers reboot)
        rpc.call('Shelly.SetProfile', {'name': target_profile})
        
        # Wait for device to reboot
        time.sleep(2)
        
        # Poll until device is back online (max 30 seconds)
        max_wait = 30
        start_time = time.time()
        device_online = False
        
        while time.time() - start_time < max_wait:
            try:
                test_rpc = core_modules.RpcClient(ip, timeout_s=2.0)
                test_rpc.call('Shelly.GetDeviceInfo')
                device_online = True
                break
            except:
                time.sleep(2)
        
        if not device_online:
            return jsonify({
                'success': False,
                'error': 'Device did not come back online after reboot',
                'changed': True
            }), 500
        
        # Update ip_state.json with new profile info
        mac = device.get('id', device_id).upper().replace(':', '').replace('-', '')
        if device_manager.state and mac in device_manager.state.devices:
            device_entry = device_manager.state.devices[mac]
            if 'stage4' not in device_entry:
                device_entry['stage4'] = {}
            device_entry['stage4']['shelly_profile'] = target_profile
            device_entry['stage4']['profile_changed_ts'] = time.strftime('%Y-%m-%dT%H:%M:%SZ')
            device_manager.save_state()
            device_manager.load_devices()
        
        return jsonify({
            'success': True,
            'message': f'Device converted to {target_profile} mode',
            'changed': True,
            'previous_profile': current_profile,
            'new_profile': target_profile
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/devices/export/labels', methods=['GET', 'POST'])
def export_labels_csv():
    """Export device labels as CSV for label printers."""
    if not is_building_active():
        return jsonify({'success': False, 'error': 'No building active'}), 400
    
    device_manager.load_devices()
    devices = device_manager.devices
    
    # Filter by MAC list if POST request
    if request.method == 'POST':
        data = request.get_json() or {}
        macs = data.get('macs', [])
        delimiter = data.get('delimiter', ';')
        requested_columns = data.get('columns', [])
        if macs:
            mac_set = set(macs)
            devices = [d for d in devices if d.get('id') in mac_set]
    else:
        delimiter = request.args.get('delimiter', ';')
        requested_columns = []
    
    # Validate delimiter
    if delimiter not in (';', ',', '\t'):
        delimiter = ';'
    
    # All available columns
    all_columns = ['friendly_name', 'label_line1', 'label_line2', 'ip_short', 'room', 'location', 'model', 'mac_short', 'ip_full', 'mac_full']
    
    # Filter to requested columns (maintain order), fallback to all
    if requested_columns:
        columns = [c for c in requested_columns if c in all_columns]
    else:
        columns = all_columns
    
    if not columns:
        columns = all_columns
    
    # Build CSV
    lines = [delimiter.join(columns)]
    
    for device in devices:
        ip = device.get('ip', '')
        mac = device.get('id', '')
        room = device.get('room', '')
        location = device.get('location', '')
        model = device.get('model', '')
        friendly_name = device.get('friendly_name', '')
        
        # ip_short = last 2 octets
        ip_parts = ip.split('.')
        ip_short = f"{ip_parts[2]}.{ip_parts[3]}" if len(ip_parts) == 4 else ip
        
        # mac_short = last 6 chars
        mac_short = mac[-6:] if len(mac) >= 6 else mac
        
        # Build label lines
        line1_parts = [ip_short]
        if room:
            line1_parts.append(room)
        if location:
            line1_parts.append(location)
        label_line1 = ' '.join(line1_parts)
        
        label_line2 = f"{model} {mac_short}" if model else mac_short
        
        # Build values dict for column selection
        values = {
            'friendly_name': friendly_name,
            'label_line1': label_line1,
            'label_line2': label_line2,
            'ip_short': ip_short,
            'room': room,
            'location': location,
            'model': model,
            'mac_short': mac_short,
            'ip_full': ip,
            'mac_full': mac,
        }
        
        line = delimiter.join([escape_csv(values.get(col, ''), delimiter) for col in columns])
        lines.append(line)
    
    csv_content = '\ufeff' + '\n'.join(lines)
    
    filename = f"{get_active_building()}_labels.csv"
    return Response(
        csv_content.encode('utf-8'),
        mimetype='text/csv; charset=utf-8',
        headers={'Content-Disposition': f'attachment; filename={filename}'}
    )


# ===========================================================================
# KVS (Key-Value Store)
# ===========================================================================

@bp.route('/api/devices/<device_id>/kvs', methods=['GET'])
def get_device_kvs(device_id):
    """Get all KVS entries from a device."""
    import requests
    
    device = device_manager.get_device(device_id)
    if not device:
        return jsonify({'success': False, 'error': 'Device not found'}), 404
    
    ip = device.get('ip')
    if not ip:
        return jsonify({'success': False, 'error': 'Device has no IP'}), 400
    
    try:
        # Get all KVS entries
        resp = requests.get(f'http://{ip}/rpc/KVS.GetMany?match=*', timeout=5)
        if resp.status_code != 200:
            return jsonify({'success': False, 'error': f'HTTP {resp.status_code}'}), 400
        
        data = resp.json()
        items = data.get('items', [])
        
        # Convert list of items to dict
        kvs = {}
        for item in items:
            key = item.get('key')
            value = item.get('value')
            if key:
                kvs[key] = value
        
        return jsonify({'success': True, 'kvs': kvs})
        
    except requests.exceptions.Timeout:
        return jsonify({'success': False, 'error': 'Device timeout'}), 504
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/devices/<device_id>/kvs', methods=['POST'])
def update_device_kvs(device_id):
    """Update or delete KVS entries on a device."""
    import requests
    
    device = device_manager.get_device(device_id)
    if not device:
        return jsonify({'success': False, 'error': 'Device not found'}), 404
    
    ip = device.get('ip')
    if not ip:
        return jsonify({'success': False, 'error': 'Device has no IP'}), 400
    
    data = request.get_json() or {}
    updates = data.get('updates', {})  # {key: value, ...}
    deletes = data.get('deletes', [])  # [key, ...]
    
    errors = []
    success_count = 0
    
    try:
        # Process updates
        for key, value in updates.items():
            try:
                # KVS.Set expects value as JSON string for complex types
                payload = {'key': key, 'value': value}
                resp = requests.post(
                    f'http://{ip}/rpc/KVS.Set',
                    json=payload,
                    timeout=5
                )
                if resp.status_code == 200:
                    success_count += 1
                else:
                    errors.append(f'Set {key}: HTTP {resp.status_code}')
            except Exception as e:
                errors.append(f'Set {key}: {str(e)}')
        
        # Process deletes
        for key in deletes:
            try:
                resp = requests.post(
                    f'http://{ip}/rpc/KVS.Delete',
                    json={'key': key},
                    timeout=5
                )
                if resp.status_code == 200:
                    success_count += 1
                else:
                    # Key might not exist, which is OK
                    if 'NotFound' not in resp.text:
                        errors.append(f'Delete {key}: HTTP {resp.status_code}')
                    else:
                        success_count += 1
            except Exception as e:
                errors.append(f'Delete {key}: {str(e)}')
        
        if errors:
            return jsonify({
                'success': False,
                'error': '; '.join(errors),
                'partial_success': success_count
            })
        
        return jsonify({'success': True, 'updated': success_count})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/kvs/delete-all', methods=['POST'])
def delete_all_kvs():
    """Delete all KVS entries from a device."""
    import requests
    
    data = request.get_json() or {}
    device_id = data.get('device')
    
    if not device_id:
        return jsonify({'success': False, 'error': 'Device ID required'}), 400
    
    device = device_manager.get_device(device_id)
    if not device:
        return jsonify({'success': False, 'error': 'Device not found'}), 404
    
    ip = device.get('ip')
    if not ip:
        return jsonify({'success': False, 'error': 'Device has no IP'}), 400
    
    try:
        # First get all keys - items is a list of {key, value} objects
        list_resp = requests.get(f'http://{ip}/rpc/KVS.GetMany?match=*', timeout=5)
        if list_resp.status_code != 200:
            return jsonify({'success': False, 'error': 'KVS.GetMany failed'}), 400
        
        items = list_resp.json().get('items', [])
        keys = [item.get('key') for item in items if item.get('key')]
        
        if not keys:
            return jsonify({'success': True, 'deleted_count': 0, 'message': 'No keys to delete'})
        
        deleted_count = 0
        errors = []
        
        for key in keys:
            try:
                del_resp = requests.post(
                    f'http://{ip}/rpc/KVS.Delete',
                    json={'key': key},
                    timeout=5
                )
                if del_resp.status_code == 200:
                    deleted_count += 1
                else:
                    errors.append(key)
            except Exception as e:
                errors.append(key)
        
        if errors:
            return jsonify({
                'success': True,
                'deleted_count': deleted_count,
                'failed_keys': errors
            })
        
        return jsonify({
            'success': True,
            'deleted_count': deleted_count
        })
    
    except requests.exceptions.Timeout:
        return jsonify({'success': False, 'error': 'Timeout'}), 504
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ===========================================================================
# Webhooks
# ===========================================================================

@bp.route('/api/devices/<device_id>/webhooks', methods=['GET'])
def get_device_webhooks(device_id):
    """Get all webhooks and available components from a device."""
    import requests
    
    device = device_manager.get_device(device_id)
    if not device:
        return jsonify({'success': False, 'error': 'Device not found'}), 404
    
    ip = device.get('ip')
    if not ip:
        return jsonify({'success': False, 'error': 'Device has no IP'}), 400
    
    try:
        # Get webhooks
        wh_resp = requests.get(f'http://{ip}/rpc/Webhook.List', timeout=5)
        webhooks = []
        if wh_resp.status_code == 200:
            webhooks = wh_resp.json().get('hooks', [])
        
        # Get components to know which event types are available
        comp_resp = requests.get(f'http://{ip}/rpc/Shelly.GetConfig', timeout=5)
        components = []
        if comp_resp.status_code == 200:
            config = comp_resp.json()
            # Extract component keys like "input:0", "switch:0", "cover:0"
            for key in config.keys():
                if ':' in key:
                    components.append(key)
        
        return jsonify({
            'success': True,
            'webhooks': webhooks,
            'components': sorted(components)
        })
        
    except requests.exceptions.Timeout:
        return jsonify({'success': False, 'error': 'Device timeout'}), 504
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/devices/<device_id>/webhooks', methods=['POST'])
def manage_device_webhooks(device_id):
    """Create, update, or delete webhooks on a device."""
    import requests
    
    device = device_manager.get_device(device_id)
    if not device:
        return jsonify({'success': False, 'error': 'Device not found'}), 404
    
    ip = device.get('ip')
    if not ip:
        return jsonify({'success': False, 'error': 'Device has no IP'}), 400
    
    data = request.get_json() or {}
    action = data.get('action', 'create')
    
    try:
        if action == 'create':
            # Create new webhook
            payload = {
                'cid': data.get('cid', 0),
                'enable': data.get('enable', True),
                'event': data.get('event'),
                'urls': [data.get('url')] if data.get('url') else data.get('urls', [])
            }
            if data.get('name'):
                payload['name'] = data.get('name')
            
            if not payload['event']:
                return jsonify({'success': False, 'error': 'Event is required'}), 400
            
            resp = requests.post(
                f'http://{ip}/rpc/Webhook.Create',
                json=payload,
                timeout=5
            )
            
            if resp.status_code == 200:
                return jsonify({'success': True, 'id': resp.json().get('id')})
            else:
                error = resp.json().get('message', f'HTTP {resp.status_code}') if resp.text else f'HTTP {resp.status_code}'
                return jsonify({'success': False, 'error': error}), 400
        
        elif action == 'update':
            # Update webhook (enable/disable, urls)
            payload = {'id': data.get('id')}
            if 'enable' in data:
                payload['enable'] = data.get('enable')
            if 'name' in data:
                payload['name'] = data.get('name')
            if 'urls' in data:
                payload['urls'] = data.get('urls')
            elif 'url' in data:
                payload['urls'] = [data.get('url')]
            
            resp = requests.post(
                f'http://{ip}/rpc/Webhook.Update',
                json=payload,
                timeout=5
            )
            
            if resp.status_code == 200:
                return jsonify({'success': True})
            else:
                error = resp.json().get('message', f'HTTP {resp.status_code}') if resp.text else f'HTTP {resp.status_code}'
                return jsonify({'success': False, 'error': error}), 400
        
        elif action == 'delete':
            # Delete webhook
            resp = requests.post(
                f'http://{ip}/rpc/Webhook.Delete',
                json={'id': data.get('id')},
                timeout=5
            )
            
            if resp.status_code == 200:
                return jsonify({'success': True})
            else:
                error = resp.json().get('message', f'HTTP {resp.status_code}') if resp.text else f'HTTP {resp.status_code}'
                return jsonify({'success': False, 'error': error}), 400
        
        else:
            return jsonify({'success': False, 'error': f'Unknown action: {action}'}), 400
        
    except requests.exceptions.Timeout:
        return jsonify({'success': False, 'error': 'Device timeout'}), 504
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/devices/<device_id>/reboot', methods=['POST'])
def reboot_device(device_id):
    """Reboot a device."""
    import requests
    
    device = device_manager.get_device(device_id)
    if not device:
        return jsonify({'success': False, 'error': 'Device not found'}), 404
    
    ip = device.get('ip')
    if not ip:
        return jsonify({'success': False, 'error': 'Device has no IP'}), 400
    
    try:
        resp = requests.post(
            f'http://{ip}/rpc',
            json={'id': 1, 'method': 'Shelly.Reboot', 'params': {}},
            timeout=5
        )
        return jsonify({'success': True, 'message': 'Reboot command sent'})
        
    except requests.exceptions.Timeout:
        return jsonify({'success': False, 'error': 'Device timeout'}), 504
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/devices/<device_id>/live', methods=['GET'])
def get_device_live_status(device_id):
    """Get live status of a device."""
    import requests
    
    device = device_manager.get_device(device_id)
    if not device:
        return jsonify({'success': False, 'error': 'Device not found'}), 404
    
    ip = device.get('ip')
    if not ip:
        return jsonify({'success': False, 'error': 'Device has no IP'}), 400
    
    try:
        # Get device status
        resp = requests.post(
            f'http://{ip}/rpc',
            json={'id': 1, 'method': 'Shelly.GetStatus', 'params': {}},
            timeout=5
        )
        data = resp.json()
        
        result = {'success': True, 'status': {}, 'device_info': {}}
        
        if 'result' in data:
            result['status'] = data['result']
        elif 'error' in data:
            return jsonify({'success': False, 'error': data['error'].get('message', 'Unknown error')}), 400
        
        # Also get device info (contains profile for 2PM devices)
        try:
            resp_info = requests.post(
                f'http://{ip}/rpc',
                json={'id': 2, 'method': 'Shelly.GetDeviceInfo', 'params': {}},
                timeout=5
            )
            info_data = resp_info.json()
            if 'result' in info_data:
                result['device_info'] = info_data['result']
        except:
            pass  # device_info is optional
        
        return jsonify(result)
        
    except requests.exceptions.Timeout:
        return jsonify({'success': False, 'error': 'Device timeout'}), 504
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ===========================================================================
# Firmware Updates
# ===========================================================================

@bp.route('/api/firmware/check', methods=['POST'])
def check_firmware():
    """Check firmware versions for multiple devices."""
    import requests
    from concurrent.futures import ThreadPoolExecutor
    
    data = request.get_json() or {}
    device_macs = data.get('devices', [])
    
    if not device_macs:
        return jsonify({'success': False, 'error': 'No devices specified'})
    
    results = []
    
    def check_device(mac):
        device = device_manager.get_device(mac)
        if not device:
            return {'mac': mac, 'current': '?', 'available': '?', 'offline': True}
        
        ip = device.get('ip')
        if not ip:
            return {'mac': mac, 'current': '?', 'available': '?', 'offline': True}
        
        name = device.get('friendly_name') or ip
        
        try:
            # Get device info for current firmware
            info_resp = requests.get(f'http://{ip}/rpc/Shelly.GetDeviceInfo', timeout=5)
            if info_resp.status_code != 200:
                return {'mac': mac, 'ip': ip, 'name': name, 'current': '?', 'available': '?', 'offline': True}
            
            info = info_resp.json()
            current_fw = info.get('fw_id', info.get('ver', '?'))
            name = device.get('friendly_name') or info.get('name') or ip
            
            # Check for available update
            status_resp = requests.get(f'http://{ip}/rpc/Shelly.CheckForUpdate', timeout=10)
            available_fw = None
            
            if status_resp.status_code == 200:
                update_info = status_resp.json()
                # Gen2+ returns stable/beta channels
                stable = update_info.get('stable', {})
                if stable and stable.get('version'):
                    available_fw = stable.get('version')
            
            return {
                'mac': mac,
                'ip': ip,
                'name': name,
                'current': current_fw,
                'available': available_fw or current_fw,
                'model': info.get('model', info.get('app', ''))
            }
            
        except requests.exceptions.Timeout:
            return {'mac': mac, 'ip': ip, 'name': name, 'current': '?', 'available': '?', 'offline': True}
        except Exception as e:
            return {'mac': mac, 'ip': ip, 'name': name, 'current': '?', 'available': '?', 'offline': True}
    
    # Check devices in parallel
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(check_device, device_macs))
    
    return jsonify({'success': True, 'results': results})


@bp.route('/api/firmware/update', methods=['POST'])
def update_firmware():
    """Trigger firmware update for multiple devices."""
    import requests
    from concurrent.futures import ThreadPoolExecutor
    
    data = request.get_json() or {}
    device_macs = data.get('devices', [])
    
    if not device_macs:
        return jsonify({'success': False, 'error': 'No devices specified'})
    
    results = []
    
    def update_device(mac):
        device = device_manager.get_device(mac)
        if not device:
            return {'mac': mac, 'success': False, 'error': 'Not found'}
        
        ip = device.get('ip')
        if not ip:
            return {'mac': mac, 'success': False, 'error': 'No IP'}
        
        try:
            # Trigger update (device will download and install)
            resp = requests.post(
                f'http://{ip}/rpc/Shelly.Update',
                json={'stage': 'stable'},
                timeout=10
            )
            
            if resp.status_code == 200:
                return {'mac': mac, 'ip': ip, 'success': True, 'message': 'Update started'}
            else:
                error = resp.json().get('message', f'HTTP {resp.status_code}') if resp.text else f'HTTP {resp.status_code}'
                return {'mac': mac, 'ip': ip, 'success': False, 'error': error}
                
        except requests.exceptions.Timeout:
            # Timeout might mean update is in progress
            return {'mac': mac, 'ip': ip, 'success': True, 'message': 'Update may be in progress'}
        except Exception as e:
            return {'mac': mac, 'ip': ip, 'success': False, 'error': str(e)}
    
    # Update devices in parallel (but not too many at once)
    with ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(update_device, device_macs))
    
    return jsonify({'success': True, 'results': results})


@bp.route('/api/devices/sync', methods=['POST'])
def sync_devices():
    """Sync device info from Shellys to ip_state.json.
    
    Queries firmware version from all online devices and updates
    ip_state.json if changes are detected.
    """
    import requests
    from concurrent.futures import ThreadPoolExecutor, as_completed
    
    devices = device_manager.devices
    if not devices:
        return jsonify({'success': True, 'synced': 0, 'changes': []})
    
    changes = []
    
    def sync_device(device):
        """Query device and return changes if any."""
        if not isinstance(device, dict):
            return None
        
        mac = device.get('id') or device.get('mac')
        ip = device.get('ip')
        if not ip or not mac:
            return None
        
        try:
            # Query device info
            resp = requests.get(f'http://{ip}/rpc/Shelly.GetDeviceInfo', timeout=3)
            if resp.status_code != 200:
                return None
            
            info = resp.json()
            new_fw = info.get('fw_id', info.get('ver'))
            if not new_fw:
                return None
            
            # Check if firmware changed
            old_fw = device.get('fw')
            if old_fw != new_fw:
                return {
                    'mac': mac,
                    'field': 'fw',
                    'old': old_fw,
                    'new': new_fw
                }
            
            return None
            
        except Exception:
            return None
    
    # Query devices in parallel
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(sync_device, d): d for d in devices}
        
        for future in as_completed(futures):
            result = future.result()
            if result:
                changes.append(result)
    
    # Apply changes to ip_state.json
    for change in changes:
        device_manager.update_device(change['mac'], {'fw': change['new']})
    
    return jsonify({
        'success': True,
        'synced': len(devices),
        'changes': changes
    })


# ===========================================================================
# Device Flags (ECO, BLE, LED, AP, MQTT) — Bulk read/apply
# ===========================================================================

def _flags_rpc(ip, method, params=None, timeout=5):
    """RPC call for flag operations (core RpcClient with HTTP fallback)."""
    from web.services import core_modules
    import requests as http_requests

    if core_modules.CORE_AVAILABLE and core_modules.RpcClient:
        try:
            rpc = core_modules.RpcClient(ip, timeout_s=float(timeout))
            return rpc.call(method, params or {})
        except Exception as e:
            return {'_error': str(e)}

    # HTTP fallback
    try:
        resp = http_requests.post(
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
    except Exception as e:
        return {'_error': str(e)}


def _read_device_flags(ip):
    """Read all 5 flags from a single device. Returns dict with flag states."""
    flags = {}

    # ECO from Sys.GetConfig
    sys_cfg = _flags_rpc(ip, 'Sys.GetConfig', timeout=3)
    if isinstance(sys_cfg, dict) and '_error' not in sys_cfg:
        device_cfg = sys_cfg.get('device', {})
        flags['eco'] = device_cfg.get('eco_mode', False)
    else:
        flags['eco'] = None

    # BLE from BLE.GetConfig
    ble_cfg = _flags_rpc(ip, 'BLE.GetConfig', timeout=2)
    if isinstance(ble_cfg, dict) and '_error' not in ble_cfg:
        flags['ble'] = ble_cfg.get('enable', False)
    else:
        flags['ble'] = None

    # AP from WiFi.GetConfig
    wifi_cfg = _flags_rpc(ip, 'WiFi.GetConfig', timeout=2)
    if isinstance(wifi_cfg, dict) and '_error' not in wifi_cfg:
        ap = wifi_cfg.get('ap', {})
        flags['ap'] = ap.get('enable', False)
    else:
        flags['ap'] = None

    # MQTT from MQTT.GetConfig
    mqtt_cfg = _flags_rpc(ip, 'MQTT.GetConfig', timeout=2)
    if isinstance(mqtt_cfg, dict) and '_error' not in mqtt_cfg:
        flags['mqtt'] = mqtt_cfg.get('enable', False)
    else:
        flags['mqtt'] = None

    return flags


# =====================================================================
# Cover Calibration & Status
# =====================================================================

@bp.route('/api/devices/<device_id>/cover/calibrate', methods=['POST'])
def cover_calibrate(device_id):
    """Start cover calibration procedure."""
    from web.services import core_modules

    device = device_manager.get_device(device_id)
    if not device:
        return jsonify({'success': False, 'error': 'Device not found'}), 404

    ip = device.get('ip')
    if not ip:
        return jsonify({'success': False, 'error': 'Device has no IP'}), 400

    if not core_modules.CORE_AVAILABLE or not core_modules.RpcClient:
        return jsonify({'success': False, 'error': 'Core not available'}), 500

    try:
        rpc = core_modules.RpcClient(ip, timeout_s=5.0)
        rpc.call('Cover.Calibrate', {'id': 0})
        return jsonify({'success': True, 'message': 'Calibration started'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/devices/<device_id>/cover/stop', methods=['POST'])
def cover_stop(device_id):
    """Stop cover movement (including calibration)."""
    from web.services import core_modules

    device = device_manager.get_device(device_id)
    if not device:
        return jsonify({'success': False, 'error': 'Device not found'}), 404

    ip = device.get('ip')
    if not ip:
        return jsonify({'success': False, 'error': 'Device has no IP'}), 400

    if not core_modules.CORE_AVAILABLE or not core_modules.RpcClient:
        return jsonify({'success': False, 'error': 'Core not available'}), 500

    try:
        rpc = core_modules.RpcClient(ip, timeout_s=5.0)
        rpc.call('Cover.Stop', {'id': 0})
        return jsonify({'success': True, 'message': 'Cover stopped'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/devices/<device_id>/cover/status', methods=['GET'])
def cover_status(device_id):
    """Get cover status (for calibration polling)."""
    from web.services import core_modules

    device = device_manager.get_device(device_id)
    if not device:
        return jsonify({'success': False, 'error': 'Device not found'}), 404

    ip = device.get('ip')
    if not ip:
        return jsonify({'success': False, 'error': 'Device has no IP'}), 400

    if not core_modules.CORE_AVAILABLE or not core_modules.RpcClient:
        return jsonify({'success': False, 'error': 'Core not available'}), 500

    try:
        rpc = core_modules.RpcClient(ip, timeout_s=5.0)
        status = rpc.call('Cover.GetStatus', {'id': 0})
        return jsonify({
            'success': True,
            'state': status.get('state', 'stopped'),
            'pos_control': status.get('pos_control', False),
            'current_pos': status.get('current_pos'),
            'slat_pos': status.get('slat_pos'),
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/devices/<device_id>/light/calibrate', methods=['POST'])
def light_calibrate(device_id):
    """Start light/dimmer calibration procedure."""
    from web.services import core_modules

    device = device_manager.get_device(device_id)
    if not device:
        return jsonify({'success': False, 'error': 'Device not found'}), 404

    ip = device.get('ip')
    if not ip:
        return jsonify({'success': False, 'error': 'Device has no IP'}), 400

    if not core_modules.CORE_AVAILABLE or not core_modules.RpcClient:
        return jsonify({'success': False, 'error': 'Core not available'}), 500

    try:
        rpc = core_modules.RpcClient(ip, timeout_s=10.0)
        rpc.call('Light.Calibrate', {'id': 0})
        return jsonify({'success': True, 'message': 'Calibration started'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/devices/<device_id>/light/status', methods=['GET'])
def light_status(device_id):
    """Get light status (for calibration polling)."""
    from web.services import core_modules

    device = device_manager.get_device(device_id)
    if not device:
        return jsonify({'success': False, 'error': 'Device not found'}), 404

    ip = device.get('ip')
    if not ip:
        return jsonify({'success': False, 'error': 'Device has no IP'}), 400

    if not core_modules.CORE_AVAILABLE or not core_modules.RpcClient:
        return jsonify({'success': False, 'error': 'Core not available'}), 500

    try:
        rpc = core_modules.RpcClient(ip, timeout_s=5.0)
        status = rpc.call('Light.GetStatus', {'id': 0})
        return jsonify({
            'success': True,
            'calibrating': status.get('calibrating', False),
            'calib_progress': status.get('calib_progress'),
            'output': status.get('output', False),
            'brightness': status.get('brightness'),
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/devices/flags/read', methods=['POST'])
def read_device_flags():
    """Read flag states (ECO, BLE, LED, AP, MQTT) from selected devices."""
    from concurrent.futures import ThreadPoolExecutor, as_completed

    if not is_building_active():
        return jsonify({'success': False, 'error': 'No building active'}), 400

    data = request.get_json() or {}
    macs = data.get('macs', [])

    if not macs:
        return jsonify({'success': False, 'error': 'No devices specified'}), 400

    device_manager.load_devices()
    devices = device_manager.devices

    # Build lookup: mac -> device
    dev_map = {d['id']: d for d in devices if d.get('id') in macs}

    results = []

    def read_one(mac):
        dev = dev_map.get(mac)
        if not dev or not dev.get('ip'):
            return {'mac': mac, 'success': False, 'error': 'No IP'}
        ip = dev['ip']
        name = dev.get('friendly_name') or dev.get('room', '') or ip
        try:
            flags = _read_device_flags(ip)
            return {'mac': mac, 'ip': ip, 'name': name, 'success': True, 'flags': flags}
        except Exception as e:
            return {'mac': mac, 'ip': ip, 'name': name, 'success': False, 'error': str(e)}

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(read_one, mac): mac for mac in macs}
        for future in as_completed(futures):
            results.append(future.result())

    # Sort by original order
    mac_order = {mac: i for i, mac in enumerate(macs)}
    results.sort(key=lambda r: mac_order.get(r['mac'], 999))

    return jsonify({'success': True, 'results': results})


@bp.route('/api/devices/flags/apply', methods=['POST'])
def apply_device_flags():
    """Apply flag changes to selected devices."""
    from concurrent.futures import ThreadPoolExecutor, as_completed

    if not is_building_active():
        return jsonify({'success': False, 'error': 'No building active'}), 400

    data = request.get_json() or {}
    macs = data.get('macs', [])
    flags = data.get('flags', {})
    mqtt_server = data.get('mqtt_server', '').strip()
    # flags = { eco: true/false/null, ble: true/false/null, ... }
    # null = skip (don't change)

    if not macs:
        return jsonify({'success': False, 'error': 'No devices specified'}), 400

    # Filter out skipped flags
    active_flags = {k: v for k, v in flags.items() if v is not None}
    if not active_flags:
        return jsonify({'success': False, 'error': 'No flags to apply'}), 400

    # MQTT enable requires server address
    if active_flags.get('mqtt') is True and not mqtt_server:
        return jsonify({'success': False, 'error': 'MQTT server address required when enabling MQTT'}), 400

    device_manager.load_devices()
    devices = device_manager.devices
    dev_map = {d['id']: d for d in devices if d.get('id') in macs}

    results = []

    def apply_one(mac):
        dev = dev_map.get(mac)
        if not dev or not dev.get('ip'):
            return {'mac': mac, 'success': False, 'error': 'No IP'}

        ip = dev['ip']
        name = dev.get('friendly_name') or dev.get('room', '') or ip
        errors = []

        # ECO via Sys.SetConfig
        if 'eco' in active_flags:
            res = _flags_rpc(ip, 'Sys.SetConfig', {
                'config': {'device': {'eco_mode': active_flags['eco']}}
            }, timeout=3)
            if isinstance(res, dict) and '_error' in res:
                errors.append(f"ECO: {res['_error']}")

        # BLE via BLE.SetConfig
        if 'ble' in active_flags:
            res = _flags_rpc(ip, 'BLE.SetConfig', {'config': {'enable': active_flags['ble']}}, timeout=2)
            if isinstance(res, dict) and '_error' in res:
                errors.append(f"BLE: {res['_error']}")

        # AP via WiFi.SetConfig
        if 'ap' in active_flags:
            res = _flags_rpc(ip, 'WiFi.SetConfig', {'config': {'ap': {'enable': active_flags['ap']}}}, timeout=2)
            if isinstance(res, dict) and '_error' in res:
                errors.append(f"AP: {res['_error']}")

        # MQTT via MQTT.SetConfig
        if 'mqtt' in active_flags:
            mqtt_config = {'enable': active_flags['mqtt']}
            if active_flags['mqtt'] and mqtt_server:
                mqtt_config['server'] = mqtt_server
            res = _flags_rpc(ip, 'MQTT.SetConfig', {'config': mqtt_config}, timeout=2)
            if isinstance(res, dict) and '_error' in res:
                errors.append(f"MQTT: {res['_error']}")

        if errors:
            return {'mac': mac, 'ip': ip, 'name': name, 'success': False, 'error': '; '.join(errors)}
        return {'mac': mac, 'ip': ip, 'name': name, 'success': True}

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(apply_one, mac): mac for mac in macs}
        for future in as_completed(futures):
            results.append(future.result())

    mac_order = {mac: i for i, mac in enumerate(macs)}
    results.sort(key=lambda r: mac_order.get(r['mac'], 999))

    ok = sum(1 for r in results if r['success'])
    return jsonify({'success': True, 'results': results, 'ok': ok, 'total': len(results)})


# =====================================================================
# Bulk Input Type Configuration
# =====================================================================

def _read_device_inputs(ip):
    """Read Input.GetConfig for all inputs on a device. Returns list of inputs."""
    inputs = []
    # Try up to 4 inputs (I4 has 4, most devices have 1-2)
    for i in range(4):
        cfg = _flags_rpc(ip, 'Input.GetConfig', {'id': i}, timeout=2)
        if isinstance(cfg, dict) and '_error' not in cfg:
            inputs.append({
                'id': i,
                'name': cfg.get('name', '') or '',
                'type': cfg.get('type', 'button'),
            })
        else:
            break  # No more inputs
    return inputs


@bp.route('/api/devices/input-type/read', methods=['POST'])
def read_device_input_types():
    """Read input types from selected devices."""
    from concurrent.futures import ThreadPoolExecutor, as_completed

    if not is_building_active():
        return jsonify({'success': False, 'error': 'No building active'}), 400

    data = request.get_json() or {}
    macs = data.get('macs', [])

    if not macs:
        return jsonify({'success': False, 'error': 'No devices specified'}), 400

    device_manager.load_devices()
    devices = device_manager.devices
    dev_map = {d['id']: d for d in devices if d.get('id') in macs}

    results = []

    def read_one(mac):
        dev = dev_map.get(mac)
        if not dev or not dev.get('ip'):
            return {'mac': mac, 'success': False, 'error': 'No IP'}
        ip = dev['ip']
        name = dev.get('friendly_name') or dev.get('room', '') or ip
        try:
            inputs = _read_device_inputs(ip)
            if not inputs:
                return {'mac': mac, 'ip': ip, 'name': name, 'success': False, 'error': 'No inputs'}
            return {'mac': mac, 'ip': ip, 'name': name, 'success': True, 'inputs': inputs}
        except Exception as e:
            return {'mac': mac, 'ip': ip, 'name': name, 'success': False, 'error': str(e)}

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(read_one, mac): mac for mac in macs}
        for future in as_completed(futures):
            results.append(future.result())

    mac_order = {mac: i for i, mac in enumerate(macs)}
    results.sort(key=lambda r: mac_order.get(r['mac'], 999))

    return jsonify({'success': True, 'results': results})


@bp.route('/api/devices/input-type/apply', methods=['POST'])
def apply_device_input_types():
    """Apply input type (button/switch) to all inputs on selected devices."""
    from concurrent.futures import ThreadPoolExecutor, as_completed

    if not is_building_active():
        return jsonify({'success': False, 'error': 'No building active'}), 400

    data = request.get_json() or {}
    macs = data.get('macs', [])
    input_type = data.get('input_type', '')  # 'button' or 'switch'

    if not macs:
        return jsonify({'success': False, 'error': 'No devices specified'}), 400

    if input_type not in ('button', 'switch'):
        return jsonify({'success': False, 'error': 'Invalid input type'}), 400

    device_manager.load_devices()
    devices = device_manager.devices
    dev_map = {d['id']: d for d in devices if d.get('id') in macs}

    results = []

    def apply_one(mac):
        dev = dev_map.get(mac)
        if not dev or not dev.get('ip'):
            return {'mac': mac, 'success': False, 'error': 'No IP'}

        ip = dev['ip']
        name = dev.get('friendly_name') or dev.get('room', '') or ip
        errors = []
        changed = 0

        # First read how many inputs exist
        inputs = _read_device_inputs(ip)
        if not inputs:
            return {'mac': mac, 'ip': ip, 'name': name, 'success': False, 'error': 'No inputs'}

        for inp in inputs:
            if inp['type'] == input_type:
                continue  # Already correct type
            res = _flags_rpc(ip, 'Input.SetConfig', {
                'id': inp['id'],
                'config': {'type': input_type}
            }, timeout=3)
            if isinstance(res, dict) and '_error' in res:
                errors.append(f"Input:{inp['id']}: {res['_error']}")
            else:
                changed += 1

        if errors:
            return {'mac': mac, 'ip': ip, 'name': name, 'success': False, 'error': '; '.join(errors)}
        return {'mac': mac, 'ip': ip, 'name': name, 'success': True, 'changed': changed, 'total': len(inputs)}

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(apply_one, mac): mac for mac in macs}
        for future in as_completed(futures):
            results.append(future.result())

    mac_order = {mac: i for i, mac in enumerate(macs)}
    results.sort(key=lambda r: mac_order.get(r['mac'], 999))

    ok = sum(1 for r in results if r['success'])
    return jsonify({'success': True, 'results': results, 'ok': ok, 'total': len(results)})