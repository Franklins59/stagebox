#!/usr/bin/env python3
"""
Stage 1 – Provision Shelly Gen3 devices via AP:

- Connect to open Shelly AP (Shelly* SSID)
- Push WiFi credentials (wifi_profiles)
- Disable cloud / BLE / AP / MQTT according to options
- Reboot device and disconnect WLAN

Usage:
    python shelly_stage1.py --building <building_name>
    python shelly_stage1.py -b <building_name> --loop
    
    # Or with environment variable:
    export STAGEBOX_BUILDING=my_building
    python shelly_stage1.py

Config model:

- <building>/stagebox/data/config.yaml
    stage1:
      shelly_ip: "192.168.33.1"
      options: { ... }
      logging: { base_path: "...", inventory: "..." }

- <building>/stagebox/data/secrets.yaml
    wifi_profiles:
      - ssid: ...
        password: ...
        ...
"""

import os
import argparse
import sys
from pathlib import Path
from typing import Any, Dict, Tuple, Optional

import yaml

from core.building import (
    require_building,
    get_building_paths,
    add_building_argument,
    BuildingError,
)
from core.provision.stage1_ap_core import provision_once

# ─────────────────────────────────────────────
# Project root / path helpers
# ─────────────────────────────────────────────

# Will be set after building is determined
PROJECT_ROOT: Optional[Path] = None


def resolve_project_path(raw: str | Path | None) -> Path | None:
    """
    Resolve a path relative to the project root.

    - Expands environment variables ($HOME, etc.).
    - If the resulting path is absolute, it is returned as-is.
    - If it is relative, it is interpreted relative to PROJECT_ROOT.
    - If raw is falsy, returns None.
    """
    if not raw:
        return None
    if PROJECT_ROOT is None:
        raise RuntimeError("PROJECT_ROOT not set - call set_building() first")
    p = Path(os.path.expandvars(str(raw)))
    if p.is_absolute():
        return p
    return PROJECT_ROOT / p


def set_building(building_name: str) -> Dict[str, Path]:
    """Set the active building and return paths."""
    global PROJECT_ROOT
    paths = get_building_paths(building_name)
    PROJECT_ROOT = paths['stagebox_root']
    return paths


# ─────────────────────────────────────────────
# ANSI colors for one-line summary
# ─────────────────────────────────────────────

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"


def print_summary(summary: Dict[str, Any]) -> None:
    """Print a single colored summary line for one provisioning run.

    Colors:
      - green: ok=True
      - yellow: ok=False but reason=no_connectable_ap (no new APs)
      - red: other failures
    """
    ok = bool(summary.get("ok"))
    reason = summary.get("reason")
    mac = summary.get("mac", "?")
    model = summary.get("model", "?")
    fw = summary.get("fw", "?")

    if ok:
        color = GREEN
        status = "OK"
    else:
        if reason == "no_connectable_ap":
            color = YELLOW
            status = "WARN"
        else:
            color = RED
            status = "FAIL"

    parts = [f"[{status}] mac={mac}", f"model={model}", f"fw={fw}"]
    if reason and not ok:
        parts.append(f"reason={reason}")

    line = " ".join(parts)
    print(f"{color}{line}{RESET}")


def _expand_and_resolve_path(value: str | None) -> str | None:
    """
    Expand ~, $VARS and make path relative to PROJECT_ROOT if not absolute.
    Returns None if value is falsy.
    """
    if not value:
        return None
    expanded = os.path.expandvars(os.path.expanduser(value))
    p = Path(expanded)
    if not p.is_absolute():
        p = PROJECT_ROOT / p
    return str(p)


# ─────────────────────────────────────────────
# Config loading (config.yaml + secrets.yaml)
# ─────────────────────────────────────────────

def load_config(config_path_str: str) -> Tuple[Dict[str, Any], str | None]:
    """
    Load configuration for Stage 1.

    Reads:
      - data/config.yaml  -> stage1.shelly_ip, stage1.options, stage1.logging
      - data/secrets.yaml -> wifi_profiles (shared with other stages)

    Only the following keys are used:
      - wifi_profiles            (from secrets.yaml, top-level list)
      - stage1.shelly_ip         (fallback: "192.168.33.1")
      - stage1.options           (mapping)
      - stage1.logging.base_path (session log)
      - stage1.logging.inventory (csv inventory)
    """
    # Resolve config.yaml path
    config_path = resolve_project_path(config_path_str)
    if config_path is None:
        raise ValueError("No config path provided")

    with config_path.open("r", encoding="utf-8") as f:
        config_data = yaml.safe_load(f) or {}

    # ---- stage1 block from config.yaml ----
    stage1 = config_data.get("stage1", {}) or {}
    if not isinstance(stage1, dict):
        raise ValueError("YAML error: stage1 must be a mapping in config.yaml")

    # Shelly AP IP for Stage 1 (fallback: 192.168.33.1)
    shelly_ip = stage1.get("shelly_ip", "192.168.33.1")

    # Stage-1-specific options
    options = stage1.get("options", {}) or {}
    if not isinstance(options, dict):
        raise ValueError("YAML error: stage1.options must be a mapping")

    # loop_mode is controlled via YAML, can later be overridden by CLI
    loop_mode = bool(options.get("loop_mode", False))
    options["loop_mode"] = loop_mode

    # Stage-1-specific logging
    logging_cfg = stage1.get("logging", {}) or {}
    if not isinstance(logging_cfg, dict):
        raise ValueError("YAML error: stage1.logging must be a mapping")

    raw_base = logging_cfg.get("base_path")
    raw_inventory = logging_cfg.get("inventory")

    expanded_base = _expand_and_resolve_path(raw_base)
    expanded_inventory = _expand_and_resolve_path(raw_inventory)

    logfile_default: str | None = None
    if expanded_base:
        logging_cfg["base_path"] = expanded_base
        logfile_default = expanded_base
    if expanded_inventory:
        logging_cfg["inventory"] = expanded_inventory

    # ---- wifi_profiles from secrets.yaml ----
    # secrets.yaml is expected in the same directory as config.yaml
    secrets_path = config_path.parent / "secrets.yaml"
    wifi_profiles: list[dict] = []
    if secrets_path.exists():
        with secrets_path.open("r", encoding="utf-8") as f:
            secrets_data = yaml.safe_load(f) or {}
        wifi_profiles = secrets_data.get("wifi_profiles", []) or []
    else:
        # Fallback: if someone still has wifi_profiles in config.yaml
        wifi_profiles = config_data.get("wifi_profiles", []) or []

    if not isinstance(wifi_profiles, list):
        raise ValueError("YAML error: wifi_profiles must be a list")

    cfg: Dict[str, Any] = {
        "wifi_profiles": wifi_profiles,
        "shelly_ip": shelly_ip,
        "options": options,
        "log": logging_cfg,
        "enabled": bool(stage1.get("enabled", True)),
    }

    return cfg, logfile_default


# ─────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="shelly_stage1.py",
        description=(
            "Stage 1: provision Shelly Gen3 devices via AP "
            "(configure WiFi, disable cloud/BLE/AP/MQTT, reboot)."
        ),
    )
    
    # Add building argument
    add_building_argument(parser)
    
    parser.add_argument(
        "-f",
        "--config",
        dest="config",
        default=None,
        help="Path to YAML config file (default: <building>/stagebox/data/config.yaml)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show planned actions but do not connect WiFi or send HTTP requests.",
    )
    parser.add_argument(
        "--log",
        dest="logfile",
        default=None,
        help="Global log file path (overrides stage1.logging.base_path).",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        dest="verbose",
        action="store_true",
        help="Verbose console output (show all provisioning steps).",
    )
    parser.add_argument(
        "--loop",
        dest="loop",
        action="store_true",
        help=(
            "Loop mode: keep scanning/provisioning until interrupted "
            "(overrides stage1.options.loop_mode)."
        ),
    )
    return parser.parse_args()


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────

def main() -> int:
    args = parse_args()

    # Require building
    try:
        building = require_building(args.building)
    except BuildingError as e:
        print(f"{RED}ERROR: {e}{RESET}", file=sys.stderr)
        return 1
    
    # Set building paths
    paths = set_building(building)
    
    # Config path: use argument or default to building's config
    config_path = args.config if args.config else str(paths['config'])

    cfg, yaml_logfile = load_config(config_path)

    dry_run = args.dry_run
    logfile = args.logfile if args.logfile else yaml_logfile
    verbose = bool(getattr(args, "verbose", False))
    quiet = not verbose

    # loop_mode: config option can be overridden by --loop
    cfg_loop = bool(cfg["options"].get("loop_mode", False))
    loop_mode = bool(getattr(args, "loop", False)) or cfg_loop

    iface_hint = None  # still delegated to stage1 core

    if loop_mode:
        try:
            while True:
                summary = provision_once(
                    cfg,
                    dry_run=dry_run,
                    logfile=logfile,
                    iface_hint=iface_hint,
                    quiet=quiet,
                )
                print_summary(summary)

                # If there is nothing useful to do anymore, exit loop gracefully
                reason = summary.get("reason")
                ok = bool(summary.get("ok"))

                if (not ok) and reason in ("no_connectable_ap", "no_shelly_found"):
                    break

        except KeyboardInterrupt:
            # Silent exit in loop mode – no additional logging
            pass
    else:
        summary = provision_once(
            cfg,
            dry_run=dry_run,
            logfile=logfile,
            iface_hint=iface_hint,
            quiet=quiet,
        )
        print_summary(summary)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
