"""
Stage 2 provisioning core logic for Shelly Gen2+ devices.

This module is API-first and independent of any CLI or Flask UI.
It is designed to be used from:

- scripts/shelly_stage2.py (CLI)
- web/ (Flask endpoints) later on

Responsibilities:
- Identify a single device (Device.GetInfo, Sys.GetConfig, etc.)
- Read current network configuration (Wifi.GetConfig)
- Compute a high-level result structure describing:
  - identity
  - current network state
  - potential / planned changes
- Apply changes in an idempotent manner:
  - only reconfigure when necessary
  - only touch network configuration inside well-defined constraints
- Update ip_state.json (via State) accordingly

The design follows a “single source of truth” approach for IP allocation:
- ip_state.json is authoritative for which IPs are in use in the pool.
- No network scanning or ping heuristics are used to guess free IPs.
- The configured pool range, ip_map, and ip_state.json together determine
  which IPs may be assigned.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional, Tuple, Callable

import datetime

# ---------------------------------------------------------------------------
# Type assumptions for RpcClient and State
# ---------------------------------------------------------------------------

# NOTE:
# These imports assume you have (or will have) these modules.
# If your actual modules differ, adjust the imports and type hints accordingly.
try:
    from core.rpc import RpcClient  # type: ignore
except ImportError:  # pragma: no cover - for early design phase
    class RpcClient:  # type: ignore
        """Fallback placeholder for type checking during early design."""

        def call(self, method: str, params: Dict[str, Any] | None = None) -> Dict[str, Any]:
            raise NotImplementedError

RpcFactory = Callable[[str], RpcClient]

try:
    from core.state import State  # type: ignore
except ImportError:  # pragma: no cover
    class State:  # type: ignore
        """Fallback placeholder for type checking during early design.

        Expected minimal interface (to be refined):

            def get_ip_entry(self, ip: str) -> Optional[Dict[str, Any]]: ...
            def update_ip_entry(self, ip: str, data: Dict[str, Any]) -> None: ...
            def save(self) -> None: ...
        """

        def get_ip_entry(self, ip: str) -> Optional[Dict[str, Any]]:
            raise NotImplementedError

        def update_ip_entry(self, ip: str, data: Dict[str, Any]) -> None:
            raise NotImplementedError

        def save(self) -> None:
            raise NotImplementedError


# ---------------------------------------------------------------------------
# Stage 2 Options / Config
# ---------------------------------------------------------------------------


@dataclass
class Stage2Options:
    """
    High-level configuration object for Stage 2.

    This is derived from secrets.yaml (stage2 section) and CLI/Web options.
    """

    network_profile: str                 # logical name, falls du Profile verwendest
    network: Dict[str, Any]              # concrete network config (pool, gw, etc.)
    hostname: Dict[str, Any]             # hostname config (prefix mapping etc.)
    wifi_profiles: List[Dict[str, Any]]  # SSID/password pairs from secrets.yaml
    model_mapping: Dict[str, str]        # hw_model -> friendly name mapping

    static_ip: str
    room: str
    location: str
    friendly_name: str
    dry_run: bool
    force_reconfigure: bool
    expected_building_id: str
    expected_vlan: str
    scan_cidr: str
    scan_exclude_pool: bool

def _normalize_options(options: Optional[Dict[str, Any]]) -> Stage2Options:
    """Normalize incoming options dict into a Stage2Options dataclass.

    This function is tolerant to missing keys; reasonable defaults are applied.
    """
    opts = options or {}
    network_cfg = opts.get("network", {}) or {}
    hostname_cfg = opts.get("hostname", {}) or {}

    return Stage2Options(
        network_profile=opts.get("network_profile", "default_sta"),
        network=network_cfg,
        hostname=hostname_cfg,
        wifi_profiles=opts.get("wifi_profiles", []) or [],
        model_mapping=opts.get("model_mapping", {}) or {},
        static_ip=network_cfg.get("static_ip", ""),
        room=opts.get("room", ""),
        location=opts.get("location", ""),
        friendly_name=opts.get("friendly_name", ""),
        dry_run=bool(opts.get("dry_run", False)),
        force_reconfigure=bool(opts.get("force_reconfigure", False)),
        expected_building_id=opts.get("expected_building_id", ""),
        expected_vlan=opts.get("expected_vlan", ""),
        scan_cidr=network_cfg.get("scan_cidr", ""),          
        scan_exclude_pool=bool(network_cfg.get("scan_exclude_pool", True)), 
    )


# ---------------------------------------------------------------------------
# Result structure
# ---------------------------------------------------------------------------


@dataclass
class Stage2Error:
    code: str
    message: str
    detail: Dict[str, Any]


@dataclass
class Stage2Warning:
    code: str
    message: str
    detail: Dict[str, Any]


@dataclass
class NetworkActionResult:
    changed: bool
    applied: bool
    methods_called: List[str]
    changes: Dict[str, Any]


@dataclass
class IpStateActionResult:
    changed: bool
    fields: Dict[str, Dict[str, Any]]  # field -> {old, new}


@dataclass
class Stage2Result:
    ok: bool
    stage: str
    ip: Optional[str]
    device_id: Optional[str]
    mac: Optional[str]
    model: Optional[str]
    hostname: Optional[str]
    actions: Dict[str, Any]
    errors: List[Stage2Error]
    warnings: List[Stage2Warning]
    meta: Dict[str, Any]


def _empty_stage2_result(ip: str) -> Stage2Result:
    return Stage2Result(
        ok=False,
        stage="stage2",
        ip=ip,
        device_id=None,
        mac=None,
        model=None,
        hostname=None,
        actions={
            "network": {
                "changed": False,
                "applied": False,
                "methods_called": [],
                "changes": {},
            },
            "ip_state": {
                "changed": False,
                "fields": {},
            },
        },
        errors=[],
        warnings=[],
        meta={
            "dry_run": False,
            "force_reconfigure": False,
            "network_profile": "",
            "network_mode": "",
            "run_ts": None,
        },
    )


from typing import Any

def _empty_network_action_result() -> Dict[str, Any]:
    """Create an empty network action result as plain dict."""
    return {
        "changed": False,
        "applied": False,
        "methods_called": [],
        "changes": {},
    }


def _empty_ip_state_action_result() -> Dict[str, Any]:
    """Create an empty ip_state action result as plain dict."""
    return {
        "changed": False,
        "fields": {},
    }

def _add_error(
    errors: List[Stage2Error],
    code: str,
    message: str,
    detail: Optional[Dict[str, Any]] = None,
) -> None:
    errors.append(Stage2Error(code=code, message=message, detail=detail or {}))


def _add_warning(
    warnings: List[Stage2Warning],
    code: str,
    message: str,
    detail: Optional[Dict[str, Any]] = None,
) -> None:
    warnings.append(Stage2Warning(code=code, message=message, detail=detail or {}))


# ---------------------------------------------------------------------------
# Device identity representation
# ---------------------------------------------------------------------------


@dataclass
class DeviceIdentity:
    ip: str
    device_id: Optional[str] = None
    mac: Optional[str] = None
    model: Optional[str] = None
    fw_ver: Optional[str] = None
    hw_model: Optional[str] = None
    hostname: Optional[str] = None

    @classmethod
    def from_rpc(
        cls,
        ip: str,
        device_info: Dict[str, Any],
        sys_config: Optional[Dict[str, Any]] = None,
    ) -> "DeviceIdentity":
        """Build a DeviceIdentity from Shelly.GetDeviceInfo and Sys.GetConfig results."""
        hostname = None
        if sys_config is not None:
            hostname = (
                sys_config.get("device", {}).get("hostname")
                or sys_config.get("sys", {}).get("device", {}).get("hostname")
            )

        # Shelly Gen2 / Plus typically uses:
        #  - id      -> device id (e.g. shellyplus1pm-...)
        #  - mac     -> MAC address
        #  - model   -> hardware model code (e.g. SNSW-001P16EU)
        #  - ver     -> firmware version (e.g. 1.2.3)
        #  - fw_id   -> full build id
        #  - app     -> app / product short name
        device_id = device_info.get("id")
        mac = device_info.get("mac")
        hw_model = device_info.get("model")
        fw_ver = device_info.get("ver") or device_info.get("fw_id") or device_info.get("fw")

        # We keep "model" as user-facing friendly name; for now use hw_model,
        # später mappen wir hw_model -> hübscher Name via model_mapping.
        model = hw_model or device_info.get("app")

        return cls(
            ip=ip,
            device_id=device_id,
            mac=mac,
            model=model,
            fw_ver=fw_ver,
            hw_model=hw_model,
            hostname=hostname,
        )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def stage2_discover_and_adopt(
    rpc_factory: RpcFactory,
    state: State,
    options: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Discover Shelly devices in the configured CIDR and adopt them into the pool.

    Semantics:
      - CIDR comes from options.network['scan_cidr'] (or derived from gateway/netmask)
      - Only hosts OUTSIDE the pool range are scanned (if scan_exclude_pool=True).
      - For each IP:
          * Try Shelly.GetDeviceInfo
          * If Shelly is found:
              - If MAC already has a pool IP in ip_state -> Stage2 will re-apply this pool IP.
              - If MAC is unknown in ip_state -> Stage2 will assign a new free pool IP.

    ip_state.json remains pool-only: no DHCP/out-of-pool IPs are written.
    """
    opts = _normalize_options(options or {})
    network_cfg = opts.network or {}

    # Get state file path for reloading during adopt loop
    state_file_path = network_cfg.get("state_file", "data/ip_state.json")

    cidr = network_cfg.get("scan_cidr") or opts.scan_cidr
    pool_start = network_cfg.get("pool_start", "192.168.1.30")
    pool_end = network_cfg.get("pool_end", "192.168.1.60")

    result_summary: Dict[str, Any] = {
        "ok": True,
        "devices": {},  # ip -> Stage2Result dict
        "meta": {
            "cidr": cidr,
            "pool_start": pool_start,
            "pool_end": pool_end,
            "scan_candidates": 0,
            "found_shellys": 0,
            "adopted": 0,
            "errors": 0,
        },
    }

#DEBUG, remove later
#    print(f"[ADOPT-CORE] cidr={cidr!r}, pool_start={pool_start}, pool_end={pool_end}, "
#        f"exclude_pool={opts.scan_exclude_pool}")

    if not cidr:
        result_summary["ok"] = False
        result_summary["meta"]["error"] = "no_scan_cidr_configured"
        return result_summary

    # Build scan candidate IPs: all hosts in cidr minus pool range
    scan_ips = _iter_cidr_hosts_excluding_pool(
        cidr=cidr,
        pool_start=pool_start,
        pool_end=pool_end,
        exclude_pool=opts.scan_exclude_pool,
    )
    
    # Optional DHCP range restriction
    dhcp_start = network_cfg.get("dhcp_scan_start")
    dhcp_end = network_cfg.get("dhcp_scan_end")

    if dhcp_start and dhcp_end:
        try:
            dhcp_start_ip = ipaddress.IPv4Address(dhcp_start)
            dhcp_end_ip = ipaddress.IPv4Address(dhcp_end)

            def _in_dhcp_range(ip_str: str) -> bool:
                ip = ipaddress.IPv4Address(ip_str)
                return dhcp_start_ip <= ip <= dhcp_end_ip

            scan_ips = [ip for ip in scan_ips if _in_dhcp_range(ip)]
            result_summary["meta"]["dhcp_scan_start"] = str(dhcp_start_ip)
            result_summary["meta"]["dhcp_scan_end"] = str(dhcp_end_ip)

        except ValueError:
            # Invalid DHCP range config -> keep full scan_ips and mark meta error
            result_summary["ok"] = False
            result_summary["meta"]["error"] = "invalid_dhcp_scan_range"
            result_summary["meta"]["dhcp_scan_start"] = dhcp_start
            result_summary["meta"]["dhcp_scan_end"] = dhcp_end

    result_summary["meta"]["scan_candidates"] = len(scan_ips)

#DEBUG, remove later
#    print(f"[ADOPT-CORE] scan_ips_count={len(scan_ips)}")

    devices_results: Dict[str, Any] = {}
    found_shellys = 0
    adopted = 0
    error_count = 0

    for ip in scan_ips:
        # Build RpcClient bound to this IP
        rpc_client = rpc_factory(ip)

        # Try Shelly.GetDeviceInfo as discovery probe
        errors: list[Stage2Error] = []
        probe = _rpc_call(
            rpc_client=rpc_client,
            target_ip=ip,
            method="Shelly.GetDeviceInfo",
            params={},
            timeout=network_cfg.get("rpc_timeout_s", 5.0),
            errors=errors,
            optional=True,  # do not fail the whole run if this IP is not a Shelly
        )

        if not probe or not isinstance(probe, dict) or not probe.get("id") or not probe.get("mac"):
            # Not a Shelly, or no useful identity -> skip
            continue

        found_shellys += 1

        # Now run full Stage 2 for this IP (which will handle pool IP assignment)
        try:
            # Reload state to see IP assignments from previous devices in this adopt run
            # This prevents IP collisions when multiple devices are adopted simultaneously
            from core.state import load_state
            state = load_state(str(state_file_path))
            
            stage2_res = stage2_configure_device_by_ip(
                rpc_client=rpc_client,
                state=state,
                target_ip=ip,
                options=options,
            )
            devices_results[ip] = _stage2_result_to_dict(stage2_res)
            if stage2_res.ok:
                adopted += 1
            else:
                error_count += 1
                result_summary["ok"] = False
        except Exception as exc:
            error_count += 1
            result_summary["ok"] = False
            devices_results[ip] = {
                "ok": False,
                "stage": "stage2",
                "ip": ip,
                "errors": [
                    {
                        "code": "adopt_exception",
                        "message": "Exception during Stage 2 adopt run",
                        "detail": {"exception": repr(exc)},
                    }
                ],
            }

    result_summary["devices"] = devices_results
    result_summary["meta"]["found_shellys"] = found_shellys
    result_summary["meta"]["adopted"] = adopted
    result_summary["meta"]["errors"] = error_count

    return result_summary


def stage2_configure_device_by_ip(
    rpc_client: RpcClient,
    state: State,
    target_ip: str,
    options: Optional[Stage2Options] = None,
) -> Stage2Result:
    """Run Stage 2 provisioning for a single device at a given IP.

    This is the main entry point used by CLI and Web layers.
    """
    opts = _normalize_options(options or {})
    result = _empty_stage2_result(target_ip)

    errors: List[Stage2Error] = []
    warnings: List[Stage2Warning] = []

    result.meta["dry_run"] = opts.dry_run
    result.meta["force_reconfigure"] = opts.force_reconfigure
    result.meta["network_profile"] = opts.network_profile
    result.meta["run_ts"] = datetime.datetime.utcnow().isoformat()

    timeout = float(opts.network.get("rpc_timeout_s", 5.0))

    # 1) Identity RPC calls
    try:
        device_info = _rpc_call(
            rpc_client,
            target_ip,
            method="Shelly.GetDeviceInfo",
            params={},
            timeout=timeout,
            errors=errors,
        )
        if device_info is None:
            _add_error(
                errors,
                code="rpc_error",
                message="Shelly.GetDeviceInfo returned no data",
                detail={"ip": target_ip},
            )
            result.errors = errors
            return result

        sys_config = _rpc_call(
            rpc_client,
            target_ip,
            method="Sys.GetConfig",
            params={},
            timeout=timeout,
            errors=errors,
            optional=True,
        )

        identity = DeviceIdentity.from_rpc(target_ip, device_info, sys_config)

    except Exception as exc:
        _add_error(
            errors,
            code="device_unreachable",
            message=f"Failed to reach device at {target_ip}",
            detail={"exception": repr(exc)},
        )
        result.errors = errors
        return result

    # 1b) Model mapping (hw_model -> friendly name)
    raw_model = (
        identity.hw_model
        or device_info.get("hw_model")
        or device_info.get("model")
        or identity.model
    )
    mapped_model = None
    if raw_model and opts.model_mapping:
        mapped_model = opts.model_mapping.get(raw_model)
        if mapped_model:
            _add_warning(
                warnings,
                code="model_mapped",
                message="Mapped hardware model to friendly name",
                detail={"raw_model": raw_model, "friendly_model": mapped_model},
            )
            identity.model = mapped_model
        else:
            identity.model = raw_model
    else:
        identity.model = raw_model

    result.device_id = identity.device_id
    result.mac = identity.mac
    result.model = identity.model
    result.hostname = identity.hostname

    # 2) Network config RPC call
    wifi_cfg = _rpc_call(
        rpc_client,
        target_ip,
        method="WiFi.GetConfig",
        params={},
        timeout=timeout,
        errors=errors,
        optional=False,
    )

    if wifi_cfg is None:
        _add_error(
            errors,
            code="wifi_getconfig_failed",
            message="WiFi.GetConfig returned no data",
            detail={"ip": target_ip},
        )
        result.errors = errors
        result.warnings = warnings
        return result

    # 2b) Snapshot current WiFi config for meta/debug
    result.meta["wifi_config_snapshot"] = wifi_cfg
    result.meta["current_ip"] = identity.ip

    # 3) IP allocation from pool based on ip_state.json
    ip_state_snapshot = _get_ip_state_snapshot(state)

    # Pool-Statistik berechnen (für Meta/CLI)
    pool_stats = _compute_pool_stats(opts.network, ip_state_snapshot)
    result.meta["pool_start"] = pool_stats["pool_start"]
    result.meta["pool_end"] = pool_stats["pool_end"]
    result.meta["pool_total"] = pool_stats["total"]
    result.meta["pool_used"] = pool_stats["used"]
    result.meta["pool_free"] = pool_stats["free"]

    assigned_ip, ip_reason, suggested_entry = _assign_ip_from_pool(
        identity, opts.network, ip_state_snapshot
    )
    result.meta["assigned_ip"] = assigned_ip
    result.meta["ip_decision_reason"] = ip_reason

    # 4) Compute network changes (static IP vs DHCP)
    network_action = _compute_network_changes(
        identity=identity,
        wifi_cfg=wifi_cfg,
        assigned_ip=assigned_ip,
        network_cfg=opts.network,
    )

    # 5) Apply network changes if needed and not in dry_run
    if not opts.dry_run and network_action["changed"] and assigned_ip:
        apply_result = _apply_network_changes(
            rpc_client=rpc_client,
            identity=identity,
            wifi_cfg=wifi_cfg,
            assigned_ip=assigned_ip,
            network_cfg=opts.network,
            wifi_profiles=opts.wifi_profiles,
            timeout=timeout,
            errors=errors,
            warnings=warnings,
        )
        network_action.update(apply_result)
    else:
        # No network change necessary or dry-run; keep "applied" False
        if opts.dry_run and network_action["changed"]:
            network_action["applied"] = False
            network_action.setdefault("methods_called", []).append(
                "WiFi.SetConfig (dry_run)"
            )

    # 6) Hostname changes (optional, based on hostname config)
    hostname_cfg = opts.hostname or {}
    if hostname_cfg:
        hostname_action = _compute_hostname_changes(identity, hostname_cfg)
        if hostname_action["changed"] and not opts.dry_run:
            hostname = hostname_action["new"]
            try:
                _rpc_call(
                    rpc_client,
                    target_ip,
                    method="Sys.SetConfig",
                    params={"config": {"device": {"hostname": hostname}}},
                    timeout=timeout,
                    errors=errors,
                    optional=True,
                )
                identity.hostname = hostname
            except Exception as exc:
                _add_warning(
                    warnings,
                    code="hostname_set_failed",
                    message="Failed to set hostname via Sys.SetConfig",
                    detail={"ip": target_ip, "exception": repr(exc)},
                )
        elif hostname_action["changed"] and opts.dry_run:
            identity.hostname = hostname_action["new"]

    # 7) Update ip_state via State
    # Determine run_status based on errors
    run_status = "ok" if not errors else "error"
    
    ip_state_action = _update_ip_state(
        state=state,
        identity=identity,
        assigned_ip=assigned_ip,
        suggested_entry=suggested_entry,
        dry_run=opts.dry_run,
        errors=errors,
        warnings=warnings,
        run_status=run_status,
    )

    # 8) Final result aggregation
    result.actions["network"] = network_action
    result.actions["ip_state"] = ip_state_action
    result.errors = errors
    result.warnings = warnings

    result.ok = not errors
    result.ip = assigned_ip or identity.ip

    # keep identity info in result
    result.device_id = identity.device_id
    result.mac = identity.mac
    result.model = identity.model
    result.hostname = identity.hostname

    return result


def stage2_configure_many(
    rpc_client: RpcClient,
    state: State,
    device_selector: Dict[str, Any],
    options: Optional[Stage2Options] = None,
) -> Dict[str, Any]:
    """Run Stage 2 for multiple devices.

    This is a higher-level API suitable for:
    - CLI "broadcast" runs
    - Flask endpoints like POST /api/stage2/run

    The current minimal implementation is intentionally simple:
    - Expects `device_selector` to contain an explicit list of IPs:
        { "ips": ["10.1.2.3", "10.1.2.4", ...] }
    - Invokes `stage2_configure_device_by_ip` for each IP.
    - Aggregates results into a summary structure.

    Later iterations can:
    - Support selectors by building, room, tags, "only_unprovisioned", etc.
    - Use State to derive IP/device lists based on richer filters.
    """
    opts = _normalize_options(options)
    ips: List[str] = list(device_selector.get("ips", []))

    devices_results: Dict[str, Stage2Result] = {}
    total_ok = True
    changed_count = 0  # placeholder for later, when we compute real changes

    for ip in ips:
        res = stage2_configure_device_by_ip(
            rpc_client=rpc_client,
            state=state,
            target_ip=ip,
            options=opts,
        )
        devices_results[ip] = res
        if not res.ok:
            total_ok = False

    return {
        "ok": total_ok,
        "devices": {ip: _stage2_result_to_dict(r) for ip, r in devices_results.items()},
        "meta": {
            "count": len(ips),
        },
    }


def _stage2_result_to_dict(result: Stage2Result) -> Dict[str, Any]:
    """Convert Stage2Result dataclass with nested types into a plain dict.

    This is useful for JSON serialization in Flask or logging.
    """
    return {
        "ok": result.ok,
        "stage": result.stage,
        "ip": result.ip,
        "device_id": result.device_id,
        "mac": result.mac,
        "model": result.model,
        "hostname": result.hostname,
        "actions": {
            "network": result.actions.get("network", {}),
            "ip_state": result.actions.get("ip_state", {}),
        },
        "errors": [asdict(e) for e in result.errors],
        "warnings": [asdict(w) for w in result.warnings],
        "meta": result.meta,
    }


# ---------------------------------------------------------------------------
# Helper functions: IP / network logic
# ---------------------------------------------------------------------------


def _get_ip_state_snapshot(state: State) -> Dict[str, Dict[str, Any]]:
    """Create a snapshot of all ip_state entries keyed by MAC.

    Unterstützt zwei Layouts:

    1) Flache Struktur (bereits normalisiert):
       {
         "AABBCCDD0011": { ... },
         "AABBCCDD0022": { ... }
       }

    2) Versioniertes Layout wie in ip_state.json:
       {
         "version": 1,
         "devices": {
           "AABBCCDD0011": { ... },
           "AABBCCDD0022": { ... }
         }
       }

    Es werden ausschließlich die Einträge unterhalb von "devices" bzw.
    auf oberster Ebene (bei flacher Struktur) als MAC→Entry-Snapshot
    zurückgegeben.
    """
    raw_snapshot: Dict[str, Any] = {}

    # Try different methods to get data from State
    if hasattr(state, "devices"):
        try:
            # State has 'devices' property (new API)
            raw_snapshot = {"devices": state.devices}
        except Exception as exc:
            print(f"[Stage2] Failed to read state.devices: {exc}")
            return {}
    elif hasattr(state, "get_all_ip_entries"):
        try:
            # Fallback for old API
            # type: ignore[attr-defined]
            raw = state.get_all_ip_entries()

            if isinstance(raw, dict):
                raw_snapshot = raw
        except Exception as exc:
            print(f"[Stage2] Failed to read ip_state from State: {exc}")
            return {}

    # Fallback: falls State keine Methode anbietet oder nichts liefert
    if not raw_snapshot:
        return {}

    # Variante 2: versioniertes Layout mit "devices"
    if "devices" in raw_snapshot and isinstance(raw_snapshot["devices"], dict):
        devices = raw_snapshot["devices"]
    else:
        # Variante 1: flache Struktur
        devices = raw_snapshot

    snapshot: Dict[str, Dict[str, Any]] = {}
    for mac, entry in devices.items():
        if isinstance(entry, dict):
            snapshot[str(mac)] = dict(entry)
    
    return snapshot


from ipaddress import IPv4Address


def _assign_ip_from_pool(
    identity: DeviceIdentity,
    network_cfg: Dict[str, Any],
    ip_state_snapshot: Dict[str, Dict[str, Any]],
) -> tuple[Optional[str], str, Dict[str, Any]]:
    """Assign an IP from the pool to the given device, purely based on ip_state.json.

    No network scanning or ping heuristics are used. We make the following
    assumptions:

      - ip_state.json is the single source of truth for device IP assignments
        inside the configured pool.
      - Any IP present in ip_state.json is considered "in use".
      - Any IP inside the pool that is not present in ip_state.json is considered
        free and may be assigned.

    Returns:
        (assigned_ip, reason, suggested_entry_for_mac)

    Reasons:
      - "static_assigned": ip was taken from ip_map, ip_state, or newly assigned
      - "no_pool_available": no free IP found in the pool
      - "dhcp_in_pool": (optional; currently not used in this strict mode)
    """

    mac = identity.mac or ""
    current_ip = identity.ip
    model = identity.model or ""
    hostname = identity.hostname or ""

    pool_start = network_cfg.get("pool_start", "192.168.1.30")
    pool_end = network_cfg.get("pool_end", "192.168.1.60")

    # Bug fix: Normalize MAC for lookup (uppercase, no separators)
    # This prevents IP collision when MAC format differs between device response
    # and ip_state.json storage format
    mac_normalized = mac.upper().replace(":", "").replace("-", "") if mac else ""
    existing = (
        ip_state_snapshot.get(mac_normalized)
        or ip_state_snapshot.get(mac)
        or ip_state_snapshot.get(mac.upper() if mac else "")
        or ip_state_snapshot.get(mac.lower() if mac else "")
        or {}
    )

    suggested_entry = dict(existing)

    # 1) Explicit MAC->IP mapping via ip_map has highest priority
    ip_map = network_cfg.get("ip_map") or {}
    if isinstance(ip_map, dict):
        forced_ip = ip_map.get(mac) or ip_map.get(mac.upper()) or ip_map.get(mac.lower())
        if forced_ip:
            suggested_entry["ip"] = forced_ip
            suggested_entry["model"] = model or suggested_entry.get("model", "")
            suggested_entry["hostname"] = hostname or suggested_entry.get("hostname", "")
            return forced_ip, "static_assigned", suggested_entry

    # 2) Reuse existing ip_state assignment for this MAC if it lies in the pool
    assigned_ip = existing.get("ip")
    if assigned_ip:
        try:
            ip_obj = IPv4Address(assigned_ip)
            start_obj = IPv4Address(pool_start)
            end_obj = IPv4Address(pool_end)
            if start_obj <= ip_obj <= end_obj:
                suggested_entry["ip"] = assigned_ip
                suggested_entry["model"] = model or suggested_entry.get("model", "")
                suggested_entry["hostname"] = hostname or suggested_entry.get("hostname", "")
                return assigned_ip, "static_assigned", suggested_entry
        except Exception:
            # invalid IP format in ip_state; ignore and continue
            pass

    # 3) Otherwise: first IP in pool not present in ip_state.json
    used_ips = {
        str(entry.get("ip"))
        for entry in ip_state_snapshot.values()
        if isinstance(entry, dict) and entry.get("ip")
    }

    for candidate in _iter_pool_ips(pool_start, pool_end):
        if candidate in used_ips:
            continue
        suggested_entry["ip"] = candidate
        suggested_entry["model"] = model or suggested_entry.get("model", "")
        suggested_entry["hostname"] = hostname or suggested_entry.get("hostname", "")
        return candidate, "static_assigned", suggested_entry

    # 4) No free IP in pool according to ip_state.json
    return None, "no_pool_available", suggested_entry

def _compute_pool_stats(
    network_cfg: Dict[str, Any],
    ip_state_snapshot: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    """Compute simple statistics for the configured pool based on ip_state.json.

    Liefert:
      - pool_start / pool_end
      - total: Anzahl IPs im Pool
      - used:  Anzahl IPs aus ip_state, die im Pool liegen
      - free:  total - used (niemals negativ)
    """
    pool_start = network_cfg.get("pool_start", "192.168.1.30")
    pool_end = network_cfg.get("pool_end", "192.168.1.60")

    # Alle IPs im Pool
    pool_ips = set(_iter_pool_ips(pool_start, pool_end))

    # Belegte IPs aus ip_state.json, aber nur, wenn sie im Pool liegen
    used_ips = {
        str(entry.get("ip"))
        for entry in ip_state_snapshot.values()
        if isinstance(entry, dict)
        and entry.get("ip") in pool_ips
    }

    total = len(pool_ips)
    used = len(used_ips)
    free = max(total - used, 0)

    return {
        "pool_start": pool_start,
        "pool_end": pool_end,
        "total": total,
        "used": used,
        "free": free,
    }

def _iter_pool_ips(start: str, end: str) -> List[str]:
    """Iterate IPv4 addresses in [start, end] inclusive."""
    import ipaddress

    start_obj = ipaddress.IPv4Address(start)
    end_obj = ipaddress.IPv4Address(end)
    if start_obj > end_obj:
        start_obj, end_obj = end_obj, start_obj

    ips: List[str] = []
    cur = start_obj
    while cur <= end_obj:
        ips.append(str(cur))
        cur += 1
    return ips

import ipaddress
def _iter_cidr_hosts_excluding_pool(
    cidr: str,
    pool_start: str,
    pool_end: str,
    exclude_pool: bool = True,
) -> list[str]:
    """Return list of IPv4 host addresses in cidr, optionally excluding pool range."""
    try:
        net = ipaddress.IPv4Network(cidr, strict=False)
    except Exception:
        return []

    pool_ips: set[str] = set(_iter_pool_ips(pool_start, pool_end)) if exclude_pool else set()

    hosts: list[str] = []
    for host in net.hosts():
        ip_str = str(host)
        if exclude_pool and ip_str in pool_ips:
            continue
        hosts.append(ip_str)
    return hosts

def _compute_network_changes(
    identity: DeviceIdentity,
    wifi_cfg: Dict[str, Any],
    assigned_ip: Optional[str],
    network_cfg: Dict[str, Any],
) -> Dict[str, Any]:
    """Compute whether a network change is required to enforce static IP.

    Wir setzen die gleiche statische IP-Konfiguration für:
      - sta  (primäres STA-Profil)
      - sta1 (sekundäres STA-Profil), falls vorhanden/aktiv

    Dadurch bleibt das Gerät auch bei einem Fallback auf sta1 statisch.
    """
    res: Dict[str, Any] = {
        "changed": False,
        "applied": False,
        "methods_called": [],
        "changes": {},
    }

    if not assigned_ip:
        return res

    try:
        current_sta = wifi_cfg.get("sta", {}) or {}
    except Exception:
        current_sta = {}

    try:
        current_sta1 = wifi_cfg.get("sta1", {}) or {}
    except Exception:
        current_sta1 = {}

    gw_new = network_cfg.get("gateway")
    mask_new = network_cfg.get("netmask")
    dns_new = network_cfg.get("nameserver")

    changes: Dict[str, Any] = {}

    # --- STA (primär) ---
    sta_changes: Dict[str, Any] = {}
    sta_ipv4mode = current_sta.get("ipv4mode", "dhcp")
    sta_ip = current_sta.get("ip")

    if not (sta_ipv4mode == "static" and sta_ip == assigned_ip):
        sta_changes["ip"] = {"old": sta_ip, "new": assigned_ip}
        sta_changes["ipv4mode"] = {"old": sta_ipv4mode, "new": "static"}
        sta_changes["gw"] = {"old": current_sta.get("gw"), "new": gw_new}
        sta_changes["mask"] = {"old": current_sta.get("netmask"), "new": mask_new}
        sta_changes["dns"] = {"old": current_sta.get("nameserver"), "new": dns_new}

    if sta_changes:
        changes["wifi_sta"] = {"fields": sta_changes}

    # --- STA1 (sekundär), falls vorhanden/aktiv ---
    # Optional: nur anfassen, wenn SSID/enable gesetzt ist
    if current_sta1:
        sta1_changes: Dict[str, Any] = {}
        sta1_ipv4mode = current_sta1.get("ipv4mode", "dhcp")
        sta1_ip = current_sta1.get("ip")

        if not (sta1_ipv4mode == "static" and sta1_ip == assigned_ip):
            sta1_changes["ip"] = {"old": sta1_ip, "new": assigned_ip}
            sta1_changes["ipv4mode"] = {"old": sta1_ipv4mode, "new": "static"}
            sta1_changes["gw"] = {"old": current_sta1.get("gw"), "new": gw_new}
            sta1_changes["mask"] = {"old": current_sta1.get("netmask"), "new": mask_new}
            sta1_changes["dns"] = {"old": current_sta1.get("nameserver"), "new": dns_new}

        if sta1_changes:
            changes["wifi_sta1"] = {"fields": sta1_changes}

    if changes:
        res["changed"] = True
        res["changes"] = changes

    return res


def _extract_sta_config(wifi_cfg: Dict[str, Any]) -> Dict[str, Any]:
    """Extract the primary STA config from Wifi.GetConfig result."""
    return wifi_cfg.get("sta", {}) or {}


def _apply_network_changes(
    rpc_client: RpcClient,
    identity: DeviceIdentity,
    wifi_cfg: Dict[str, Any],
    assigned_ip: str,
    network_cfg: Dict[str, Any],
    wifi_profiles: List[Dict[str, Any]],
    timeout: float,
    errors: List[Stage2Error],
    warnings: List[Stage2Warning],
) -> Dict[str, Any]:
    """Apply WiFi.SetConfig changes to enforce static IP on STA/STA1.

    Wir konfigurieren:
      - sta:  immer auf static + assigned_ip
      - sta1: ebenfalls, wenn Eintrag existiert (damit Roaming/Fallback nicht auf DHCP fällt)
    
    WICHTIG: Nach WiFi.SetConfig wechselt der Shelly möglicherweise sofort die IP.
    Ein Timeout/Connection-Error ist daher kein echter Fehler, sondern erwartetes Verhalten.
    """
    res = _empty_network_action_result()
    res["changed"] = True  # wir werden nur aufgerufen, wenn _compute_network_changes das so sieht
    res["applied"] = False
    res["methods_called"] = []

    gw_new = network_cfg.get("gateway")
    mask_new = network_cfg.get("netmask")
    dns_new = network_cfg.get("nameserver")

    config_block: Dict[str, Any] = {}

    # --- STA ---
    # FIX: SSID muss IMMER gesetzt werden wenn wir sta konfigurieren,
    # sonst gibt Shelly "STA SSID must be between 1 and 32 chars!" Fehler
    sta_cfg = _extract_sta_config(wifi_cfg)
    current_ssid = sta_cfg.get("ssid") or ""
    
    sta_payload: Dict[str, Any] = {
        "enable": True,
        "ipv4mode": "static",
        "ip": assigned_ip,
        "gw": gw_new,
        "mask": mask_new,
        "dns": dns_new,
        "ssid": current_ssid,  # FIX: Immer aktuelle SSID übernehmen
    }

    # Passwort nur hinzufügen wenn in wifi_profiles gefunden
    try:
        if current_ssid and wifi_profiles:
            password = _find_wifi_password(wifi_profiles, current_ssid)
            if password:
                sta_payload["pass"] = password
    except Exception as exc:
        _add_warning(
            warnings,
            code="wifi_prepare_failed",
            message="Failed to enrich WiFi STA payload with password",
            detail={"ip": identity.ip, "exception": repr(exc)},
        )

    config_block["sta"] = sta_payload

    # --- STA1 (nur wenn echte SSID vorhanden) ---
    sta1_cfg = wifi_cfg.get("sta1", {}) or {}
    current_ssid1 = sta1_cfg.get("ssid") or ""
    
    # FIX: sta1 nur konfigurieren wenn es eine echte SSID hat
    # Sonst verlangt Shelly ein Passwort für eine leere SSID
    if sta1_cfg and current_ssid1:
        sta1_payload: Dict[str, Any] = {
            "enable": True,
            "ipv4mode": "static",
            "ip": assigned_ip,
            "gw": gw_new,
            "mask": mask_new,
            "dns": dns_new,
            "ssid": current_ssid1,
        }

        # Passwort nur hinzufügen wenn in wifi_profiles gefunden
        try:
            if wifi_profiles:
                password1 = _find_wifi_password(wifi_profiles, current_ssid1)
                if password1:
                    sta1_payload["pass"] = password1
        except Exception as exc:
            _add_warning(
                warnings,
                code="wifi_prepare_failed_sta1",
                message="Failed to enrich WiFi STA1 payload with password",
                detail={"ip": identity.ip, "exception": repr(exc)},
            )

        config_block["sta1"] = sta1_payload

    payload = {"config": config_block}

    # FIX: Bei WiFi.SetConfig ist ein Timeout nach dem Senden oft normal,
    # weil der Shelly sofort die IP wechselt und die Verbindung abbricht.
    # Wir unterscheiden daher zwischen "RPC komplett fehlgeschlagen" und
    # "RPC gesendet, aber Antwort timeout".
    
    ip_is_changing = (assigned_ip != identity.ip)
    
    rpc_result = _rpc_call(
        rpc_client=rpc_client,
        target_ip=identity.ip,
        method="WiFi.SetConfig",
        params=payload,
        timeout=timeout,
        errors=errors,
        optional=False,
    )
    
    if rpc_result is not None:
        # Normale erfolgreiche Antwort
        res["applied"] = True
        res["methods_called"].append("WiFi.SetConfig")
    else:
        # RPC hat einen Fehler zurückgegeben
        # Wenn die IP sich ändert, ist ein Timeout nach dem Senden erwartbar
        if ip_is_changing and errors:
            # Prüfe ob der letzte Fehler ein Timeout/Connection-Error war
            # In diesem Fall war der RPC wahrscheinlich erfolgreich
            last_error = errors[-1]
            if last_error.code in ("rpc_error", "rpc_error_optional"):
                exc_detail = last_error.detail.get("exception", "")
                # Typische Timeout/Connection-Fehler erkennen
                if any(hint in exc_detail.lower() for hint in [
                    "timeout", "timed out", "connection", "refused", 
                    "reset", "broken pipe", "eof", "closed", "errno"
                ]):
                    # Fehler entfernen und als Warning umwandeln
                    errors.pop()
                    _add_warning(
                        warnings,
                        code="wifi_setconfig_timeout_expected",
                        message=(
                            f"WiFi.SetConfig timeout (IP change {identity.ip} -> {assigned_ip}). "
                            "This is expected behavior - device likely reconfigured successfully."
                        ),
                        detail={
                            "old_ip": identity.ip,
                            "new_ip": assigned_ip,
                            "original_exception": exc_detail,
                        },
                    )
                    res["applied"] = True  # Wahrscheinlich erfolgreich
                    res["methods_called"].append("WiFi.SetConfig (timeout, likely OK)")
                else:
                    res["applied"] = False
            else:
                res["applied"] = False
        else:
            res["applied"] = False

    return res


def _find_wifi_password(
    wifi_profiles: List[Dict[str, Any]],
    ssid: str,
) -> Optional[str]:
    """Lookup the password for a given SSID in wifi_profiles."""
    for profile in wifi_profiles:
        if profile.get("ssid") == ssid:
            return profile.get("password") or None
    return None


def _build_hostname(identity: DeviceIdentity, hostname_cfg: Dict[str, Any]) -> str:
    """Build a hostname based on model and MAC tail.

    Example config:

      hostname:
        prefix:
          SNSW-001P16EU: "shelly-plus1pm-"
        default_prefix: "shelly-"
        suffix_mac_chars: 6

    If no specific prefix is found for the model, default_prefix is used.
    """
    mac = identity.mac or ""
    model = identity.hw_model or identity.model or ""

    model_prefix_map = hostname_cfg.get("prefix", {}) or {}
    default_prefix = hostname_cfg.get("default_prefix", "shelly-")
    prefix = model_prefix_map.get(model, default_prefix)

    import re as _re

    # Strip separators and non-hex chars from MAC
    mac_clean = _re.sub(r"[^0-9A-Fa-f]", "", mac)
    suffix_len = int(hostname_cfg.get("suffix_mac_chars", 6))
    suffix = mac_clean[-suffix_len:] if len(mac_clean) >= suffix_len else mac_clean

    if not suffix:
        # Fallback, but avoid empty hostname
        suffix = "device"

    return f"{prefix}{suffix.lower()}"


def _compute_hostname_changes(identity: DeviceIdentity, hostname_cfg: Dict[str, Any]) -> Dict[str, Any]:
    """Compute desired hostname based on hostname config and current identity."""
    res = {"changed": False, "current": identity.hostname, "new": None}

    if not hostname_cfg:
        return res

    desired = _build_hostname(identity, hostname_cfg)
    if desired and desired != identity.hostname:
        res["changed"] = True
        res["new"] = desired

    return res


def _update_ip_state(
    state: State,
    identity: DeviceIdentity,
    assigned_ip: Optional[str],
    suggested_entry: Dict[str, Any],
    dry_run: bool,
    errors: List[Stage2Error],
    warnings: List[Stage2Warning],
    run_status: str = "ok",
) -> IpStateActionResult:
    """Update the ip_state.json entry for this device.

    We always key entries by MAC (if available). If no MAC is known, we skip
    ip_state updates to avoid ambiguous entries.
    
    WICHTIG: Wir verwenden update_device (merge) statt upsert_device (replace),
    damit Stage3/4-Felder und andere custom fields erhalten bleiben.
    
    Stage-Tracking: Setzt stage2 Block mit ts/status und stage_completed.
    """
    result = _empty_ip_state_action_result()

    mac = identity.mac
    if not mac:
        _add_warning(
            warnings,
            code="no_mac_for_ip_state",
            message="Device has no MAC; skipping ip_state update",
            detail={"ip": identity.ip, "device_id": identity.device_id},
        )
        return result

    # Normalize MAC for lookup (uppercase, no separators)
    mac_normalized = mac.upper().replace(":", "").replace("-", "")

    # FIX: Direkt aus state.devices lesen statt nicht-existierende get_entry_by_mac
    before_entry: Optional[Dict[str, Any]] = None
    try:
        # Versuche verschiedene MAC-Formate
        before_entry = (
            state.devices.get(mac_normalized)
            or state.devices.get(mac)
            or state.devices.get(mac.upper())
            or state.devices.get(mac.lower())
        )
        if before_entry:
            before_entry = dict(before_entry)  # Kopie erstellen
    except Exception as exc:
        _add_warning(
            warnings,
            code="ip_state_read_failed",
            message="Failed to read ip_state entry from State",
            detail={"mac": mac, "exception": repr(exc)},
        )

    before_entry = before_entry or {}

    # Build the patch with only Stage2-relevant fields
    # Andere Felder (stage3, stage4, custom fields) bleiben erhalten
    patch: Dict[str, Any] = {}
    
    if assigned_ip:
        patch["ip"] = assigned_ip
    if identity.model:
        patch["model"] = identity.model
    if identity.hw_model:
        patch["hw_model"] = identity.hw_model
    if identity.hostname:
        patch["hostname"] = identity.hostname
    if identity.fw_ver:
        patch["fw"] = identity.fw_ver
    
    # Initialize remarks field if not present in existing entry
    if "remarks" not in before_entry:
        patch["remarks"] = ""

    # Stage 2 tracking block
    now_ts = datetime.datetime.utcnow().isoformat() + "Z"
    patch["stage2"] = {
        "ts": now_ts,
        "status": run_status,
        "assigned_ip": assigned_ip,
    }
    
    # Update stage_completed: set to 2 if not already higher
    current_stage = before_entry.get("stage_completed", 0)
    if isinstance(current_stage, int) and current_stage < 2:
        patch["stage_completed"] = 2
    elif not isinstance(current_stage, int):
        patch["stage_completed"] = 2

    # Compute field-wise diffs (nur für Stage2-Felder)
    fields_changed: Dict[str, Dict[str, Any]] = {}

    def _diff_field(field: str, old_value: Any, new_value: Any) -> None:
        if old_value != new_value:
            fields_changed[field] = {"old": old_value, "new": new_value}

    for field in ["ip", "model", "hw_model", "hostname", "fw"]:
        if field in patch:
            _diff_field(field, before_entry.get(field), patch.get(field))

    # Always mark as changed when we update stage2 block
    result["changed"] = True
    result["fields"] = fields_changed

    # Persist changes
    try:
        # FIX: update_device (merge) statt upsert_device (replace) verwenden
        from core.state import update_device, save_state_atomic_with_bak
        
        # Update the device entry in state (merge, nicht replace!)
        update_device(state, mac_normalized, patch)
        
        # Only save to disk if not dry-run
        if not dry_run:
            # Use state.path if available, otherwise fall back to default
            state_path = getattr(state, 'path', None) or "data/ip_state.json"
            bak_path = state_path + ".bak"
            save_state_atomic_with_bak(state, state_path, bak_path)
    except Exception as exc:
        _add_error(
            errors,
            code="ip_state_persist_failed",
            message="Failed to persist ip_state entry",
            detail={"mac": mac, "exception": repr(exc)},
        )

    return result


# ---------------------------------------------------------------------------
# RPC wrapper
# ---------------------------------------------------------------------------


def _rpc_call(
    rpc_client: RpcClient,
    target_ip: str,
    *,
    method: str,
    params: Dict[str, Any],
    timeout: Optional[float],
    errors: List[Stage2Error],
    optional: bool = False,
) -> Optional[Dict[str, Any]]:
    """Wrapper around RpcClient.call with basic error handling.

    NOTE:
    Your RpcClient.call has a signature like:

        def call(self, method, params=None)

    The target IP is *not* passed into call(), but is taken from the
    RpcClient instance (host set in __init__). We therefore use target_ip
    only for logging and error context.
    """
    try:
        # Call signature aligned with your RpcClient implementation:
        # - first argument: method name (e.g. "Device.GetInfo")
        # - second argument: params dict (or None)
        res = rpc_client.call(method, params)

        if not isinstance(res, dict):
            _add_error(
                errors,
                code="rpc_protocol_error",
                message=f"Unexpected RPC response type for {method}",
                detail={"ip": target_ip, "response_type": type(res).__name__},
            )
            return None
        return res

    except Exception as exc:
        code = "rpc_error_optional" if optional else "rpc_error"
        msg = f"RPC call {method} failed"
        _add_error(
            errors,
            code=code,
            message=msg,
            detail={"ip": target_ip, "exception": repr(exc)},
        )
        return None


# ---------------------------------------------------------------------------
# Optional: helpers for device selection by id (not yet used)
# ---------------------------------------------------------------------------


def _resolve_ip_for_device(
    state: State,
    device_id: str,
    errors: List[Stage2Error],
) -> Optional[str]:
    """Resolve IP from device_id via State, if supported.

    This is a placeholder for future convenience methods like
    stage2_configure_device(device_id=...).
    """
    # Preferred: a dedicated lookup method
    if hasattr(state, "get_ip_by_device_id"):
        try:
            # type: ignore[attr-defined]
            ip = state.get_ip_by_device_id(device_id)
            return ip
        except Exception as exc:
            _add_error(
                errors,
                code="state_lookup_failed",
                message="Exception while resolving IP by device_id",
                detail={"device_id": device_id, "exception": repr(exc)},
            )
            return None

    # Fallback: if State does not expose such a method, we cannot resolve
    _add_error(
        errors,
        code="state_lookup_unsupported",
        message="State does not support get_ip_by_device_id",
        detail={"device_id": device_id},
    )
    return None