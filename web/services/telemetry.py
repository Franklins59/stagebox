"""
Stagebox Telemetry Service

Sends anonymous usage data to help improve the product.
Pro edition only.
"""

from datetime import datetime
from typing import Any, Dict, Optional

import requests

from web.config import (
    TELEMETRY_ENABLED,
    TELEMETRY_URL,
    get_version,
)
from web.edition import is_pro
from web.utils.helpers import get_mac_address, get_hostname, get_ui_language


# Last update check timestamp (for periodic checking)
_last_update_check: Optional[datetime] = None
_last_update_result: Optional[Dict] = None


def send_telemetry(action: str = 'update_check') -> bool:
    """Send telemetry data to the server (non-blocking, fire-and-forget).
    
    Only active in Pro edition.
    
    Args:
        action: 'update_check', 'update_installed', or 'startup'
    
    Returns:
        True if sent successfully, False otherwise
    """
    # Only send telemetry in Pro edition
    if not is_pro():
        return False
    
    if not TELEMETRY_ENABLED:
        return False
    
    try:
        data = {
            'mac': get_mac_address(),
            'version': get_version(),
            'language': get_ui_language(),
            'hostname': get_hostname(),
            'action': action
        }
        
        # Fire and forget with short timeout
        requests.post(TELEMETRY_URL, json=data, timeout=3)
        return True
    except Exception:
        return False


def get_last_update_check() -> Optional[datetime]:
    """Get timestamp of last update check."""
    return _last_update_check


def set_last_update_check(timestamp: datetime):
    """Set timestamp of last update check."""
    global _last_update_check
    _last_update_check = timestamp


def get_last_update_result() -> Optional[Dict]:
    """Get result of last update check."""
    return _last_update_result


def set_last_update_result(result: Dict):
    """Set result of last update check."""
    global _last_update_result
    _last_update_result = result
