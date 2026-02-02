"""
Stagebox Admin Routes (Pro Only)

PIN-protected admin functions.
"""

import hashlib
import subprocess
import time
from functools import wraps
from pathlib import Path
from flask import Blueprint, jsonify, request, session

import yaml

from web import config
from web.edition import is_pro

bp = Blueprint('admin', __name__)

# Master PIN (recovery)
MASTER_PIN_HASH = hashlib.sha256('09071959'.encode()).hexdigest()
DEFAULT_PIN = '0000'


def hash_pin(pin: str) -> str:
    """Hash a PIN using SHA256."""
    return hashlib.sha256(pin.encode()).hexdigest()


def load_admin_config():
    """Load admin configuration."""
    if config.ADMIN_CONFIG_FILE.exists():
        try:
            with open(config.ADMIN_CONFIG_FILE, 'r') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            print(f"Error loading admin config: {e}")
    return {}


def save_admin_config(cfg):
    """Save admin configuration."""
    try:
        config.ADMIN_CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(config.ADMIN_CONFIG_FILE, 'w') as f:
            yaml.dump(cfg, f, default_flow_style=False)
        return True
    except Exception as e:
        print(f"Error saving admin config: {e}")
        return False


def is_admin_authenticated():
    """Check if current session has valid admin authentication."""
    if 'admin_auth_time' not in session:
        return False
    
    auth_time = session['admin_auth_time']
    if time.time() - auth_time > config.ADMIN_SESSION_TIMEOUT:
        session.pop('admin_auth_time', None)
        return False
    
    return True


def require_admin(f):
    """Decorator to require admin authentication.
    
    Personal Edition: No auth required (skip check).
    Pro Edition: Requires PIN authentication.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Personal Edition: No admin auth needed
        if not is_pro():
            return f(*args, **kwargs)
        
        # Pro Edition: Require authentication
        if not is_admin_authenticated():
            return jsonify({'success': False, 'error': 'Admin authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function


def require_pro(f):
    """Decorator to require Pro edition."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_pro():
            return jsonify({
                'success': False, 
                'error': 'This feature requires Stagebox Pro',
                'pro_required': True
            }), 403
        return f(*args, **kwargs)
    return decorated_function


@bp.route('/api/admin/status', methods=['GET'])
def admin_status():
    """Check admin authentication status and if PIN is set."""
    admin_cfg = load_admin_config()
    pin_set = 'pin_hash' in admin_cfg and admin_cfg['pin_hash']
    
    return jsonify({
        'success': True,
        'authenticated': is_admin_authenticated(),
        'pin_set': pin_set,
        'pro_edition': is_pro()
    })


@bp.route('/api/admin/authenticate', methods=['POST'])
def admin_authenticate():
    """Authenticate with admin PIN."""
    data = request.get_json() or {}
    pin = data.get('pin', '')
    
    if not pin:
        return jsonify({'success': False, 'error': 'PIN required'}), 400
    
    # Check master PIN first
    if hash_pin(pin) == MASTER_PIN_HASH:
        session['admin_auth_time'] = time.time()
        return jsonify({'success': True, 'message': 'Authenticated'})
    
    admin_cfg = load_admin_config()
    
    # If no PIN set, use default factory PIN
    if 'pin_hash' not in admin_cfg or not admin_cfg['pin_hash']:
        if pin == DEFAULT_PIN:
            session['admin_auth_time'] = time.time()
            return jsonify({'success': True, 'message': 'Authenticated', 'default_pin': True})
        return jsonify({'success': False, 'error': 'Invalid PIN'}), 401
    
    # Verify PIN
    if hash_pin(pin) == admin_cfg['pin_hash']:
        session['admin_auth_time'] = time.time()
        return jsonify({'success': True, 'message': 'Authenticated'})
    
    return jsonify({'success': False, 'error': 'Invalid PIN'}), 401


@bp.route('/api/admin/logout', methods=['POST'])
def admin_logout():
    """Logout from admin session."""
    session.pop('admin_auth_time', None)
    return jsonify({'success': True, 'message': 'Logged out'})


@bp.route('/api/admin/setup-pin', methods=['POST'])
def admin_setup_pin():
    """Set up initial admin PIN."""
    data = request.get_json() or {}
    pin = data.get('pin', '')
    
    if not pin or len(pin) < 4:
        return jsonify({'success': False, 'error': 'PIN must be at least 4 characters'}), 400
    
    admin_cfg = load_admin_config()
    
    if 'pin_hash' in admin_cfg and admin_cfg['pin_hash']:
        return jsonify({'success': False, 'error': 'PIN already configured'}), 400
    
    admin_cfg['pin_hash'] = hash_pin(pin)
    
    if save_admin_config(admin_cfg):
        session['admin_auth_time'] = time.time()
        return jsonify({'success': True, 'message': 'PIN configured'})
    
    return jsonify({'success': False, 'error': 'Failed to save PIN'}), 500


@bp.route('/api/admin/change-pin', methods=['POST'])
@require_admin
def admin_change_pin():
    """Change admin PIN."""
    data = request.get_json() or {}
    new_pin = data.get('new_pin', '')
    
    if not new_pin or len(new_pin) < 4:
        return jsonify({'success': False, 'error': 'PIN must be at least 4 characters'}), 400
    
    admin_cfg = load_admin_config()
    admin_cfg['pin_hash'] = hash_pin(new_pin)
    
    if save_admin_config(admin_cfg):
        return jsonify({'success': True, 'message': 'PIN changed'})
    
    return jsonify({'success': False, 'error': 'Failed to save PIN'}), 500


# ===========================================================================
# Admin Settings
# ===========================================================================

@bp.route('/api/admin/settings', methods=['GET'])
@require_admin
def admin_get_settings():
    """Get building settings from config.yaml."""
    if not config.DATA_DIR:
        return jsonify({'success': False, 'error': 'No building active'}), 400
    
    config_path = config.DATA_DIR / 'config.yaml'
    if not config_path.exists():
        return jsonify({'success': False, 'error': 'config.yaml not found'}), 404
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            cfg = yaml.safe_load(f) or {}
        
        settings = {
            'stage1': {
                'loop_mode': cfg.get('stage1', {}).get('options', {}).get('loop_mode', True),
                'disable_ap': cfg.get('stage1', {}).get('options', {}).get('disable_ap', True),
                'disable_bluetooth': cfg.get('stage1', {}).get('options', {}).get('disable_bluetooth', True),
                'disable_cloud': cfg.get('stage1', {}).get('options', {}).get('disable_cloud', True),
                'mqtt_disable': cfg.get('stage1', {}).get('options', {}).get('mqtt_disable', True),
            },
            'stage3': {
                'ota_enabled': cfg.get('stage3', {}).get('ota', {}).get('enabled', True),
                'ota_mode': cfg.get('stage3', {}).get('ota', {}).get('mode', 'check_and_update'),
                'ota_timeout': cfg.get('stage3', {}).get('ota', {}).get('timeout', 20),
            },
            'report': {
                'csv_delimiter': cfg.get('report', {}).get('export', {}).get('csv_delimiter', ';'),
                'default_columns': cfg.get('report', {}).get('export', {}).get('default_columns', []),
            }
        }
        
        return jsonify({'success': True, 'settings': settings})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/admin/settings', methods=['PUT'])
@require_admin
def admin_save_settings():
    """Save building settings to config.yaml."""
    if not config.DATA_DIR:
        return jsonify({'success': False, 'error': 'No building active'}), 400
    
    data = request.get_json() or {}
    
    # Handle nested 'settings' wrapper from frontend
    if 'settings' in data:
        data = data['settings']
    
    try:
        cfg = config.load_config()
        
        # Update stage1 options
        if 'stage1' in data:
            if 'stage1' not in cfg:
                cfg['stage1'] = {}
            if 'options' not in cfg['stage1']:
                cfg['stage1']['options'] = {}
            
            s1 = data['stage1']
            for key in ['loop_mode', 'disable_ap', 'disable_bluetooth', 'disable_cloud', 'mqtt_disable']:
                if key in s1:
                    cfg['stage1']['options'][key] = s1[key]
        
        # Update stage3 options
        if 'stage3' in data:
            if 'stage3' not in cfg:
                cfg['stage3'] = {}
            
            s3 = data['stage3']
            if 'ota' not in cfg['stage3']:
                cfg['stage3']['ota'] = {}
            if 'friendly' not in cfg['stage3']:
                cfg['stage3']['friendly'] = {}
            
            for key in ['enabled', 'mode', 'timeout']:
                ota_key = f'ota_{key}' if key != 'enabled' else 'ota_enabled'
                if ota_key in s3:
                    cfg['stage3']['ota'][key] = s3[ota_key]
        
        # Update report/export options
        if 'report' in data:
            if 'report' not in cfg:
                cfg['report'] = {}
            if 'export' not in cfg['report']:
                cfg['report']['export'] = {}
            
            rpt = data['report']
            if 'csv_delimiter' in rpt:
                cfg['report']['export']['csv_delimiter'] = rpt['csv_delimiter']
            if 'default_columns' in rpt:
                cfg['report']['export']['default_columns'] = rpt['default_columns']
        
        # Save
        with open(config.CONFIG_FILE, 'w', encoding='utf-8') as f:
            yaml.dump(cfg, f, default_flow_style=False, allow_unicode=True)
        
        return jsonify({'success': True, 'message': 'Settings saved'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ===========================================================================
# Model Map (Pro Only)
# ===========================================================================

@bp.route('/api/admin/model-map', methods=['GET'])
@require_pro
@require_admin
def get_model_map():
    """Get shelly model mapping."""
    model_map = config.load_model_mapping()
    # Convert dict to list of entries for frontend
    entries = [{'hw_id': k, 'display_name': v} for k, v in model_map.items()]
    return jsonify({'success': True, 'models': model_map, 'entries': entries})


@bp.route('/api/admin/model-map', methods=['PUT'])
@require_pro
@require_admin
def save_model_map():
    """Save shelly model mapping."""
    if not config.DATA_DIR:
        return jsonify({'success': False, 'error': 'No building active'}), 400
    
    data = request.get_json() or {}
    
    # Accept both 'models' (dict) and 'entries' (list) format
    if 'entries' in data:
        # Convert list of {hw_id, display_name} to dict
        models = {e['hw_id']: e['display_name'] for e in data['entries'] if e.get('hw_id') and e.get('display_name')}
    else:
        models = data.get('models', {})
    
    # Don't overwrite if no models provided - keep existing
    if not models:
        return jsonify({'success': True, 'message': 'No changes (empty model map)'})
    
    try:
        model_map_file = config.DATA_DIR / 'shelly_model_map.yaml'
        with open(model_map_file, 'w', encoding='utf-8') as f:
            yaml.dump(models, f, default_flow_style=False, allow_unicode=True)
        
        return jsonify({'success': True, 'message': 'Model map saved'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ===========================================================================
# Installer Profile (Pro Only)
# ===========================================================================

# File paths for installer profile
INSTALLER_PROFILE_FILE = config.STAGEBOX_ROOT / 'data' / 'installer_profile.json'
INSTALLER_LOGO_FILE = config.STAGEBOX_ROOT / 'data' / 'installer_logo.png'
INSTALLER_LOGO_MAX_SIZE = 2 * 1024 * 1024  # 2 MB
INSTALLER_LOGO_MAX_WIDTH = 800
INSTALLER_LOGO_MAX_HEIGHT = 400


@bp.route('/api/admin/installer-profile', methods=['GET'])
@require_pro
@require_admin
def get_installer_profile():
    """Get the global installer profile."""
    import json
    try:
        if INSTALLER_PROFILE_FILE.exists():
            with open(INSTALLER_PROFILE_FILE, 'r', encoding='utf-8') as f:
                profile = json.load(f)
        else:
            # Return default empty profile
            profile = {
                'company_name': '',
                'address': '',
                'phone': '',
                'email': '',
                'website': ''
            }
        
        # Check if logo exists
        profile['has_logo'] = INSTALLER_LOGO_FILE.exists()
        
        return jsonify({'success': True, 'profile': profile})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/admin/installer-profile', methods=['POST'])
@require_pro
@require_admin
def save_installer_profile():
    """Save the global installer profile."""
    import json
    try:
        data = request.get_json() or {}
        
        # Validate and extract profile fields
        profile = {
            'company_name': str(data.get('company_name', '')).strip()[:200],
            'address': str(data.get('address', '')).strip()[:500],
            'phone': str(data.get('phone', '')).strip()[:50],
            'email': str(data.get('email', '')).strip()[:100],
            'website': str(data.get('website', '')).strip()[:100]
        }
        
        # Ensure data directory exists
        INSTALLER_PROFILE_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        # Save profile
        with open(INSTALLER_PROFILE_FILE, 'w', encoding='utf-8') as f:
            json.dump(profile, f, indent=2, ensure_ascii=False)
        
        return jsonify({'success': True, 'message': 'Profile saved'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/admin/installer-logo', methods=['GET'])
@require_pro
def get_installer_logo():
    """Get the installer logo image."""
    from flask import send_file
    
    if not INSTALLER_LOGO_FILE.exists():
        return jsonify({'success': False, 'error': 'No logo uploaded'}), 404
    
    try:
        return send_file(
            INSTALLER_LOGO_FILE,
            mimetype='image/png',
            as_attachment=False,
            download_name='installer_logo.png'
        )
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/admin/installer-logo', methods=['POST'])
@require_pro
@require_admin
def upload_installer_logo():
    """Upload a new installer logo."""
    try:
        if 'logo' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400
        
        file = request.files['logo']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        # Check file size
        file.seek(0, 2)  # Seek to end
        size = file.tell()
        file.seek(0)  # Seek back to start
        
        if size > INSTALLER_LOGO_MAX_SIZE:
            return jsonify({
                'success': False, 
                'error': f'File too large. Maximum size is {INSTALLER_LOGO_MAX_SIZE // 1024 // 1024} MB'
            }), 400
        
        # Read and validate image
        from PIL import Image
        
        try:
            img = Image.open(file)
            
            # Resize if too large while maintaining aspect ratio
            if img.width > INSTALLER_LOGO_MAX_WIDTH or img.height > INSTALLER_LOGO_MAX_HEIGHT:
                img.thumbnail((INSTALLER_LOGO_MAX_WIDTH, INSTALLER_LOGO_MAX_HEIGHT), Image.Resampling.LANCZOS)
            
            # Convert to RGBA if necessary for PNG transparency support
            if img.mode not in ('RGBA', 'RGB'):
                img = img.convert('RGBA')
            
            # Ensure data directory exists
            INSTALLER_LOGO_FILE.parent.mkdir(parents=True, exist_ok=True)
            
            # Save as PNG
            img.save(INSTALLER_LOGO_FILE, 'PNG', optimize=True)
            
            return jsonify({
                'success': True, 
                'message': 'Logo uploaded',
                'width': img.width,
                'height': img.height
            })
        except Exception as img_error:
            return jsonify({
                'success': False, 
                'error': f'Invalid image file: {str(img_error)}'
            }), 400
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/admin/installer-logo', methods=['DELETE'])
@require_pro
@require_admin
def delete_installer_logo():
    """Delete the installer logo."""
    try:
        if INSTALLER_LOGO_FILE.exists():
            INSTALLER_LOGO_FILE.unlink()
            return jsonify({'success': True, 'message': 'Logo deleted'})
        else:
            return jsonify({'success': False, 'error': 'No logo to delete'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ===========================================================================
# Profile Files (Advanced Editor)
# ===========================================================================

@bp.route('/api/admin/profiles', methods=['GET'])
@require_pro
@require_admin
def list_profiles():
    """List available profile files, config.yaml and secrets.yaml for Advanced editor."""
    if not config.DATA_DIR:
        return jsonify({'success': False, 'error': 'No building active'}), 400
    
    files = []
    
    # Add config.yaml
    config_path = config.DATA_DIR / 'config.yaml'
    if config_path.exists():
        files.append({'name': 'config.yaml', 'path': 'config.yaml', 'type': 'config'})
    
    # Add secrets.yaml (show even if not exists, will be created on first save)
    secrets_path = config.DATA_DIR / 'secrets.yaml'
    files.append({
        'name': 'secrets.yaml',
        'path': 'secrets.yaml',
        'type': 'secrets',
        'exists': secrets_path.exists()
    })
    
    # Add profiles
    profiles_dir = config.DATA_DIR / 'profiles'
    if profiles_dir.exists():
        for f in sorted(profiles_dir.glob('*.yaml')):
            files.append({
                'name': f.name,
                'path': f'profiles/{f.name}',
                'type': 'profile'
            })
    
    return jsonify({'success': True, 'files': files})


@bp.route('/api/admin/profiles/<path:filepath>', methods=['GET'])
@require_pro
@require_admin
def get_profile(filepath):
    """Get content of a profile file, config.yaml or secrets.yaml."""
    if not config.DATA_DIR:
        return jsonify({'success': False, 'error': 'No building active'}), 400
    
    # Security: only allow config.yaml, secrets.yaml or files in profiles/
    if filepath == 'config.yaml':
        file_path = config.DATA_DIR / 'config.yaml'
    elif filepath == 'secrets.yaml':
        file_path = config.DATA_DIR / 'secrets.yaml'
    elif filepath.startswith('profiles/') and filepath.endswith('.yaml'):
        file_path = config.DATA_DIR / filepath
    else:
        return jsonify({'success': False, 'error': 'Invalid file path'}), 400
    
    # For secrets.yaml, return template if file doesn't exist
    if not file_path.exists():
        if filepath == 'secrets.yaml':
            template = """# Stagebox Secrets Configuration
# Add your credentials here (MQTT, external services, etc.)

# Example MQTT configuration:
# mqtt:
#   broker: "mqtt.example.com"
#   port: 1883
#   username: "user"
#   password: "secret"

# WiFi profiles are managed via Network Settings dialog
# wifi_profiles:
#   - ssid: "MyNetwork"
#     password: "secret"
"""
            return jsonify({
                'success': True,
                'content': template,
                'filepath': filepath,
                'valid': True,
                'parse_error': None,
                'is_new': True
            })
        return jsonify({'success': False, 'error': 'File not found'}), 404
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Validate YAML
        try:
            yaml.safe_load(content)
            valid = True
            parse_error = None
        except yaml.YAMLError as e:
            valid = False
            parse_error = str(e)
        
        return jsonify({
            'success': True,
            'content': content,
            'filepath': filepath,
            'valid': valid,
            'parse_error': parse_error
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/admin/profiles/<path:filepath>', methods=['PUT'])
@require_pro
@require_admin
def save_profile(filepath):
    """Save content to a profile file, config.yaml or secrets.yaml."""
    if not config.DATA_DIR:
        return jsonify({'success': False, 'error': 'No building active'}), 400
    
    # Security: only allow config.yaml, secrets.yaml or files in profiles/
    if filepath == 'config.yaml':
        file_path = config.DATA_DIR / 'config.yaml'
    elif filepath == 'secrets.yaml':
        file_path = config.DATA_DIR / 'secrets.yaml'
    elif filepath.startswith('profiles/') and filepath.endswith('.yaml'):
        file_path = config.DATA_DIR / filepath
        file_path.parent.mkdir(parents=True, exist_ok=True)
    else:
        return jsonify({'success': False, 'error': 'Invalid file path'}), 400
    
    data = request.get_json() or {}
    content = data.get('content', '')
    
    if not content.strip():
        return jsonify({'success': False, 'error': 'Content cannot be empty'}), 400
    
    # Validate YAML
    try:
        yaml.safe_load(content)
    except yaml.YAMLError as e:
        return jsonify({
            'success': False,
            'error': 'Invalid YAML syntax',
            'parse_error': str(e)
        }), 400
    
    try:
        # Create backup
        if file_path.exists():
            from datetime import datetime
            import shutil
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = file_path.parent / f"{file_path.stem}.bak_{timestamp}{file_path.suffix}"
            shutil.copy2(file_path, backup_path)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return jsonify({'success': True, 'message': f'{filepath} saved'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ===========================================================================
# YAML Editor Routes
# ===========================================================================

def _get_yaml_file_path(file_type: str):
    """Get the path to a YAML config file."""
    if not config.DATA_DIR:
        return None
    
    if file_type == 'config':
        return config.DATA_DIR / 'config.yaml'
    elif file_type == 'secrets':
        return config.DATA_DIR / 'secrets.yaml'
    else:
        return None


def _create_yaml_backup(file_path):
    """Create a timestamped backup of a YAML file."""
    import glob
    import shutil
    import time as time_module
    
    if not file_path.exists():
        return None
    
    try:
        timestamp = time_module.strftime('%Y%m%d_%H%M%S')
        backup_path = file_path.with_suffix(f'.yaml.bak_{timestamp}')
        
        shutil.copy2(file_path, backup_path)
        
        # Keep only last 5 backups
        backup_pattern = str(file_path) + '.bak_*'
        backups = sorted(glob.glob(backup_pattern), reverse=True)
        for old_backup in backups[5:]:
            try:
                Path(old_backup).unlink()
            except:
                pass
        
        return backup_path
    except Exception as e:
        print(f"Error creating backup: {e}")
        return None


@bp.route('/api/admin/yaml/<file_type>', methods=['GET'])
@require_admin
def admin_get_yaml(file_type: str):
    """Get contents of a YAML config file."""
    if file_type not in ('config', 'secrets'):
        return jsonify({'success': False, 'error': 'Invalid file type'}), 400
    
    if not config.active_building:
        return jsonify({'success': False, 'error': 'No building active'}), 400
    
    file_path = _get_yaml_file_path(file_type)
    if not file_path:
        return jsonify({'success': False, 'error': 'Could not determine file path'}), 500
    
    if not file_path.exists():
        return jsonify({
            'success': True,
            'content': '',
            'file_type': file_type,
            'file_path': str(file_path),
            'exists': False
        })
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Validate it's valid YAML
        try:
            yaml.safe_load(content)
            valid = True
            error = None
        except yaml.YAMLError as e:
            valid = False
            error = str(e)
        
        return jsonify({
            'success': True,
            'content': content,
            'file_type': file_type,
            'file_path': str(file_path),
            'exists': True,
            'valid': valid,
            'parse_error': error
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/admin/yaml/<file_type>', methods=['PUT'])
@require_admin
def admin_save_yaml(file_type: str):
    """Save contents to a YAML config file."""
    if file_type not in ('config', 'secrets'):
        return jsonify({'success': False, 'error': 'Invalid file type'}), 400
    
    if not config.active_building:
        return jsonify({'success': False, 'error': 'No building active'}), 400
    
    data = request.get_json() or {}
    content = data.get('content', '')
    
    if not content.strip():
        return jsonify({'success': False, 'error': 'Content cannot be empty'}), 400
    
    # Validate YAML syntax
    try:
        yaml.safe_load(content)
    except yaml.YAMLError as e:
        return jsonify({
            'success': False, 
            'error': 'Invalid YAML syntax',
            'parse_error': str(e)
        }), 400
    
    file_path = _get_yaml_file_path(file_type)
    if not file_path:
        return jsonify({'success': False, 'error': 'Could not determine file path'}), 500
    
    try:
        # Create backup before saving
        backup_path = None
        if file_path.exists():
            backup_path = _create_yaml_backup(file_path)
        
        # Write new content
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return jsonify({
            'success': True,
            'message': f'{file_type}.yaml saved successfully',
            'backup_created': backup_path is not None,
            'backup_path': str(backup_path) if backup_path else None
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/admin/yaml/<file_type>/validate', methods=['POST'])
@require_admin
def admin_validate_yaml(file_type: str):
    """Validate YAML content without saving."""
    data = request.get_json() or {}
    content = data.get('content', '')
    
    if not content.strip():
        return jsonify({
            'success': True,
            'valid': False,
            'error': 'Content is empty'
        })
    
    try:
        parsed = yaml.safe_load(content)
        
        # Additional validation for specific file types
        warnings = []
        
        if file_type == 'config':
            if not parsed:
                warnings.append('Config is empty')
            else:
                if 'stage2' not in parsed:
                    warnings.append('Missing stage2 section')
                if 'stage3' not in parsed:
                    warnings.append('Missing stage3 section')
                if 'stage4' not in parsed:
                    warnings.append('Missing stage4 section')
        
        elif file_type == 'secrets':
            if not parsed:
                warnings.append('Secrets file is empty')
            else:
                if 'wifi_profiles' not in parsed:
                    warnings.append('Missing wifi_profiles - Stage 1 will not work')
                elif not parsed.get('wifi_profiles'):
                    warnings.append('wifi_profiles is empty - Stage 1 will not work')
        
        return jsonify({
            'success': True,
            'valid': True,
            'warnings': warnings,
            'parsed_keys': list(parsed.keys()) if parsed else []
        })
        
    except yaml.YAMLError as e:
        error_msg = str(e)
        line_number = None
        
        if hasattr(e, 'problem_mark') and e.problem_mark:
            line_number = e.problem_mark.line + 1
        
        return jsonify({
            'success': True,
            'valid': False,
            'error': error_msg,
            'line_number': line_number
        })


@bp.route('/api/admin/yaml/<file_type>/backups', methods=['GET'])
@require_admin
def admin_list_yaml_backups(file_type: str):
    """List available backups for a YAML file."""
    import glob
    import time as time_module
    
    if file_type not in ('config', 'secrets'):
        return jsonify({'success': False, 'error': 'Invalid file type'}), 400
    
    file_path = _get_yaml_file_path(file_type)
    if not file_path:
        return jsonify({'success': False, 'error': 'Could not determine file path'}), 500
    
    try:
        backup_pattern = str(file_path) + '.bak_*'
        backups = []
        
        for backup_file in sorted(glob.glob(backup_pattern), reverse=True):
            backup_path = Path(backup_file)
            stat = backup_path.stat()
            backups.append({
                'filename': backup_path.name,
                'path': str(backup_path),
                'size': stat.st_size,
                'modified': stat.st_mtime,
                'modified_iso': time_module.strftime('%Y-%m-%d %H:%M:%S', time_module.localtime(stat.st_mtime))
            })
        
        return jsonify({
            'success': True,
            'backups': backups
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/admin/yaml/<file_type>/restore', methods=['POST'])
@require_admin
def admin_restore_yaml_backup(file_type: str):
    """Restore a YAML file from backup."""
    import shutil
    
    if file_type not in ('config', 'secrets'):
        return jsonify({'success': False, 'error': 'Invalid file type'}), 400
    
    data = request.get_json() or {}
    backup_path = data.get('backup_path', '')
    
    if not backup_path:
        return jsonify({'success': False, 'error': 'Backup path required'}), 400
    
    backup_file = Path(backup_path)
    if not backup_file.exists():
        return jsonify({'success': False, 'error': 'Backup file not found'}), 404
    
    # Security: Ensure backup is in expected directory
    file_path = _get_yaml_file_path(file_type)
    if not file_path:
        return jsonify({'success': False, 'error': 'Could not determine file path'}), 500
    
    if backup_file.parent != file_path.parent:
        return jsonify({'success': False, 'error': 'Invalid backup path'}), 400
    
    try:
        # Read backup content
        with open(backup_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Validate YAML
        yaml.safe_load(content)
        
        # Backup current file before restoring
        _create_yaml_backup(file_path)
        
        # Restore
        shutil.copy2(backup_file, file_path)
        
        return jsonify({
            'success': True,
            'message': f'{file_type}.yaml restored from backup'
        })
    except yaml.YAMLError as e:
        return jsonify({
            'success': False,
            'error': f'Backup file contains invalid YAML: {e}'
        }), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ===========================================================================
# Dependencies Management
# ===========================================================================

DEPENDENCIES_FILE = Path('/home/coredev/stagebox/dependencies.yaml')
DEPS_PENDING_FILE = Path('/tmp/stagebox_deps_pending')


def load_dependencies():
    """Load dependencies from dependencies.yaml."""
    if not DEPENDENCIES_FILE.exists():
        return {'apt': [], 'pip': [], 'apt_update_prefixes': []}
    
    try:
        with open(DEPENDENCIES_FILE, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        print(f"Error loading dependencies.yaml: {e}")
        return {'apt': [], 'pip': [], 'apt_update_prefixes': []}


def check_apt_package_installed(package: str) -> bool:
    """Check if an apt package is installed."""
    try:
        result = subprocess.run(
            ['dpkg', '-s', package],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0 and 'Status: install ok installed' in result.stdout
    except:
        return False


def check_pip_package_installed(package: str):
    """Check if a pip package is installed. Returns (is_installed, version)."""
    # Extract package name (without version spec)
    pkg_name = package.split('>=')[0].split('==')[0].split('<')[0].strip()
    
    try:
        result = subprocess.run(
            ['pip3', 'show', pkg_name],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if line.startswith('Version:'):
                    version = line.split(':', 1)[1].strip()
                    return True, version
            return True, None
        return False, None
    except:
        return False, None


@bp.route('/api/admin/system/deps/check', methods=['GET'])
@require_admin
def check_dependencies():
    """Check for missing or pending dependencies."""
    deps = load_dependencies()
    
    missing_apt = []
    missing_pip = []
    
    for pkg in deps.get('apt', []):
        if not check_apt_package_installed(pkg):
            missing_apt.append(pkg)
    
    for pkg in deps.get('pip', []):
        installed, version = check_pip_package_installed(pkg)
        if not installed:
            pkg_name = pkg.split('>=')[0].split('==')[0].split('<')[0].strip()
            missing_pip.append(pkg_name)
    
    deps_pending = DEPS_PENDING_FILE.exists()
    
    return jsonify({
        'success': True,
        'missing_apt': missing_apt,
        'missing_pip': missing_pip,
        'has_missing': len(missing_apt) > 0 or len(missing_pip) > 0,
        'deps_pending': deps_pending
    })


@bp.route('/api/admin/system/deps/install', methods=['POST'])
@require_admin
def install_dependencies():
    """Install missing dependencies (apt and pip)."""
    deps = load_dependencies()
    
    # Re-check what's actually missing
    missing_apt = []
    missing_pip = []
    
    for pkg in deps.get('apt', []):
        if not check_apt_package_installed(pkg):
            missing_apt.append(pkg)
    
    for pkg in deps.get('pip', []):
        installed, _ = check_pip_package_installed(pkg)
        if not installed:
            missing_pip.append(pkg)
    
    if not missing_apt and not missing_pip:
        # Clear pending flag if exists
        if DEPS_PENDING_FILE.exists():
            DEPS_PENDING_FILE.unlink()
        return jsonify({
            'success': True,
            'message': 'All dependencies already installed',
            'installed_apt': 0,
            'installed_pip': 0
        })
    
    results = {
        'apt_success': [],
        'apt_failed': [],
        'pip_success': [],
        'pip_failed': []
    }
    
    try:
        # Install apt packages
        if missing_apt:
            # First update package lists
            subprocess.run(
                ['sudo', 'apt-get', 'update'],
                capture_output=True,
                timeout=300
            )
            
            # Install packages
            cmd = ['sudo', 'apt-get', 'install', '-y'] + missing_apt
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=1800
            )
            
            if result.returncode == 0:
                results['apt_success'] = missing_apt
            else:
                # Try installing one by one
                for pkg in missing_apt:
                    pkg_result = subprocess.run(
                        ['sudo', 'apt-get', 'install', '-y', pkg],
                        capture_output=True,
                        text=True,
                        timeout=600
                    )
                    if pkg_result.returncode == 0:
                        results['apt_success'].append(pkg)
                    else:
                        results['apt_failed'].append(pkg)
        
        # Install pip packages
        if missing_pip:
            for pkg in missing_pip:
                result = subprocess.run(
                    ['pip3', 'install', '--break-system-packages', pkg],
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                if result.returncode == 0:
                    results['pip_success'].append(pkg)
                else:
                    results['pip_failed'].append(pkg)
        
        # Clear pending flag
        if DEPS_PENDING_FILE.exists():
            DEPS_PENDING_FILE.unlink()
        
        reboot_recommended = len(results['apt_success']) > 0
        total_success = len(results['apt_success']) + len(results['pip_success'])
        total_failed = len(results['apt_failed']) + len(results['pip_failed'])
        
        return jsonify({
            'success': total_failed == 0,
            'message': f'{total_success} packages installed' + 
                      (f', {total_failed} failed' if total_failed > 0 else ''),
            'installed_apt': len(results['apt_success']),
            'installed_pip': len(results['pip_success']),
            'failed_apt': results['apt_failed'],
            'failed_pip': results['pip_failed'],
            'reboot_recommended': reboot_recommended
        })
        
    except subprocess.TimeoutExpired:
        return jsonify({
            'success': False,
            'error': 'Operation timed out. Try again or check your internet connection.'
        }), 504
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/api/admin/system/deps/set-pending', methods=['POST'])
@require_admin
def set_deps_pending():
    """Set the deps pending flag (called after stagebox update)."""
    try:
        DEPS_PENDING_FILE.touch()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
