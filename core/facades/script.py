from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from ..rpc import RpcClient


@dataclass
class ScriptSlot:
    """Lightweight view on a script slot as returned by Script.List/GetConfig."""
    id: int
    name: str
    enable: bool
    running: bool
    # Optional additional info
    error: Optional[str] = None
    raw: Dict[str, Any] = None


def _normalize_script_entry(entry: Dict[str, Any]) -> ScriptSlot:
    """Convert raw Script.List entry to ScriptSlot."""
    sid = int(entry.get("id", -1))
    cfg = entry.get("config", {}) or {}
    status = entry.get("status", {}) or {}

    return ScriptSlot(
        id=sid,
        name=str(cfg.get("name", f"script_{sid}")),
        enable=bool(cfg.get("enable", False)),
        running=bool(status.get("running", False)),
        error=status.get("error"),
        raw=entry,
    )


# ---------------------------------------------------------------------------
# Basic RPC wrappers
# ---------------------------------------------------------------------------

def list_scripts(client: RpcClient) -> List[ScriptSlot]:
    """
    List all script slots on the device.

    Uses Script.List RPC.
    """
    res = client.call("Script.List", {})  # 
    entries = res.get("scripts", res.get("result", res))  # be tolerant to shape
    if not isinstance(entries, list):
        return []
    return [_normalize_script_entry(e) for e in entries if isinstance(e, dict)]


def get_script_config(client: RpcClient, script_id: int) -> Dict[str, Any]:
    return client.call("Script.GetConfig", {"id": int(script_id)})  # 


def set_script_config(client: RpcClient, script_id: int, config: Dict[str, Any]) -> Dict[str, Any]:
    return client.call("Script.SetConfig", {"id": int(script_id), "config": config})  # 


def get_script_code(client: RpcClient, script_id: int) -> str:
    res = client.call("Script.GetCode", {"id": int(script_id)})  # 
    # Docs nennen typischerweise 'code' oder 'source'; wir sind tolerant
    return res.get("code") or res.get("source", "")


def put_script_code(client: RpcClient, script_id: int, source: str) -> Dict[str, Any]:
    """
    Upload / overwrite script code in a given slot.

    Uses Script.PutCode RPC.
    """
    return client.call("Script.PutCode", {"id": int(script_id), "code": source})  # 


def start_script(client: RpcClient, script_id: int) -> Dict[str, Any]:
    return client.call("Script.Start", {"id": int(script_id)})  # 


def stop_script(client: RpcClient, script_id: int) -> Dict[str, Any]:
    return client.call("Script.Stop", {"id": int(script_id)})  # 


def create_script_slot(client: RpcClient, script_id: int, name: str, enable: bool = True) -> Dict[str, Any]:
    """
    Create a script slot with a given id and name.

    Per offizieller API-Doku nimmt Script.Create typischerweise Parameter:
      { "id": <int>, "name": <string>, "enable": <bool> } 
    Falls sich das auf deinem Device anders verhält, kannst du die Payload hier anpassen.
    """
    payload = {
        "id": int(script_id),
        "name": str(name),
        "enable": bool(enable),
    }
    return client.call("Script.Create", payload)  # 


def delete_script_slot(client: RpcClient, script_id: int) -> Dict[str, Any]:
    return client.call("Script.Delete", {"id": int(script_id)})  # 


# ---------------------------------------------------------------------------
# Higher-level helpers for your Stage 4 concept
# ---------------------------------------------------------------------------

def find_script_by_name(client: RpcClient, name: str) -> Optional[ScriptSlot]:
    """
    Search Script.List() for a given config.name.
    """
    name = str(name)
    for slot in list_scripts(client):
        if slot.name == name:
            return slot
    return None


def find_free_slot_id(client: RpcClient, min_id: int = 1, max_id: int = 32) -> Optional[int]:
    """
    Find a free numeric slot id in [min_id, max_id].

    If the device supports fewer script slots, you'll just not reach max_id.
    """
    used = {s.id for s in list_scripts(client)}
    for i in range(min_id, max_id + 1):
        if i not in used:
            return i
    return None


def ensure_script_slot_for_name(
    client: RpcClient,
    name: str,
    *,
    run_on_startup: bool = True,
    preferred_id: Optional[int] = None,
) -> ScriptSlot:
    """
    Ensure there is a script slot with the given config.name.

    - If a script with that name exists: return its slot info.
    - Else: choose a free id (or preferred_id if provided), create a slot,
      then set config to the given name + enable flag.
    """
    existing = find_script_by_name(client, name)
    if existing:
        # Make sure the enable flag matches our desired default (if needed)
        cfg = get_script_config(client, existing.id)
        cfg_cfg = cfg.get("config", cfg)
        desired_enable = bool(run_on_startup)
        if cfg_cfg.get("enable") != desired_enable or cfg_cfg.get("name") != name:
            cfg_cfg["enable"] = desired_enable
            cfg_cfg["name"] = name
            set_script_config(client, existing.id, cfg_cfg)
        # Re-read status
        slots = list_scripts(client)
        for s in slots:
            if s.id == existing.id:
                return s
        return existing

    # Need to create a new slot
    if preferred_id is not None:
        sid = int(preferred_id)
    else:
        sid = find_free_slot_id(client) or 1

    create_script_slot(client, sid, name=name, enable=run_on_startup)
    # After creating, we normalise through list_scripts
    for s in list_scripts(client):
        if s.id == sid:
            return s

    # Fallback — construct minimal slot if List does not yet reflect it
    return ScriptSlot(id=sid, name=name, enable=run_on_startup, running=False, raw={})


def upload_script_from_source(
    client: RpcClient,
    *,
    name: str,
    source: str,
    run_on_startup: bool = True,
    preferred_id: Optional[int] = None,
    auto_start: bool = True,
) -> ScriptSlot:
    """
    High-level helper:
      - ensure script slot exists (by name),
      - upload script source (overwrite if exists),
      - set config (name, enable),
      - optionally start script.

    This matches dein Flow:
      - mehrere Scripts pro Shelly
      - nummerische Slot-IDs
      - "wenn Scriptname existiert → überschreiben"
      - "run on startup" konfigurieren
    """
    slot = ensure_script_slot_for_name(
        client,
        name=name,
        run_on_startup=run_on_startup,
        preferred_id=preferred_id,
    )

    put_script_code(client, slot.id, source)

    cfg = {
        "name": name,
        "enable": bool(run_on_startup),
    }
    set_script_config(client, slot.id, cfg)

    if auto_start:
        try:
            start_script(client, slot.id)
        except Exception:
            # Nicht kritisch, kann z.B. fehlschlagen wenn Device gerade rebootet.
            pass

    # Refresh view
    for s in list_scripts(client):
        if s.id == slot.id:
            return s
    return slot
