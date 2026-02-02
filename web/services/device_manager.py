"""
Stagebox Device Manager

Manages device state, loading, saving, and status checking.
"""

import json
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List, Optional

from web.config import MAX_WORKERS


# Core module availability flags
CORE_AVAILABLE = False

# Placeholders for core imports
load_state = None
save_state_atomic_with_bak = None
update_device = None
State = None


class FallbackState:
    """Fallback State class when core modules not available."""
    def __init__(self, version=1, devices=None):
        self.version = version
        self.devices = devices or {}


def init_core_modules():
    """Initialize core module imports."""
    global CORE_AVAILABLE, load_state, save_state_atomic_with_bak, update_device, State
    
    try:
        from core.state import load_state as _load_state
        from core.state import save_state_atomic_with_bak as _save_state
        from core.state import update_device as _update_device
        from core.models import State as _State
        
        load_state = _load_state
        save_state_atomic_with_bak = _save_state
        update_device = _update_device
        State = _State
        CORE_AVAILABLE = True
    except ImportError as e:
        print(f"WARNING: Core modules not available: {e}")
        CORE_AVAILABLE = False
        State = FallbackState


class DeviceManager:
    """Manages Shelly device state and operations."""
    
    def __init__(self, state_file=None):
        self.state_file = state_file
        self.devices: List[Dict[str, Any]] = []
        self.state = None
        if state_file:
            self.load_devices()
    
    def set_state_file(self, state_file):
        """Set or change the state file path."""
        self.state_file = state_file
    
    def load_devices(self):
        """Load devices from ip_state.json."""
        if not self.state_file:
            self.devices = []
            self.state = FallbackState() if State is None else State()
            return
        
        try:
            if CORE_AVAILABLE and load_state:
                self.state = load_state(str(self.state_file))
                self.devices = []
                for mac, device in self.state.devices.items():
                    if 'id' not in device:
                        device['id'] = mac
                    self.devices.append(device)
            else:
                # Fallback to direct JSON loading
                state_path = Path(self.state_file)
                if state_path.exists():
                    with open(state_path, 'r') as f:
                        data = json.load(f)
                    
                    if isinstance(data, dict) and 'devices' in data:
                        self.devices = []
                        for mac, device in data['devices'].items():
                            if 'id' not in device:
                                device['id'] = mac
                            self.devices.append(device)
                        StateClass = State if State else FallbackState
                        self.state = StateClass(
                            version=data.get('version', 1),
                            devices=data['devices']
                        )
                    else:
                        self.devices = []
                        self.state = FallbackState()
                else:
                    self.devices = []
                    self.state = FallbackState()
                    
            print(f"Loaded {len(self.devices)} devices from {self.state_file}")
        except Exception as e:
            print(f"Error loading state file: {e}")
            import traceback
            traceback.print_exc()
            self.devices = []
            self.state = FallbackState()
    
    def save_state(self) -> bool:
        """Save state to ip_state.json."""
        try:
            if CORE_AVAILABLE and self.state and save_state_atomic_with_bak:
                bak_path = str(self.state_file) + ".bak"
                save_state_atomic_with_bak(self.state, str(self.state_file), bak_path)
            else:
                # Fallback
                data = {
                    'version': self.state.version if self.state else 1,
                    'devices': self.state.devices if self.state else {}
                }
                with open(self.state_file, 'w') as f:
                    json.dump(data, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving state: {e}")
            return False
    
    def get_device(self, device_id: str) -> Optional[Dict[str, Any]]:
        """Get device by ID (MAC)."""
        if self.state:
            mac_normalized = device_id.upper().replace(':', '').replace('-', '')
            return (
                self.state.devices.get(mac_normalized) or
                self.state.devices.get(device_id) or
                self.state.devices.get(device_id.upper()) or
                self.state.devices.get(device_id.lower())
            )
        return None
    
    def update_device(self, device_id: str, updates: Dict[str, Any]) -> bool:
        """Update device metadata."""
        try:
            mac_normalized = device_id.upper().replace(':', '').replace('-', '')
            
            if CORE_AVAILABLE and self.state and update_device:
                update_device(self.state, mac_normalized, updates)
                self.save_state()
                self.load_devices()
                return True
            else:
                # Fallback
                if self.state and mac_normalized in self.state.devices:
                    self.state.devices[mac_normalized].update(updates)
                    self.save_state()
                    self.load_devices()
                    return True
            return False
        except Exception as e:
            print(f"Error updating device: {e}")
            return False
    
    def delete_device(self, device_id: str) -> bool:
        """Remove a device from ip_state.json."""
        try:
            mac_normalized = device_id.upper().replace(':', '').replace('-', '')
            
            if self.state and hasattr(self.state, 'devices') and mac_normalized in self.state.devices:
                del self.state.devices[mac_normalized]
                self.save_state()
                self.load_devices()
                return True
            return False
        except Exception as e:
            print(f"Error deleting device: {e}")
            return False
    
    @staticmethod
    def ping_device(ip: str) -> bool:
        """Ping a single device (returns True if online)."""
        try:
            result = subprocess.run(
                ['ping', '-c', '1', '-W', '1', ip],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=2
            )
            return result.returncode == 0
        except:
            return False
    
    def check_devices_status(self) -> Dict[str, bool]:
        """Check online status of all devices in parallel."""
        status = {}
        
        if not self.devices:
            return status
        
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            future_to_device = {}
            for device in self.devices:
                if not isinstance(device, dict):
                    continue
                device_ip = device.get('ip', '')
                if device_ip:
                    future = executor.submit(self.ping_device, device_ip)
                    future_to_device[future] = device
            
            for future in as_completed(future_to_device):
                device = future_to_device[future]
                device_id = device.get('id', device.get('ip'))
                try:
                    status[device_id] = future.result()
                except:
                    status[device_id] = False
        
        return status


# Global device manager instance
device_manager = DeviceManager()


def get_device_manager() -> DeviceManager:
    """Get the global device manager instance."""
    return device_manager
