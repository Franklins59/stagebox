"""
Stagebox Updates Routes

Stagebox application updates - available in both editions.
"""

import hashlib
import subprocess
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import requests
import yaml
from flask import Blueprint, jsonify, request

from web import config
from web.services.telemetry import send_telemetry

bp = Blueprint('stagebox_updates', __name__)

# Update paths
STAGEBOX_ROOT = Path('/home/coredev/stagebox')
RASPI_ROOT = Path('/home/coredev/raspi')
UPDATE_BACKUP_DIR = Path('/home/coredev/stagebox_backups')
UPDATE_KEYS_FILE = Path('/home/coredev/raspi/keys/keys.yaml')

# Files/folders to update (relative to stagebox root)
UPDATE_TARGETS = [
    'web/',
    'core/',
    'scripts/',
    'data/profiles/',
    'data/scripts/',
    'data/shelly_model_map.yaml',
    'shelly_stage1.py',
    'shelly_stage2.py',
    'shelly_stage3.py',
    'shelly_stage4.py',
    'shelly_report.py',
    'shelly_snapshot.py',
    'VERSION',
    'dependencies.yaml',
]

# Raspi files/folders to update
RASPI_UPDATE_TARGETS = [
    'keys/',
    'oled/',
]


def load_update_key() -> Optional[str]:
    """Load ZIP password from keys.yaml for update system."""
    try:
        if UPDATE_KEYS_FILE.exists():
            with open(UPDATE_KEYS_FILE, 'r') as f:
                keys = yaml.safe_load(f) or {}
                return keys.get('update', {}).get('zip_password')
    except Exception as e:
        print(f"Error loading update key: {e}")
    return None


def get_version() -> str:
    """Get current version from VERSION file."""
    version_file = STAGEBOX_ROOT / 'VERSION'
    if version_file.exists():
        return version_file.read_text().strip()
    return '0.0.0'


@bp.route('/api/system/updates/check', methods=['GET'])
def check_updates():
    """Check for Stagebox updates."""
    from web.edition import is_pro
    
    try:
        # Send telemetry
        send_telemetry('update_check')
        
        # Determine edition and update URL
        if is_pro():
            edition = 'pro'
            base_url = config.get_update_url()
            manifest_url = f"{base_url}/{edition}/{config.UPDATE_MANIFEST_FILE}"
        else:
            edition = 'personal'
            # GitHub release URL structure
            base_url = config.get_update_url()
            manifest_url = f"{base_url}/{config.UPDATE_MANIFEST_FILE}"
        
        resp = requests.get(manifest_url, timeout=10)
        
        if resp.status_code != 200:
            return jsonify({'success': False, 'error': 'Failed to fetch update manifest'}), 500
        
        manifest = resp.json()
        latest_version = manifest.get('version', '0.0.0')
        current_version = config.VERSION
        
        # Simple version comparison
        def parse_version(v):
            try:
                return tuple(int(x) for x in v.split('.'))
            except:
                return (0, 0, 0)
        
        update_available = parse_version(latest_version) > parse_version(current_version)
        
        # Build download URL
        download_file = manifest.get('file', '')
        if is_pro():
            download_url = f"{base_url}/{edition}/{download_file}"
        else:
            # GitHub direct download URL
            download_url = f"{base_url}/{download_file}"
        
        return jsonify({
            'success': True,
            'current_version': current_version,
            'latest_version': latest_version,
            'remote_version': latest_version,  # Frontend uses this name
            'update_available': update_available,
            'release_notes': manifest.get('notes', ''),
            'release_date': manifest.get('date'),
            'download_url': download_url,
            'sha256': manifest.get('sha256'),
            'size_bytes': manifest.get('size_bytes'),
            'file_size': manifest.get('size_bytes'),  # Frontend uses this name
            'edition': edition,
            'encrypted': is_pro()  # Indicate if update is encrypted
        })
        
    except requests.exceptions.Timeout:
        return jsonify({'success': False, 'error': 'Update server timeout'}), 504
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/system/updates/check-background', methods=['GET'])
def check_updates_background():
    """Background update check (cached)."""
    from web.edition import is_pro
    from web.services.telemetry import (
        get_last_update_check, set_last_update_check,
        get_last_update_result, set_last_update_result
    )
    
    last_check = get_last_update_check()
    
    # Return cached result if checked recently
    if last_check:
        hours_since = (datetime.now() - last_check).total_seconds() / 3600
        if hours_since < config.UPDATE_CHECK_INTERVAL_HOURS:
            cached = get_last_update_result()
            if cached:
                return jsonify({
                    'success': True,
                    'cached': True,
                    **cached
                })
    
    # Perform fresh check
    try:
        if is_pro():
            edition = 'pro'
            base_url = config.get_update_url()
            manifest_url = f"{base_url}/{edition}/{config.UPDATE_MANIFEST_FILE}"
        else:
            edition = 'personal'
            base_url = config.get_update_url()
            manifest_url = f"{base_url}/{config.UPDATE_MANIFEST_FILE}"
        
        resp = requests.get(manifest_url, timeout=5)
        
        if resp.status_code == 200:
            manifest = resp.json()
            latest_version = manifest.get('version', '0.0.0')
            
            def parse_version(v):
                try:
                    return tuple(int(x) for x in v.split('.'))
                except:
                    return (0, 0, 0)
            
            update_available = parse_version(latest_version) > parse_version(config.VERSION)
            
            result = {
                'current_version': config.VERSION,
                'latest_version': latest_version,
                'update_available': update_available,
                'edition': edition
            }
            
            set_last_update_check(datetime.now())
            set_last_update_result(result)
            
            return jsonify({'success': True, 'cached': False, **result})
        
        return jsonify({'success': False, 'error': 'Update check failed'}), 500
        
    except:
        return jsonify({'success': False, 'error': 'Update check failed'}), 500


@bp.route('/api/system/updates/install', methods=['POST'])
def install_update():
    """Download and install update.
    
    Steps:
    1. Create backup of current installation
    2. Download ZIP from update server
    3. Verify SHA256 checksum
    4. Extract (with password for Pro, without for Personal)
    5. Copy update targets to stagebox directory
    6. Restart services
    """
    from web.edition import is_pro
    
    data = request.get_json() or {}
    download_url = data.get('download_url')
    expected_sha256 = data.get('sha256')
    
    if not download_url:
        return jsonify({'success': False, 'error': 'Download URL required'}), 400
    
    # Pro edition requires ZIP password from keys.yaml
    zip_password = None
    if is_pro():
        zip_password = load_update_key()
        if not zip_password:
            return jsonify({
                'success': False,
                'error': 'Update key not configured. Check /home/coredev/raspi/keys/keys.yaml'
            }), 500
    
    try:
        # Step 1: Create backup (keep only one)
        UPDATE_BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        
        # Remove old backups first
        for old_backup in UPDATE_BACKUP_DIR.glob('stagebox-backup-*.tar.gz'):
            old_backup.unlink()
        
        backup_name = f"stagebox-backup-{datetime.now().strftime('%Y%m%d_%H%M%S')}.tar.gz"
        backup_path = UPDATE_BACKUP_DIR / backup_name
        
        # Create tar backup of current installation
        # Pro: backup stagebox + raspi (includes keys)
        # Personal: backup stagebox only (no keys)
        if is_pro():
            backup_dirs = ['stagebox', 'raspi']
        else:
            backup_dirs = ['stagebox']
        
        result = subprocess.run(
            ['tar', '-czf', str(backup_path), '-C', '/home/coredev'] + backup_dirs,
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode != 0:
            return jsonify({
                'success': False,
                'error': f'Backup failed: {result.stderr}'
            }), 500
        
        # Step 2: Download ZIP
        tmp_zip = Path('/tmp/stagebox_update.zip')
        
        response = requests.get(download_url, timeout=300, stream=True)
        if response.status_code != 200:
            return jsonify({
                'success': False,
                'error': f'Download failed: HTTP {response.status_code}'
            }), 502
        
        with open(tmp_zip, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        # Step 3: Verify SHA256
        if expected_sha256:
            sha256_hash = hashlib.sha256()
            with open(tmp_zip, 'rb') as f:
                for byte_block in iter(lambda: f.read(4096), b''):
                    sha256_hash.update(byte_block)
            actual_sha256 = sha256_hash.hexdigest()
            
            if actual_sha256.lower() != expected_sha256.lower():
                tmp_zip.unlink()
                return jsonify({
                    'success': False,
                    'error': 'Checksum verification failed'
                }), 400
        
        # Step 4: Extract ZIP (with password for Pro, without for Personal)
        tmp_extract = Path('/tmp/stagebox_update_extracted')
        if tmp_extract.exists():
            subprocess.run(['rm', '-rf', str(tmp_extract)])
        tmp_extract.mkdir()
        
        if is_pro() and zip_password:
            # Pro: encrypted ZIP
            result = subprocess.run(
                ['unzip', '-P', zip_password, '-o', str(tmp_zip), '-d', str(tmp_extract)],
                capture_output=True,
                text=True,
                timeout=60
            )
        else:
            # Personal: unencrypted ZIP
            result = subprocess.run(
                ['unzip', '-o', str(tmp_zip), '-d', str(tmp_extract)],
                capture_output=True,
                text=True,
                timeout=60
            )
        
        if result.returncode != 0:
            return jsonify({
                'success': False,
                'error': f'Extraction failed: {result.stderr}'
            }), 500
        
        # Step 5: Copy update targets
        # Find the stagebox folder in extracted content
        extracted_stagebox = tmp_extract / 'stagebox'
        if not extracted_stagebox.exists():
            # Maybe it's directly in the root
            extracted_stagebox = tmp_extract
        
        for target in UPDATE_TARGETS:
            source = extracted_stagebox / target
            dest = STAGEBOX_ROOT / target
            
            if not source.exists():
                continue
            
            if source.is_dir():
                # Remove old directory and copy new
                if dest.exists():
                    subprocess.run(['rm', '-rf', str(dest)])
                subprocess.run(['cp', '-r', str(source), str(dest)])
            else:
                # Copy file
                subprocess.run(['cp', str(source), str(dest)])
        
        # Copy raspi update targets (Pro only - contains keys)
        if is_pro():
            extracted_raspi = tmp_extract / 'raspi'
            if extracted_raspi.exists():
                for target in RASPI_UPDATE_TARGETS:
                    source = extracted_raspi / target
                    dest = RASPI_ROOT / target
                    
                    if not source.exists():
                        continue
                    
                    if source.is_dir():
                        # Remove old directory and copy new
                        if dest.exists():
                            subprocess.run(['rm', '-rf', str(dest)])
                        subprocess.run(['cp', '-r', str(source), str(dest)])
                    else:
                        # Copy file
                        subprocess.run(['cp', str(source), str(dest)])
        
        # Cleanup temp files
        tmp_zip.unlink()
        subprocess.run(['rm', '-rf', str(tmp_extract)])
        
        # Step 6: Schedule system reboot
        # Read new version before reboot
        new_version = get_version()
        
        # Schedule reboot in background (2 seconds delay to allow response to be sent)
        def delayed_reboot():
            time.sleep(2)
            subprocess.Popen(['systemctl', 'reboot'], 
                           stdout=subprocess.DEVNULL, 
                           stderr=subprocess.DEVNULL)
        
        reboot_thread = threading.Thread(target=delayed_reboot)
        reboot_thread.daemon = True
        reboot_thread.start()
        
        # Send telemetry for successful update
        threading.Thread(target=send_telemetry, args=('update_installed',), daemon=True).start()
        
        return jsonify({
            'success': True,
            'message': 'Update installed successfully. Rebooting...',
            'backup_path': str(backup_path),
            'new_version': new_version,
            'rebooting': True
        })
        
    except subprocess.TimeoutExpired:
        return jsonify({
            'success': False,
            'error': 'Operation timed out'
        }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@bp.route('/api/system/updates/backups', methods=['GET'])
def list_backups():
    """List available backups."""
    backups = []
    
    if UPDATE_BACKUP_DIR.exists():
        for f in sorted(UPDATE_BACKUP_DIR.glob('stagebox-backup-*.tar.gz'), reverse=True):
            stat = f.stat()
            backups.append({
                'name': f.name,
                'path': str(f),
                'size_bytes': stat.st_size,
                'created': datetime.fromtimestamp(stat.st_mtime).isoformat()
            })
    
    return jsonify({
        'success': True,
        'backups': backups
    })
