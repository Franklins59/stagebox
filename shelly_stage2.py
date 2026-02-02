#!/usr/bin/env python3
"""
Stage 2 provisioning CLI wrapper for StageBox.

This script is a thin wrapper around the core Stage 2 API:

    core/provision/stage2_core.py

Responsibilities:
- Parse CLI arguments
- Load YAML config (config.yaml / stage2 section)
- Load wifi_profiles from secrets.yaml (top-level)
- Construct Stage2Options from config
- Initialize RpcClient and State
- Run Stage 2 for one or multiple devices (by IP) or in "adopt" mode
- Print one colored summary line per device
- Append the same summaries to a session log file (if configured)

It does NOT contain any provisioning logic itself; all RPC and state logic
lives in the core modules.

Usage:
    python shelly_stage2.py --building <building_name> --adopt
    python shelly_stage2.py -b <building_name> --ip 192.168.1.150
    
    # Or with environment variable:
    export STAGEBOX_BUILDING=my_building
    python shelly_stage2.py --adopt
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Dict, List, Callable, Optional

import yaml

from core.building import (
    require_building,
    get_building_paths,
    add_building_argument,
    BuildingError,
)
from core.provision.stage2_core import (
    stage2_configure_device_by_ip,
    stage2_discover_and_adopt,
    _stage2_result_to_dict,
)
from core.state import State, load_state
from core.rpc import RpcClient  # your RpcClient in core/rpc.py

# ---------- Simple ANSI colors for one-line output ----------

COLOR_RESET = "\033[0m"
COLOR_GREEN = "\033[32m"
COLOR_RED = "\033[31m"
COLOR_YELLOW = "\033[33m"
COLOR_CYAN = "\033[36m"


# ---------- Config / secrets loading ----------


def load_yaml(path: Path) -> Dict[str, Any]:
    """Load a YAML file and return a dict (empty dict on error)."""
    try:
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return data if isinstance(data, dict) else {}
    except FileNotFoundError:
        print(f"WARNING: YAML file not found: {path}", file=sys.stderr)
        return {}
    except Exception as exc:
        print(f"ERROR: Failed to load YAML {path}: {exc}", file=sys.stderr)
        return {}


def get_stage2_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract stage2-related settings from config.yaml.

    Expected structure, for example:

        stage2:
          enabled: true
          rpc:
            timeout_s: 0.30
          network:
            mode: static_pool
            pool_start: 192.168.1.30
            pool_end: 192.168.1.99
            gateway: 192.168.1.1
            netmask: 255.255.255.0
            nameserver: 192.168.1.1
            state_file: "data/ip_state.json"
          naming:
            enabled: true
          model_mapping_file: "data/shelly_model_map.yaml"
          logging:
            base_path: "var/log/stage2_session.log"
          inventory:
            enabled: true
            file: "var/log/stage2_inventory.csv"
    """
    return config.get("stage2", {}) or {}


def load_wifi_profiles(secrets_path: Path) -> List[Dict[str, Any]]:
    """
    Load wifi_profiles from secrets.yaml (top-level key).

    Expected structure in secrets.yaml:

        wifi_profiles:
          - ssid: "IoT"
            password: "xxx"
          - ssid: "FORSTEC2"
            password: "yyy"

    Returns a list (possibly empty) of {ssid, password} dicts.
    """
    data = load_yaml(secrets_path)
    profiles = data.get("wifi_profiles") or []
    if not isinstance(profiles, list):
        print(
            f"WARNING: wifi_profiles in {secrets_path} is not a list; ignoring.",
            file=sys.stderr,
        )
        return []

    normalized: List[Dict[str, Any]] = []
    for item in profiles:
        if not isinstance(item, dict):
            continue
        ssid = item.get("ssid")
        password = item.get("password")
        if isinstance(ssid, str) and password is not None:
            normalized.append({"ssid": ssid, "password": password})
    return normalized


# ---------- Model mapping ----------


def load_model_mapping(map_path: Path) -> Dict[str, str]:
    """
    Load Shelly model mapping from a YAML file.

    If the file does not exist or is invalid, an empty mapping is returned.
    """
    mapping: Dict[str, str] = {}
    if not map_path.exists():
        return mapping

    try:
        with map_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        if isinstance(data, dict):
            for k, v in data.items():
                if isinstance(k, str) and isinstance(v, str):
                    mapping[k] = v
    except Exception as exc:
        print(f"WARNING: Failed to load model map {map_path}: {exc}", file=sys.stderr)

    return mapping


# ---------- Path helpers ----------


def detect_default_paths(building_name: str) -> Dict[str, Path]:
    """
    Get paths for a specific building.

    Layout:
        /home/coredev/buildings/<building>/stagebox/
          data/
            config.yaml
            secrets.yaml
            ip_state.json
            shelly_model_map.yaml
    """
    paths = get_building_paths(building_name)
    
    return {
        "project_root": paths['stagebox_root'],
        "data_dir": paths['data_dir'],
        "config": paths['config'],
        "secrets": paths['secrets'],
        "ip_state": paths['ip_state'],
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


def get_session_log_path(stage2_cfg: Dict[str, Any], defaults: Dict[str, Path]) -> Optional[Path]:
    """
    Resolve the session log path from stage2.logging.base_path (if present),
    relative to project_root when not absolute.
    """
    logging_cfg = stage2_cfg.get("logging") or {}
    base_path = logging_cfg.get("base_path")
    if not base_path:
        return None
    project_root = defaults["project_root"]
    return resolve_path(base_path, project_root)


def append_session_log_line(
    stage2_cfg: Dict[str, Any],
    defaults: Dict[str, Path],
    text: str,
) -> None:
    """
    Append a single line to the Stage 2 session log, if configured.

    Failures are non-fatal and only reported as warnings on stderr.
    """
    log_path = get_session_log_path(stage2_cfg, defaults)
    if log_path is None:
        return

    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("a", encoding="utf-8") as f:
            f.write(text + "\n")
    except Exception as exc:
        print(f"WARNING: Failed to write session log {log_path}: {exc}", file=sys.stderr)


# ---------- Options / State / RPC ----------


def build_stage2_options(
    stage2_cfg: Dict[str, Any],
    model_mapping: Dict[str, str],
    wifi_profiles: List[Dict[str, Any]],
    dry_run: bool,
) -> Dict[str, Any]:
    """
    Build Stage2Options dict for stage2_core from the stage2 section of the YAML.

    The core fills in defaults for missing keys. Here we just forward:
      - network
      - hostname/naming
      - wifi_profiles (from secrets.yaml)
      - model_mapping
      - dry_run, force_reconfigure
    """
    hostname_cfg = stage2_cfg.get("hostname", {}) or stage2_cfg.get("naming", {}) or {}
    options: Dict[str, Any] = {}

    # This is a logical placeholder if you ever introduce multiple network profiles.
    options["network_profile"] = stage2_cfg.get("network_profile", "default_sta")
    options["network"] = stage2_cfg.get("network", {}) or {}
    options["hostname"] = hostname_cfg

    # Prefer wifi_profiles from secrets.yaml, but allow override in stage2 if present
    stage_wifi = stage2_cfg.get("wifi_profiles", []) or []
    merged_wifi: List[Dict[str, Any]] = []
    merged_wifi.extend(wifi_profiles)
    # Only append additional profiles defined in stage2 (avoid duplicates with same SSID)
    known_ssids = {p.get("ssid") for p in wifi_profiles if isinstance(p.get("ssid"), str)}
    for item in stage_wifi:
        if isinstance(item, dict):
            ssid = item.get("ssid")
            if isinstance(ssid, str) and ssid not in known_ssids:
                merged_wifi.append(item)

    options["wifi_profiles"] = merged_wifi
    options["model_mapping"] = model_mapping

    options["dry_run"] = dry_run
    options["force_reconfigure"] = stage2_cfg.get("force_reconfigure", False)

    return options


def build_state(stage2_cfg: Dict[str, Any], defaults: Dict[str, Path]) -> State:
    """Construct the State instance for Stage 2 from config and defaults."""
    network_cfg = stage2_cfg.get("network", {}) or {}
    state_file = network_cfg.get("state_file")

    if state_file:
        # resolve relative to project root
        project_root = defaults["project_root"]
        state_path = resolve_path(state_file, project_root)
    else:
        state_path = defaults["ip_state"]

    return load_state(str(state_path))


def build_rpc_client_for_ip(target_ip: str, stage2_cfg: Dict[str, Any]) -> RpcClient:
    rpc_cfg = stage2_cfg.get("rpc", {}) or {}
    timeout_s = float(rpc_cfg.get("timeout_s", 5.0))
    return RpcClient(host=target_ip, timeout_s=timeout_s)


def make_rpc_factory(stage2_cfg: Dict[str, Any]) -> Callable[[str], RpcClient]:
    """Create a factory that builds RpcClient instances for a given IP."""
    rpc_cfg = stage2_cfg.get("rpc", {}) or {}
    timeout_s = float(rpc_cfg.get("timeout_s", 5.0))

    def _factory(ip: str) -> RpcClient:
        return RpcClient(host=ip, timeout_s=timeout_s)

    return _factory


# ---------- One-line result formatting ----------


def summarize_result_line(result: Dict[str, Any]) -> str:
    """Build a colored one-line summary string from a Stage2Result dict."""
    ok = bool(result.get("ok", False))
    model = result.get("model") or "?"
    ip = result.get("ip") or "?"
    hostname = result.get("hostname") or ""
    meta = result.get("meta") or {}
    assigned_ip = meta.get("assigned_ip") or ip

    actions = result.get("actions") or {}
    net_action = actions.get("network") or {}
    state_action = actions.get("ip_state") or {}

    net_changed = bool(net_action.get("changed"))
    state_changed = bool(state_action.get("changed"))

    status_color = COLOR_GREEN if ok else COLOR_RED
    status_text = "OK" if ok else "FAIL"

    # Show IP change if current IP differs from assigned IP
    if ip != assigned_ip:
        ip_display = f"{COLOR_YELLOW}{ip}{COLOR_RESET} → {COLOR_CYAN}{assigned_ip}{COLOR_RESET}"
    else:
        ip_display = f"{COLOR_CYAN}{assigned_ip}{COLOR_RESET}"

    base = f"{COLOR_CYAN}{model}{COLOR_RESET} @ {ip_display}"
    if hostname:
        base += f" ({hostname})"

    details: List[str] = []

    # Uncomment if you want to see change flags in the future:
    # details.append(f"net={'1' if net_changed else '0'}")
    # details.append(f"state={'1' if state_changed else '0'}")

    errors = result.get("errors") or []
    if errors and not ok:
        first_err = errors[0]
        code = first_err.get("code", "")
        msg = first_err.get("message", "")
        if code or msg:
            details.append(f"err={code or msg}")

    detail_str = ", ".join(details)

    line = f"{base} — {status_color}{status_text}{COLOR_RESET}"
    if detail_str:
        line += f" [{detail_str}]"
    return line


# ---------- Core run logic ----------


def run_stage2_for_ips(
    ips: List[str],
    cfg_path: Path,
    dry_run: bool,
    quiet: bool,
    building: str,
) -> int:
    """Run Stage 2 for the given list of IPs using the new core API."""
    if not ips:
        print("No IPs specified. Use --ip or --from-file.", file=sys.stderr)
        return 1

    defaults = detect_default_paths(building)
    config = load_yaml(cfg_path)
    stage2_cfg = get_stage2_config(config)

    project_root = defaults["project_root"]
    data_dir = defaults["data_dir"]
    secrets_path = defaults["secrets"]

    # wifi_profiles from secrets.yaml (plus optional override / additions in stage2_cfg)
    wifi_profiles = load_wifi_profiles(secrets_path)

    # model mapping: from stage2_cfg.model_mapping_file if present, otherwise default
    model_map_cfg = stage2_cfg.get("model_mapping_file")
    if model_map_cfg:
        model_map_path = resolve_path(model_map_cfg, project_root)
    else:
        model_map_path = data_dir / "shelly_model_map.yaml"

    model_mapping = load_model_mapping(model_map_path)

    options = build_stage2_options(
        stage2_cfg=stage2_cfg,
        model_mapping=model_mapping,
        wifi_profiles=wifi_profiles,
        dry_run=dry_run,
    )
    state = build_state(stage2_cfg, defaults)

    overall_ok = True
    last_meta: Dict[str, Any] | None = None

    for ip in ips:
        rpc_client = build_rpc_client_for_ip(ip, stage2_cfg)

        try:
            result = stage2_configure_device_by_ip(
                rpc_client=rpc_client,
                state=state,
                target_ip=ip,
                options=options,
            )
        except Exception as exc:
            overall_ok = False
            msg = f"ERROR while processing {ip}: {exc}"
            print(f"{COLOR_RED}{msg}{COLOR_RESET}", file=sys.stderr)
            append_session_log_line(stage2_cfg, defaults, msg)
            continue

        dict_result = _stage2_result_to_dict(result)

        meta = dict_result.get("meta") or {}
        if meta:
            last_meta = meta

        line = summarize_result_line(dict_result)

        if not quiet:
            print(line)

        # Write per-device summary to session log as plain text (no ANSI)
        plain_line = strip_ansi(line)
        append_session_log_line(stage2_cfg, defaults, plain_line)

        if not dict_result.get("ok", False):
            overall_ok = False

    if last_meta:
        pool_total = last_meta.get("pool_total")
        pool_used = last_meta.get("pool_used")
        pool_free = last_meta.get("pool_free")
        pool_start = last_meta.get("pool_start")
        pool_end = last_meta.get("pool_end")

        if pool_total is not None and pool_used is not None and pool_free is not None:
            summary_line = (
                f"Pool {pool_start}–{pool_end}: used {pool_used}/{pool_total}, free {pool_free}"
            )
            if not quiet:
                print(f"{COLOR_CYAN}{summary_line}{COLOR_RESET}")
            append_session_log_line(stage2_cfg, defaults, summary_line)

    return 0 if overall_ok else 2


def strip_ansi(text: str) -> str:
    """
    Very small helper to strip ANSI color codes for log files.
    """
    import re

    ansi_re = re.compile(r"\x1b\[[0-9;]*m")
    return ansi_re.sub("", text)


def read_ips_from_file(path: Path) -> List[str]:
    """Read IP addresses or hostnames from a text file (one per line)."""
    ips: List[str] = []
    try:
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                ips.append(line)
    except Exception as exc:
        print(f"ERROR: Failed to read IP list from {path}: {exc}", file=sys.stderr)
    return ips


def run_adopt_mode(
    cfg_path: Path,
    dry_run: bool,
    quiet: bool,
    cidr_override: Optional[str] = None,
    building: str = "",
) -> int:
    """
    Run 'discover & adopt' mode: scan CIDR, adopt Shellys into pool via Stage 2.
    """
    defaults = detect_default_paths(building)
    config = load_yaml(cfg_path)
    stage2_cfg = get_stage2_config(config)

    project_root = defaults["project_root"]
    data_dir = defaults["data_dir"]
    secrets_path = defaults["secrets"]

    wifi_profiles = load_wifi_profiles(secrets_path)

    model_map_cfg = stage2_cfg.get("model_mapping_file")
    if model_map_cfg:
        model_map_path = resolve_path(model_map_cfg, project_root)
    else:
        model_map_path = data_dir / "shelly_model_map.yaml"

    model_mapping = load_model_mapping(model_map_path)

    options = build_stage2_options(
        stage2_cfg=stage2_cfg,
        model_mapping=model_mapping,
        wifi_profiles=wifi_profiles,
        dry_run=dry_run,
    )

    if cidr_override:
        options.setdefault("network", {})
        options["network"]["scan_cidr"] = cidr_override

    # Ensure absolute state_file path is set to avoid writing to wrong location
    options.setdefault("network", {})
    options["network"]["state_file"] = str(defaults["ip_state"])

    state = build_state(stage2_cfg, defaults)
    rpc_factory = make_rpc_factory(stage2_cfg)

    summary = stage2_discover_and_adopt(
        rpc_factory=rpc_factory,
        state=state,
        options=options,
    )
    meta = summary.get("meta", {}) or {}
    error_code = meta.get("error")

    if error_code == "invalid_dhcp_scan_range":
        dhcp_start = meta.get("dhcp_scan_start")
        dhcp_end = meta.get("dhcp_scan_end")
        msg = (
            f"WARNING: invalid DHCP scan range configuration "
            f"({dhcp_start!r}–{dhcp_end!r}). "
            "Falling back to full CIDR scan minus pool range."
        )
        print(msg, file=sys.stderr)
        append_session_log_line(stage2_cfg, defaults, msg)

    devices = summary.get("devices", {}) or {}
    meta = summary.get("meta", {}) or {}

    cidr = meta.get("cidr", "")
    pool_start = meta.get("pool_start")
    pool_end = meta.get("pool_end")
    scan_candidates = meta.get("scan_candidates", 0)
    found_shellys = meta.get("found_shellys", 0)
    adopted = meta.get("adopted", 0)
    errors = meta.get("errors", 0)

    dhcp_start = meta.get("dhcp_scan_start")
    dhcp_end = meta.get("dhcp_scan_end")

    range_parts: list[str] = []
    if pool_start and pool_end:
        range_parts.append(f"excl. {pool_start}–{pool_end}")
    if dhcp_start and dhcp_end:
        range_parts.append(f"DHCP {dhcp_start}–{dhcp_end}")

    if range_parts:
        range_desc = " (" + ", ".join(range_parts) + ")"
    else:
        range_desc = ""

    summary_line = (
        f"Adopt CIDR {cidr}{range_desc}: "
        f"scan={scan_candidates}, "
        f"found={found_shellys}, "
        f"adopted={adopted}, "
        f"errors={errors}"
    )

    # Console
    print(summary_line)
    # Session log
    append_session_log_line(stage2_cfg, defaults, summary_line)

    # Optional: per-device lines also into the session log (non-colored)
    for _, dev_result in devices.items():
        line = summarize_result_line(dev_result)
        append_session_log_line(stage2_cfg, defaults, strip_ansi(line))
        if not quiet:
            # Show per-device lines on console to display IP changes
            print(line)

    return 0 if summary.get("ok", False) else 2


# ---------- Argument parsing ----------


def build_arg_parser() -> argparse.ArgumentParser:
    """Create the top-level argument parser for Stage 2 CLI."""
    parser = argparse.ArgumentParser(
        description="Stage 2 provisioning for Shelly Gen2/Gen3 devices (StageBox core)."
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
        "--ip",
        nargs="+",
        metavar="IP",
        help="One or more device IP addresses to run Stage 2 on.",
    )
    parser.add_argument(
        "--from-file",
        type=Path,
        metavar="FILE",
        help="Read device IPs from a text file (one IP/hostname per line).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not apply changes, only show what would be done.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Only print errors; suppress per-device summary lines.",
    )
    parser.add_argument(
        "--adopt",
        action="store_true",
        help=(
            "Discover Shellys in configured CIDR (outside pool) "
            "and adopt them into the pool"
        ),
    )
    parser.add_argument(
        "--cidr",
        help="Override scan CIDR for adopt mode (e.g. 192.168.1.0/24)",
    )

    return parser


def main(argv: List[str] | None = None) -> int:
    """Main entry point for CLI usage."""
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    # Require building
    try:
        building = require_building(args.building)
    except BuildingError as e:
        print(f"{COLOR_RED}ERROR: {e}{COLOR_RESET}", file=sys.stderr)
        return 1
    
    # Get paths for building
    defaults = detect_default_paths(building)
    
    # Config path: use argument or default to building's config
    cfg_path: Path = args.config if args.config else defaults["config"]

    # 1) Adopt mode has priority and does not require explicit IP list
    if args.adopt:
        return run_adopt_mode(
            cfg_path=cfg_path,
            dry_run=bool(args.dry_run),
            quiet=bool(args.quiet),
            cidr_override=args.cidr,
            building=building,
        )

    # 2) Normal Stage-2 mode: collect IPs
    ips: List[str] = []
    if args.ip:
        ips.extend(args.ip)
    if args.from_file:
        ips_from_file = read_ips_from_file(args.from_file)
        ips.extend(ips_from_file)

    # Deduplicate while preserving order
    seen: set[str] = set()
    unique_ips: List[str] = []
    for ip in ips:
        if ip not in seen:
            unique_ips.append(ip)
            seen.add(ip)

    if not unique_ips:
        print("No IPs given. Use --ip or --from-file.", file=sys.stderr)
        return 1

    return run_stage2_for_ips(
        ips=unique_ips,
        cfg_path=cfg_path,
        dry_run=bool(args.dry_run),
        quiet=bool(args.quiet),
        building=building,
    )


if __name__ == "__main__":
    raise SystemExit(main())