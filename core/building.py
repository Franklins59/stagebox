"""
core/building.py - Building path management for Stagebox

This module provides centralized path resolution for multi-building deployments.
All building-specific data lives in:
    /home/coredev/buildings/<building_name>/stagebox/data/

Global data (admin.yaml, scripts pool, profiles templates) remains in:
    /home/coredev/stagebox/data/

Usage in CLI scripts:
    from core.building import get_building_paths, require_building
    
    # Get building from --building arg or STAGEBOX_BUILDING env
    building = require_building(args.building)
    paths = get_building_paths(building)
    
    config = load_yaml(paths['config'])
    secrets = load_yaml(paths['secrets'])

Usage in webui.py (when calling subprocesses):
    env = os.environ.copy()
    env['STAGEBOX_BUILDING'] = active_building
    subprocess.run([...], env=env)
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Dict, Optional


# Base directories
BUILDINGS_DIR = Path('/home/coredev/buildings')
GLOBAL_STAGEBOX_DIR = Path('/home/coredev/stagebox')
GLOBAL_DATA_DIR = GLOBAL_STAGEBOX_DIR / 'data'

# Environment variable name
BUILDING_ENV_VAR = 'STAGEBOX_BUILDING'


class BuildingError(Exception):
    """Raised when building is not specified or not found."""
    pass


def get_building_name(cli_arg: Optional[str] = None) -> Optional[str]:
    """
    Get building name from CLI argument or environment variable.
    
    Args:
        cli_arg: Building name from --building argument (takes priority)
    
    Returns:
        Building name or None if not specified
    """
    # CLI argument takes priority
    if cli_arg:
        return cli_arg.strip().lower()
    
    # Fall back to environment variable
    env_building = os.environ.get(BUILDING_ENV_VAR)
    if env_building:
        return env_building.strip().lower()
    
    return None


def require_building(cli_arg: Optional[str] = None) -> str:
    """
    Get building name, raising an error if not specified.
    
    Args:
        cli_arg: Building name from --building argument
    
    Returns:
        Building name
    
    Raises:
        BuildingError: If no building is specified
    """
    building = get_building_name(cli_arg)
    
    if not building:
        raise BuildingError(
            "No building specified.\n"
            "Use --building <name> or set STAGEBOX_BUILDING environment variable.\n"
            f"Available buildings: {', '.join(list_buildings()) or '(none)'}"
        )
    
    # Validate building exists
    building_path = BUILDINGS_DIR / building
    if not building_path.exists():
        available = list_buildings()
        raise BuildingError(
            f"Building '{building}' not found in {BUILDINGS_DIR}\n"
            f"Available buildings: {', '.join(available) or '(none)'}"
        )
    
    return building


def list_buildings() -> list[str]:
    """
    List all available buildings.
    
    Returns:
        List of building names
    """
    if not BUILDINGS_DIR.exists():
        return []
    
    buildings = []
    for path in BUILDINGS_DIR.iterdir():
        if path.is_dir() and not path.name.startswith('.'):
            # Check if it looks like a valid building (has stagebox/data structure)
            config_path = path / 'stagebox' / 'data' / 'config.yaml'
            if config_path.exists():
                buildings.append(path.name)
    
    return sorted(buildings)


def get_building_paths(building_name: str) -> Dict[str, Path]:
    """
    Get all relevant paths for a building.
    
    Args:
        building_name: Name of the building
    
    Returns:
        Dictionary with path keys:
            - building_root: /home/coredev/buildings/<building>
            - stagebox_root: /home/coredev/buildings/<building>/stagebox
            - data_dir: /home/coredev/buildings/<building>/stagebox/data
            - config: config.yaml path
            - secrets: secrets.yaml path
            - ip_state: ip_state.json path
            - profiles_dir: profiles/ directory
            - scripts_dir: scripts/ directory (building-local)
            - model_map: shelly_model_map.yaml path
            - var_dir: var/ directory (for logs)
    """
    building_root = BUILDINGS_DIR / building_name
    stagebox_root = building_root / 'stagebox'
    data_dir = stagebox_root / 'data'
    
    return {
        'building_root': building_root,
        'stagebox_root': stagebox_root,
        'data_dir': data_dir,
        'config': data_dir / 'config.yaml',
        'secrets': data_dir / 'secrets.yaml',
        'ip_state': data_dir / 'ip_state.json',
        'profiles_dir': data_dir / 'profiles',
        'scripts_dir': data_dir / 'scripts',
        'model_map': data_dir / 'shelly_model_map.yaml',
        'var_dir': stagebox_root / 'var',
    }


def get_global_paths() -> Dict[str, Path]:
    """
    Get paths for global (non-building-specific) resources.
    
    Returns:
        Dictionary with path keys:
            - stagebox_root: /home/coredev/stagebox
            - data_dir: /home/coredev/stagebox/data
            - admin_config: admin.yaml path
            - internal_secrets: internal_secrets.yaml path
            - scripts_pool: global scripts/ directory (Shelly .js pool)
            - profiles_templates: global profiles/ directory (templates)
            - model_map_template: shelly_model_map.yaml (template)
    """
    return {
        'stagebox_root': GLOBAL_STAGEBOX_DIR,
        'data_dir': GLOBAL_DATA_DIR,
        'admin_config': GLOBAL_DATA_DIR / 'admin.yaml',
        'internal_secrets': GLOBAL_DATA_DIR / 'internal_secrets.yaml',
        'scripts_pool': GLOBAL_DATA_DIR / 'scripts',
        'profiles_templates': GLOBAL_DATA_DIR / 'profiles',
        'model_map_template': GLOBAL_DATA_DIR / 'shelly_model_map.yaml',
    }


def add_building_argument(parser) -> None:
    """
    Add --building argument to an argparse parser.
    
    Args:
        parser: argparse.ArgumentParser instance
    """
    parser.add_argument(
        '-b', '--building',
        type=str,
        metavar='NAME',
        help=(
            f"Building name (or set {BUILDING_ENV_VAR} env var). "
            f"Buildings are in {BUILDINGS_DIR}/"
        ),
    )


def setup_building_environment(building_name: str) -> Dict[str, Path]:
    """
    Set up environment for a building and return paths.
    
    This is a convenience function that:
    1. Validates the building exists
    2. Sets STAGEBOX_BUILDING environment variable
    3. Returns the building paths
    
    Args:
        building_name: Name of the building
    
    Returns:
        Building paths dictionary
    
    Raises:
        BuildingError: If building not found
    """
    # Validate
    building = require_building(building_name)
    
    # Set environment (for any subprocesses)
    os.environ[BUILDING_ENV_VAR] = building
    
    # Return paths
    return get_building_paths(building)


# For backwards compatibility and convenience
def get_data_dir(building_name: Optional[str] = None) -> Path:
    """
    Get data directory path.
    
    Args:
        building_name: Building name (optional, uses env var if not provided)
    
    Returns:
        Path to data directory
    
    Raises:
        BuildingError: If no building specified
    """
    building = require_building(building_name)
    return get_building_paths(building)['data_dir']


def get_config_path(building_name: Optional[str] = None) -> Path:
    """Get config.yaml path for a building."""
    building = require_building(building_name)
    return get_building_paths(building)['config']


def get_secrets_path(building_name: Optional[str] = None) -> Path:
    """Get secrets.yaml path for a building."""
    building = require_building(building_name)
    return get_building_paths(building)['secrets']


def get_ip_state_path(building_name: Optional[str] = None) -> Path:
    """Get ip_state.json path for a building."""
    building = require_building(building_name)
    return get_building_paths(building)['ip_state']
