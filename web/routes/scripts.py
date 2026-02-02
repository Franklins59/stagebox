"""
Stagebox Scripts Routes

Manage Shelly scripts - local files and GitHub library.
Available in both editions.
"""

import json
import re
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from flask import Blueprint, jsonify, request

from web import config
from web.services import device_manager, get_active_building

bp = Blueprint('scripts', __name__)

# GitHub Shelly script library
GITHUB_SCRIPTS_URL = 'https://raw.githubusercontent.com/ALLTERCO/shelly-script-examples/main'
GITHUB_MANIFEST_URL = f'{GITHUB_SCRIPTS_URL}/examples-manifest.json'
SCRIPT_CHUNK_SIZE = 1024  # Shelly recommends 1024 bytes per chunk


def get_scripts_dir():
    """Get the scripts directory for the active building."""
    active = get_active_building()
    if not active:
        return None
    return config.DATA_DIR / 'scripts' if config.DATA_DIR else None


# ===========================================================================
# Script Listing (Local and GitHub)
# ===========================================================================

@bp.route('/api/scripts', methods=['GET'])
def list_scripts():
    """List available scripts from local or GitHub source."""
    source = request.args.get('source', 'local')
    
    scripts = []
    
    if source == 'local':
        # List scripts from data/scripts/ directory
        scripts_dir = get_scripts_dir()
        
        if not scripts_dir:
            return jsonify({'success': False, 'error': 'No building active'})
        
        if scripts_dir.exists():
            for script_file in scripts_dir.glob('*.js'):
                # Try to extract description from first comment
                description = ''
                try:
                    with open(script_file, 'r', encoding='utf-8') as f:
                        first_lines = f.read(500)
                        if first_lines.startswith('//'):
                            description = first_lines.split('\n')[0][2:].strip()
                        elif '/*' in first_lines:
                            start = first_lines.find('/*') + 2
                            end = first_lines.find('*/')
                            if end > start:
                                description = first_lines[start:end].strip()[:100]
                except:
                    pass
                
                scripts.append({
                    'name': script_file.stem,
                    'filename': script_file.name,
                    'description': description,
                    'source': 'local',
                    'path': str(script_file)
                })
    
    elif source == 'github':
        # Fetch manifest from GitHub
        try:
            resp = requests.get(GITHUB_MANIFEST_URL, timeout=10)
            if resp.status_code == 200:
                manifest = resp.json()
                for item in manifest:
                    scripts.append({
                        'name': item.get('title', item.get('fname', 'Unknown')),
                        'filename': item.get('fname', ''),
                        'description': item.get('description', '')[:100],
                        'source': 'github'
                    })
        except Exception as e:
            return jsonify({'success': False, 'error': f'GitHub fetch failed: {str(e)}'})
    
    return jsonify({
        'success': True,
        'scripts': sorted(scripts, key=lambda s: s['name'].lower()),
        'source': source
    })


# ===========================================================================
# Script Deployment
# ===========================================================================

@bp.route('/api/scripts/deploy', methods=['POST'])
def deploy_script():
    """Deploy a script to multiple devices.
    
    Workflow per device:
    1. Script.Create (or find existing by name)
    2. Script.PutCode (chunked upload with append)
    3. Script.SetConfig (enable on boot)
    4. Script.Start (optional)
    """
    data = request.get_json() or {}
    script_file = data.get('script')  # Source filename
    source = data.get('source', 'local')
    device_macs = data.get('devices', [])
    enable_on_boot = data.get('enable_on_boot', True)
    start_after_deploy = data.get('start_after_deploy', True)
    custom_script_name = data.get('script_name', '')  # Custom name for device
    script_file_base = data.get('script_file_base', '')  # Original filename without .js
    
    if not script_file:
        return jsonify({'success': False, 'error': 'No script specified'})
    
    if not device_macs:
        return jsonify({'success': False, 'error': 'No devices specified'})
    
    # Load script content
    script_code = None
    # Use custom name if provided, otherwise derive from filename
    script_display_name = custom_script_name.strip() if custom_script_name else script_file.replace('.js', '')
    # Fallback for script_file_base
    if not script_file_base:
        script_file_base = script_file.replace('.js', '')
    
    if source == 'local':
        scripts_dir = get_scripts_dir()
        
        if not scripts_dir:
            return jsonify({'success': False, 'error': 'No building active'})
        
        script_path = scripts_dir / script_file
        
        if not script_path.exists():
            # Try with .js extension
            script_path = scripts_dir / f'{script_file}.js'
        
        if not script_path.exists():
            return jsonify({'success': False, 'error': f'Script not found: {script_file}'})
        
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                script_code = f.read()
        except Exception as e:
            return jsonify({'success': False, 'error': f'Failed to read script: {str(e)}'})
    
    elif source == 'github':
        try:
            url = f'{GITHUB_SCRIPTS_URL}/{script_file}'
            resp = requests.get(url, timeout=15)
            if resp.status_code != 200:
                return jsonify({'success': False, 'error': f'GitHub download failed: {resp.status_code}'})
            script_code = resp.text
        except Exception as e:
            return jsonify({'success': False, 'error': f'GitHub download error: {str(e)}'})
    
    if not script_code:
        return jsonify({'success': False, 'error': 'Could not load script content'})
    
    if len(script_code.strip()) == 0:
        return jsonify({'success': False, 'error': 'Script file is empty'})
    
    # Deploy to each device
    results = []
    
    def deploy_to_device(mac):
        device = device_manager.get_device(mac)
        if not device:
            return {'device': mac, 'success': False, 'error': 'Device not found'}
        
        ip = device.get('ip')
        if not ip:
            return {'device': mac, 'success': False, 'error': 'No IP'}
        
        try:
            # 1. List existing scripts to find or create slot
            list_resp = requests.post(
                f'http://{ip}/rpc/Script.List',
                json={},
                timeout=5
            )
            if list_resp.status_code != 200:
                return {'device': mac, 'ip': ip, 'success': False, 'error': f'Script.List: {list_resp.status_code}'}
            
            existing_scripts = list_resp.json().get('scripts', [])
            
            # If script name changed, delete the old script (with original filename)
            if script_file_base != script_display_name:
                for s in existing_scripts:
                    if s.get('name') == script_file_base:
                        old_id = s.get('id')
                        # Stop if running before delete
                        if s.get('running'):
                            requests.post(f'http://{ip}/rpc/Script.Stop', json={'id': old_id}, timeout=5)
                            time.sleep(0.3)
                        # Delete old script
                        requests.post(f'http://{ip}/rpc/Script.Delete', json={'id': old_id}, timeout=5)
                        break
            
            # Find script by name or create new
            script_id = None
            for s in existing_scripts:
                if s.get('name') == script_display_name:
                    script_id = s.get('id')
                    # Stop if running (required before PutCode)
                    if s.get('running'):
                        requests.post(f'http://{ip}/rpc/Script.Stop', json={'id': script_id}, timeout=5)
                        time.sleep(0.5)
                    break
            
            if script_id is None:
                # Create new script
                create_resp = requests.post(
                    f'http://{ip}/rpc/Script.Create',
                    json={'name': script_display_name},
                    timeout=5
                )
                if create_resp.status_code != 200:
                    return {'device': mac, 'ip': ip, 'success': False, 'error': f'Create: {create_resp.text[:100]}'}
                script_id = create_resp.json().get('id')
            
            if script_id is None:
                return {'device': mac, 'ip': ip, 'success': False, 'error': 'No script ID'}
            
            # 2. Upload code in chunks
            pos = 0
            append = False
            while pos < len(script_code):
                chunk = script_code[pos:pos + SCRIPT_CHUNK_SIZE]
                
                # Use explicit JSON with ensure_ascii for safe encoding
                payload = json.dumps({'id': script_id, 'code': chunk, 'append': append}, ensure_ascii=False)
                
                put_resp = requests.post(
                    f'http://{ip}/rpc/Script.PutCode',
                    data=payload.encode('utf-8'),
                    headers={'Content-Type': 'application/json'},
                    timeout=10
                )
                if put_resp.status_code != 200:
                    return {'device': mac, 'ip': ip, 'success': False, 'error': f'PutCode failed: {put_resp.text[:50]}'}
                
                pos += len(chunk)
                append = True
            
            # 3. Set config (enable on boot)
            if enable_on_boot:
                requests.post(
                    f'http://{ip}/rpc/Script.SetConfig',
                    json={'id': script_id, 'config': {'enable': True}},
                    timeout=5
                )
            
            # 4. Start script
            if start_after_deploy:
                time.sleep(0.3)
                start_resp = requests.post(
                    f'http://{ip}/rpc/Script.Start',
                    json={'id': script_id},
                    timeout=5
                )
                if start_resp.status_code != 200:
                    return {'device': mac, 'ip': ip, 'success': True, 'message': 'Deployed (start failed)'}
            
            return {'device': mac, 'ip': ip, 'success': True, 'message': 'OK'}
            
        except requests.exceptions.Timeout:
            return {'device': mac, 'ip': ip, 'success': False, 'error': 'Timeout'}
        except Exception as e:
            return {'device': mac, 'ip': ip, 'success': False, 'error': str(e)}
    
    # Run deployments in parallel
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(deploy_to_device, mac): mac for mac in device_macs}
        for future in as_completed(futures):
            results.append(future.result())
    
    return jsonify({
        'success': True,
        'results': results
    })


# ===========================================================================
# Script Status
# ===========================================================================

@bp.route('/api/scripts/status', methods=['POST'])
def script_status():
    """Get script status from multiple devices."""
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
                f'http://{ip}/rpc/Script.List',
                json={},
                timeout=5
            )
            if resp.status_code != 200:
                return {'device': mac, 'ip': ip, 'success': False, 'error': 'Script.List failed'}
            
            scripts = resp.json().get('scripts', [])
            return {
                'device': mac,
                'ip': ip,
                'success': True,
                'scripts': [{'id': s.get('id'), 'name': s.get('name'), 'running': s.get('running', False)} for s in scripts]
            }
        except requests.exceptions.Timeout:
            return {'device': mac, 'ip': ip, 'success': False, 'error': 'Timeout'}
        except Exception as e:
            return {'device': mac, 'ip': ip, 'success': False, 'error': str(e)}
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(get_status, mac): mac for mac in device_macs}
        for future in as_completed(futures):
            results.append(future.result())
    
    return jsonify({
        'success': True,
        'results': results
    })


# ===========================================================================
# Script Delete (from devices)
# ===========================================================================

@bp.route('/api/scripts/delete', methods=['POST'])
def delete_script_from_devices():
    """Delete scripts from multiple devices."""
    data = request.get_json() or {}
    device_macs = data.get('devices', [])
    script_name = data.get('script_name', '')
    
    if not device_macs:
        return jsonify({'success': False, 'error': 'No devices specified'})
    
    if not script_name:
        return jsonify({'success': False, 'error': 'No script name specified'})
    
    delete_all = script_name.lower() == 'all'
    
    results = []
    
    def delete_from_device(mac):
        device = device_manager.get_device(mac)
        if not device:
            return {'device': mac, 'success': False, 'error': 'Device not found'}
        
        ip = device.get('ip')
        if not ip:
            return {'device': mac, 'success': False, 'error': 'No IP'}
        
        try:
            # First list scripts
            list_resp = requests.post(
                f'http://{ip}/rpc/Script.List',
                json={},
                timeout=5
            )
            if list_resp.status_code != 200:
                return {'device': mac, 'ip': ip, 'success': False, 'error': 'Script.List failed'}
            
            scripts = list_resp.json().get('scripts', [])
            deleted_count = 0
            
            for s in scripts:
                if delete_all or s.get('name') == script_name:
                    # Stop if running
                    if s.get('running'):
                        requests.post(f'http://{ip}/rpc/Script.Stop', json={'id': s['id']}, timeout=5)
                        time.sleep(0.2)
                    
                    # Delete
                    del_resp = requests.post(
                        f'http://{ip}/rpc/Script.Delete',
                        json={'id': s['id']},
                        timeout=5
                    )
                    if del_resp.status_code == 200:
                        deleted_count += 1
            
            if deleted_count > 0:
                return {'device': mac, 'ip': ip, 'success': True, 'message': f'{deleted_count} deleted'}
            else:
                return {'device': mac, 'ip': ip, 'success': True, 'message': 'None found'}
                
        except requests.exceptions.Timeout:
            return {'device': mac, 'ip': ip, 'success': False, 'error': 'Timeout'}
        except Exception as e:
            return {'device': mac, 'ip': ip, 'success': False, 'error': str(e)}
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(delete_from_device, mac): mac for mac in device_macs}
        for future in as_completed(futures):
            results.append(future.result())
    
    return jsonify({
        'success': True,
        'results': results
    })


# ===========================================================================
# Script Control (Start/Stop/Restart)
# ===========================================================================

@bp.route('/api/scripts/control', methods=['POST'])
def control_scripts():
    """Start/Stop/Restart scripts on multiple devices."""
    data = request.get_json() or {}
    device_macs = data.get('devices', [])
    action = data.get('action', '').lower()  # start, stop, restart
    
    if not device_macs:
        return jsonify({'success': False, 'error': 'No devices specified'})
    
    if action not in ('start', 'stop', 'restart'):
        return jsonify({'success': False, 'error': 'Invalid action (use start/stop/restart)'})
    
    results = []
    
    def control_device(mac):
        device = device_manager.get_device(mac)
        if not device:
            return {'device': mac, 'success': False, 'error': 'Device not found'}
        
        ip = device.get('ip')
        if not ip:
            return {'device': mac, 'success': False, 'error': 'No IP'}
        
        try:
            # First list scripts
            list_resp = requests.post(
                f'http://{ip}/rpc/Script.List',
                json={},
                timeout=5
            )
            if list_resp.status_code != 200:
                return {'device': mac, 'ip': ip, 'success': False, 'error': 'Script.List failed'}
            
            scripts = list_resp.json().get('scripts', [])
            
            if not scripts:
                return {'device': mac, 'ip': ip, 'success': True, 'message': 'No scripts'}
            
            action_count = 0
            
            for s in scripts:
                script_id = s['id']
                is_running = s.get('running', False)
                
                if action == 'stop' and is_running:
                    resp = requests.post(f'http://{ip}/rpc/Script.Stop', json={'id': script_id}, timeout=5)
                    if resp.status_code == 200:
                        action_count += 1
                        
                elif action == 'start' and not is_running:
                    resp = requests.post(f'http://{ip}/rpc/Script.Start', json={'id': script_id}, timeout=5)
                    if resp.status_code == 200:
                        action_count += 1
                        
                elif action == 'restart':
                    if is_running:
                        requests.post(f'http://{ip}/rpc/Script.Stop', json={'id': script_id}, timeout=5)
                        time.sleep(0.3)
                    resp = requests.post(f'http://{ip}/rpc/Script.Start', json={'id': script_id}, timeout=5)
                    if resp.status_code == 200:
                        action_count += 1
            
            return {'device': mac, 'ip': ip, 'success': True, 'message': f'{action_count} scripts'}
                
        except requests.exceptions.Timeout:
            return {'device': mac, 'ip': ip, 'success': False, 'error': 'Timeout'}
        except Exception as e:
            return {'device': mac, 'ip': ip, 'success': False, 'error': str(e)}
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(control_device, mac): mac for mac in device_macs}
        for future in as_completed(futures):
            results.append(future.result())
    
    return jsonify({
        'success': True,
        'results': results
    })


# ===========================================================================
# Admin Routes (Local file management)
# ===========================================================================

@bp.route('/api/admin/scripts/list', methods=['GET'])
def admin_list_scripts():
    """List all scripts in the active building's data/scripts/."""
    scripts_dir = get_scripts_dir()
    
    if not scripts_dir:
        return jsonify({'success': False, 'error': 'No building active'}), 400
    
    scripts = []
    
    if scripts_dir.exists():
        for script_file in scripts_dir.glob('*.js'):
            scripts.append(script_file.name)
    
    return jsonify({
        'success': True,
        'scripts': sorted(scripts)
    })


@bp.route('/api/admin/scripts/upload', methods=['POST'])
def admin_upload_script():
    """Upload a script to the active building's data/scripts/."""
    scripts_dir = get_scripts_dir()
    
    if not scripts_dir:
        return jsonify({'success': False, 'error': 'No building active'}), 400
    
    if 'script' not in request.files:
        return jsonify({'success': False, 'error': 'No script file provided'}), 400
    
    file = request.files['script']
    if not file.filename:
        return jsonify({'success': False, 'error': 'No filename'}), 400
    
    if not file.filename.endswith('.js'):
        return jsonify({'success': False, 'error': 'Only .js files allowed'}), 400
    
    # Sanitize filename
    filename = re.sub(r'[^a-zA-Z0-9_.-]', '_', file.filename)
    
    scripts_dir.mkdir(parents=True, exist_ok=True)
    script_path = scripts_dir / filename
    
    try:
        file.save(str(script_path))
        return jsonify({'success': True, 'name': filename})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/admin/scripts/delete', methods=['POST'])
def admin_delete_script():
    """Delete a script from the active building's data/scripts/."""
    scripts_dir = get_scripts_dir()
    
    if not scripts_dir:
        return jsonify({'success': False, 'error': 'No building active'}), 400
    
    data = request.get_json() or {}
    name = data.get('name')
    
    if not name:
        return jsonify({'success': False, 'error': 'No script name provided'}), 400
    
    # Security: prevent path traversal
    if not re.match(r'^[a-zA-Z0-9_.-]+\.js$', name):
        return jsonify({'success': False, 'error': 'Invalid script name'}), 400
    
    script_path = scripts_dir / name
    
    if not script_path.exists():
        return jsonify({'success': False, 'error': 'Script not found'}), 404
    
    try:
        script_path.unlink()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
