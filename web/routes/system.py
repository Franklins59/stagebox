"""
Stagebox System Routes

System-level operations: reboot, shutdown, language.
Available in both editions.
"""

import subprocess
from pathlib import Path
from flask import Blueprint, jsonify, request

from web import config
from web.utils import get_mac_suffix

bp = Blueprint('system', __name__)


@bp.route('/api/system/device-id', methods=['GET'])
def get_device_id():
    """Get the Raspberry Pi's MAC address suffix as device identifier."""
    try:
        device_id = get_mac_suffix()
        return jsonify({'success': True, 'device_id': device_id})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e), 'device_id': '------'})


@bp.route('/api/system/reboot', methods=['POST'])
def system_reboot():
    """Reboot the Raspberry Pi."""
    try:
        subprocess.Popen(['systemctl', 'reboot'], 
                        stdout=subprocess.DEVNULL, 
                        stderr=subprocess.DEVNULL)
        return jsonify({'success': True, 'message': 'Rebooting...'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/system/shutdown', methods=['POST'])
def system_shutdown():
    """Shutdown the Raspberry Pi."""
    try:
        subprocess.Popen(['systemctl', 'poweroff'], 
                        stdout=subprocess.DEVNULL, 
                        stderr=subprocess.DEVNULL)
        return jsonify({'success': True, 'message': 'Shutting down...'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ===========================================================================
# Language / i18n
# ===========================================================================

@bp.route('/api/system/language', methods=['GET'])
def get_language():
    """Get current UI language."""
    try:
        lang_file = config.STAGEBOX_ROOT / 'data' / 'language.txt'
        if lang_file.exists():
            lang = lang_file.read_text().strip()
            return jsonify({'success': True, 'language': lang})
        return jsonify({'success': True, 'language': 'en'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/system/language', methods=['POST'])
def set_language():
    """Set UI language."""
    data = request.get_json() or {}
    lang = data.get('language', 'en').strip().lower()
    
    supported = ['en', 'de', 'fr', 'it', 'nl']
    if lang not in supported:
        return jsonify({'success': False, 'error': f'Unsupported language: {lang}'}), 400
    
    try:
        lang_file = config.STAGEBOX_ROOT / 'data' / 'language.txt'
        lang_file.parent.mkdir(parents=True, exist_ok=True)
        lang_file.write_text(lang)
        return jsonify({'success': True, 'language': lang})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/api/system/languages', methods=['GET'])
def get_available_languages():
    """Get list of available languages."""
    languages = [
        {'code': 'en', 'name': 'English', 'native': 'English'},
        {'code': 'de', 'name': 'German', 'native': 'Deutsch'},
        {'code': 'fr', 'name': 'French', 'native': 'Français'},
        {'code': 'it', 'name': 'Italian', 'native': 'Italiano'},
        {'code': 'nl', 'name': 'Dutch', 'native': 'Nederlands'},
    ]
    return jsonify({'success': True, 'languages': languages})
