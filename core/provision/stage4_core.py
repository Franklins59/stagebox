"""
Stage 4 provisioning core logic for Shelly Gen2+ devices.

This module is API-first and independent of any CLI or Flask UI.
It is designed to be used from:

- scripts/shelly_stage4.py (CLI) - minimal
- web/ (Flask endpoints) - primary

Responsibilities:
- Load and match profiles to devices
- Apply Shelly profile (switch/cover) with reboot handling
- Configure components (Switch, Input, Cover)
- Deploy scripts
- Create/manage webhooks
- Read/update KVS values

The design follows the same patterns as stage2_core.py and stage3_core.py.
"""

from __future__ import annotations

import datetime as dt
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests
import yaml


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DEFAULT_PROFILES_DIR = Path("data/profiles")
DEFAULT_SCRIPTS_DIR = Path("data/scripts")
DEFAULT_TIMEOUT = 5.0
REBOOT_WAIT_TIME = 10.0  # seconds to wait after reboot


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class Stage4Config:
    """Top-level configuration for Stage 4."""
    enabled: bool = True
    profiles_dir: str = "data/profiles"
    scripts_dir: str = "data/scripts"
    timeout_s: float = 5.0
    reboot_wait_s: float = 10.0


@dataclass
class Profile:
    """Parsed profile from YAML."""
    name: str
    description: str
    device_types: List[str]
    shelly_profile: Optional[str]  # "switch" | "cover" | None
    components: Dict[str, Dict[str, Any]]
    scripts: List[Dict[str, Any]]
    webhooks: List[Dict[str, Any]]
    raw: Dict[str, Any]  # Original YAML data


@dataclass
class Stage4Error:
    code: str
    message: str
    detail: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Stage4Warning:
    code: str
    message: str
    detail: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Stage4Result:
    """Result of a Stage 4 operation."""
    ok: bool
    mac: str
    ip: str
    profile_name: Optional[str]
    actions: Dict[str, Any]
    errors: List[Stage4Error]
    warnings: List[Stage4Warning]
    meta: Dict[str, Any]


# ---------------------------------------------------------------------------
# HTTP/RPC helpers
# ---------------------------------------------------------------------------

def _build_url(ip: str, method: str) -> str:
    """Build RPC URL for a Shelly device."""
    return f"http://{ip}/rpc/{method}"


def _rpc_call(
    ip: str,
    method: str,
    params: Optional[Dict[str, Any]] = None,
    timeout: float = DEFAULT_TIMEOUT,
) -> Tuple[bool, Optional[Dict[str, Any]], str]:
    """
    Make an RPC call to a Shelly device.
    
    Returns:
        (ok, result_data, error_message)
    """
    url = _build_url(ip, method)
    
    try:
        if params:
            # POST with JSON body
            resp = requests.post(
                url,
                json=params,
                timeout=timeout,
            )
        else:
            # GET for simple calls
            resp = requests.get(url, timeout=timeout)
        
        if resp.status_code != 200:
            return False, None, f"HTTP {resp.status_code}"
        
        data = resp.json()
        
        # Check for RPC error in response
        if isinstance(data, dict) and "error" in data:
            err = data["error"]
            code = err.get("code", "unknown")
            msg = err.get("message", "RPC error")
            return False, None, f"RPC error {code}: {msg}"
        
        return True, data, ""
        
    except requests.exceptions.Timeout:
        return False, None, "Request timeout"
    except requests.exceptions.ConnectionError as e:
        return False, None, f"Connection error: {e}"
    except Exception as e:
        return False, None, f"Request failed: {e}"


def _wait_for_device(ip: str, timeout: float = 30.0, interval: float = 2.0) -> bool:
    """
    Wait for device to come back online after reboot.
    
    Returns True if device is reachable, False if timeout.
    """
    start = time.time()
    while time.time() - start < timeout:
        ok, _, _ = _rpc_call(ip, "Shelly.GetDeviceInfo", timeout=2.0)
        if ok:
            return True
        time.sleep(interval)
    return False


# ---------------------------------------------------------------------------
# Profile loading
# ---------------------------------------------------------------------------

def load_profile(profile_path: Path) -> Optional[Profile]:
    """Load a single profile from YAML file."""
    try:
        with profile_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        
        return Profile(
            name=data.get("name", profile_path.stem),
            description=data.get("description", ""),
            device_types=data.get("device_types", []),
            shelly_profile=data.get("shelly_profile"),
            components=data.get("components", {}),
            scripts=data.get("scripts", []),
            webhooks=data.get("webhooks", []),
            raw=data,
        )
    except Exception as e:
        print(f"Error loading profile {profile_path}: {e}")
        return None


def load_all_profiles(profiles_dir: Path) -> Dict[str, Profile]:
    """Load all profiles from directory."""
    profiles = {}
    
    if not profiles_dir.exists():
        return profiles
    
    for path in profiles_dir.glob("*.yaml"):
        if path.name.startswith("_"):
            continue  # Skip schema and other special files
        
        profile = load_profile(path)
        if profile:
            profiles[path.stem] = profile
    
    return profiles


def match_profile_for_device(
    hw_model: str,
    profiles: Dict[str, Profile],
) -> Optional[Tuple[str, Profile]]:
    """
    Find matching profile for a device based on hw_model.
    
    Returns:
        (profile_name, Profile) or None if no match
    """
    for name, profile in profiles.items():
        if hw_model in profile.device_types:
            return name, profile
    return None


# ---------------------------------------------------------------------------
# Shelly profile (switch/cover)
# ---------------------------------------------------------------------------

def get_current_shelly_profile(ip: str, timeout: float = DEFAULT_TIMEOUT) -> Optional[str]:
    """
    Get current Shelly profile (switch/cover).
    
    Returns None if device doesn't support profiles or on error.
    """
    ok, data, _ = _rpc_call(ip, "Shelly.GetDeviceInfo", timeout=timeout)
    if not ok or not data:
        return None
    
    return data.get("profile")


def set_shelly_profile(
    ip: str,
    profile_name: str,
    timeout: float = DEFAULT_TIMEOUT,
    wait_for_reboot: bool = True,
    reboot_timeout: float = 30.0,
) -> Tuple[bool, str]:
    """
    Set Shelly profile (switch/cover).
    
    WARNING: This triggers a device reboot!
    
    Returns:
        (ok, message)
    """
    # Check current profile first
    current = get_current_shelly_profile(ip, timeout)
    
    if current is None:
        return False, "Device doesn't support profiles or unreachable"
    
    if current == profile_name:
        return True, f"Profile already set to '{profile_name}'"
    
    # Set new profile
    ok, _, msg = _rpc_call(
        ip,
        "Shelly.SetProfile",
        params={"name": profile_name},
        timeout=timeout,
    )
    
    if not ok:
        return False, f"Failed to set profile: {msg}"
    
    # Wait for reboot
    if wait_for_reboot:
        time.sleep(2)  # Give device time to start rebooting
        if not _wait_for_device(ip, timeout=reboot_timeout):
            return False, "Device did not come back online after profile change"
    
    return True, f"Profile changed to '{profile_name}'"


# ---------------------------------------------------------------------------
# Component configuration
# ---------------------------------------------------------------------------

def get_component_config(
    ip: str,
    component: str,
    component_id: int,
    timeout: float = DEFAULT_TIMEOUT,
) -> Tuple[bool, Optional[Dict[str, Any]], str]:
    """
    Get configuration of a component.
    
    Args:
        component: "Switch", "Input", "Cover", etc.
        component_id: 0, 1, 2, ...
    
    Returns:
        (ok, config_dict, error_message)
    """
    method = f"{component}.GetConfig"
    params = {"id": component_id}
    
    return _rpc_call(ip, method, params, timeout)


def set_component_config(
    ip: str,
    component: str,
    component_id: int,
    config: Dict[str, Any],
    timeout: float = DEFAULT_TIMEOUT,
) -> Tuple[bool, str]:
    """
    Set configuration of a component.
    
    Args:
        component: "Switch", "Input", "Cover", etc.
        component_id: 0, 1, 2, ...
        config: Configuration dict (only changed fields)
    
    Returns:
        (ok, message)
    """
    # Filter out None values - Shelly doesn't accept null in SetConfig
    filtered_config = {k: v for k, v in config.items() if v is not None}
    
    if not filtered_config:
        return True, f"{component}:{component_id} no changes (all values null)"
    
    method = f"{component}.SetConfig"
    params = {
        "id": component_id,
        "config": filtered_config,
    }
    
    ok, data, msg = _rpc_call(ip, method, params, timeout)
    
    if not ok:
        return False, f"{method} failed: {msg}"
    
    # Check if restart required
    restart_required = False
    if isinstance(data, dict):
        restart_required = data.get("restart_required", False)
    
    if restart_required:
        return True, f"{component}:{component_id} configured (restart required)"
    
    return True, f"{component}:{component_id} configured"


def apply_component_configs(
    ip: str,
    components: Dict[str, Dict[str, Any]],
    timeout: float = DEFAULT_TIMEOUT,
    errors: List[Stage4Error] = None,
    warnings: List[Stage4Warning] = None,
) -> Dict[str, Any]:
    """
    Apply all component configurations from profile.
    
    Args:
        components: Dict like {"switch:0": {...}, "input:0": {...}}
    
    Returns:
        Action result dict with changed components
    
    Note:
        This function handles the tricky input.type / switch.in_mode dependency:
        - Certain switch.in_mode values are only valid with certain input.type values
        - When changing input.type, we first set switch to safe intermediate values
    """
    if errors is None:
        errors = []
    if warnings is None:
        warnings = []
    
    result = {
        "changed": [],
        "unchanged": [],
        "failed": [],
        "restart_required": False,
    }
    
    # Separate components by type
    switch_configs = {}
    input_configs = {}
    cover_configs = {}
    other_configs = {}
    
    for comp_key, config in components.items():
        if comp_key.startswith("switch:"):
            switch_configs[comp_key] = config
        elif comp_key.startswith("input:"):
            input_configs[comp_key] = config
        elif comp_key.startswith("cover:"):
            cover_configs[comp_key] = config
        else:
            other_configs[comp_key] = config
    
    # Helper to apply a single component
    def apply_single(comp_key: str, config: Dict[str, Any]) -> bool:
        if ":" not in comp_key:
            warnings.append(Stage4Warning(
                code="invalid_component_key",
                message=f"Invalid component key: {comp_key}",
                detail={"key": comp_key},
            ))
            return False
        
        component, id_str = comp_key.split(":", 1)
        try:
            component_id = int(id_str)
        except ValueError:
            warnings.append(Stage4Warning(
                code="invalid_component_id",
                message=f"Invalid component ID: {id_str}",
                detail={"key": comp_key},
            ))
            return False
        
        component_name = component.capitalize()
        ok, msg = set_component_config(ip, component_name, component_id, config, timeout)
        
        if ok:
            result["changed"].append(comp_key)
            if "restart required" in msg.lower():
                result["restart_required"] = True
            return True
        else:
            result["failed"].append(comp_key)
            errors.append(Stage4Error(
                code="component_config_failed",
                message=msg,
                detail={"component": comp_key, "config": config},
            ))
            return False
    
    # Step 1: Handle switch/input dependency
    # For each input that changes type, we need to handle the switch carefully
    for input_key, input_config in input_configs.items():
        target_type = input_config.get("type")
        if not target_type:
            continue
        
        # Get input ID
        input_id_str = input_key.split(":")[1]
        try:
            input_id = int(input_id_str)
        except ValueError:
            continue
        
        # Check current input type on device
        ok, current_input, _ = get_component_config(ip, "Input", input_id, timeout)
        if not ok or not current_input:
            continue
        
        current_type = current_input.get("type")
        
        # If input type is changing, we need to set switch to safe values first
        if current_type != target_type:
            switch_key = f"switch:{input_id}"
            if switch_key in switch_configs:
                # Set switch to safe intermediate values that work with ANY input type
                # "detached" mode works with both "switch" and "button" input types
                safe_config = {
                    "in_mode": "detached",
                    "initial_state": "off",
                }
                ok, msg = set_component_config(ip, "Switch", input_id, safe_config, timeout)
                if not ok:
                    # Log warning but continue - maybe it will work anyway
                    warnings.append(Stage4Warning(
                        code="safe_mode_failed",
                        message=f"Could not set switch:{input_id} to safe mode: {msg}",
                        detail={"switch": switch_key},
                    ))
    
    # Step 2: Apply cover configs (no dependency issues)
    for comp_key, config in sorted(cover_configs.items()):
        apply_single(comp_key, config)
    
    # Step 3: Apply input configs (change input.type)
    for comp_key, config in sorted(input_configs.items()):
        apply_single(comp_key, config)
    
    # Step 4: Apply switch configs (now input.type is correct)
    for comp_key, config in sorted(switch_configs.items()):
        apply_single(comp_key, config)
    
    # Step 5: Apply other configs
    for comp_key, config in sorted(other_configs.items()):
        apply_single(comp_key, config)
    
    return result


# ---------------------------------------------------------------------------
# Script management
# ---------------------------------------------------------------------------

def list_scripts(
    ip: str,
    timeout: float = DEFAULT_TIMEOUT,
) -> Tuple[bool, List[Dict[str, Any]], str]:
    """
    List all scripts on device.
    
    Returns:
        (ok, list_of_scripts, error_message)
    """
    ok, data, msg = _rpc_call(ip, "Script.List", timeout=timeout)
    
    if not ok:
        return False, [], msg
    
    scripts = data.get("scripts", []) if data else []
    return True, scripts, ""


def get_script(
    ip: str,
    script_id: int,
    timeout: float = DEFAULT_TIMEOUT,
) -> Tuple[bool, Optional[Dict[str, Any]], str]:
    """Get script config by ID."""
    return _rpc_call(ip, "Script.GetConfig", {"id": script_id}, timeout)


def create_script(
    ip: str,
    name: str,
    timeout: float = DEFAULT_TIMEOUT,
) -> Tuple[bool, Optional[int], str]:
    """
    Create a new script slot.
    
    Returns:
        (ok, script_id, error_message)
    """
    ok, data, msg = _rpc_call(
        ip,
        "Script.Create",
        {"name": name},
        timeout,
    )
    
    if not ok:
        return False, None, msg
    
    script_id = data.get("id") if data else None
    return True, script_id, ""


def put_script_code(
    ip: str,
    script_id: int,
    code: str,
    timeout: float = DEFAULT_TIMEOUT,
) -> Tuple[bool, str]:
    """
    Upload code to a script slot.
    
    For large scripts, this may need to be called multiple times
    with append=True (not implemented yet).
    """
    ok, _, msg = _rpc_call(
        ip,
        "Script.PutCode",
        {"id": script_id, "code": code, "append": False},
        timeout,
    )
    
    if not ok:
        return False, f"Script.PutCode failed: {msg}"
    
    return True, ""


def set_script_config(
    ip: str,
    script_id: int,
    name: Optional[str] = None,
    enable: Optional[bool] = None,
    timeout: float = DEFAULT_TIMEOUT,
) -> Tuple[bool, str]:
    """Set script configuration (name, enable/disable)."""
    config = {}
    if name is not None:
        config["name"] = name
    if enable is not None:
        config["enable"] = enable
    
    if not config:
        return True, "No changes"
    
    ok, _, msg = _rpc_call(
        ip,
        "Script.SetConfig",
        {"id": script_id, "config": config},
        timeout,
    )
    
    if not ok:
        return False, f"Script.SetConfig failed: {msg}"
    
    return True, ""


def delete_script(
    ip: str,
    script_id: int,
    timeout: float = DEFAULT_TIMEOUT,
) -> Tuple[bool, str]:
    """Delete a script."""
    ok, _, msg = _rpc_call(
        ip,
        "Script.Delete",
        {"id": script_id},
        timeout,
    )
    
    if not ok:
        return False, f"Script.Delete failed: {msg}"
    
    return True, ""


def deploy_script(
    ip: str,
    name: str,
    code: str,
    run_on_start: bool = False,
    timeout: float = DEFAULT_TIMEOUT,
) -> Tuple[bool, Optional[int], str]:
    """
    Deploy a script to device.
    
    Creates a new script slot, uploads code, and optionally enables it.
    
    Returns:
        (ok, script_id, message)
    """
    # Create script slot
    ok, script_id, msg = create_script(ip, name, timeout)
    if not ok or script_id is None:
        return False, None, f"Failed to create script: {msg}"
    
    # Upload code
    ok, msg = put_script_code(ip, script_id, code, timeout)
    if not ok:
        # Try to clean up
        delete_script(ip, script_id, timeout)
        return False, None, msg
    
    # Enable if run_on_start
    if run_on_start:
        ok, msg = set_script_config(ip, script_id, enable=True, timeout=timeout)
        if not ok:
            return False, script_id, f"Script created but failed to enable: {msg}"
    
    return True, script_id, f"Script '{name}' deployed (id={script_id})"


# ---------------------------------------------------------------------------
# Webhook management
# ---------------------------------------------------------------------------

def list_webhooks(
    ip: str,
    timeout: float = DEFAULT_TIMEOUT,
) -> Tuple[bool, List[Dict[str, Any]], str]:
    """List all webhooks on device."""
    ok, data, msg = _rpc_call(ip, "Webhook.List", timeout=timeout)
    
    if not ok:
        return False, [], msg
    
    hooks = data.get("hooks", []) if data else []
    return True, hooks, ""


def create_webhook(
    ip: str,
    event: str,
    urls: List[str],
    component_id: Optional[int] = None,
    condition: Optional[str] = None,
    timeout: float = DEFAULT_TIMEOUT,
) -> Tuple[bool, Optional[int], str]:
    """
    Create a webhook.
    
    Args:
        event: Event type like "input.button_push", "switch.on"
        urls: List of target URLs
        component_id: Component ID (e.g. 0 for input:0)
        condition: Optional condition expression
    
    Returns:
        (ok, hook_id, message)
    """
    params: Dict[str, Any] = {
        "event": event,
        "urls": urls,
    }
    
    if component_id is not None:
        params["cid"] = component_id
    
    if condition:
        params["condition"] = condition
    
    ok, data, msg = _rpc_call(ip, "Webhook.Create", params, timeout)
    
    if not ok:
        return False, None, f"Webhook.Create failed: {msg}"
    
    hook_id = data.get("id") if data else None
    return True, hook_id, ""


def delete_webhook(
    ip: str,
    hook_id: int,
    timeout: float = DEFAULT_TIMEOUT,
) -> Tuple[bool, str]:
    """Delete a webhook."""
    ok, _, msg = _rpc_call(ip, "Webhook.Delete", {"id": hook_id}, timeout)
    
    if not ok:
        return False, f"Webhook.Delete failed: {msg}"
    
    return True, ""


# ---------------------------------------------------------------------------
# KVS management
# ---------------------------------------------------------------------------

def get_kvs(
    ip: str,
    timeout: float = DEFAULT_TIMEOUT,
) -> Tuple[bool, Dict[str, Any], str]:
    """
    Get all KVS entries.
    
    Returns:
        (ok, dict_of_key_values, error_message)
    """
    ok, data, msg = _rpc_call(ip, "KVS.GetMany", timeout=timeout)
    
    if not ok:
        return False, {}, msg
    
    # Parse items into simple dict
    # Shelly returns: {"items": [{"key": "foo", "value": "bar", "etag": "..."}, ...]}
    items = data.get("items", []) if data else []
    kvs = {}
    
    if isinstance(items, list):
        # List format (actual Shelly response)
        for entry in items:
            if isinstance(entry, dict) and "key" in entry:
                kvs[entry["key"]] = entry.get("value")
    elif isinstance(items, dict):
        # Dict format (fallback)
        for key, entry in items.items():
            if isinstance(entry, dict):
                kvs[key] = entry.get("value")
            else:
                kvs[key] = entry
    
    return True, kvs, ""


def set_kvs(
    ip: str,
    key: str,
    value: Any,
    timeout: float = DEFAULT_TIMEOUT,
) -> Tuple[bool, str]:
    """Set a KVS value."""
    ok, _, msg = _rpc_call(
        ip,
        "KVS.Set",
        {"key": key, "value": value},
        timeout,
    )
    
    if not ok:
        return False, f"KVS.Set failed: {msg}"
    
    return True, ""


# ---------------------------------------------------------------------------
# High-level: Apply profile to device
# ---------------------------------------------------------------------------

def apply_profile_to_device(
    ip: str,
    profile: Profile,
    dry_run: bool = False,
    timeout: float = DEFAULT_TIMEOUT,
    reboot_timeout: float = 30.0,
) -> Stage4Result:
    """
    Apply a complete profile to a device.
    
    Steps:
    1. Set Shelly profile (if specified, triggers reboot)
    2. Apply component configurations
    3. Deploy scripts
    4. Create webhooks
    
    Returns:
        Stage4Result with all actions taken
    """
    errors: List[Stage4Error] = []
    warnings: List[Stage4Warning] = []
    actions: Dict[str, Any] = {}
    
    now = dt.datetime.utcnow().isoformat() + "Z"
    
    # Get device info first
    ok, device_info, msg = _rpc_call(ip, "Shelly.GetDeviceInfo", timeout=timeout)
    if not ok:
        errors.append(Stage4Error(
            code="device_unreachable",
            message=f"Cannot reach device: {msg}",
            detail={"ip": ip},
        ))
        return Stage4Result(
            ok=False,
            mac="",
            ip=ip,
            profile_name=profile.name,
            actions=actions,
            errors=errors,
            warnings=warnings,
            meta={"ts": now, "dry_run": dry_run},
        )
    
    mac = device_info.get("mac", "") if device_info else ""
    
    # 1. Shelly profile (switch/cover)
    if profile.shelly_profile:
        if dry_run:
            actions["shelly_profile"] = {
                "action": "would_set",
                "target": profile.shelly_profile,
            }
        else:
            ok, msg = set_shelly_profile(
                ip,
                profile.shelly_profile,
                timeout=timeout,
                wait_for_reboot=True,
                reboot_timeout=reboot_timeout,
            )
            actions["shelly_profile"] = {
                "ok": ok,
                "message": msg,
                "target": profile.shelly_profile,
            }
            if not ok:
                errors.append(Stage4Error(
                    code="profile_change_failed",
                    message=msg,
                    detail={"profile": profile.shelly_profile},
                ))
    
    # 2. Component configs
    if profile.components:
        if dry_run:
            actions["components"] = {
                "action": "would_configure",
                "components": list(profile.components.keys()),
            }
        else:
            comp_result = apply_component_configs(
                ip, profile.components, timeout, errors, warnings
            )
            actions["components"] = comp_result
    
    # 3. Scripts
    if profile.scripts:
        actions["scripts"] = []
        for script_def in profile.scripts:
            script_name = script_def.get("name", "unnamed")
            script_file = script_def.get("file", "")
            run_on_start = script_def.get("run_on_start", False)
            
            if dry_run:
                actions["scripts"].append({
                    "action": "would_deploy",
                    "name": script_name,
                    "file": script_file,
                })
            else:
                # Load script code from file
                # TODO: Resolve path properly
                warnings.append(Stage4Warning(
                    code="script_deploy_not_implemented",
                    message=f"Script deployment not fully implemented: {script_name}",
                    detail={"file": script_file},
                ))
    
    # 4. Webhooks
    if profile.webhooks:
        actions["webhooks"] = []
        for hook_def in profile.webhooks:
            event = hook_def.get("event", "")
            urls = hook_def.get("urls", [])
            
            if not event or not urls:
                continue
            
            if dry_run:
                actions["webhooks"].append({
                    "action": "would_create",
                    "event": event,
                    "urls": urls,
                })
            else:
                ok, hook_id, msg = create_webhook(
                    ip,
                    event=event,
                    urls=urls,
                    component_id=hook_def.get("component_id"),
                    condition=hook_def.get("condition"),
                    timeout=timeout,
                )
                actions["webhooks"].append({
                    "ok": ok,
                    "event": event,
                    "hook_id": hook_id,
                    "message": msg if not ok else "",
                })
                if not ok:
                    errors.append(Stage4Error(
                        code="webhook_create_failed",
                        message=msg,
                        detail={"event": event},
                    ))
    
    return Stage4Result(
        ok=len(errors) == 0,
        mac=mac,
        ip=ip,
        profile_name=profile.name,
        actions=actions,
        errors=errors,
        warnings=warnings,
        meta={"ts": now, "dry_run": dry_run},
    )


# ---------------------------------------------------------------------------
# State update (ip_state.json)
# ---------------------------------------------------------------------------

def update_device_state(
    state: Dict[str, Any],
    mac: str,
    result: Stage4Result,
    dry_run: bool = False,
) -> bool:
    """
    Update ip_state.json with Stage 4 results.
    
    Args:
        state: The state dict (will be modified in-place)
        mac: Device MAC address
        result: Stage4Result from apply_profile_to_device
    
    Returns:
        True if state was updated
    """
    if not mac:
        return False
    
    # Normalize MAC
    mac_normalized = mac.upper().replace(":", "").replace("-", "")
    
    # Get devices dict
    if "devices" in state and isinstance(state["devices"], dict):
        devices = state["devices"]
    else:
        devices = state
    
    # Find or create device entry
    device_entry = (
        devices.get(mac_normalized)
        or devices.get(mac)
        or devices.get(mac.upper())
        or devices.get(mac.lower())
    )
    
    if device_entry is None:
        # Device not in state - shouldn't happen if Stage 2 ran first
        return False
    
    # Build stage4 block
    now = dt.datetime.utcnow().isoformat() + "Z"
    stage4_block = {
        "ts": now,
        "status": "ok" if result.ok else "error",
        "profile": result.profile_name,
    }
    
    # Add action summary
    if result.actions.get("shelly_profile"):
        stage4_block["shelly_profile"] = result.actions["shelly_profile"].get("target")
    
    if result.actions.get("components"):
        comp = result.actions["components"]
        stage4_block["components_changed"] = comp.get("changed", [])
        stage4_block["components_failed"] = comp.get("failed", [])
    
    # Update device entry
    device_entry["stage4"] = stage4_block
    
    # Update stage_completed: set to 4 if currently at 3
    current_stage = device_entry.get("stage_completed", 0)
    if isinstance(current_stage, int) and current_stage == 3 and result.ok:
        device_entry["stage_completed"] = 4
    elif not isinstance(current_stage, int) and result.ok:
        device_entry["stage_completed"] = 4
    
    return True


def run_stage4_for_device(
    ip: str,
    mac: str,
    profile: Profile,
    state: Dict[str, Any],
    dry_run: bool = False,
    timeout: float = DEFAULT_TIMEOUT,
    reboot_timeout: float = 30.0,
) -> Stage4Result:
    """
    Run Stage 4 for a single device and update state.
    
    This is the main entry point that:
    1. Applies the profile
    2. Updates ip_state.json
    
    Args:
        ip: Device IP address
        mac: Device MAC address (for state lookup)
        profile: Profile to apply
        state: State dict (modified in-place)
        dry_run: If True, don't actually apply changes
    
    Returns:
        Stage4Result
    """
    # Apply profile
    result = apply_profile_to_device(
        ip=ip,
        profile=profile,
        dry_run=dry_run,
        timeout=timeout,
        reboot_timeout=reboot_timeout,
    )
    
    # Use MAC from result if not provided
    if not mac and result.mac:
        mac = result.mac
    
    # Update state
    if not dry_run:
        update_device_state(state, mac, result, dry_run)
    
    return result


def run_stage4_on_state(
    state: Dict[str, Any],
    profiles: Dict[str, Profile],
    only_ips: Optional[List[str]] = None,
    only_macs: Optional[List[str]] = None,
    dry_run: bool = False,
    force: bool = False,
    timeout: float = DEFAULT_TIMEOUT,
) -> Tuple[Dict[str, Stage4Result], Dict[str, str]]:
    """
    Run Stage 4 on all devices in state that match a profile.
    
    SAFETY: By default, only processes devices with stage_completed < 4.
    Devices without stage_completed field are SKIPPED (legacy protection).
    Use force=True to override (with confirmation in CLI).
    
    Args:
        state: ip_state.json dict
        profiles: Dict of loaded profiles
        only_ips: Optional filter by IP
        only_macs: Optional filter by MAC
        dry_run: If True, don't apply changes
        force: If True, also process devices with stage_completed >= 4
    
    Returns:
        Tuple of (results dict, skipped dict with reasons)
    """
    results: Dict[str, Stage4Result] = {}
    skipped: Dict[str, str] = {}
    
    # Get devices dict
    if "devices" in state and isinstance(state["devices"], dict):
        devices = state["devices"]
    else:
        devices = state
    
    # Build filter sets
    ip_filter = set(only_ips) if only_ips else None
    mac_filter = set(m.upper().replace(":", "").replace("-", "") for m in only_macs) if only_macs else None
    
    for mac, entry in devices.items():
        if not isinstance(entry, dict):
            continue
        
        ip = entry.get("ip")
        if not ip:
            continue
        
        # Apply filters
        mac_normalized = mac.upper().replace(":", "").replace("-", "")
        
        if ip_filter and ip not in ip_filter:
            continue
        
        if mac_filter and mac_normalized not in mac_filter:
            continue
        
        # SAFETY CHECK: stage_completed
        stage_completed = entry.get("stage_completed")
        
        if stage_completed is None:
            # No stage_completed field - legacy device, skip for safety
            skipped[mac_normalized] = "no_stage_completed (legacy device)"
            continue
        
        if not isinstance(stage_completed, int):
            skipped[mac_normalized] = f"invalid_stage_completed: {stage_completed}"
            continue
        
        if stage_completed >= 4 and not force:
            # Already configured, skip unless forced
            skipped[mac_normalized] = f"stage_completed={stage_completed} (use --force to override)"
            continue
        
        # Find matching profile
        hw_model = entry.get("hw_model") or entry.get("model") or ""
        match = match_profile_for_device(hw_model, profiles)
        
        if not match:
            # No matching profile - skip
            skipped[mac_normalized] = f"no_matching_profile for hw_model={hw_model}"
            continue
        
        profile_name, profile = match
        
        # Run Stage 4
        result = run_stage4_for_device(
            ip=ip,
            mac=mac_normalized,
            profile=profile,
            state=state,
            dry_run=dry_run,
            timeout=timeout,
        )
        
        results[mac_normalized] = result
    
    return results, skipped


# ---------------------------------------------------------------------------
# Utility: Reboot device
# ---------------------------------------------------------------------------

def reboot_device(
    ip: str,
    wait: bool = True,
    timeout: float = DEFAULT_TIMEOUT,
    reboot_timeout: float = 30.0,
) -> Tuple[bool, str]:
    """
    Reboot a device.
    
    Args:
        wait: If True, wait for device to come back online
    
    Returns:
        (ok, message)
    """
    ok, _, msg = _rpc_call(ip, "Shelly.Reboot", timeout=timeout)
    
    if not ok:
        return False, f"Reboot failed: {msg}"
    
    if wait:
        time.sleep(2)
        if not _wait_for_device(ip, timeout=reboot_timeout):
            return False, "Device did not come back online after reboot"
    
    return True, "Device rebooted"