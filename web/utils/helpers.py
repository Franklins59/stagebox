"""
Stagebox Helper Functions

Shared utility functions used across the application.
"""

import socket
import uuid
from pathlib import Path
from typing import Optional

from web.config import STAGEBOX_ROOT


def sanitize_ha_name(name: str) -> str:
    """Sanitize name for HomeAssistant compatibility.
    
    - Lowercase
    - Replace spaces and special chars with underscore
    - Replace German umlauts: ä→ae, ö→oe, ü→ue, ß→ss
    - Remove consecutive underscores
    - Strip leading/trailing underscores
    """
    if not name:
        return ''
    
    # German umlauts
    replacements = {
        'ä': 'ae', 'Ä': 'Ae',
        'ö': 'oe', 'Ö': 'Oe', 
        'ü': 'ue', 'Ü': 'Ue',
        'ß': 'ss'
    }
    for old, new in replacements.items():
        name = name.replace(old, new)
    
    # Lowercase
    name = name.lower()
    
    # Replace non-alphanumeric with underscore
    result = []
    for char in name:
        if char.isalnum():
            result.append(char)
        else:
            result.append('_')
    name = ''.join(result)
    
    # Remove consecutive underscores
    while '__' in name:
        name = name.replace('__', '_')
    
    # Strip leading/trailing underscores
    name = name.strip('_')
    
    return name


def get_mac_address() -> str:
    """Get the primary MAC address of the system."""
    try:
        for iface in ['eth0', 'wlan0', 'end0', 'wlan1']:
            mac_path = Path(f'/sys/class/net/{iface}/address')
            if mac_path.exists():
                mac = mac_path.read_text().strip().upper()
                if mac and mac != '00:00:00:00:00:00':
                    return mac
        # Fallback: use uuid to generate MAC from hardware
        mac_int = uuid.getnode()
        return ':'.join(f'{(mac_int >> i) & 0xff:02X}' for i in range(40, -1, -8))
    except Exception:
        return 'UNKNOWN'


def get_mac_suffix() -> str:
    """Get the last 6 characters of the primary network interface MAC.
    
    Returns:
        MAC suffix like 'aabbcc' or '------' if not found
    """
    for interface in ['eth0', 'wlan0', 'end0', 'wlan1']:
        mac_path = f'/sys/class/net/{interface}/address'
        try:
            with open(mac_path, 'r') as f:
                mac = f.read().strip().replace(':', '')
                return mac[-6:].lower()
        except FileNotFoundError:
            continue
    return '------'


def get_hostname() -> str:
    """Get the system hostname."""
    try:
        return socket.gethostname()
    except Exception:
        return 'unknown'


def get_ui_language() -> Optional[str]:
    """Get the currently configured UI language."""
    try:
        lang_file = STAGEBOX_ROOT / 'data' / 'language.txt'
        if lang_file.exists():
            return lang_file.read_text().strip()
    except Exception:
        pass
    return 'en'


def ip_to_int(ip: str) -> int:
    """Convert IP address string to integer."""
    parts = ip.split('.')
    return int(parts[0]) << 24 | int(parts[1]) << 16 | int(parts[2]) << 8 | int(parts[3])


def int_to_ip(i: int) -> str:
    """Convert integer to IP address string."""
    return f"{(i >> 24) & 0xFF}.{(i >> 16) & 0xFF}.{(i >> 8) & 0xFF}.{i & 0xFF}"


def escape_csv(val) -> str:
    """Escape a value for CSV output."""
    val = str(val)
    if ',' in val or '"' in val or '\n' in val:
        return '"' + val.replace('"', '""') + '"'
    return val


# =============================================================================
# Hardware Info Functions
# =============================================================================

def get_pi_model() -> str:
    """Get Raspberry Pi model name.
    
    Returns:
        Model string like 'Raspberry Pi 5 Model B Rev 1.0' or 'Unknown'
    """
    try:
        model_path = Path('/proc/device-tree/model')
        if model_path.exists():
            model = model_path.read_text().rstrip('\x00').strip()
            # Shorten for display
            model = model.replace('Raspberry Pi ', 'Pi ')
            model = model.replace(' Model ', ' ')
            model = model.replace(' Rev ', ' Rev')
            return model
    except Exception:
        pass
    return 'Unknown'


def get_pi_model_short() -> str:
    """Get short Pi model name.
    
    Returns:
        Short string like 'Pi 4B' or 'Pi 5B'
    """
    try:
        model_path = Path('/proc/device-tree/model')
        if model_path.exists():
            model = model_path.read_text().rstrip('\x00').strip()
            if 'Raspberry Pi 5' in model:
                return 'Pi 5'
            elif 'Raspberry Pi 4' in model:
                return 'Pi 4'
            elif 'Raspberry Pi 3' in model:
                return 'Pi 3'
            elif 'Raspberry Pi Zero 2' in model:
                return 'Pi Zero 2'
            elif 'Raspberry Pi Zero' in model:
                return 'Pi Zero'
    except Exception:
        pass
    return 'Unknown'


def get_pi_ram() -> str:
    """Get total RAM in GB.
    
    Returns:
        RAM string like '4GB' or '8GB'
    """
    try:
        with open('/proc/meminfo', 'r') as f:
            for line in f:
                if line.startswith('MemTotal:'):
                    kb = int(line.split()[1])
                    gb = round(kb / 1024 / 1024)
                    return f'{gb}GB'
    except Exception:
        pass
    return '?GB'


def get_pi_serial() -> str:
    """Get Raspberry Pi serial number (last 8 chars).
    
    Returns:
        Serial string like 'a1b2c3d4' or 'unknown'
    """
    try:
        # Try device-tree first (more reliable)
        serial_path = Path('/sys/firmware/devicetree/base/serial-number')
        if serial_path.exists():
            serial = serial_path.read_text().rstrip('\x00').strip()
            return serial[-8:].lower()
        
        # Fallback to cpuinfo
        with open('/proc/cpuinfo', 'r') as f:
            for line in f:
                if line.startswith('Serial'):
                    serial = line.split(':')[1].strip()
                    return serial[-8:].lower()
    except Exception:
        pass
    return 'unknown'


def get_cpu_temp() -> Optional[float]:
    """Get CPU temperature in Celsius.
    
    Returns:
        Temperature as float like 45.2 or None if unavailable
    """
    try:
        temp_path = Path('/sys/class/thermal/thermal_zone0/temp')
        if temp_path.exists():
            temp_millideg = int(temp_path.read_text().strip())
            return round(temp_millideg / 1000, 1)
    except Exception:
        pass
    return None


def get_uptime() -> str:
    """Get system uptime as human-readable string.
    
    Returns:
        Uptime string like '3d 12h' or '45m' or '2h 15m'
    """
    try:
        with open('/proc/uptime', 'r') as f:
            uptime_seconds = float(f.read().split()[0])
        
        days = int(uptime_seconds // 86400)
        hours = int((uptime_seconds % 86400) // 3600)
        minutes = int((uptime_seconds % 3600) // 60)
        
        if days > 0:
            return f'{days}d {hours}h'
        elif hours > 0:
            return f'{hours}h {minutes}m'
        else:
            return f'{minutes}m'
    except Exception:
        pass
    return '?'


def get_hardware_info() -> dict:
    """Get all hardware info as a dictionary.
    
    Returns:
        Dict with model, ram, serial, mac_suffix, cpu_temp, uptime
    """
    return {
        'model': get_pi_model_short(),
        'ram': get_pi_ram(),
        'serial': get_pi_serial(),
        'mac_suffix': get_mac_suffix(),
        'cpu_temp': get_cpu_temp(),
        'uptime': get_uptime()
    }
