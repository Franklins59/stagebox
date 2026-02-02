"""
Stagebox Configuration

Shared configuration, paths, and constants used across the application.
"""

import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

# ===========================================================================
# Paths
# ===========================================================================

STAGEBOX_CODE_ROOT = Path('/home/coredev/stagebox')
if str(STAGEBOX_CODE_ROOT) not in sys.path:
    sys.path.insert(0, str(STAGEBOX_CODE_ROOT))

BUILDINGS_DIR = Path('/home/coredev/buildings')
STAGEBOX_ROOT = Path('/home/coredev/stagebox')
RASPI_ROOT = Path('/home/coredev/raspi')
WEB_DIR = Path(__file__).resolve().parent

# Admin config file location
ADMIN_CONFIG_FILE = Path('/home/coredev/stagebox/data/admin.yaml')

# Internal secrets (NAS backup credentials - per Raspi, not per building)
INTERNAL_SECRETS_FILE = Path('/home/coredev/stagebox/data/internal_secrets.yaml')

# Installer profile (global - company branding for reports)
INSTALLER_PROFILE_FILE = Path('/home/coredev/stagebox/data/installer_profile.json')
INSTALLER_LOGO_FILE = Path('/home/coredev/stagebox/data/installer_logo.png')
INSTALLER_LOGO_MAX_SIZE = 2 * 1024 * 1024  # 2 MB max
INSTALLER_LOGO_MAX_WIDTH = 800
INSTALLER_LOGO_MAX_HEIGHT = 400

# Stage 1 configuration
STAGE1_STATUS_FILE = Path('/tmp/stage1_status.json')
STAGE1_HEARTBEAT_TIMEOUT = 15  # seconds without heartbeat before auto-stop
STAGE1_CORE_PATH = Path('/home/coredev/stagebox/core/provision/stage1_ap_core.py')

# Update system
UPDATE_KEYS_FILE = Path('/home/coredev/raspi/keys/keys.yaml')
UPDATE_BACKUP_DIR = Path('/home/coredev/stagebox_backups')
UPDATE_MANIFEST_FILE = 'latest.json'

# Dependencies
DEPENDENCIES_FILE = STAGEBOX_ROOT / 'dependencies.yaml'
DEPS_PENDING_FILE = Path('/tmp/stagebox_deps_pending')

# ===========================================================================
# Timeouts and Limits
# ===========================================================================

ADMIN_SESSION_TIMEOUT = 1800  # 30 minutes
MAX_WORKERS = 50  # For parallel ping
UPDATE_CHECK_INTERVAL_HOURS = 24

# ===========================================================================
# Default Server URLs
# ===========================================================================

# Pro edition: encrypted updates from private server
_PRO_UPDATE_SERVER_URL = 'https://franklins.forstec.ch/stagebox/dl/3tGWuvcecUcs1YGdrtfIqg=='

# Personal edition: unencrypted updates from GitHub
_PERSONAL_UPDATE_URL = 'https://github.com/franklins59/stagebox/releases/latest/download'

_DEFAULT_TELEMETRY_URL = 'https://franklins.forstec.ch/stagebox/telemetry.php'

# These will be set based on edition in get_update_url()
UPDATE_SERVER_URL = _PRO_UPDATE_SERVER_URL  # Default for Pro
TELEMETRY_URL = _DEFAULT_TELEMETRY_URL
TELEMETRY_ENABLED = True


def get_update_url():
    """Get the update URL based on edition."""
    from web.edition import is_pro
    if is_pro():
        return _PRO_UPDATE_SERVER_URL
    else:
        return _PERSONAL_UPDATE_URL


def is_encrypted_update():
    """Check if updates are encrypted (Pro only)."""
    from web.edition import is_pro
    return is_pro()

# ===========================================================================
# Update Targets
# ===========================================================================

UPDATE_TARGETS = [
    'web/',
    'core/',
    'scripts/',
    'shelly_stage1.py',
    'shelly_stage2.py',
    'shelly_stage3.py',
    'shelly_stage4.py',
    'shelly_report.py',
    'shelly_snapshot.py',
    'VERSION',
    'dependencies.yaml',
]

UPDATE_PRESERVE = [
    'data/',
    'var/',
    'tests/',
    '__pycache__/',
]

RASPI_UPDATE_TARGETS = [
    'keys/',
    'oled/',
]

# ===========================================================================
# Active Building State
# ===========================================================================

active_building: Optional[str] = None
PROJECT_ROOT: Optional[Path] = None
DATA_DIR: Optional[Path] = None
STATE_FILE: Optional[Path] = None
CONFIG_FILE: Optional[Path] = None
SECRETS_FILE: Optional[Path] = None


def load_server_urls():
    """Load server URLs from keys.yaml, with fallback to defaults."""
    global UPDATE_SERVER_URL, TELEMETRY_URL
    
    if not UPDATE_KEYS_FILE.exists():
        return
    
    try:
        with open(UPDATE_KEYS_FILE, 'r', encoding='utf-8') as f:
            keys_data = yaml.safe_load(f) or {}
        
        update_config = keys_data.get('update', {})
        
        if 'server_url' in update_config:
            UPDATE_SERVER_URL = update_config['server_url'].rstrip('/')
        
        if 'telemetry_url' in update_config:
            TELEMETRY_URL = update_config['telemetry_url']
            
    except Exception as e:
        print(f"[Config] Warning: Could not load URLs from keys.yaml: {e}")


# Load URLs at module import
load_server_urls()


# ===========================================================================
# Version
# ===========================================================================

def get_version() -> str:
    """Read version from VERSION file."""
    version_file = STAGEBOX_ROOT / 'VERSION'
    if version_file.exists():
        try:
            return version_file.read_text().strip()
        except:
            pass
    return '0.0.0'

VERSION = get_version()


# ===========================================================================
# Config Loading Functions
# ===========================================================================

def load_config() -> Dict[str, Any]:
    """Load config.yaml for active building."""
    if CONFIG_FILE is None:
        return {}
    try:
        if CONFIG_FILE.exists():
            with CONFIG_FILE.open('r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
    except Exception as e:
        print(f"Error loading config: {e}")
    return {}


def load_secrets() -> Dict[str, Any]:
    """Load secrets.yaml for active building."""
    if SECRETS_FILE is None:
        return {}
    try:
        if SECRETS_FILE.exists():
            with SECRETS_FILE.open('r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
    except Exception as e:
        print(f"Error loading secrets: {e}")
    return {}


def load_model_mapping() -> Dict[str, str]:
    """Load model mapping from shelly_model_map.yaml."""
    if DATA_DIR is None:
        return {}
    try:
        model_map_file = DATA_DIR / 'shelly_model_map.yaml'
        if model_map_file.exists():
            with model_map_file.open('r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
                if 'models' in data:
                    return data.get('models', {})
                else:
                    return data
    except Exception as e:
        print(f"Error loading model map: {e}")
    return {}
