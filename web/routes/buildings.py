"""
Stagebox Building Routes

Building activation and settings.
Available in both editions (Personal: single building only).
"""

import re
from flask import Blueprint, jsonify, request

import yaml

from web import config
from web.edition import is_pro, is_personal, is_limited, get_device_limit
from web.services import (
    discover_buildings,
    activate_building,
    deactivate_building,
    get_active_building,
    is_building_active,
    device_manager,
)

bp = Blueprint('buildings', __name__)


def _create_yaml_backup(file_path):
    """Create a timestamped backup of a YAML file."""
    from datetime import datetime
    import shutil
    
    if file_path.exists():
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = file_path.parent / f"{file_path.stem}.bak_{timestamp}{file_path.suffix}"
        shutil.copy2(file_path, backup_path)


@bp.route('/api/buildings', methods=['GET'])
def get_buildings():
    """Get list of available buildings."""
    buildings = discover_buildings()
    
    # Personal edition: only show building with "my_" prefix
    if is_limited() and len(buildings) > 1:
        my_buildings = [b for b in buildings if b['name'].startswith('my_')]
        if my_buildings:
            buildings = my_buildings[:1]  # Show first my_* building
        else:
            # Fallback: show active or first
            active = get_active_building()
            if active:
                buildings = [b for b in buildings if b['name'] == active]
            else:
                buildings = buildings[:1]
    
    return jsonify({
        'success': True,
        'buildings': buildings,
        'active': get_active_building()
    })


@bp.route('/api/buildings/activate', methods=['POST'])
def activate_building_route():
    """Activate a building."""
    data = request.get_json() or {}
    building_name = data.get('name')
    
    if not building_name:
        return jsonify({'success': False, 'error': 'Building name required'}), 400
    
    if activate_building(building_name):
        # Check device limit (currently unlimited for all editions)
        device_limit = get_device_limit()
        if device_limit > 0:
            device_count = len(device_manager.devices)
            if device_count > device_limit:
                return jsonify({
                    'success': True,
                    'message': f'Building {building_name} activated',
                    'active': building_name,
                    'warning': f'Device limit exceeded ({device_count}/{device_limit}).'
                })
        
        return jsonify({
            'success': True,
            'message': f'Building {building_name} activated',
            'active': building_name
        })
    
    return jsonify({'success': False, 'error': 'Building not found'}), 404


@bp.route('/api/buildings/deactivate', methods=['POST'])
def deactivate_building_route():
    """Deactivate current building."""
    deactivate_building()
    return jsonify({'success': True, 'message': 'Building deactivated'})


@bp.route('/api/buildings/active', methods=['GET'])
def get_active_building_route():
    """Get currently active building."""
    return jsonify({
        'success': True,
        'active': get_active_building()
    })


# ===========================================================================
# Building Settings (No PIN required - Planner/Electrician access)
# ===========================================================================

@bp.route('/api/settings/building', methods=['GET'])
def get_building_settings():
    """Get current building settings (WiFi + Network ranges)."""
    if not is_building_active():
        return jsonify({'success': False, 'error': 'No building active'}), 400
    
    cfg = config.load_config()
    secrets = config.load_secrets()
    
    # Extract WiFi profiles from secrets
    wifi_profiles = secrets.get('wifi_profiles', [])
    wifi_primary = wifi_profiles[0] if wifi_profiles else {'ssid': '', 'password': ''}
    wifi_fallback = wifi_profiles[1] if len(wifi_profiles) > 1 else {'ssid': '', 'password': ''}
    
    # Extract network settings from config
    stage2 = cfg.get('stage2', {})
    network = stage2.get('network', {})
    
    return jsonify({
        'success': True,
        'building': get_active_building(),
        'wifi': {
            'primary': {
                'ssid': wifi_primary.get('ssid', ''),
                'password': wifi_primary.get('password', '')
            },
            'fallback': {
                'ssid': wifi_fallback.get('ssid', ''),
                'password': wifi_fallback.get('password', '')
            }
        },
        'network': {
            'pool_start': network.get('pool_start', ''),
            'pool_end': network.get('pool_end', ''),
            'gateway': network.get('gateway', ''),
            'dhcp_scan_start': network.get('dhcp_scan_start', ''),
            'dhcp_scan_end': network.get('dhcp_scan_end', '')
        }
    })


@bp.route('/api/settings/building', methods=['PUT'])
def save_building_settings():
    """Save building settings (WiFi + Network ranges)."""
    if not is_building_active():
        return jsonify({'success': False, 'error': 'No building active'}), 400
    
    data = request.get_json() or {}
    
    # Validate required fields
    wifi = data.get('wifi', {})
    network = data.get('network', {})
    
    primary_ssid = wifi.get('primary', {}).get('ssid', '').strip()
    primary_password = wifi.get('primary', {}).get('password', '')
    
    if not primary_ssid:
        return jsonify({'success': False, 'error': 'Primary WiFi SSID is required'}), 400
    
    pool_start = network.get('pool_start', '').strip()
    pool_end = network.get('pool_end', '').strip()
    gateway = network.get('gateway', '').strip()
    dhcp_start = network.get('dhcp_scan_start', '').strip()
    dhcp_end = network.get('dhcp_scan_end', '').strip()
    
    if not pool_start or not pool_end:
        return jsonify({'success': False, 'error': 'Pool Start and Pool End are required'}), 400
    
    # Validate IP format
    ip_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
    for ip, name in [(pool_start, 'Pool Start'), (pool_end, 'Pool End')]:
        if not re.match(ip_pattern, ip):
            return jsonify({'success': False, 'error': f'Invalid IP format for {name}: {ip}'}), 400
    
    # Auto-derive gateway from pool_start if not provided
    subnet_prefix = '.'.join(pool_start.split('.')[:3])
    if not gateway:
        gateway = f"{subnet_prefix}.1"
    else:
        if not re.match(ip_pattern, gateway):
            return jsonify({'success': False, 'error': f'Invalid IP format for Gateway: {gateway}'}), 400
    
    user_provided_dhcp = bool(dhcp_start and dhcp_end)
    
    if user_provided_dhcp:
        for ip, name in [(dhcp_start, 'DHCP Start'), (dhcp_end, 'DHCP End')]:
            if not re.match(ip_pattern, ip):
                return jsonify({'success': False, 'error': f'Invalid IP format for {name}: {ip}'}), 400
    
    # Auto-derive other network settings
    netmask = '255.255.255.0'
    nameserver = gateway
    scan_cidr = f"{subnet_prefix}.0/24"
    
    try:
        cfg = config.load_config()
        secrets = config.load_secrets()
        
        # Create backups
        if config.CONFIG_FILE and config.CONFIG_FILE.exists():
            _create_yaml_backup(config.CONFIG_FILE)
        if config.SECRETS_FILE and config.SECRETS_FILE.exists():
            _create_yaml_backup(config.SECRETS_FILE)
        
        # Update secrets.yaml - WiFi profiles
        wifi_profiles = []
        wifi_profiles.append({
            'ssid': primary_ssid,
            'password': primary_password
        })
        
        fallback_ssid = wifi.get('fallback', {}).get('ssid', '').strip()
        fallback_password = wifi.get('fallback', {}).get('password', '')
        if fallback_ssid:
            wifi_profiles.append({
                'ssid': fallback_ssid,
                'password': fallback_password
            })
        
        secrets['wifi_profiles'] = wifi_profiles
        
        # Update config.yaml - Network settings
        if 'stage2' not in cfg:
            cfg['stage2'] = {}
        if 'network' not in cfg['stage2']:
            cfg['stage2']['network'] = {}
        
        cfg['stage2']['network']['pool_start'] = pool_start
        cfg['stage2']['network']['pool_end'] = pool_end
        cfg['stage2']['network']['gateway'] = gateway
        cfg['stage2']['network']['netmask'] = netmask
        cfg['stage2']['network']['nameserver'] = nameserver
        cfg['stage2']['network']['scan_cidr'] = scan_cidr
        
        if user_provided_dhcp:
            cfg['stage2']['network']['dhcp_scan_start'] = dhcp_start
            cfg['stage2']['network']['dhcp_scan_end'] = dhcp_end
        else:
            cfg['stage2']['network'].pop('dhcp_scan_start', None)
            cfg['stage2']['network'].pop('dhcp_scan_end', None)
        
        # Save files
        with open(config.SECRETS_FILE, 'w', encoding='utf-8') as f:
            yaml.dump(secrets, f, default_flow_style=False, allow_unicode=True)
        
        with open(config.CONFIG_FILE, 'w', encoding='utf-8') as f:
            yaml.dump(cfg, f, default_flow_style=False, allow_unicode=True)
        
        return jsonify({
            'success': True,
            'message': 'Building settings saved successfully',
            'derived': {
                'netmask': netmask,
                'nameserver': nameserver,
                'scan_cidr': scan_cidr,
                'dhcp_mode': 'custom' if user_provided_dhcp else 'full_scan'
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/settings/building/validate-network', methods=['POST'])
def validate_network_settings():
    """Validate network settings without saving."""
    data = request.get_json() or {}
    
    pool_start = data.get('pool_start', '').strip()
    pool_end = data.get('pool_end', '').strip()
    dhcp_start = data.get('dhcp_scan_start', '').strip()
    dhcp_end = data.get('dhcp_scan_end', '').strip()
    
    errors = []
    warnings = []
    
    def ip_to_int(ip):
        try:
            parts = ip.split('.')
            return (int(parts[0]) << 24) + (int(parts[1]) << 16) + (int(parts[2]) << 8) + int(parts[3])
        except:
            return None
    
    def validate_ip(ip, name):
        if not re.match(r'^(\d{1,3}\.){3}\d{1,3}$', ip):
            errors.append(f'{name}: Invalid IP format')
            return False
        parts = ip.split('.')
        for part in parts:
            if int(part) > 255:
                errors.append(f'{name}: Octet value > 255')
                return False
        return True
    
    # Validate required IPs
    pool_start_valid = validate_ip(pool_start, 'Pool Start') if pool_start else False
    pool_end_valid = validate_ip(pool_end, 'Pool End') if pool_end else False
    
    if not pool_start:
        errors.append('Pool Start is required')
    if not pool_end:
        errors.append('Pool End is required')
    
    pool_count = 0
    dhcp_count = 0
    
    if pool_start_valid and pool_end_valid:
        pool_start_int = ip_to_int(pool_start)
        pool_end_int = ip_to_int(pool_end)
        
        if pool_start_int and pool_end_int:
            if pool_start_int > pool_end_int:
                errors.append('Pool Start must be less than Pool End')
            else:
                pool_count = pool_end_int - pool_start_int + 1
    
    # Validate DHCP range if provided
    if dhcp_start and dhcp_end:
        dhcp_start_valid = validate_ip(dhcp_start, 'DHCP Start')
        dhcp_end_valid = validate_ip(dhcp_end, 'DHCP End')
        
        if dhcp_start_valid and dhcp_end_valid:
            dhcp_start_int = ip_to_int(dhcp_start)
            dhcp_end_int = ip_to_int(dhcp_end)
            
            if dhcp_start_int and dhcp_end_int:
                if dhcp_start_int > dhcp_end_int:
                    errors.append('DHCP Start must be less than DHCP End')
                else:
                    dhcp_count = dhcp_end_int - dhcp_start_int + 1
                
                # Check for overlap with pool
                if pool_start_valid and pool_end_valid:
                    pool_start_int = ip_to_int(pool_start)
                    pool_end_int = ip_to_int(pool_end)
                    
                    if not (dhcp_end_int < pool_start_int or dhcp_start_int > pool_end_int):
                        errors.append('DHCP range overlaps with Pool range')
    
    # Warnings
    if pool_count > 0 and pool_count < 10:
        warnings.append(f'Pool has only {pool_count} IPs - may be too small')
    
    return jsonify({
        'success': True,
        'valid': len(errors) == 0,
        'errors': errors,
        'warnings': warnings,
        'info': {
            'pool_count': pool_count,
            'dhcp_count': dhcp_count
        }
    })


# ===========================================================================
# Building Export/Import (Available in all editions)
# ===========================================================================

import io
import json
import shutil
import zipfile
from datetime import datetime
from flask import send_file


def generate_stagebox_signature(building_name, file_count):
    """Generate a simple signature for Stagebox exports."""
    import hashlib
    # Create a signature based on building name, file count, and a secret
    secret = "StageboxValidExport2024"
    data = f"{building_name}:{file_count}:{secret}"
    return hashlib.sha256(data.encode()).hexdigest()[:16]


def verify_stagebox_signature(building_name, file_count, signature):
    """Verify a Stagebox export signature."""
    expected = generate_stagebox_signature(building_name, file_count)
    return signature == expected


@bp.route('/api/buildings/export', methods=['POST'])
def export_buildings():
    """Export building(s) as ZIP file.
    
    Personal edition: exports the single displayed building.
    Pro edition: exports all buildings.
    """
    if not config.BUILDINGS_DIR.exists():
        return jsonify({'success': False, 'error': 'Buildings directory not found'}), 404
    
    try:
        zip_buffer = io.BytesIO()
        buildings_to_export = []
        
        if is_limited():
            # Personal: export the same building that is displayed in the UI
            # Use same logic as get_buildings()
            all_buildings = discover_buildings()
            
            if not all_buildings:
                return jsonify({'success': False, 'error': 'No building found to export'}), 400
            
            # Same logic as get_buildings: active building or first one
            active = get_active_building()
            if active and any(b['name'] == active for b in all_buildings):
                building_name = active
            else:
                building_name = all_buildings[0]['name']
            
            building_dir = config.BUILDINGS_DIR / building_name
            if building_dir.exists():
                buildings_to_export.append(building_dir)
            else:
                return jsonify({'success': False, 'error': f'Building directory not found: {building_name}'}), 400
        else:
            # Pro: all buildings
            for building_dir in config.BUILDINGS_DIR.iterdir():
                if building_dir.is_dir():
                    buildings_to_export.append(building_dir)
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            for building_dir in buildings_to_export:
                file_count = 0
                for file_path in building_dir.rglob('*'):
                    if file_path.is_file():
                        arcname = str(file_path.relative_to(config.BUILDINGS_DIR))
                        zf.write(file_path, arcname)
                        file_count += 1
                
                # Add signature file for each building
                signature = generate_stagebox_signature(building_dir.name, file_count)
                sig_content = json.dumps({
                    'version': '1.0',
                    'building': building_dir.name,
                    'files': file_count,
                    'sig': signature
                })
                zf.writestr(f"{building_dir.name}/.stagebox", sig_content)
        
        zip_buffer.seek(0)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        if is_limited() and buildings_to_export:
            building_name = buildings_to_export[0].name
            filename = f'stagebox_{building_name}_{timestamp}.zip'
        else:
            filename = f'stagebox_buildings_{timestamp}.zip'
        
        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/buildings/import/analyze', methods=['POST'])
def analyze_import():
    """Analyze a buildings ZIP file before import."""
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    
    try:
        zip_data = io.BytesIO(file.read())
        
        with zipfile.ZipFile(zip_data, 'r') as zf:
            namelist = zf.namelist()
            
            # Find buildings with valid .stagebox signature
            valid_buildings = []
            for name in namelist:
                if name.endswith('/.stagebox'):
                    building_name = name.rsplit('/', 2)[0]
                    try:
                        sig_data = json.loads(zf.read(name).decode('utf-8'))
                        # Verify signature
                        file_count = sig_data.get('files', 0)
                        signature = sig_data.get('sig', '')
                        if verify_stagebox_signature(building_name, file_count, signature):
                            valid_buildings.append(building_name)
                    except:
                        pass
            
            # No valid buildings found
            if not valid_buildings:
                return jsonify({
                    'success': False,
                    'error': 'Invalid backup file. Please use a file exported from Stagebox.'
                }), 400
            
            # Personal edition: only allow importing one building
            if is_limited() and len(valid_buildings) > 1:
                return jsonify({
                    'success': False,
                    'error': 'This edition supports only one building. Please use a single-building export file.'
                }), 400
            
            # Personal edition: special handling
            if is_limited() and valid_buildings:
                original_name = valid_buildings[0]
                # Add my_ prefix if not present
                if not original_name.startswith('my_'):
                    target_name = 'my_' + original_name
                else:
                    target_name = original_name
                
                # Check if any my_* building exists
                existing_my_buildings = [
                    d.name for d in config.BUILDINGS_DIR.iterdir() 
                    if d.is_dir() and d.name.startswith('my_')
                ]
                
                if existing_my_buildings:
                    # Existing my_* building found - offer to overwrite
                    return jsonify({
                        'success': True,
                        'buildings': [{
                            'name': original_name,
                            'target_name': target_name,
                            'exists': True,
                            'existing_building': existing_my_buildings[0],
                            'action': 'overwrite',
                            'message': f'Will replace "{existing_my_buildings[0]}" with imported building'
                        }],
                        'is_personal': True
                    })
                else:
                    # No my_* building - can import directly
                    return jsonify({
                        'success': True,
                        'buildings': [{
                            'name': original_name,
                            'target_name': target_name,
                            'exists': False,
                            'action': 'import'
                        }],
                        'is_personal': True
                    })
            
            # Pro edition: Check which exist
            result = []
            for building in sorted(valid_buildings):
                exists = (config.BUILDINGS_DIR / building).exists()
                result.append({
                    'name': building,
                    'exists': exists,
                    'action': 'skip' if exists else 'import'
                })
            
            return jsonify({
                'success': True,
                'buildings': result
            })
        
    except zipfile.BadZipFile:
        return jsonify({'success': False, 'error': 'Invalid ZIP file'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500



@bp.route('/api/buildings/import/execute', methods=['POST'])
def execute_import():
    """Execute the import with selected buildings."""
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    selections_json = request.form.get('selections', '[]')
    
    try:
        selections = json.loads(selections_json)
    except:
        return jsonify({'success': False, 'error': 'Invalid selections'}), 400
    
    if not selections:
        return jsonify({'success': False, 'error': 'No buildings selected'}), 400
    
    # Personal edition: only allow importing one building
    if is_limited() and len(selections) > 1:
        return jsonify({
            'success': False,
            'error': 'This edition supports only one building'
        }), 400
    
    # Sanitize building names to prevent path traversal
    for sel in selections:
        name = sel.get('name', '')
        if not name or '..' in name or name.startswith('/') or '\\' in name:
            return jsonify({
                'success': False,
                'error': 'Invalid backup file'
            }), 400
    
    try:
        zip_data = io.BytesIO(file.read())
        
        imported = 0
        skipped = 0
        errors = []
        new_building_name = None
        
        with zipfile.ZipFile(zip_data, 'r') as zf:
            namelist = zf.namelist()
            
            for sel in selections:
                building_name = sel.get('name')
                action = sel.get('action', 'import')
                target_name = sel.get('target_name', building_name)  # For Personal edition rename
                existing_to_delete = sel.get('existing_building')  # For Personal edition overwrite
                
                if not building_name:
                    continue
                
                # Verify signature
                sig_file = f"{building_name}/.stagebox"
                if sig_file not in namelist:
                    errors.append(f"{building_name}: Invalid backup")
                    continue
                
                try:
                    sig_data = json.loads(zf.read(sig_file).decode('utf-8'))
                    file_count = sig_data.get('files', 0)
                    signature = sig_data.get('sig', '')
                    if not verify_stagebox_signature(building_name, file_count, signature):
                        errors.append(f"{building_name}: Invalid backup")
                        continue
                except:
                    errors.append(f"{building_name}: Invalid backup")
                    continue
                
                # Personal edition: delete existing my_* building first
                if is_limited() and existing_to_delete and action == 'overwrite':
                    existing_path = config.BUILDINGS_DIR / existing_to_delete
                    if existing_path.exists():
                        # Deactivate if active
                        if get_active_building() == existing_to_delete:
                            deactivate_building()
                        # Delete existing building (user was offered backup download in UI)
                        shutil.rmtree(str(existing_path))
                
                # Determine target path (may be renamed for Personal edition)
                target_path = config.BUILDINGS_DIR / target_name
                
                if target_path.exists():
                    if action == 'skip':
                        skipped += 1
                        continue
                    elif action == 'overwrite':
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                        backup_path = config.BUILDINGS_DIR / f"{target_name}_old_{timestamp}"
                        shutil.move(str(target_path), str(backup_path))
                
                try:
                    prefix = f"{building_name}/"
                    for name in namelist:
                        if name.startswith(prefix):
                            # Security: skip files with suspicious paths
                            if '..' in name or name.startswith('/'):
                                continue
                            
                            # Skip the signature file itself
                            if name.endswith('/.stagebox'):
                                continue
                            
                            # Replace original building name with target name in path
                            relative_path = name[len(prefix):]
                            target_file = config.BUILDINGS_DIR / target_name / relative_path
                            
                            if name.endswith('/'):
                                target_file.mkdir(parents=True, exist_ok=True)
                            else:
                                target_file.parent.mkdir(parents=True, exist_ok=True)
                                with zf.open(name) as src, open(target_file, 'wb') as dst:
                                    dst.write(src.read())
                    
                    imported += 1
                    new_building_name = target_name
                    
                except Exception as e:
                    errors.append(f"{building_name}: {str(e)}")
        
        # Personal edition: activate the imported building
        if is_limited() and new_building_name and imported > 0:
            activate_building(new_building_name)
        
        return jsonify({
            'success': True,
            'imported': imported,
            'skipped': skipped,
            'errors': errors,
            'new_building': new_building_name if is_limited() else None
        })
        
    except zipfile.BadZipFile:
        return jsonify({'success': False, 'error': 'Invalid ZIP file'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ===========================================================================
# Building Profile
# ===========================================================================

@bp.route('/api/settings/building-profile', methods=['GET'])
def get_building_profile():
    """Get the building profile for the active building."""
    if not is_building_active():
        return jsonify({'success': False, 'error': 'No building active'}), 400
    
    profile_file = config.DATA_DIR / 'building_profile.json'
    
    try:
        if profile_file.exists():
            import json
            with open(profile_file, 'r', encoding='utf-8') as f:
                profile = json.load(f)
        else:
            # Return default empty profile
            profile = {
                'object_name': '',
                'address': '',
                'customer_name': '',
                'contact_phone': '',
                'contact_email': '',
                'notes': ''
            }
        
        return jsonify({'success': True, 'profile': profile})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/settings/building-profile', methods=['POST'])
def save_building_profile():
    """Save the building profile for the active building."""
    if not is_building_active():
        return jsonify({'success': False, 'error': 'No building active'}), 400
    
    profile_file = config.DATA_DIR / 'building_profile.json'
    
    try:
        import json
        data = request.get_json() or {}
        
        # Validate and extract profile fields
        profile = {
            'object_name': str(data.get('object_name', '')).strip()[:200],
            'address': str(data.get('address', '')).strip()[:500],
            'customer_name': str(data.get('customer_name', '')).strip()[:200],
            'contact_phone': str(data.get('contact_phone', '')).strip()[:50],
            'contact_email': str(data.get('contact_email', '')).strip()[:100],
            'notes': str(data.get('notes', '')).strip()[:1000]
        }
        
        # Save profile
        with open(profile_file, 'w', encoding='utf-8') as f:
            json.dump(profile, f, indent=2, ensure_ascii=False)
        
        return jsonify({'success': True, 'message': 'Building profile saved'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ===========================================================================
# Building Rename (available in all editions)
# ===========================================================================

@bp.route('/api/admin/buildings/rename', methods=['POST'])
def admin_rename_building():
    """Rename a building. Available in all editions."""
    data = request.get_json() or {}
    old_name = data.get('old_name', '').strip()
    new_name = data.get('new_name', '').strip()
    
    if not old_name or not new_name:
        return jsonify({'success': False, 'error': 'Both old and new name required'}), 400
    
    # Normalize new name
    new_name = new_name.lower().replace(' ', '_').replace('-', '_')
    new_name = re.sub(r'[^a-z0-9_]', '', new_name)
    new_name = re.sub(r'_+', '_', new_name)
    new_name = new_name.strip('_')
    
    if not new_name:
        return jsonify({'success': False, 'error': 'Invalid name'}), 400
    
    # Personal edition: ensure "my_" prefix
    if is_limited() and not new_name.startswith('my_'):
        new_name = 'my_' + new_name
    
    if len(new_name) > 32:
        return jsonify({'success': False, 'error': 'Name too long (max 32 characters)'}), 400
    
    if new_name == old_name:
        return jsonify({'success': True, 'message': 'Name unchanged', 'name': new_name})
    
    old_path = config.BUILDINGS_DIR / old_name
    if not old_path.exists():
        return jsonify({'success': False, 'error': 'Building not found'}), 404
    
    new_path = config.BUILDINGS_DIR / new_name
    if new_path.exists():
        return jsonify({'success': False, 'error': f'Building "{new_name}" already exists'}), 400
    
    try:
        old_path.rename(new_path)
        
        # Update active_building reference if needed
        if config.active_building == old_name:
            config.active_building = new_name
            # Re-activate to update paths
            activate_building(new_name)
        
        return jsonify({
            'success': True, 
            'message': f'Building renamed to "{new_name}"',
            'name': new_name
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ===========================================================================
# Building Delete / Reset (Pro: delete, Personal: reset to empty)
# ===========================================================================

@bp.route('/api/admin/buildings/delete', methods=['POST'])
def admin_delete_building():
    """
    Delete a building.
    - Pro edition: Deletes the building
    - Personal edition: Resets the building (delete + create new empty one)
    """
    import subprocess
    from web.services.building_manager import create_building
    
    data = request.get_json() or {}
    name = data.get('name', '').strip()
    
    if not name:
        return jsonify({'success': False, 'error': 'Building name required'}), 400
    
    building_path = config.BUILDINGS_DIR / name / 'stagebox' / 'data' / 'config.yaml'
    if not building_path.exists():
        return jsonify({'success': False, 'error': 'Building not found'}), 404
    
    # For Pro edition: cannot delete active building
    # For Personal edition: we're resetting, so active is OK
    if is_pro() and name == get_active_building():
        return jsonify({'success': False, 'error': 'Cannot delete active building'}), 400
    
    try:
        # Deactivate if this is the active building (Personal reset case)
        was_active = (name == get_active_building())
        if was_active:
            deactivate_building()
        
        # Delete the building
        result = subprocess.run(
            ['/home/coredev/scripts/building_scripts/del_building.sh', name],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode != 0:
            return jsonify({'success': False, 'error': result.stderr or 'Delete failed'}), 500
        
        # Personal edition: immediately create a new empty building
        if is_limited():
            create_result = create_building('my_building')
            if create_result.get('success'):
                new_name = create_result.get('name', 'my_building')
                # Activate the new building
                activate_building(new_name)
                return jsonify({
                    'success': True, 
                    'message': 'Building reset successfully',
                    'new_building': new_name,
                    'is_reset': True
                })
            else:
                return jsonify({
                    'success': False, 
                    'error': 'Building deleted but failed to create new one: ' + create_result.get('error', '')
                }), 500
        
        # Pro edition: just confirm deletion
        return jsonify({'success': True, 'message': f'Building {name} deleted'})
        
    except subprocess.TimeoutExpired:
        return jsonify({'success': False, 'error': 'Timeout'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
