"""
Stagebox Multi-Building Routes (Pro Only)

Create buildings (Pro only).
Delete and Rename are in buildings.py (available in all editions).
"""

import re
import subprocess
from flask import Blueprint, jsonify, request

from web import config
from web.edition import is_pro
from web.services import discover_buildings, get_active_building
from web.routes.pro.admin import require_admin, require_pro

bp = Blueprint('multi_building', __name__)


@bp.route('/api/admin/buildings', methods=['GET'])
@require_pro
@require_admin
def admin_list_buildings():
    """List all buildings (admin view)."""
    buildings = discover_buildings()
    return jsonify({'success': True, 'buildings': buildings})


@bp.route('/api/admin/buildings/create', methods=['POST'])
@require_pro
@require_admin
def admin_create_building():
    """Create a new building. Pro only - Personal edition auto-creates one building."""
    data = request.get_json() or {}
    name = data.get('name', '').strip()
    
    if not name:
        return jsonify({'success': False, 'error': 'Building name required'}), 400
    
    # Normalize name
    name = name.lower().replace(' ', '_').replace('-', '_')
    name = re.sub(r'[^a-z0-9_]', '', name)
    name = re.sub(r'_+', '_', name)
    name = name.strip('_')
    
    if not name:
        return jsonify({'success': False, 'error': 'Invalid name'}), 400
    
    building_path = config.BUILDINGS_DIR / name
    if building_path.exists():
        return jsonify({'success': False, 'error': 'Building already exists'}), 400
    
    try:
        result = subprocess.run(
            ['/home/coredev/scripts/building_scripts/mk_new_building.sh', name],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            return jsonify({
                'success': True, 
                'message': f'Building {name} created',
                'name': name,
                'is_new': True
            })
        else:
            return jsonify({'success': False, 'error': result.stderr or 'Script failed'}), 500
            
    except subprocess.TimeoutExpired:
        return jsonify({'success': False, 'error': 'Timeout creating building'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# NOTE: Delete and Rename routes moved to routes/buildings.py (available in all editions)
# NOTE: Export/Import routes are also in routes/buildings.py
