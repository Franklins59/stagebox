"""
Stagebox USB Routes (Pro Only)

USB backup, restore, and format functions.
"""

from flask import Blueprint, jsonify, request

from web import config
from web.routes.pro.admin import require_admin, require_pro
from web import usb_manager

bp = Blueprint('usb', __name__)


@bp.route('/api/admin/system/usb', methods=['GET'])
@require_pro
@require_admin
def get_usb_status():
    """Get USB backup drive status."""
    try:
        drives = usb_manager.list_drives()
        drives_data = [
            {
                'device': d.device,
                'name': d.name,
                'size': d.size,
                'fstype': d.fstype,
                'mountpoint': d.mountpoint,
                'label': d.label,
                'is_stagebox': d.is_stagebox,
                'total_bytes': d.total_bytes,
                'free_bytes': d.free_bytes,
                'used_bytes': d.used_bytes,
                'usage_percent': d.usage_percent
            }
            for d in drives
        ]
        
        return jsonify({
            'success': True,
            'drives': drives_data,
            'has_usb': len(drives_data) > 0
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/system/backup/usb', methods=['POST'])
@require_pro
def backup_to_usb():
    """Backup buildings to USB stick as ZIP.
    
    Creates a ZIP file in /mnt/backup_usb/stagebox-<mac>-<timestamp>.zip
    Keeps last 10 backups (rotation).
    """
    result = usb_manager.create_backup(config.BUILDINGS_DIR)
    
    if result['success']:
        return jsonify(result)
    else:
        return jsonify(result), 400


@bp.route('/api/system/backup/usb/list', methods=['GET'])
@require_pro
def list_usb_backups():
    """List available backups on USB stick."""
    result = usb_manager.list_backups()
    
    if result['success']:
        return jsonify(result)
    else:
        return jsonify(result), 400


@bp.route('/api/system/backup/usb/analyze', methods=['POST'])
@require_pro
def analyze_usb_backup():
    """Analyze a USB backup ZIP file and return list of buildings."""
    data = request.get_json() or {}
    zip_path = data.get('path', '')
    
    if not zip_path:
        return jsonify({'success': False, 'error': 'No backup path specified'}), 400
    
    result = usb_manager.analyze_backup(zip_path)
    
    if result['success']:
        # Add existing buildings info
        existing = []
        if config.BUILDINGS_DIR.exists():
            existing = [d.name for d in config.BUILDINGS_DIR.iterdir() 
                       if d.is_dir() and '_old_' not in d.name]
        result['existing'] = existing
        return jsonify(result)
    else:
        return jsonify(result), 400


@bp.route('/api/system/backup/usb/restore', methods=['POST'])
@require_pro
@require_admin
def restore_usb_backup():
    """Restore selected buildings from USB backup."""
    data = request.get_json() or {}
    zip_path = data.get('path', '')
    selections = data.get('selections', [])
    
    if not zip_path:
        return jsonify({'success': False, 'error': 'No backup path specified'}), 400
    
    if not selections:
        return jsonify({'success': False, 'error': 'No buildings selected'}), 400
    
    result = usb_manager.restore_backup(zip_path, selections, config.BUILDINGS_DIR)
    
    if result['success']:
        return jsonify(result)
    else:
        return jsonify(result), 400


@bp.route('/api/admin/system/usb/format', methods=['POST'])
@require_pro
@require_admin
def format_usb_drive():
    """Format a USB drive for backup use.
    
    WARNING: This will erase all data on the drive!
    Formats as FAT32 with label STAGEBOXBAK.
    """
    data = request.get_json() or {}
    device = data.get('device', '')
    
    if not device:
        return jsonify({'success': False, 'error': 'Device is required'}), 400
    
    result = usb_manager.format_drive(device)
    
    if result['success']:
        return jsonify(result)
    else:
        return jsonify(result), 500
