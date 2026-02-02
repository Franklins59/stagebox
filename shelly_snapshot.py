#!/usr/bin/env python3
"""
shelly_snapshot.py - Shelly Gen3+ Configuration Snapshot Tool

Scans an IP range for Shelly Gen3+ devices and exports all configuration
data to a JSON file for backup/documentation purposes.

Requirements: Python 3.7+ (no external dependencies)

Author: Claude (Anthropic)
License: MIT
"""

import argparse
import concurrent.futures
import json
import socket
import sys
import urllib.request
import urllib.error
import urllib.parse
from datetime import datetime
from pathlib import Path
from typing import Optional

# ANSI color codes
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"
BOLD = "\033[1m"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Shelly Gen3+ Configuration Snapshot Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --ip-start 192.168.1.30 --ip-end 192.168.1.149
  %(prog)s --ip-start 192.168.1.1 --ip-end 192.168.1.254 --output backups/
  %(prog)s --ip-start 192.168.1.30 --ip-end 192.168.1.149 --auth admin:secret
        """,
    )
    parser.add_argument(
        "--ip-start",
        required=True,
        help="Start IP address of the range (e.g., 192.168.1.30)",
    )
    parser.add_argument(
        "--ip-end",
        required=True,
        help="End IP address of the range (e.g., 192.168.1.149)",
    )
    parser.add_argument(
        "--output",
        "-o",
        default=".",
        help="Output directory or file path (default: current directory)",
    )
    parser.add_argument(
        "--timeout",
        "-t",
        type=float,
        default=3.0,
        help="Request timeout in seconds (default: 3)",
    )
    parser.add_argument(
        "--parallel",
        "-p",
        type=int,
        default=20,
        help="Number of parallel connections (default: 20)",
    )
    parser.add_argument(
        "--auth",
        help="HTTP Basic Auth as USER:PASS (if Shellys are protected)",
    )
    parser.add_argument(
        "--include-methods",
        action="store_true",
        help="Include Shelly.ListMethods in output",
    )
    parser.add_argument(
        "--min-gen",
        type=int,
        default=2,
        help="Minimum generation to include (default: 2)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output",
    )
    return parser.parse_args()


def ip_to_int(ip: str) -> int:
    """Convert IP address string to integer."""
    parts = ip.split(".")
    return (int(parts[0]) << 24) + (int(parts[1]) << 16) + (int(parts[2]) << 8) + int(parts[3])


def int_to_ip(num: int) -> str:
    """Convert integer to IP address string."""
    return f"{(num >> 24) & 0xFF}.{(num >> 16) & 0xFF}.{(num >> 8) & 0xFF}.{num & 0xFF}"


def generate_ip_range(start_ip: str, end_ip: str) -> list:
    """Generate list of IP addresses in range."""
    start = ip_to_int(start_ip)
    end = ip_to_int(end_ip)
    return [int_to_ip(i) for i in range(start, end + 1)]


def extract_short_type(device_id: str) -> str:
    """Extract short device type from device ID.
    
    Examples:
        shellyi4g3-e4b3233dc35c -> I4G3
        shelly1pmminig3-dcda0cb9de60 -> 1PMMiniG3
        shelly2pmg3-8cbfea91fdf8 -> 2PMG3
        shellydimmerg3-e4b3233b4dd4 -> DimmerG3
    """
    # Remove 'shelly' prefix
    if device_id.lower().startswith("shelly"):
        device_id = device_id[6:]
    
    # Remove MAC address (after last hyphen, if it looks like a MAC)
    parts = device_id.rsplit("-", 1)
    if len(parts) == 2 and len(parts[1]) == 12:
        device_id = parts[0]
    
    # Type mapping for known devices
    type_map = {
        "i4g3": "I4G3",
        "1pmminig3": "1PMMiniG3",
        "1minig3": "1MiniG3", 
        "1pmg3": "1PMG3",
        "1g3": "1G3",
        "2pmg3": "2PMG3",
        "dimmerg3": "DimmerG3",
        "dimmer0110vpmg3": "Dimmer010VG3",
        "plugsg3": "PlugSG3",
        "htg3": "HTG3",
        "motionsensor2": "MotionSensor2",
        "blugwg3": "BluGWG3",
        "walldisplayg3": "WallDisplayG3",
        "emg3": "EMG3",
        "3emg3": "3EMG3",
        # Gen2 Pro devices
        "pro1": "Pro1",
        "pro1pm": "Pro1PM",
        "pro2": "Pro2",
        "pro2pm": "Pro2PM",
        "pro3": "Pro3",
        "pro4pm": "Pro4PM",
        "prodm1pm": "ProDM1PM",
        "prodm2pm": "ProDM2PM",
        "proem50": "ProEM50",
        "pro3em": "Pro3EM",
        # Gen2 Plus devices  
        "plus1": "Plus1",
        "plus1pm": "Plus1PM",
        "plus2pm": "Plus2PM",
        "plusi4": "PlusI4",
        "plusplugit": "PlusPlugIT",
        "pluspluguk": "PlusPlugUK",
        "plusplugus": "PlusPlugUS",
        "plugus": "PlugUS",
    }
    
    lower = device_id.lower()
    if lower in type_map:
        return type_map[lower]
    
    # Fallback: basic formatting
    return device_id.upper() if len(device_id) <= 6 else device_id


class ShellyScanner:
    """Scanner for Shelly devices using urllib."""

    def __init__(
        self,
        timeout: float = 3.0,
        auth: Optional[tuple] = None,
        min_gen: int = 2,
        include_methods: bool = False,
        verbose: bool = False,
    ):
        self.timeout = timeout
        self.auth = auth
        self.min_gen = min_gen
        self.include_methods = include_methods
        self.verbose = verbose

    def _http_get(self, url: str) -> Optional[dict]:
        """Make HTTP GET request and return JSON response."""
        try:
            req = urllib.request.Request(url)
            
            if self.auth:
                import base64
                credentials = f"{self.auth[0]}:{self.auth[1]}"
                b64_credentials = base64.b64encode(credentials.encode()).decode()
                req.add_header("Authorization", f"Basic {b64_credentials}")
            
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                if response.status == 200:
                    return json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, urllib.error.HTTPError, 
                socket.timeout, json.JSONDecodeError, OSError):
            pass
        return None

    def _rpc_call(self, ip: str, method: str, params: Optional[dict] = None) -> Optional[dict]:
        """Make an RPC call to a Shelly device."""
        url = f"http://{ip}/rpc/{method}"
        if params:
            param_parts = []
            for k, v in params.items():
                if isinstance(v, str):
                    param_parts.append(f"{k}={urllib.parse.quote(v)}")
                else:
                    param_parts.append(f"{k}={v}")
            url = f"{url}?{'&'.join(param_parts)}"
        
        return self._http_get(url)

    def _get_kvs_all(self, ip: str) -> dict:
        """Get all KVS entries with paging support."""
        all_items = []
        offset = 0
        
        while True:
            url = f"http://{ip}/rpc/KVS.GetMany?match=%2A&offset={offset}"
            data = self._http_get(url)
            
            if not data:
                break
                
            items = data.get("items", [])
            all_items.extend(items)
            
            total = data.get("total", 0)
            if offset + len(items) >= total:
                break
            offset += len(items)
        
        # Convert to dict format
        return {item["key"]: item["value"] for item in all_items}

    def probe_device(self, ip: str) -> Optional[dict]:
        """Probe a single IP for a Shelly Gen3+ device."""
        # Step 1: Check if it's a Shelly and get device info
        device_info = self._rpc_call(ip, "Shelly.GetDeviceInfo")
        if not device_info:
            return None

        # Check generation
        gen = device_info.get("gen", 0)
        if gen < self.min_gen:
            if self.verbose:
                print(f"  {YELLOW}Skipping Gen{gen} device at {ip}{RESET}")
            return None

        # Extract display info
        device_id = device_info.get("id", "unknown")
        short_type = extract_short_type(device_id)
        
        # Step 2: Get full config
        config = self._rpc_call(ip, "Shelly.GetConfig")
        
        # Extract device name from config
        device_name = None
        if config:
            sys_config = config.get("sys", {})
            device_config = sys_config.get("device", {})
            device_name = device_config.get("name")

        # Print discovery line
        name_str = f" - {device_name}" if device_name else ""
        print(f"  {CYAN}{short_type} @ {ip}{RESET} ({device_id}){name_str}")

        # Step 3: Get webhooks
        webhooks = self._rpc_call(ip, "Webhook.List")

        # Step 4: Get schedules  
        schedules = self._rpc_call(ip, "Schedule.List")

        # Step 5: Get KVS
        kvs = self._get_kvs_all(ip)

        # Step 6: Optionally get methods
        methods = None
        if self.include_methods:
            methods_result = self._rpc_call(ip, "Shelly.ListMethods")
            if methods_result:
                methods = methods_result.get("methods", [])

        # Assemble result
        result = {
            "ip": ip,
            "device_info": device_info,
            "config": config,
            "webhooks": webhooks,
            "schedules": schedules,
            "kvs": kvs if kvs else None,
        }
        
        if methods is not None:
            result["methods"] = methods

        return result

    def scan_range(self, ips: list, max_parallel: int = 20) -> list:
        """Scan a list of IPs for Shelly devices using thread pool."""
        devices = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_parallel) as executor:
            future_to_ip = {executor.submit(self.probe_device, ip): ip for ip in ips}
            
            for future in concurrent.futures.as_completed(future_to_ip):
                result = future.result()
                if result:
                    devices.append(result)
        
        return devices


def generate_output_path(output_arg: str) -> Path:
    """Generate output file path with timestamp."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"shelly_snapshot_{timestamp}.json"
    
    path = Path(output_arg)
    if path.is_dir() or output_arg.endswith("/"):
        path.mkdir(parents=True, exist_ok=True)
        return path / filename
    elif path.suffix == ".json":
        path.parent.mkdir(parents=True, exist_ok=True)
        return path
    else:
        # Treat as directory
        path.mkdir(parents=True, exist_ok=True)
        return path / filename


def create_summary(devices: list) -> dict:
    """Create summary statistics."""
    type_counts = {}
    
    for device in devices:
        device_id = device.get("device_info", {}).get("id", "unknown")
        short_type = extract_short_type(device_id)
        type_counts[short_type] = type_counts.get(short_type, 0) + 1

    return {
        "total_devices": len(devices),
        "by_type": type_counts,
    }


def main() -> int:
    args = parse_args()

    # Parse auth if provided
    auth = None
    if args.auth:
        if ":" not in args.auth:
            print(f"{RED}Error: --auth must be in format USER:PASS{RESET}")
            return 1
        auth = tuple(args.auth.split(":", 1))

    # Generate IP list
    try:
        ips = generate_ip_range(args.ip_start, args.ip_end)
    except (ValueError, IndexError) as e:
        print(f"{RED}Error: Invalid IP range: {e}{RESET}")
        return 1

    print(f"{BOLD}Scanning {args.ip_start} - {args.ip_end} ({len(ips)} addresses)...{RESET}")
    print()

    # Create scanner and run
    scanner = ShellyScanner(
        timeout=args.timeout,
        auth=auth,
        min_gen=args.min_gen,
        include_methods=args.include_methods,
        verbose=args.verbose,
    )

    devices = scanner.scan_range(ips, max_parallel=args.parallel)

    # Sort by IP
    devices.sort(key=lambda d: ip_to_int(d["ip"]))

    print()
    
    if not devices:
        print(f"{YELLOW}No Shelly Gen{args.min_gen}+ devices found.{RESET}")
        return 0

    # Create output
    output_path = generate_output_path(args.output)
    
    snapshot = {
        "snapshot_timestamp": datetime.now().isoformat(),
        "scan_range": f"{args.ip_start} - {args.ip_end}",
        "min_generation": args.min_gen,
        "devices": devices,
        "summary": create_summary(devices),
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, indent=2, ensure_ascii=False)

    print(f"{GREEN}Found {len(devices)} Shelly Gen{args.min_gen}+ device(s){RESET}")
    print(f"{GREEN}Saved to: {output_path}{RESET}")

    return 0


if __name__ == "__main__":
    sys.exit(main())