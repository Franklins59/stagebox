#!/usr/bin/env python3
"""
Shelly Provisioning – Stage 3 (OTA & Friendly Names, Metadata)

Thin CLI wrapper around the Stage 3 core API:

    core/provision/stage3_core.py

Usage:
    python shelly_stage3.py --building <building_name>
    python shelly_stage3.py -b <building_name> --ip 192.168.1.35
    
    # Or with environment variable:
    export STAGEBOX_BUILDING=my_building
    python shelly_stage3.py
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
import yaml

from core.building import (
    require_building,
    get_building_paths,
    add_building_argument,
    BuildingError,
)
from core.provision.stage3_core import (
    Stage3Config,
    Stage3FriendlyConfig,
    Stage3LoggingConfig,
    Stage3OtaConfig,
    run_stage3_on_state_dict,
)

# ---------- ANSI colors ----------

COLOR_RESET = "\033[0m"
COLOR_RED = "\033[31m"
COLOR_GREEN = "\033[32m"
COLOR_YELLOW = "\033[33m"

# ---------- Path helpers ----------


def detect_default_paths(building_name: str) -> Dict[str, Path]:
    """
    Get paths for a specific building.
    """
    paths = get_building_paths(building_name)

    return {
        "project_root": paths['stagebox_root'],
        "config": paths['config'],
        "secrets": paths['secrets'],
        "ip_state": paths['ip_state'],
        "model_map": paths['model_map'],
    }


def resolve_path(maybe_path: str | Path, project_root: Path) -> Path:
    """
    Resolve a path from config relative to project_root if it is not absolute.
    """
    p = Path(str(maybe_path))
    if p.is_absolute():
        return p
    return project_root / p


# ---------- Logging helpers ----------

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def strip_ansi(text: str) -> str:
    """Remove ANSI color escape sequences from a string."""
    return _ANSI_RE.sub("", text)


def get_session_log_path(
    stage3_cfg: Dict[str, Any],
    defaults: Dict[str, Path],
) -> Optional[Path]:
    """
    Resolve the session log path from stage3.logging.base_path (if present),
    relative to the project root. Returns None if logging is disabled.
    """
    logging_cfg = (stage3_cfg.get("logging") or {}) if isinstance(stage3_cfg, dict) else {}
    base_path = logging_cfg.get("base_path")
    if not base_path:
        return None

    project_root = defaults["project_root"]
    return resolve_path(base_path, project_root)


def append_session_log_line(
    stage3_cfg: Dict[str, Any],
    defaults: Dict[str, Path],
    text: str,
) -> None:
    """
    Append a single line to the Stage 3 session log, if configured.

    Failures are non-fatal and only reported as warnings on stderr.
    """
    log_path = get_session_log_path(stage3_cfg, defaults)
    if log_path is None:
        return

    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("a", encoding="utf-8") as f:
            f.write(text + "\n")
    except Exception as exc:
        print(f"WARNING: cannot append to session log {log_path}: {exc}", file=sys.stderr)


# ---------- Safe writing of ip_state.json ----------


def save_state_safe(path: Path, state: Dict[str, Any]) -> None:
    """
    Safely save ip_state.json:

    - If file exists, create a backup "<path>.bak"
    - Write to "<path>.tmp"
    - Atomically replace the original file with the tmp file
    """
    path_str = str(path)
    backup_path = path_str + ".bak"
    tmp_path = path_str + ".tmp"

    # Backup existing file (best effort)
    if Path(path_str).exists():
        try:
            import shutil

            shutil.copy2(path_str, backup_path)
#            print(f"[state_backup: ok file={path_str} backup={backup_path}]")
        except Exception as exc:
            print(f"[state_backup: warn file={path_str} err={exc}]", file=sys.stderr)

    # Write new state to tmp file and atomically replace original
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
        Path(tmp_path).replace(path_str)
#        print(f"[state_save: ok file={path_str} entries={len(_get_devices_dict(state))}]")
    except Exception as exc:
        print(f"[error: cannot write state file {path_str}: {exc}]", file=sys.stderr)
        # Best-effort cleanup
        try:
            tmp = Path(tmp_path)
            if Path(tmp_path).exists():
                Path(tmp_path).unlink()
        except Exception:
            pass
        sys.exit(1)


def _get_devices_dict(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Helper to get the devices mapping from ip_state.json-like dictionaries.
    """
    if "devices" in state and isinstance(state["devices"], dict):
        return state["devices"]
    return state


# ---------- Config loading ----------


def load_yaml(path: Path) -> Dict[str, Any]:
    """Load a YAML file and return a dict; exit on error."""
    try:
        with path.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError:
        print(f"ERROR: config file not found: {path}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        print(f"ERROR: cannot parse config file {path}: {exc}", file=sys.stderr)
        sys.exit(1)


def get_stage3_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Extract the 'stage3' section from the loaded config dict."""
    stage3 = config.get("stage3")
    return stage3 or {}


def build_stage3_config(stage3_cfg: Dict[str, Any]) -> Stage3Config:
    """Construct a Stage3Config dataclass from the YAML stage3 section."""
    ota_cfg = stage3_cfg.get("ota", {}) or {}
    friendly_cfg = stage3_cfg.get("friendly", {}) or {}
    logging_cfg = stage3_cfg.get("logging", {}) or {}

    return Stage3Config(
        enabled=bool(stage3_cfg.get("enabled", True)),
        ip_state_file=str(stage3_cfg.get("ip_state_file", "data/ip_state.json")),
        ota=Stage3OtaConfig(
            enabled=bool(ota_cfg.get("enabled", True)),
            mode=str(ota_cfg.get("mode", "check_and_update")),
            timeout_s=float(ota_cfg.get("timeout", 20)),
        ),
        friendly=Stage3FriendlyConfig(
            enabled=bool(friendly_cfg.get("enabled", True)),
            field_name=str(friendly_cfg.get("field_name", "friendly_name")),
            backfill=bool(friendly_cfg.get("backfill", True)),
        ),
        logging=Stage3LoggingConfig(
            base_path=logging_cfg.get("base_path"),
        ),
    )


# ---------- Argument parsing ----------


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Stage 3 – Shelly OTA & friendly-name sync.",
    )
    
    # Add building argument
    add_building_argument(parser)
    
    parser.add_argument(
        "-c",
        "--config",
        type=Path,
        default=None,
        help="Path to YAML config (default: <building>/stagebox/data/config.yaml)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not modify devices or ip_state.json (read-only RPCs only).",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Only print errors; suppress per-device summary lines.",
    )
    parser.add_argument(
        "--ip",
        nargs="+",
        metavar="IP",
        help="Only run Stage 3 for devices with these IP addresses.",
    )
    parser.add_argument(
        "--online",
        action="store_true",
        help="Show only online devices (skip devices with OTA=offline).",
    )

    return parser


# ---------- Output helpers ----------


def _classify_ota(ota_status: str) -> tuple[str, str]:
    """
    Map internal ota_status to a compact display label and color category.

    Returns:
        (label, color) where color in {"green", "yellow", "red"}.
    """
    s = ota_status or "unknown"

    if s == "offline":
        return "offline", "red"
    if s in ("update_available", "update_triggered"):
        return "updateable", "yellow"
    if s in ("up_to_date", "skipped", "no_value"):
        return "up_to_date", "green"

    # error, check_failed, unknown, etc.
    return s, "red"


def format_device_line(
    entry: Dict[str, Any],
    ota_status: str,
    friendly_status: str,
    friendly_field_name: str,
    message: str = "",
) -> str:
    """
    Format a single device summary line.

    Ziel: ca. < 80 sichtbare Zeichen, farbiger Punkt + farbiges OTA.
    Beispiel:
        ● S2PMG3 @ 192.168.1.35 - OTA=up_to_date | Friendly=ok (Kueche_Tuer)
        ● ... - OTA=up_to_date | Friendly=error (Name) | ERR=Sys.SetConfig failed: ...
    """
    model = entry.get("model", "unknown")
    ip = entry.get("ip", "unknown")
    fname = entry.get(friendly_field_name)

    ota_label, color = _classify_ota(ota_status)

    if color == "green":
        bullet = f"{COLOR_GREEN}●{COLOR_RESET}"
        ota_part = f"{COLOR_GREEN}OTA={ota_label}{COLOR_RESET}"
    elif color == "yellow":
        bullet = f"{COLOR_YELLOW}●{COLOR_RESET}"
        ota_part = f"{COLOR_YELLOW}OTA={ota_label}{COLOR_RESET}"
    else:
        bullet = f"{COLOR_RED}●{COLOR_RESET}"
        ota_part = f"{COLOR_RED}OTA={ota_label}{COLOR_RESET}"

    # Friendly part: status + optional name; name ggf. kürzen
    if fname:
        if len(fname) > 24:
            fname_disp = fname[:21] + "..."
        else:
            fname_disp = fname
        friendly_part = f"{friendly_status} ({fname_disp})"
    else:
        friendly_part = friendly_status

    # Basis-Zeile zuerst aufbauen
    if ota_label == "offline":
        # Offline: kurze Zeile
        line = f"{bullet} {model} @ {ip} - {ota_part}"
    else:
        line = f"{bullet} {model} @ {ip} - {ota_part} | Friendly={friendly_part}"

    # Bei Fehlern (Friendly=error oder OTA-Fehler) kurze Fehlermeldung anhängen
    if (friendly_status == "error" or ota_status in ("check_failed", "error")) and message:
        msg_plain = strip_ansi(message)
        if len(msg_plain) > 40:
            msg_plain = msg_plain[:37] + "..."
        line = f"{line} | ERR={msg_plain}"

    # Max. ca. 80 sichtbare Zeichen
    plain = strip_ansi(line)
    max_len = 120
    if len(plain) > max_len:
        over = len(plain) - max_len
        line = line[:-over]

    return line


# ---------- Main ----------


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    # Require building
    try:
        building = require_building(args.building)
    except BuildingError as e:
        print(f"{COLOR_RED}ERROR: {e}{COLOR_RESET}", file=sys.stderr)
        return 1

    defaults = detect_default_paths(building)
    
    # Config path: use argument or default to building's config
    config_path = args.config if args.config else defaults["config"]
    
    config = load_yaml(config_path)
    stage3_cfg = get_stage3_config(config)
    cfg = build_stage3_config(stage3_cfg)

    if not cfg.enabled:
        print("Stage 3 is disabled in config (stage3.enabled=false).")
        return 0

    project_root = defaults["project_root"]
    ip_state_path = resolve_path(cfg.ip_state_file, project_root)

    # Load ip_state.json
    try:
        with ip_state_path.open("r", encoding="utf-8") as f:
            state: Dict[str, Any] = json.load(f)
    except FileNotFoundError:
        print(f"ERROR: state file not found: {ip_state_path}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"ERROR: cannot read state file {ip_state_path}: {exc}", file=sys.stderr)
        return 1

    devices = _get_devices_dict(state)
    if not isinstance(devices, dict):
        print(
            f"ERROR: state file {ip_state_path} has unexpected structure (no 'devices' map).",
            file=sys.stderr,
        )
        return 1

    session = requests.Session()

    summary = run_stage3_on_state_dict(
        state=state,
        config=cfg,
        session=session,
        only_ips=args.ip,
        dry_run=bool(args.dry_run),
        concurrency=8,
    )

    # Per-device console output + session log
    if not args.quiet:
        for mac in sorted(devices.keys()):
            if mac not in summary.devices:
                # Filtered by IP or skipped → do not print
                continue

            entry = devices[mac]
            result = summary.devices[mac]

            # --online filter
            if args.online and result.ota_status == "offline":
                continue

            line = format_device_line(
                entry=entry,
                ota_status=result.ota_status,
                friendly_status=result.friendly_status,
                friendly_field_name=cfg.friendly.field_name,
                message=result.message,
            )

            print(line)
            append_session_log_line(stage3_cfg, defaults, strip_ansi(line))

    # Overall summary (einfach gehalten, OTA-Farben genügen oben)
    meta = summary.meta
    total = meta.get("total_devices", 0)
    ok_devices = meta.get("ok_devices", 0)
    failed = meta.get("failed_devices", 0)

    print(f"Stage 3 summary: total={total} ok={ok_devices} failed={failed}")

    # Persist modified state unless this is a dry-run
    if not args.dry_run:
        save_state_safe(ip_state_path, state)
    else:
        print("[dry-run: not writing ip_state.json]")

    return 0 if summary.ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
