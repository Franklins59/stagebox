#!/usr/bin/env python3
"""
Shelly offline report & label tool.

Features:

- Read ip_state.json (single source of truth).
- Print a simple device report to stdout.
- Export devices as CSV (Excel-friendly).
- Generate label CSVs for DYMO (band or multiline).

Configuration:

- Uses <building>/stagebox/data/config.yaml, section "report:" for all settings.
- Never writes to ip_state.json, only reads it.

Usage:
    python shelly_report.py --building <building_name> report
    python shelly_report.py -b <building_name> export --format csv
    
    # Or with environment variable:
    export STAGEBOX_BUILDING=my_building
    python shelly_report.py report
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from core.building import (
    require_building,
    get_building_paths,
    add_building_argument,
    BuildingError,
)

# ANSI colors
COLOR_RED = "\033[31m"
COLOR_RESET = "\033[0m"


# ---------------------------------------------------------------------------
# Datamodel
# ---------------------------------------------------------------------------


@dataclass
class ShellyDevice:
    """Stable internal representation of one Shelly device for reporting."""

    # Base fields
    id: str
    ip: str
    hostname: str
    model: str
    hw_model: str
    fw: str
    friendly_name: str
    room: str
    location: str
    assigned_at: Optional[str]
    last_seen: Optional[str]

    # Stage 3
    stage3_friendly_status: str
    stage3_ota_status: str
    stage3_last_run: Optional[str]

    # Stage 4 (optional, schema may evolve)
    stage4_script_enabled: Optional[bool]
    stage4_script_name: Optional[str]
    stage4_script_file: Optional[str]
    stage4_status_result: Optional[str]
    stage4_status_last_run: Optional[str]

    # KVS is kept generic to be future-proof
    kvs: Dict[str, Any]


# ---------------------------------------------------------------------------
# Config handling
# ---------------------------------------------------------------------------


def load_config(config_path: Path) -> Dict[str, Any]:
    """Load non-secret configuration from config.yaml and return as dict."""
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with config_path.open("r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}

    report_cfg = cfg.get("report")
    if report_cfg is None:
        raise RuntimeError("Missing 'report:' section in config.yaml")

    # Basic sanity checks
    if "state_file" not in report_cfg:
        raise RuntimeError("config.yaml: 'report.state_file' is required")

    output_cfg = report_cfg.get("output", {})
    if "table_dir" not in output_cfg or "labels_dir" not in output_cfg:
        raise RuntimeError(
            "config.yaml: 'report.output.table_dir' and 'report.output.labels_dir' are required"
        )

    return cfg


# ---------------------------------------------------------------------------
# ip_state loader and conversion into ShellyDevice
# ---------------------------------------------------------------------------


def load_ip_state(path: Path) -> Dict[str, Any]:
    """Load ip_state.json from disk and return the raw dictionary."""
    if not path.exists():
        raise FileNotFoundError(f"ip_state file not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        state = json.load(f)

    if not isinstance(state, dict):
        raise ValueError("ip_state.json: expected a JSON object at top level")

    return state


def build_devices_from_state(state: Dict[str, Any]) -> List[ShellyDevice]:
    """
    Convert ip_state.json structure into a list of ShellyDevice objects.

    This is the ONLY place that knows the JSON schema; all other code uses
    the ShellyDevice dataclass and is therefore insulated from schema changes.
    """
    devices: List[ShellyDevice] = []

    version = state.get("version", 1)
    if version not in (1, 2):
        # For future versions, branch here and call dedicated parsers.
        raise RuntimeError(f"Unsupported ip_state version: {version}")

    raw_devices = state.get("devices", {})
    if not isinstance(raw_devices, dict):
        raise ValueError("ip_state.json: 'devices' must be an object/dict")

    for dev_id, raw in raw_devices.items():
        if not isinstance(raw, dict):
            # Defensive: skip malformed entries
            continue

        stage3 = raw.get("stage3") or {}
        stage4 = raw.get("stage4") or {}

        # Legacy stage4 structure (v1)
        s4_kvs = stage4.get("kvs") or {}
        s4_script = stage4.get("script") or {}
        s4_status = stage4.get("status") or {}
        
        # New stage4 structure (v2): status is now top-level in stage4 block
        # Map new "status" field ("ok"/"error") to legacy "result" field
        s4_status_result = s4_status.get("result")
        if s4_status_result is None and "status" in stage4:
            s4_status_result = stage4.get("status")  # "ok" or "error"

        device = ShellyDevice(
            id=str(raw.get("id", dev_id)),
            ip=str(raw.get("ip", "")),
            hostname=str(raw.get("hostname", "")),
            model=str(raw.get("model", "")),
            hw_model=str(raw.get("hw_model", "")),
            fw=str(raw.get("fw", "")),
            friendly_name=str(raw.get("friendly_name", "")),
            room=str(raw.get("room", "")),
            location=str(raw.get("location", "")),
            assigned_at=raw.get("assigned_at"),
            last_seen=raw.get("last_seen"),
            stage3_friendly_status=str(stage3.get("friendly_status", "unknown")),
            stage3_ota_status=str(stage3.get("ota_status", "unknown")),
            stage3_last_run=stage3.get("ts") or stage3.get("last_run"),
            stage4_script_enabled=s4_script.get("enabled"),
            stage4_script_name=s4_script.get("name"),
            stage4_script_file=s4_script.get("file"),
            stage4_status_result=s4_status_result,
            stage4_status_last_run=s4_status.get("last_run") or stage4.get("ts"),
            kvs=dict(s4_kvs),
        )
        devices.append(device)

    # No fixed sort here: sorting is done centrally based on config / CLI.
    return devices


# ---------------------------------------------------------------------------
# Filtering logic (purely offline, no ping)
# ---------------------------------------------------------------------------


def filter_devices(devices: List[ShellyDevice], mode: str) -> List[ShellyDevice]:
    """
    Filter devices according to the given mode.

    All logic is purely based on fields from ip_state.json, no live checks.
    """
    if mode == "all":
        return devices

    if mode == "friendly_ok":
        return [d for d in devices if d.stage3_friendly_status == "ok"]

    if mode == "ota_ok":
        return [d for d in devices if d.stage3_ota_status == "up_to_date"]

    if mode == "script_ok":
        return [d for d in devices if d.stage4_status_result == "ok"]

    if mode == "done":
        # "Done" example: all relevant stages report OK / up_to_date
        return [
            d
            for d in devices
            if d.stage3_friendly_status == "ok"
            and d.stage3_ota_status in ("ok", "up_to_date")
            and d.stage4_status_result == "ok"
        ]

    if mode == "error_only":
        return [
            d
            for d in devices
            if d.stage3_friendly_status != "ok"
            or d.stage3_ota_status not in ("ok", "up_to_date")
            or (d.stage4_status_result not in (None, "ok"))
        ]

    # Fallback: no filtering
    return devices


# ---------------------------------------------------------------------------
# Sorting logic
# ---------------------------------------------------------------------------


def sort_devices(devices: List[ShellyDevice], order: List[str]) -> List[ShellyDevice]:
    """
    Sort devices by a list of fields (ascending or descending).

    Fields prefixed with '-' are sorted descending.
    Example order: ["location", "room", "-model"]

    Implementation uses stable multi-key sorting:
    - we sort by the last key first, then by the previous one, etc.
    """
    if not order:
        return devices

    sorted_devices = devices[:]

    # Apply stable sort field by field, rightmost key first.
    for field in reversed(order):
        reverse = field.startswith("-")
        fname = field[1:] if reverse else field

        sorted_devices.sort(
            key=lambda d: getattr(d, fname, "") or "",
            reverse=reverse,
        )

    return sorted_devices


# ---------------------------------------------------------------------------
# Stdout report
# ---------------------------------------------------------------------------


def get_column_value(device: ShellyDevice, column: str) -> str:
    """
    Resolve a column name to a string value on ShellyDevice.

    Currently supports direct attribute names. This can be extended
    later (e.g. kvs[...] or derived fields) if needed.
    """
    if hasattr(device, column):
        value = getattr(device, column)
    else:
        # Unknown column, return empty string
        value = ""

    if value is None:
        return ""
    return str(value)


def print_stdout_report(devices: List[ShellyDevice], columns: List[str]) -> None:
    """Print a simple, plain-text device report to stdout."""
    # Build a 2D list for simple "dynamic width" formatting
    rows: List[List[str]] = []
    rows.append(columns)
    for d in devices:
        row = [get_column_value(d, col) for col in columns]
        rows.append(row)

    # Determine column widths
    col_widths: List[int] = []
    num_cols = len(columns)
    for idx in range(num_cols):
        max_len = max(len(row[idx]) for row in rows)
        col_widths.append(max_len)

    # Print header
    header_cells = [
        columns[i].ljust(col_widths[i]) for i in range(num_cols)
    ]
    print("  ".join(header_cells))
    print("  ".join("-" * col_widths[i] for i in range(num_cols)))

    # Print rows
    for row in rows[1:]:
        cells = [row[i].ljust(col_widths[i]) for i in range(num_cols)]
        print("  ".join(cells))

    print(f"\nTotal devices: {len(devices)}")


# ---------------------------------------------------------------------------
# CSV / table export
# ---------------------------------------------------------------------------


def export_csv(
    devices: List[ShellyDevice],
    path: Path,
    columns: List[str],
    delimiter: str = ";",
) -> None:
    """Export devices to a CSV file with the given columns."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter=delimiter)
        writer.writerow(columns)
        for d in devices:
            row = [get_column_value(d, col) for col in columns]
            writer.writerow(row)


# ---------------------------------------------------------------------------
# Label generation (band + multiline)
# ---------------------------------------------------------------------------


def _device_context(device: ShellyDevice) -> Dict[str, Any]:
    """
    Build a context dict used for label templates.

    Currently exposes the dataclass __dict__ directly. This can later be
    extended to support kvs[...] access or derived values if needed.
    """
    return dict(device.__dict__)


def build_band_label(device: ShellyDevice, template: str) -> str:
    """Render a one-line band label from a format string."""
    ctx = _device_context(device)
    try:
        return template.format(**ctx)
    except Exception:
        # Defensive: never crash on formatting errors; return a fallback.
        return template


def build_multiline_label_row(
    device: ShellyDevice,
    field_templates: Dict[str, str],
) -> Dict[str, str]:
    """
    Render a dict {column_name: value} for multiline labels based on per-field
    format strings.
    """
    ctx = _device_context(device)
    row: Dict[str, str] = {}
    for col_name, fmt in field_templates.items():
        try:
            row[col_name] = fmt.format(**ctx)
        except Exception:
            row[col_name] = fmt  # fallback: raw template
    return row


def write_band_csv(
    devices: List[ShellyDevice],
    path: Path,
    template: str,
    delimiter: str,
) -> None:
    """Write band labels (single 'label_text' column) to a CSV file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter=delimiter)
        writer.writerow(["label_text"])
        for d in devices:
            writer.writerow([build_band_label(d, template)])


def write_multiline_csv(
    devices: List[ShellyDevice],
    path: Path,
    field_templates: Dict[str, str],
    delimiter: str,
) -> None:
    """Write multiline label CSV (one column per field)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    columns = list(field_templates.keys())
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter=delimiter)
        writer.writerow(columns)
        for d in devices:
            row_map = build_multiline_label_row(d, field_templates)
            writer.writerow([row_map.get(c, "") for c in columns])


# ---------------------------------------------------------------------------
# CLI / argument parsing
# ---------------------------------------------------------------------------


def build_arg_parser(report_cfg: Dict[str, Any]) -> argparse.ArgumentParser:
    """Build the top-level CLI parser with subcommands."""
    parser = argparse.ArgumentParser(
        description="Shelly offline reporting and label generator",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    # Add building argument
    add_building_argument(parser)

    default_filter = report_cfg.get("stdout", {}).get("default_filter", "all")

    sort_cfg = report_cfg.get("sort", {})
    default_sort = sort_cfg.get("default_order", [])

    sub = parser.add_subparsers(dest="command", required=True)

    # report
    p_report = sub.add_parser("report", help="Print a simple report to stdout")
    p_report.add_argument(
        "--filter",
        default=default_filter,
        choices=["all", "friendly_ok", "ota_ok", "script_ok", "done", "error_only"],
        help="Filter devices based on provisioning status",
    )
    p_report.add_argument(
        "--columns",
        nargs="+",
        help="Override default stdout columns from config.yaml",
    )
    p_report.add_argument(
        "--sort",
        nargs="+",
        default=default_sort,
        help="Sort devices by one or more fields (e.g. --sort location room -model)",
    )

    # export
    p_export = sub.add_parser("export", help="Export device table (CSV)")
    p_export.add_argument(
        "--filter",
        default=default_filter,
        choices=["all", "friendly_ok", "ota_ok", "script_ok", "done", "error_only"],
        help="Filter devices before export",
    )
    p_export.add_argument(
        "--format",
        choices=["csv"],  # XLSX can be added later
        default=report_cfg.get("export", {}).get("default_format", "csv"),
        help="Export format (currently only csv is implemented)",
    )
    p_export.add_argument(
        "--basename",
        default="shelly_export",
        help="Base filename (without extension) for export file",
    )
    p_export.add_argument(
        "--columns",
        nargs="+",
        help="Override default export columns from config.yaml",
    )
    p_export.add_argument(
        "--sort",
        nargs="+",
        default=default_sort,
        help="Sort devices by one or more fields (e.g. --sort location room -model)",
    )

    # labels
    p_labels = sub.add_parser("labels", help="Generate label CSVs for DYMO")
    p_labels.add_argument(
        "--filter",
        default=default_filter,
        choices=["all", "friendly_ok", "ota_ok", "script_ok", "done", "error_only"],
        help="Filter devices before label generation",
    )
    p_labels.add_argument(
        "--mode",
        choices=["multiline", "band"],
        help="Label mode (overrides report.labels.default_mode)",
    )
    p_labels.add_argument(
        "--template",
        help="Template name from config 'report.labels.templates'",
    )
    p_labels.add_argument(
        "--basename",
        help="Override default label basename from config",
    )
    p_labels.add_argument(
        "--sort",
        nargs="+",
        default=default_sort,
        help="Sort devices by one or more fields (e.g. --sort location room -model)",
    )

    return parser


# ---------------------------------------------------------------------------
# main()
# ---------------------------------------------------------------------------


def main() -> int:
    """Entry point for CLI."""
    # First parse only --building to get paths
    preliminary_parser = argparse.ArgumentParser(add_help=False)
    add_building_argument(preliminary_parser)
    prelim_args, _ = preliminary_parser.parse_known_args()
    
    # Require building
    try:
        building = require_building(prelim_args.building)
    except BuildingError as e:
        print(f"{COLOR_RED}ERROR: {e}{COLOR_RESET}", file=sys.stderr)
        return 1
    
    # Get paths for building
    paths = get_building_paths(building)
    config_path = paths['config']

    # Load configuration and build full parser with defaults
    cfg = load_config(config_path)
    report_cfg = cfg["report"]

    parser = build_arg_parser(report_cfg)
    args = parser.parse_args()

    # Paths from config (relative to building's stagebox root)
    project_root = paths['stagebox_root']
    
    def resolve_path(p: str) -> Path:
        """Resolve path relative to project root."""
        path = Path(p)
        if path.is_absolute():
            return path
        return project_root / path
    
    state_file = resolve_path(report_cfg["state_file"])
    output_cfg = report_cfg["output"]
    table_dir = resolve_path(output_cfg["table_dir"])
    labels_dir = resolve_path(output_cfg["labels_dir"])

    # Load state and build devices (offline only)
    state = load_ip_state(state_file)
    devices = build_devices_from_state(state)

    # Subcommand: report
    if args.command == "report":
        filtered = filter_devices(devices, args.filter)

        # Sorting
        sort_order = args.sort or report_cfg.get("sort", {}).get("default_order", [])
        if sort_order:
            filtered = sort_devices(filtered, sort_order)

        stdout_cfg = report_cfg.get("stdout", {})
        columns = args.columns or stdout_cfg.get("default_columns") or [
            "location",
            "room",
            "model",
            "ip",
            "hostname",
            "friendly_name",
        ]
        print_stdout_report(filtered, columns)

    # Subcommand: export
    elif args.command == "export":
        filtered = filter_devices(devices, args.filter)

        # Sorting
        sort_order = args.sort or report_cfg.get("sort", {}).get("default_order", [])
        if sort_order:
            filtered = sort_devices(filtered, sort_order)

        export_cfg = report_cfg.get("export", {})
        columns = args.columns or export_cfg.get("default_columns") or [
            "id",
            "ip",
            "hostname",
            "model",
            "friendly_name",
        ]
        if args.format == "csv":
            delimiter = export_cfg.get("csv_delimiter", ";")
            out_path = table_dir / f"{args.basename}.csv"
            export_csv(filtered, out_path, columns, delimiter=delimiter)
            print(f"Exported CSV to {out_path}")
        else:
            # Currently not implemented; placeholder for future XLSX export.
            raise NotImplementedError("Only CSV export is implemented at the moment")

    # Subcommand: labels
    elif args.command == "labels":
        filtered = filter_devices(devices, args.filter)

        # Sorting
        sort_order = args.sort or report_cfg.get("sort", {}).get("default_order", [])
        if sort_order:
            filtered = sort_devices(filtered, sort_order)

        labels_cfg = report_cfg.get("labels", {})
        templates_cfg = labels_cfg.get("templates", {})

        if not templates_cfg:
            raise RuntimeError("config.yaml: 'report.labels.templates' is empty or missing")

        # Determine template
        if args.template:
            tmpl_name = args.template
        else:
            # Use first template as fallback if default is not set
            default_tmpl_name = labels_cfg.get("default_template")
            tmpl_name = default_tmpl_name or next(iter(templates_cfg.keys()))

        if tmpl_name not in templates_cfg:
            raise RuntimeError(f"Unknown label template: {tmpl_name}")

        tmpl = templates_cfg[tmpl_name]

        # Determine mode
        mode = args.mode or labels_cfg.get("default_mode", "multiline")
        if mode not in ("multiline", "band"):
            raise RuntimeError(f"Invalid label mode: {mode}")

        # Determine basename
        basename = args.basename or labels_cfg.get("default_basename", "shelly_labels")

        delimiter = report_cfg.get("export", {}).get("csv_delimiter", ";")

        if mode == "band":
            text_template = tmpl.get("text")
            if not isinstance(text_template, str):
                raise RuntimeError(
                    f"Template '{tmpl_name}' must define 'text' for band mode"
                )
            out_path = labels_dir / f"{basename}_band.csv"
            write_band_csv(filtered, out_path, text_template, delimiter)
            print(f"Wrote band label CSV to {out_path}")
        else:
            field_templates = tmpl.get("fields")
            if not isinstance(field_templates, dict):
                raise RuntimeError(
                    f"Template '{tmpl_name}' must define 'fields' for multiline mode"
                )
            out_path = labels_dir / f"{basename}.csv"
            write_multiline_csv(filtered, out_path, field_templates, delimiter)
            print(f"Wrote multiline label CSV to {out_path}")
    else:
        # Should not happen due to argparse 'required=True'
        parser.error("No command specified")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())