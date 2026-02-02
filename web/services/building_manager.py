"""
Stagebox Building Manager

Manages building discovery, activation, and state.
"""

import json
import re
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from web import config
from web.services.device_manager import device_manager, init_core_modules
from web.services.core_modules import reload_core_modules


def create_building(name: str) -> Dict[str, Any]:
    """
    Create a new building using the mk_new_building.sh script.
    
    Returns dict with 'success', 'message', and optionally 'name'.
    """
    # Normalize name: lowercase, spaces to underscores, remove special chars
    name = name.lower().replace(' ', '_').replace('-', '_')
    name = re.sub(r'[^a-z0-9_]', '', name)
    name = re.sub(r'_+', '_', name)
    name = name.strip('_')
    
    if not name:
        return {'success': False, 'error': 'Invalid name'}
    
    # Check if building already exists
    building_path = config.BUILDINGS_DIR / name
    if building_path.exists():
        return {'success': False, 'error': 'Building already exists', 'name': name}
    
    try:
        script_path = Path('/home/coredev/scripts/building_scripts/mk_new_building.sh')
        if not script_path.exists():
            return {'success': False, 'error': 'Build script not found'}
        
        result = subprocess.run(
            [str(script_path), name],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            return {'success': True, 'message': f'Building {name} created', 'name': name}
        else:
            return {'success': False, 'error': result.stderr or 'Script failed'}
            
    except subprocess.TimeoutExpired:
        return {'success': False, 'error': 'Timeout creating building'}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def ensure_default_building_exists() -> Optional[str]:
    """
    Ensure at least one 'my_*' building exists for Personal edition.
    Creates 'my_building' if no my_* buildings exist and activates it.
    
    Returns the name of the created/activated building, or None if not needed/failed.
    """
    from web.edition import is_limited
    
    if not is_limited():
        return None
    
    buildings = discover_buildings()
    
    # Check if any my_* building exists
    my_buildings = [b for b in buildings if b['name'].startswith('my_')]
    if my_buildings:
        # Building exists - ensure it's activated
        active = get_active_building()
        if not active:
            building_name = my_buildings[0]['name']
            if activate_building(building_name):
                print(f"[Stagebox] Activated existing building: {building_name}")
                return building_name
        return None  # Building exists and is (or was) active
    
    # Create default building (will be named my_building)
    result = create_building('my_building')
    if result.get('success'):
        building_name = result.get('name', 'my_building')
        print(f"[Stagebox] Created default building: {building_name}")
        
        # Activate the newly created building
        if activate_building(building_name):
            print(f"[Stagebox] Activated default building: {building_name}")
            return building_name
        else:
            print(f"[Stagebox] Warning: Could not activate building: {building_name}")
            return building_name
    else:
        print(f"[Stagebox] Failed to create default building: {result.get('error')}")
        return None


def discover_buildings() -> List[Dict[str, Any]]:
    """Discover all buildings by scanning BUILDINGS_DIR/*/stagebox/data/config.yaml."""
    buildings = []
    
    if not config.BUILDINGS_DIR.exists():
        return buildings
    
    for building_dir in config.BUILDINGS_DIR.iterdir():
        if not building_dir.is_dir():
            continue
        
        config_path = building_dir / 'stagebox' / 'data' / 'config.yaml'
        if not config_path.exists():
            continue
        
        # Found a building!
        building_info = {
            'name': building_dir.name,
            'path': str(building_dir / 'stagebox'),
            'config_path': str(config_path),
            'device_count': 0,
        }
        
        # Try to read network config
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                cfg = yaml.safe_load(f) or {}
            
            network = cfg.get('stage2', {}).get('network', {})
            building_info['pool_start'] = network.get('pool_start', '')
            building_info['pool_end'] = network.get('pool_end', '')
            building_info['gateway'] = network.get('gateway', '')
            building_info['dhcp_start'] = network.get('dhcp_scan_start', '')
            building_info['dhcp_end'] = network.get('dhcp_scan_end', '')
        except Exception as e:
            print(f"Error reading config for {building_dir.name}: {e}")
        
        # Try to count devices from ip_state.json
        try:
            state_path = building_dir / 'stagebox' / 'data' / 'ip_state.json'
            if state_path.exists():
                with open(state_path, 'r', encoding='utf-8') as f:
                    state = json.load(f)
                    devices = state.get('devices', {})
                    building_info['device_count'] = len(devices)
        except Exception as e:
            print(f"Error reading ip_state for {building_dir.name}: {e}")
        
        buildings.append(building_info)
    
    return sorted(buildings, key=lambda b: b['name'])


def activate_building(building_name: str) -> bool:
    """Activate a building by setting up paths and reloading config."""
    building_path = config.BUILDINGS_DIR / building_name / 'stagebox'
    config_path = building_path / 'data' / 'config.yaml'
    
    if not config_path.exists():
        return False
    
    config.active_building = building_name
    config.PROJECT_ROOT = building_path
    config.DATA_DIR = building_path / 'data'
    config.STATE_FILE = config.DATA_DIR / 'ip_state.json'
    config.CONFIG_FILE = config.DATA_DIR / 'config.yaml'
    config.SECRETS_FILE = config.DATA_DIR / 'secrets.yaml'
    
    # Initialize device manager core modules
    init_core_modules()
    
    # Initialize provisioning core modules (Stage 2, 3, 4)
    reload_core_modules()
    
    # Reload device manager with new path
    device_manager.set_state_file(config.STATE_FILE)
    device_manager.load_devices()
    
    print(f"Activated building: {building_name} at {building_path}")
    return True


def deactivate_building():
    """Deactivate current building."""
    config.active_building = None
    config.PROJECT_ROOT = None
    config.DATA_DIR = None
    config.STATE_FILE = None
    config.CONFIG_FILE = None
    config.SECRETS_FILE = None
    
    device_manager.devices = []
    device_manager.state = None


def get_active_building() -> Optional[str]:
    """Get currently active building name."""
    return config.active_building


def is_building_active() -> bool:
    """Check if any building is currently active."""
    return config.active_building is not None
