# core/stage3_core.py
from __future__ import annotations

import datetime as dt
import json
import os
import subprocess
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from concurrent.futures import ThreadPoolExecutor, as_completed

import requests


# ---------- Configuration data classes ----------


@dataclass
class Stage3OtaConfig:
    """Configuration for OTA behaviour."""

    enabled: bool = True
    # "check_only" → only check for updates
    # "check_and_update" → check, and if available, trigger Shelly.Update
    mode: str = "check_and_update"
    # Timeout (seconds) for individual OTA RPC calls (CheckForUpdate / Update)
    timeout_s: float = 20.0


@dataclass
class Stage3FriendlyConfig:
    """Configuration for friendly-name synchronisation."""

    enabled: bool = True
    # Field name in ip_state.json entry that contains the friendly name
    field_name: str = "friendly_name"
    # If True, write JSON → device only if device has no name configured
    backfill: bool = True


@dataclass
class Stage3LoggingConfig:
    """Configuration for Stage 3 specific logging."""

    # Path to a session log file (relative to project root or absolute).
    # If None or empty, logging is disabled at core level.
    base_path: Optional[str] = None


@dataclass
class Stage3Config:
    """Top-level configuration for Stage 3."""

    enabled: bool = True
    # Path to ip_state.json (relative to project root or absolute), mainly for
    # informational purposes at core level.
    ip_state_file: str = "data/ip_state.json"
    ota: Stage3OtaConfig = field(default_factory=Stage3OtaConfig)
    friendly: Stage3FriendlyConfig = field(default_factory=Stage3FriendlyConfig)
    logging: Stage3LoggingConfig = field(default_factory=Stage3LoggingConfig)


# ---------- Device model & result types ----------


@dataclass
class DeviceEntry:
    """View of a device entry inside ip_state.json."""

    mac: str
    ip: Optional[str]
    model: Optional[str]
    fw: Optional[str]
    hostname: Optional[str]
    friendly_name: Optional[str]
    # Direct reference to the raw JSON sub-dict (state["devices"][mac])
    raw: Dict[str, Any]


@dataclass
class DeviceResult:
    """Result of processing a single device in Stage 3."""

    mac: str
    ip: Optional[str]
    ok: bool
    ota_status: str
    friendly_status: str
    message: str = ""


@dataclass
class Stage3Summary:
    """Aggregate result of a Stage 3 run on the whole state."""

    ok: bool
    devices: Dict[str, DeviceResult]
    meta: Dict[str, Any]


# ---------- Ping helper ----------


def ping_ip(ip: str, timeout_s: float = 0.25) -> Optional[bool]:
    """
    Ping an IP address once.

    Returns:
        True  -> host reachable (ping succeeded)
        False -> host unreachable (ping failed)
        None  -> ping could not be executed (unexpected error)

    This uses the system ping command and is therefore platform-dependent,
    but keeps dependencies minimal.
    """
    if not ip:
        return None

    if os.name == "nt":
        # Windows: -n 1 (one echo) -w timeout_ms
        cmd = ["ping", "-n", "1", "-w", str(int(timeout_s * 1000)), ip]
    else:
        # POSIX: -c 1 (one echo), timeout is provided via subprocess timeout
        cmd = ["ping", "-c", "1", ip]

    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=timeout_s + 0.5,
            check=False,
        )
        return result.returncode == 0
    except Exception:
        # Any error (missing ping, timeout, etc.) → unknown
        return None


# ---------- HTTP / RPC helpers ----------


def _build_base_url(ip: str) -> str:
    """Build the HTTP base URL for a Shelly device."""
    return f"http://{ip}"


def http_get_json(
    session: requests.Session,
    url: str,
    timeout_s: float,
    params: Optional[Dict[str, Any]] = None,
) -> Tuple[bool, Optional[Dict[str, Any]], str]:
    """
    Perform a GET request and parse JSON body.

    Returns:
        (ok, json_obj, message)
    """
    try:
        resp = session.get(url, params=params, timeout=timeout_s)
    except Exception as exc:
        return False, None, f"HTTP GET failed: {exc}"

    if resp.status_code != 200:
        return False, None, f"HTTP {resp.status_code}"

    try:
        data = resp.json()
    except Exception as exc:
        return False, None, f"Invalid JSON: {exc}"

    return True, data, ""


def check_ota_status(
    ip: str,
    session: requests.Session,
    timeout_s: float,
) -> Tuple[str, str]:
    """
    Check for an available firmware update using Shelly.CheckForUpdate.

    Returns:
        (ota_status, message)

        ota_status in:
          - "up_to_date"
          - "update_available"
          - "check_failed"

        message is a short human-readable string, e.g.:
          - "version=1.3.3 stage=stable"
          - "version=unknown stage=beta"
    """
    url = f"{_build_base_url(ip)}/rpc/Shelly.CheckForUpdate"
    ok, data, msg = http_get_json(session, url, timeout_s=timeout_s)

    if not ok or data is None:
        return "check_failed", msg or "Shelly.CheckForUpdate failed"

    # Leere Antwort => kein Update
    if not data:
        return "up_to_date", ""

    # --- Gen3-Style: verschachtelte Channels (stable/beta/etc.) ---
    # Beispiel:
    #   {"stable":{"version":"1.3.3","build_id":"20240625-122608/1.3.3-gbdfd9b3"}}
    if "stable" in data or "beta" in data:
        # bevorzugt stable, sonst beta
        channel = "stable"
        ch_data = data.get("stable") or {}
        if not ch_data and "beta" in data:
            channel = "beta"
            ch_data = data.get("beta") or {}

        version = None
        if isinstance(ch_data, dict):
            version = ch_data.get("version") or ch_data.get("build_id")

        if version:
            return "update_available", f"version={version} stage={channel}"

        # Falls aus irgendeinem Grund kein version-Feld vorhanden ist
        return "update_available", f"version=unknown stage={channel}"

    # --- Klassischer Style (Gen1/Gen2) mit has_update/version/... ---
    has_update = data.get("has_update")
    if has_update is False:
        return "up_to_date", ""
    if has_update is True:
        version = data.get("version") or data.get("new_version") or "unknown"
        channel = data.get("channel") or data.get("stage") or "stable"
        return "update_available", f"version={version} stage={channel}"

    # Fallback: wenn irgendeine Form von version vorhanden ist, als Update werten
    if "version" in data or "new_version" in data:
        version = data.get("version") or data.get("new_version") or "unknown"
        channel = data.get("channel") or data.get("stage") or "stable"
        return "update_available", f"version={version} stage={channel}"

    # Default: nichts erkannt => kein Update
    return "up_to_date", ""


def trigger_ota_update(
    ip: str,
    session: requests.Session,
    timeout_s: float,
    stage: str = "stable",
) -> Tuple[bool, str]:
    """
    Trigger a firmware update using Shelly.Update.

    Uses the official RPC endpoint (HTTP RPC style):
        GET http://<ip>/rpc/Shelly.Update?stage=stable

    The update itself is asynchronous; this helper only checks whether the
    RPC call was accepted successfully, not whether the update has completed.
    """
    url = f"{_build_base_url(ip)}/rpc/Shelly.Update"
    params = {"stage": stage}
    ok, data, msg = http_get_json(session, url, timeout_s=timeout_s, params=params)

    if not ok:
        return False, msg or "Shelly.Update failed"

    # In many firmwares the reply is either "null" or a small JSON status.
    # We treat any successful HTTP+JSON response as "accepted".
    return True, ""


def get_device_name(
    ip: str,
    session: requests.Session,
    timeout_s: float,
) -> Tuple[Optional[str], str]:
    """
    Read the device name via Sys.GetConfig.

    Uses the official RPC endpoint:
        GET http://<ip>/rpc/Sys.GetConfig

    Returns:
        (device_name_or_None, message_on_error_or_empty)
    """
    url = f"{_build_base_url(ip)}/rpc/Sys.GetConfig"
    ok, data, msg = http_get_json(session, url, timeout_s=timeout_s)

    if not ok or data is None:
        return None, msg or "Sys.GetConfig failed"

    device_cfg = data.get("device") or {}
    name = device_cfg.get("name")
    if isinstance(name, str):
        return name, ""
    return None, ""


def set_device_name(
    ip: str,
    new_name: str,
    session: requests.Session,
    timeout_s: float,
) -> Tuple[bool, str]:
    """
    Set the device name via Sys.SetConfig.

    Uses the official RPC endpoint with query parameter:
        GET http://<ip>/rpc/Sys.SetConfig?config={"device":{"name":"<name>"}}

    The JSON is passed as URL-encoded string in the "config" query parameter,
    as described in the Shelly RPC HTTP documentation.
    """
    url = f"{_build_base_url(ip)}/rpc/Sys.SetConfig"
    payload = {"device": {"name": new_name}}

    # IMPORTANT:
    # Use compact JSON without spaces to match the working curl example:
    #   {"device":{"name":"Test789"}}
    # Some firmwares appear to choke on the default json.dumps with spaces.
    config_str = json.dumps(payload, separators=(",", ":"))
    params = {"config": config_str}

    ok, _, msg = http_get_json(session, url, timeout_s=timeout_s, params=params)
    if not ok:
        return False, msg or "Sys.SetConfig failed"
    return True, ""


def check_http_reachability(
    ip: str,
    session: requests.Session,
    timeout_s: float = 1.0,
) -> bool:
    """
    Lightweight reachability check via HTTP.

    Uses a cheap RPC call (Shelly.GetStatus or Sys.GetStatus).
    If this fails, the device is assumed to be offline.
    """
    base = _build_base_url(ip)
    # Prefer Shelly.GetStatus; fall back to Sys.GetStatus.
    for path in ("/rpc/Shelly.GetStatus", "/rpc/Sys.GetStatus"):
        url = f"{base}{path}"
        ok, _, _ = http_get_json(session, url, timeout_s=timeout_s)
        if ok:
            return True
    return False


# ---------- Core per-device logic ----------


def build_device_entry(
    mac: str,
    raw_entry: Dict[str, Any],
    friendly_field: str,
) -> DeviceEntry:
    """Construct a DeviceEntry from a raw ip_state.json device dict."""
    ip = raw_entry.get("ip")
    model = raw_entry.get("model")
    fw = raw_entry.get("fw")
    hostname = raw_entry.get("hostname")
    friendly = raw_entry.get(friendly_field) or None

    return DeviceEntry(
        mac=mac,
        ip=ip,
        model=model,
        fw=fw,
        hostname=hostname,
        friendly_name=friendly,
        raw=raw_entry,
    )


def process_device(
    entry: DeviceEntry,
    config: Stage3Config,
    session: requests.Session,
    dry_run: bool = False,
) -> DeviceResult:
    """
    Process a single device:

    - Ping + HTTP reachability check
    - OTA check (and optional update, depending on mode)
    - Friendly name backfill (JSON → device), if configured
    - Update stage3 block inside the raw state entry
    """
    now = dt.datetime.now().isoformat()
    stage3_block = entry.raw.setdefault("stage3", {})

    # Default statuses before we know anything.
    ota_status = stage3_block.get("ota_status", "unknown")
    friendly_status = stage3_block.get("friendly_status", "unknown")
    message_parts: List[str] = []

    if not entry.ip:
        ota_status = "offline"
        friendly_status = "unknown"
        stage3_block["ota_status"] = ota_status
        stage3_block["friendly_status"] = friendly_status
        stage3_block["last_run"] = now

        return DeviceResult(
            mac=entry.mac,
            ip=None,
            ok=False,
            ota_status=ota_status,
            friendly_status=friendly_status,
            message="no IP in ip_state.json",
        )

    ip = entry.ip

    # 1) Reachability: ping first, HTTP as fallback.
    ping_ok = ping_ip(ip, timeout_s=0.25)
    http_ok = False

    if ping_ok is False:
        # Only try HTTP if ping clearly failed (not None).
        http_ok = check_http_reachability(ip, session, timeout_s=1.0)
    elif ping_ok is True:
        http_ok = True
    else:
        # ping unknown → try HTTP
        http_ok = check_http_reachability(ip, session, timeout_s=1.0)

    if not http_ok:
        ota_status = "offline"
        # Leave friendly_status as-is or mark as unknown.
        if friendly_status == "unknown":
            friendly_status = "unknown"
        stage3_block["ota_status"] = ota_status
        stage3_block["friendly_status"] = friendly_status
        stage3_block["last_run"] = now

        return DeviceResult(
            mac=entry.mac,
            ip=ip,
            ok=False,
            ota_status=ota_status,
            friendly_status=friendly_status,
            message="device offline",
        )

    # 2) OTA handling
    if config.ota.enabled:
        # Immer zuerst OTA-Status prüfen
        ota_status, ota_msg = check_ota_status(
            ip, session, timeout_s=config.ota.timeout_s
        )
        if ota_msg:
            message_parts.append(f"OTA: {ota_msg}")

        # Optional: bei verfügbarem Update und check_and_update → Update anstoßen
        # Nur updaten wenn stable verfügbar (nicht beta)
        if (
            config.ota.mode == "check_and_update"
            and ota_status == "update_available"
            and "stage=stable" in ota_msg
            and not dry_run
        ):
            ok_update, upd_msg = trigger_ota_update(
                ip, session, timeout_s=config.ota.timeout_s, stage="stable"
            )
            if ok_update:
                info = "Update triggered (stage=stable)"
                if upd_msg:
                    info += f" ({upd_msg})"
                message_parts.append(info)
            else:
                ota_status = "check_failed"
                if upd_msg:
                    message_parts.append(f"Update: {upd_msg}")
        elif (
            config.ota.mode == "check_and_update"
            and ota_status == "update_available"
            and "stage=beta" in ota_msg
        ):
            # Beta update verfügbar aber nicht installiert
            ota_status = "up_to_date"
            message_parts.append("Update: skipped (beta only)")
    else:
        ota_status = "skipped"

    # 3) Friendly-name sync
    if config.friendly.enabled:
        friendly_status, friendly_msg = _process_friendly(
            entry=entry,
            config=config.friendly,
            session=session,
            dry_run=dry_run,
        )
        if friendly_msg:
            message_parts.append(f"friendly: {friendly_msg}")
    else:
        friendly_status = "skipped"

    # 4) Store final stage3 block
    # Compute ok first, then store
    ok = (
        ota_status not in ("offline", "check_failed")
        and friendly_status not in ("error",)
    )
    
    stage3_block["ts"] = now
    stage3_block["status"] = "ok" if ok else "error"
    stage3_block["ota_status"] = ota_status
    stage3_block["friendly_status"] = friendly_status
    
    # Update stage_completed: set to 3 if currently at 2
    current_stage = entry.raw.get("stage_completed", 0)
    if isinstance(current_stage, int) and current_stage == 2:
        entry.raw["stage_completed"] = 3
    elif not isinstance(current_stage, int):
        # Handle legacy entries without stage_completed
        entry.raw["stage_completed"] = 3

    return DeviceResult(
        mac=entry.mac,
        ip=ip,
        ok=ok,
        ota_status=ota_status,
        friendly_status=friendly_status,
        message="; ".join(message_parts),
    )


def _process_friendly(
    entry: DeviceEntry,
    config: Stage3FriendlyConfig,
    session: requests.Session,
    dry_run: bool,
) -> Tuple[str, str]:
    """
    Handle friendly-name synchronisation for a single device.

    Behaviour:
        - If no friendly_name in JSON → "no_value"
        - If backfill=True:
            - Read device name via Sys.GetConfig
            - If device name is empty → set device name from JSON
            - Else leave unchanged
        - If backfill=False:
            - Always try to set device name from JSON
    """
    if not entry.friendly_name:
        return "no_value", ""

    if dry_run:
        # For dry runs we do not touch the device, but we consider the
        # potential friendly-name action as "ok".
        return "ok", "dry-run: would write device name"

    # Step 1: determine current device name
    device_name, msg = get_device_name(
        entry.ip, session, timeout_s=3.0  # type: ignore[arg-type]
    )

    # If Sys.GetConfig fails, treat current device name as unknown
    # but do NOT fail hard. This allows us to still try Sys.SetConfig.
    if msg and device_name is None:
        device_name = None  # explicitly "unknown" and continue

    # If names already match, we are done.
    if device_name == entry.friendly_name:
        return "ok", "already in sync"

    if config.backfill:
        # Only write JSON → device if device name is empty or None.
        if device_name:
            # Device already has a name; leave it as is.
            return "ok", "device name already set"
    # If backfill=False, we always try to push JSON → device.

    ok, set_msg = set_device_name(
        entry.ip, entry.friendly_name, session, timeout_s=5.0  # type: ignore[arg-type]
    )
    if not ok:
        return "error", set_msg or "Sys.SetConfig failed"

    return "ok", "device name updated"


def _process_device_with_new_session(
    entry: DeviceEntry,
    config: Stage3Config,
    dry_run: bool,
) -> DeviceResult:
    """
    Helper to process a device with its own dedicated HTTP session.

    This is used in the concurrent path so that each thread operates on a
    separate requests.Session instance.
    """
    session = requests.Session()
    try:
        return process_device(entry=entry, config=config, session=session, dry_run=dry_run)
    finally:
        session.close()


# ---------- Top-level API ----------


def run_stage3_on_state_dict(
    state: Dict[str, Any],
    config: Stage3Config,
    session: Optional[requests.Session] = None,
    now: Optional[dt.datetime] = None,
    only_ips: Optional[List[str]] = None,
    dry_run: bool = False,
    concurrency: int = 8,
) -> Stage3Summary:
    """
    Run Stage 3 over an ip_state.json-like dictionary.

    The expected structure is either:
        { <mac>: { ... } }

    or the newer nested form:
        {
          "version": 1,
          "devices": {
            <mac>: { ... }
          }
        }

    The function updates the provided 'state' in-place and returns a
    Stage3Summary object with per-device results.

    Devices can be processed concurrently by setting 'concurrency' > 1.
    """
    # Determine device mapping based on the structure
    if "devices" in state and isinstance(state["devices"], dict):
        devices_dict = state["devices"]
    else:
        devices_dict = state

    ip_filter: Optional[set[str]] = set(only_ips) if only_ips else None

    # Build list of tasks (DeviceEntry objects)
    tasks: List[DeviceEntry] = []
    for mac in sorted(devices_dict.keys()):
        raw_entry = devices_dict.get(mac)
        if not isinstance(raw_entry, dict):
            continue

        ip = raw_entry.get("ip")
        if ip_filter is not None and ip not in ip_filter:
            continue

        entry = build_device_entry(
            mac=mac,
            raw_entry=raw_entry,
            friendly_field=config.friendly.field_name,
        )
        tasks.append(entry)

    total = len(tasks)
    results: Dict[str, DeviceResult] = {}
    ok_count = 0

    # Sequential path (for debug / very small sets)
    if concurrency <= 1 or total <= 1:
        local_session = session or requests.Session()
        try:
            for entry in tasks:
                result = process_device(
                    entry=entry,
                    config=config,
                    session=local_session,
                    dry_run=dry_run,
                )
                results[entry.mac] = result
                if result.ok:
                    ok_count += 1
        finally:
            if session is None:
                local_session.close()
    else:
        # Concurrent path: each device gets its own Session instance
        max_workers = max(2, int(concurrency))
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_mac = {
                executor.submit(
                    _process_device_with_new_session,
                    entry,
                    config,
                    dry_run,
                ): entry.mac
                for entry in tasks
            }

            for future in as_completed(future_to_mac):
                mac = future_to_mac[future]
                try:
                    result = future.result()
                except Exception as exc:
                    result = DeviceResult(
                        mac=mac,
                        ip=None,
                        ok=False,
                        ota_status="error",
                        friendly_status="error",
                        message=f"exception in worker: {exc}",
                    )

                results[mac] = result
                if result.ok:
                    ok_count += 1

    summary_ok = total == 0 or ok_count == total
    meta = {
        "total_devices": total,
        "ok_devices": ok_count,
        "failed_devices": total - ok_count,
        "timestamp": (now or dt.datetime.now()).isoformat(),
    }

    return Stage3Summary(ok=summary_ok, devices=results, meta=meta)