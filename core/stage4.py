#!/usr/bin/env python3
"""
Stage 4 high-level API: manage scripts on a single Shelly device.

This module connects your local script pool (files on disk) with the Script.*
RPC methods exposed in core.facades.script.

Key features:
    - Multiple scripts per device
    - Name-based overwrite: if a script with the same name exists, reuse its id
    - Automatic creation of missing scripts via Script.Create
    - Upload/overwrite code via Script.PutCode
    - Optionally enable scripts and start them after upload
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Iterable

from core.rpc_client import RpcClient
from core.facades import script as script_api
from core.errors import RpcError


@dataclass
class ScriptSpec:
    """
    Desired script configuration on a device.

    - 'name' is the script name that will appear on the Shelly.
    - 'file' is the local source file path (absolute or relative to project root).
    - 'enable_on_boot' indicates whether the script should be enabled.
    - 'start_after_upload' indicates whether the script should be explicitly
      started right after upload (in addition to being enabled).
    - 'extra_config' lets you pass firmware-specific config fields, which are
      merged into Script.SetConfig's 'config' object.
    """
    name: str
    file: Path
    enable_on_boot: bool = True
    start_after_upload: bool = True
    extra_config: Optional[Dict[str, object]] = None


@dataclass
class SyncResult:
    """
    Result of syncing a single script to a device.
    """
    name: str
    script_id: int
    created: bool
    updated_code: bool
    updated_config: bool
    started: bool


def _read_script_file(path: Path) -> str:
    """Read script source code from a file, raising a helpful error on failure."""
    if not path.is_file():
        raise FileNotFoundError(f"Script file does not exist: {path}")
    return path.read_text(encoding="utf-8")


def _ensure_script_exists(
    client: RpcClient,
    name: str,
    existing: Dict[str, script_api.ScriptInfo],
) -> tuple[int, bool]:
    """
    Ensure there is a script with the given name on the device.

    Returns:
        (script_id, created_flag)

        created_flag == True  → script was created via Script.Create
        created_flag == False → existing script was reused
    """
    info = existing.get(name)
    if info is not None:
        return info.id, False

    # No existing script with that name → create a new one
    sid = script_api.create_script(client, name=name, enable=True)
    return sid, True


def sync_device_scripts(
    client: RpcClient,
    specs: Iterable[ScriptSpec],
) -> List[SyncResult]:
    """
    Sync a set of local scripts to a single Shelly device.

    For each ScriptSpec:
        - find existing script with matching name (via Script.List)
        - if none exists: Script.Create(name=...)
        - Script.PutCode(id=..., code=<file contents>)
        - Script.SetConfig(id=..., name=..., enable=<enable_on_boot>, extra_config=...)
        - optionally Script.Start(id=...) if start_after_upload is true

    Returns:
        List of SyncResult entries (one per ScriptSpec).
    """
    # Fetch current scripts once
    current_scripts = script_api.list_scripts(client)
    by_name: Dict[str, script_api.ScriptInfo] = {s.name: s for s in current_scripts}

    results: List[SyncResult] = []

    for spec in specs:
        code = _read_script_file(spec.file)

        # Ensure script exists (by name)
        script_id, created = _ensure_script_exists(client, spec.name, by_name)

        # Upload / overwrite code
        script_api.put_code(client, script_id, code)
        updated_code = True

        # Update config (name + enable flag + extra_config)
        extra_cfg = dict(spec.extra_config or {})
        # If your firmware distinguishes between "enable" and "run_on_startup",
        # you can add a dedicated key here, for example:
        #
        #   extra_cfg.setdefault("run_on_startup", spec.enable_on_boot)
        #
        # For now, we use "enable" only and rely on firmware defaults.
        script_api.set_config(
            client,
            script_id=script_id,
            name=spec.name,
            enable=spec.enable_on_boot,
            extra_config=extra_cfg or None,
        )
        updated_config = True

        # Optionally start the script
        started = False
        if spec.start_after_upload and spec.enable_on_boot:
            script_api.start(client, script_id)
            started = True

        results.append(
            SyncResult(
                name=spec.name,
                script_id=script_id,
                created=created,
                updated_code=updated_code,
                updated_config=updated_config,
                started=started,
            )
        )

    return results
