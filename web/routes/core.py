"""
Stagebox Core Routes

Basic routes available in both Personal and Pro editions:
- Index page
- Manual
- Version API
- System status
- Hardware info
"""

from flask import Blueprint, render_template, jsonify, request
from pathlib import Path

from web.config import get_version, VERSION
from web.edition import get_edition_name, is_pro, EDITION
from web.services import get_active_building, is_building_active
from web.utils.helpers import get_hardware_info, get_cpu_temp, get_uptime

bp = Blueprint('core', __name__)


@bp.route('/')
def index():
    """Serve main page - greeting or building UI depending on state."""
    if is_building_active():
        return render_template('index.html')
    else:
        hw_info = get_hardware_info()
        return render_template('greeting.html', 
                               version=get_version(),
                               hw_info=hw_info)


@bp.route('/manual')
def manual():
    """Serve the user manual page in the requested language."""
    lang = request.args.get('lang', 'en')
    
    supported_langs = ['en', 'de', 'fr', 'it', 'nl']
    if lang not in supported_langs:
        lang = 'en'
    
    manual_template = f'manual_{lang}.html'
    template_path = Path(__file__).parent.parent / 'templates' / manual_template
    if not template_path.exists():
        manual_template = 'manual.html'
    
    return render_template(manual_template)


@bp.route('/api/system/version', methods=['GET'])
def get_system_version():
    """Get current system version and edition."""
    return jsonify({
        'success': True,
        'version': VERSION,
        'edition': EDITION,
        'edition_name': get_edition_name(),
        'is_pro': is_pro()
    })


@bp.route('/api/status', methods=['GET'])
def check_status():
    """Check online status of all devices."""
    from web.services import device_manager
    status = device_manager.check_devices_status()
    return jsonify({'success': True, 'status': status})


@bp.route('/api/backend/status', methods=['GET'])
def backend_status():
    """Check if backend is running and core modules available."""
    from web.services.device_manager import device_manager, CORE_AVAILABLE
    from web.services.core_modules import (
        STAGE2_AVAILABLE, STAGE3_AVAILABLE, STAGE4_AVAILABLE
    )
    
    return jsonify({
        'success': True,
        'status': 'online',
        'device_count': len(device_manager.devices),
        'core_available': CORE_AVAILABLE,
        'stage2_available': STAGE2_AVAILABLE,
        'stage3_available': STAGE3_AVAILABLE,
        'stage4_available': STAGE4_AVAILABLE,
        'edition': EDITION,
    })


@bp.route('/api/system/ping', methods=['GET'])
def system_ping():
    """Simple ping endpoint to check if server is responsive."""
    return jsonify({'success': True, 'pong': True})


@bp.route('/api/system/hardware', methods=['GET'])
def get_system_hardware():
    """Get hardware info (for dynamic updates)."""
    return jsonify({
        'success': True,
        'cpu_temp': get_cpu_temp(),
        'uptime': get_uptime()
    })
