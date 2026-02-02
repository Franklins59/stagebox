"""
core/state.py — load/save of ip_state.json with .bak, migration support,
and a helper API for device manipulation.
"""

from __future__ import annotations

from pathlib import Path
import json
import shutil
from typing import Dict, Any, Iterable, Tuple, Optional

from .models import State
from .errors import ValidationError
from .utils.atomic import atomic_write

DEFAULT_STATE_PATH = "data/ip_state.json"
DEFAULT_BAK_PATH = "data/ip_state.json.bak"


def _empty_state() -> State:
    """Return a new empty State with default version."""
    return State(version=1, devices={})


def _migrate_old_top_level(obj: dict) -> Dict[str, Dict[str, Any]]:
    """
    Migration for very old schema, where the top-level keys were device IDs:

      {
         "<id1>": {...},
         "<id2>": {...}
      }

    We convert this into the new schema with a `devices` dict.
    """
    devices: Dict[str, Dict[str, Any]] = {}
    for key, value in obj.items():
        # Skip control keys
        if key in ("version", "devices"):
            continue
        if isinstance(value, dict):
            value.setdefault("id", key)
            devices[key] = value
    return devices


def load_state(path: str = DEFAULT_STATE_PATH) -> State:
    """
    Load ip_state.json into a State object.

    Supports:
      - new schema: {"version":1,"devices":{...}}
      - legacy list schema
      - very old schema: top-level keys = device IDs

    Returns:
      core.models.State instance.
    """
    p = Path(path)
    if not p.exists():
        state = _empty_state()
        state.path = str(p.resolve())
        return state

    try:
        obj = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ValidationError(f"ip_state.json is not valid JSON: {e}") from e

    if not isinstance(obj, dict):
        raise ValidationError("ip_state.json root must be an object")

    # Detect top-level migration
    if "devices" not in obj:
        devices = _migrate_old_top_level(obj)
        state = State(version=1, devices=devices, path=str(p.resolve()))
        return state

    version = int(obj.get("version", 1))
    raw_devices = obj.get("devices", {})

    if isinstance(raw_devices, dict):
        devices = {str(k): v for k, v in raw_devices.items() if isinstance(v, dict)}
    elif isinstance(raw_devices, list):
        # list → dict migration
        devices = {}
        for idx, item in enumerate(raw_devices):
            if isinstance(item, dict):
                dev_id = str(item.get("id", f"dev_{idx}"))
                devices[dev_id] = item
    else:
        raise ValidationError("ip_state.json: 'devices' must be an object or list")

    return State(version=version, devices=devices, path=str(p.resolve()))


def save_state_atomic_with_bak(
    state: State,
    path: str = DEFAULT_STATE_PATH,
    bak_path: str = DEFAULT_BAK_PATH,
) -> None:
    """
    Save State atomically and write a .bak first.

    - Bestehende Datei wird nach `bak_path` kopiert.
    - Die neue Datei wird per atomic_write geschrieben.
    """
    src = Path(path)
    if src.exists():
        shutil.copy2(src, bak_path)

    payload = {
        "version": state.version,
        "devices": state.devices,
    }
    data = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
    atomic_write(path, data)


# ---------------------------------------------------------------------------
# Helper API
# ---------------------------------------------------------------------------

def get_device(state: State, device_id: str) -> Optional[Dict[str, Any]]:
    """Return a single device dict by its id (or None if missing)."""
    return state.devices.get(str(device_id))


def upsert_device(state: State, device_id: str, data: Dict[str, Any]) -> None:
    """
    Insert or replace a device entry fully.
    """
    state.devices[str(device_id)] = dict(data)


def update_device(state: State, device_id: str, patch: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge a partial patch into an existing device entry, or create a new one.

    Ensures the 'id' field in the device dict matches the key.
    """
    key = str(device_id)
    current = state.devices.get(key, {})
    merged = {**current, **patch}
    merged.setdefault("id", key)
    state.devices[key] = merged
    return merged


def delete_device(state: State, device_id: str) -> bool:
    """Delete a device from the state. Returns True if it existed."""
    return state.devices.pop(str(device_id), None) is not None


def iter_devices(state: State) -> Iterable[Tuple[str, Dict[str, Any]]]:
    """Iterate over (id, device_dict) pairs."""
    return state.devices.items()
