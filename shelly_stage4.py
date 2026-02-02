#!/usr/bin/env python3
"""
Shelly Provisioning — Stage 4 (Device Configuration)

Thin CLI wrapper around the Stage 4 core API:

    core/provision/stage4_core.py

Usage:
    # Apply profile to single device
    python3 shelly_stage4.py -b <building> --ip 192.168.50.30 --profile 1pm

    # Auto-match profile based on hw_model
    python3 shelly_stage4.py --building <building> --ip 192.168.50.30

    # Apply to all devices in ip_state.json
    python3 shelly_stage4.py -b <building> --all

    # Dry-run (show what would be done)
    python3 shelly_stage4.py -b <building> --ip 192.168.50.30 --dry-run

    # List available profiles
    python3 shelly_stage4.py -b <building> --list-profiles
    
    # Or with environment variable:
    export STAGEBOX_BUILDING=my_building
    python3 shelly_stage4.py --all
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.building import (
    require_building,
    get_building_paths,
    add_building_argument,
    BuildingError,
)
from core.provision.stage4_core import (
    Profile,
    Stage4Result,
    load_all_profiles,
    load_profile,
    match_profile_for_device,
    run_stage4_for_device,
    run_stage4_on_state,
    get_kvs,
    list_scripts,
    list_webhooks,
    reboot_device,
    _rpc_call,
)

# ---------- ANSI colors ----------

COLOR_RESET = "\033[0m"
COLOR_RED = "\033[31m"
COLOR_GREEN = "\033[32m"
COLOR_YELLOW = "\033[33m"
COLOR_CYAN = "\033[36m"

# ---------- Path helpers ----------


def detect_default_paths(building_name: str) -> Dict[str, Path]:
    """Get paths for a specific building."""
    paths = get_building_paths(building_name)

    return {
        "project_root": paths['stagebox_root'],
        "ip_state": paths['ip_state'],
        "profiles": paths['profiles_dir'],
        "scripts": paths['scripts_dir'],
    }


# ---------- State helpers ----------


def load_state(path: Path) -> Dict[str, Any]:
    """Load ip_state.json."""
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"ERROR: State file not found: {path}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Cannot load state file: {e}", file=sys.stderr)
        sys.exit(1)


def save_state(path: Path, state: Dict[str, Any]) -> None:
    """Save ip_state.json with backup."""
    backup_path = str(path) + ".bak"
    
    # Create backup
    if path.exists():
        try:
            import shutil
            shutil.copy2(path, backup_path)
        except Exception as e:
            print(f"WARNING: Could not create backup: {e}", file=sys.stderr)
    
    # Write new state
    try:
        with path.open("w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        print(f"ERROR: Cannot save state file: {e}", file=sys.stderr)
        sys.exit(1)


def get_device_by_ip(state: Dict[str, Any], ip: str) -> Optional[tuple]:
    """Find device entry by IP. Returns (mac, entry) or None."""
    devices = state.get("devices", state)
    
    for mac, entry in devices.items():
        if isinstance(entry, dict) and entry.get("ip") == ip:
            return mac, entry
    
    return None


# ---------- Output formatting ----------


def format_result(result: Stage4Result, verbose: bool = False) -> str:
    """Format Stage4Result for console output."""
    if result.ok:
        status = f"{COLOR_GREEN}OK{COLOR_RESET}"
    else:
        status = f"{COLOR_RED}FAILED{COLOR_RESET}"
    
    profile = result.profile_name or "none"
    line = f"{result.ip} ({result.mac}) — {status} (profile: {profile})"
    
    if verbose:
        lines = [line]
        
        # Actions
        if result.actions.get("shelly_profile"):
            sp = result.actions["shelly_profile"]
            lines.append(f"  Shelly profile: {sp.get('target')} — {sp.get('message', '')}")
        
        if result.actions.get("components"):
            comp = result.actions["components"]
            if comp.get("changed"):
                lines.append(f"  Components changed: {', '.join(comp['changed'])}")
            if comp.get("failed"):
                lines.append(f"  {COLOR_RED}Components failed: {', '.join(comp['failed'])}{COLOR_RESET}")
        
        # Errors
        for err in result.errors:
            lines.append(f"  {COLOR_RED}Error: {err.message}{COLOR_RESET}")
        
        # Warnings
        for warn in result.warnings:
            lines.append(f"  {COLOR_YELLOW}Warning: {warn.message}{COLOR_RESET}")
        
        return "\n".join(lines)
    
    return line


def print_profiles(profiles: Dict[str, Profile]) -> None:
    """Print available profiles."""
    print(f"\n{COLOR_CYAN}Available profiles:{COLOR_RESET}\n")
    
    for name, profile in sorted(profiles.items()):
        print(f"  {COLOR_GREEN}{name}{COLOR_RESET}")
        print(f"    Name: {profile.name}")
        print(f"    Device types: {', '.join(profile.device_types)}")
        if profile.shelly_profile:
            print(f"    Shelly profile: {profile.shelly_profile}")
        if profile.components:
            print(f"    Components: {', '.join(profile.components.keys())}")
        print()


def print_device_info(ip: str) -> None:
    """Print device info, scripts, webhooks, KVS."""
    print(f"\n{COLOR_CYAN}Device info for {ip}:{COLOR_RESET}\n")
    
    # Device info
    ok, info, msg = _rpc_call(ip, "Shelly.GetDeviceInfo")
    if ok and info:
        print(f"  ID: {info.get('id')}")
        print(f"  MAC: {info.get('mac')}")
        print(f"  Model: {info.get('model')}")
        print(f"  FW: {info.get('ver')}")
        print(f"  Profile: {info.get('profile', 'n/a')}")
    else:
        print(f"  {COLOR_RED}Cannot reach device: {msg}{COLOR_RESET}")
        return
    
    # Scripts
    print(f"\n  {COLOR_CYAN}Scripts:{COLOR_RESET}")
    ok, scripts, _ = list_scripts(ip)
    if ok and scripts:
        for s in scripts:
            enabled = "enabled" if s.get("enable") else "disabled"
            running = ", running" if s.get("running") else ""
            print(f"    [{s.get('id')}] {s.get('name')} — {enabled}{running}")
    else:
        print("    (none)")
    
    # Webhooks
    print(f"\n  {COLOR_CYAN}Webhooks:{COLOR_RESET}")
    ok, hooks, _ = list_webhooks(ip)
    if ok and hooks:
        for h in hooks:
            print(f"    [{h.get('id')}] {h.get('event')} → {h.get('urls', [])}")
    else:
        print("    (none)")
    
    # KVS
    print(f"\n  {COLOR_CYAN}KVS:{COLOR_RESET}")
    ok, kvs, _ = get_kvs(ip)
    if ok and kvs:
        for k, v in kvs.items():
            print(f"    {k}: {v}")
    else:
        print("    (none)")
    
    print()


# ---------- Argument parsing ----------


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Stage 4 — Shelly device configuration (profiles, scripts, webhooks).",
    )
    
    # Add building argument
    add_building_argument(parser)
    
    # Target selection
    target = parser.add_mutually_exclusive_group()
    target.add_argument(
        "--ip",
        type=str,
        help="Target device IP address",
    )
    target.add_argument(
        "--mac",
        type=str,
        help="Target device MAC address",
    )
    target.add_argument(
        "--all",
        action="store_true",
        help="Apply to NEW devices only (stage_completed < 4). Use --force for all.",
    )
    
    # Profile selection
    parser.add_argument(
        "--profile",
        type=str,
        help="Profile name to apply (auto-detected from hw_model if not specified)",
    )
    
    # Actions
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without applying changes",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force apply to devices with stage_completed >= 4 (DANGEROUS!)",
    )
    parser.add_argument(
        "--list-profiles",
        action="store_true",
        help="List available profiles and exit",
    )
    parser.add_argument(
        "--info",
        action="store_true",
        help="Show device info (scripts, webhooks, KVS) and exit",
    )
    parser.add_argument(
        "--reboot",
        action="store_true",
        help="Reboot device and exit",
    )
    
    # Paths (defaults set in main after building is determined)
    parser.add_argument(
        "--state-file",
        type=Path,
        default=None,
        help="Path to ip_state.json (default: <building>/stagebox/data/ip_state.json)",
    )
    parser.add_argument(
        "--profiles-dir",
        type=Path,
        default=None,
        help="Path to profiles directory (default: <building>/stagebox/data/profiles)",
    )
    
    # Output
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output",
    )

    return parser


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
    
    # Set defaults if not provided
    if args.state_file is None:
        args.state_file = defaults["ip_state"]
    if args.profiles_dir is None:
        args.profiles_dir = defaults["profiles"]
    
    # Load profiles
    profiles = load_all_profiles(args.profiles_dir)
    
    if not profiles:
        print(f"WARNING: No profiles found in {args.profiles_dir}", file=sys.stderr)
    
    # --list-profiles
    if args.list_profiles:
        print_profiles(profiles)
        return 0
    
    # --info (requires --ip)
    if args.info:
        if not args.ip:
            print("ERROR: --info requires --ip", file=sys.stderr)
            return 1
        print_device_info(args.ip)
        return 0
    
    # --reboot (requires --ip)
    if args.reboot:
        if not args.ip:
            print("ERROR: --reboot requires --ip", file=sys.stderr)
            return 1
        print(f"Rebooting {args.ip}...")
        ok, msg = reboot_device(args.ip, wait=True)
        if ok:
            print(f"{COLOR_GREEN}OK{COLOR_RESET}: {msg}")
            return 0
        else:
            print(f"{COLOR_RED}FAILED{COLOR_RESET}: {msg}")
            return 1
    
    # Load state
    state = load_state(args.state_file)
    
    # --all: Apply to all matching devices
    if args.all:
        if not profiles:
            print("ERROR: No profiles available", file=sys.stderr)
            return 1
        
        # Force confirmation
        if args.force and not args.dry_run:
            print(f"{COLOR_RED}WARNING: --force will overwrite ALL device configurations!{COLOR_RESET}")
            print("This includes devices that have already been configured (stage_completed >= 4).")
            print("Your custom settings (maxtime, auto_off, etc.) will be LOST.\n")
            confirm = input("Type 'YES' to continue: ")
            if confirm != "YES":
                print("Aborted.")
                return 1
            print()
        
        mode = "NEW devices only (stage_completed < 4)"
        if args.force:
            mode = f"{COLOR_RED}ALL devices (--force){COLOR_RESET}"
        
        print(f"Running Stage 4 on {mode} (dry_run={args.dry_run})...\n")
        
        results, skipped = run_stage4_on_state(
            state=state,
            profiles=profiles,
            dry_run=args.dry_run,
            force=args.force,
        )
        
        # Show skipped devices
        if skipped and args.verbose:
            print(f"{COLOR_YELLOW}Skipped devices:{COLOR_RESET}")
            for mac, reason in sorted(skipped.items()):
                print(f"  {mac}: {reason}")
            print()
        
        if not results:
            skip_count = len(skipped)
            print(f"No devices to process. ({skip_count} skipped)")
            if skip_count > 0 and not args.verbose:
                print("Use -v to see skipped devices.")
            return 0
        
        ok_count = 0
        fail_count = 0
        
        for mac, result in sorted(results.items(), key=lambda x: x[1].ip):
            print(format_result(result, args.verbose))
            if result.ok:
                ok_count += 1
            else:
                fail_count += 1
        
        skip_count = len(skipped)
        print(f"\nStage 4 summary: processed={len(results)} ok={ok_count} failed={fail_count} skipped={skip_count}")
        
        # Save state
        if not args.dry_run:
            save_state(args.state_file, state)
        else:
            print("[dry-run: not saving state]")
        
        return 0 if fail_count == 0 else 2
    
    # Single device (--ip or --mac)
    if not args.ip and not args.mac:
        print("ERROR: Specify --ip, --mac, or --all", file=sys.stderr)
        parser.print_help()
        return 1
    
    # Resolve MAC/IP
    if args.mac:
        mac = args.mac.upper().replace(":", "").replace("-", "")
        devices = state.get("devices", state)
        entry = devices.get(mac)
        if not entry:
            print(f"ERROR: MAC {args.mac} not found in state", file=sys.stderr)
            return 1
        ip = entry.get("ip")
        if not ip:
            print(f"ERROR: No IP for MAC {args.mac}", file=sys.stderr)
            return 1
    else:
        ip = args.ip
        result = get_device_by_ip(state, ip)
        if result:
            mac, entry = result
        else:
            # Device not in state - try to reach it directly
            print(f"WARNING: IP {ip} not in state, fetching device info...")
            ok, info, msg = _rpc_call(ip, "Shelly.GetDeviceInfo")
            if not ok:
                print(f"ERROR: Cannot reach device: {msg}", file=sys.stderr)
                return 1
            mac = info.get("mac", "").upper().replace(":", "")
            entry = {"ip": ip, "hw_model": info.get("model")}
    
    # Determine profile
    if args.profile:
        # Explicit profile
        if args.profile not in profiles:
            print(f"ERROR: Profile '{args.profile}' not found", file=sys.stderr)
            print(f"Available: {', '.join(profiles.keys())}")
            return 1
        profile = profiles[args.profile]
    else:
        # Auto-match
        hw_model = entry.get("hw_model") or entry.get("model") or ""
        match = match_profile_for_device(hw_model, profiles)
        if not match:
            print(f"ERROR: No matching profile for hw_model '{hw_model}'", file=sys.stderr)
            print(f"Use --profile to specify one manually")
            return 1
        profile_name, profile = match
        print(f"Auto-matched profile: {profile_name} (hw_model: {hw_model})")
    
    # SAFETY CHECK for single device
    stage_completed = entry.get("stage_completed") if entry else None
    
    if stage_completed is not None and stage_completed >= 4 and not args.force and not args.dry_run:
        print(f"\n{COLOR_YELLOW}WARNING: Device already configured (stage_completed={stage_completed}){COLOR_RESET}")
        print("Applying profile will OVERWRITE existing configuration.")
        print("Use --dry-run to preview changes, or --force to apply anyway.\n")
        confirm = input("Type 'YES' to continue: ")
        if confirm != "YES":
            print("Aborted.")
            return 1
        print()
    
    # Run Stage 4
    print(f"\nApplying profile '{profile.name}' to {ip} (dry_run={args.dry_run})...\n")
    
    result = run_stage4_for_device(
        ip=ip,
        mac=mac,
        profile=profile,
        state=state,
        dry_run=args.dry_run,
    )
    
    print(format_result(result, verbose=True))
    
    # Save state
    if not args.dry_run:
        save_state(args.state_file, state)
    else:
        print("\n[dry-run: not saving state]")
    
    return 0 if result.ok else 2


if __name__ == "__main__":
    raise SystemExit(main())