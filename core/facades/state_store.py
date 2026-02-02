"""
State facade for handling ip_state.json and related device inventory data.

This module extracts and refactors the ip_state-related logic from the legacy
shelly_stage2.py into a reusable, testable component for the new core
architecture.

Responsibilities:
- Load and save ip_state.json with a stable schema and key ordering
- Provide lookup helpers (by MAC, by IP)
- Provide update helpers for per-device entries
"""

from __future__ import annotations

import copy
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


# Default schema for entries in ip_state.json
STATE_ENTRY_TEMPLATE: Dict[str, Any] = {
    "assigned_at": "",
    "friendly_name": "",
    "ip": "",
    "model": "",
    "hw_model": "",
    "hostname": "",
    "room": "",
    "location": "",
    "stage3": {},
    "fw": "",
    "last_seen": "",
}

# Desired key order inside each device entry
STATE_KEY_ORDER = [
    "assigned_at",
    "friendly_name",
    "ip",
    "model",
    "hw_model",
    "hostname",
    "room",
    "location",
    "stage3",
    "fw",
    "last_seen",
]


@dataclass
class IpStateEntry:
    """Typed wrapper for a single ip_state.json entry."""

    mac: str
    assigned_at: str = ""
    friendly_name: str = ""
    ip: str = ""
    model: str = ""
    hw_model: str = ""
    hostname: str = ""
    room: str = ""
    location: str = ""
    stage3: Dict[str, Any] = None
    fw: str = ""
    last_seen: str = ""

    extra: Dict[str, Any] = None  # for any future fields

    def to_dict(self) -> Dict[str, Any]:
        """Convert the entry into a dict compatible with ip_state.json."""
        base = copy.deepcopy(STATE_ENTRY_TEMPLATE)
        base.update(
            {
                "assigned_at": self.assigned_at,
                "friendly_name": self.friendly_name,
                "ip": self.ip,
                "model": self.model,
                "hw_model": self.hw_model,
                "hostname": self.hostname,
                "room": self.room,
                "location": self.location,
                "stage3": self.stage3 or {},
                "fw": self.fw,
                "last_seen": self.last_seen,
            }
        )
        if self.extra:
            base.update(self.extra)
        return base

    @classmethod
    def from_dict(cls, mac: str, data: Dict[str, Any]) -> "IpStateEntry":
        """Create an IpStateEntry from a raw dict (merged with template)."""
        merged = copy.deepcopy(STATE_ENTRY_TEMPLATE)
        merged.update(data or {})

        # Extract "extra" fields not in the standard template
        extra: Dict[str, Any] = {}
        for k, v in data.items():
            if k not in STATE_ENTRY_TEMPLATE:
                extra[k] = v

        return cls(
            mac=mac,
            assigned_at=merged.get("assigned_at", ""),
            friendly_name=merged.get("friendly_name", ""),
            ip=merged.get("ip", ""),
            model=merged.get("model", ""),
            hw_model=merged.get("hw_model", ""),
            hostname=merged.get("hostname", ""),
            room=merged.get("room", ""),
            location=merged.get("location", ""),
            stage3=merged.get("stage3") or {},
            fw=merged.get("fw", ""),
            last_seen=merged.get("last_seen", ""),
            extra=extra,
        )


class IpStateStore:
    """Encapsulates loading, querying and updating ip_state.json.

    This is designed to back the `State` abstraction used by stage2_core.
    """

    def __init__(self, path: Path):
        self._path = path
        self._entries_by_mac: Dict[str, IpStateEntry] = {}

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def load(self) -> None:
        """Load ip_state.json from disk, creating an empty store if not present."""
        if not self._path.exists():
            self._entries_by_mac = {}
            return

        try:
            with self._path.open("r", encoding="utf-8") as f:
                raw = json.load(f)
        except Exception:
            # On any error, we start with an empty dict; caller can decide how to react.
            self._entries_by_mac = {}
            return

        entries: Dict[str, IpStateEntry] = {}
        if isinstance(raw, dict):
            for mac, entry in raw.items():
                if not isinstance(entry, dict):
                    continue
                entries[mac] = IpStateEntry.from_dict(mac, entry)

        self._entries_by_mac = entries

    def save(self) -> None:
        """Persist ip_state.json to disk using a defined key order."""
        self._path.parent.mkdir(parents=True, exist_ok=True)

        ordered_state: Dict[str, Dict[str, Any]] = {}
        for mac in sorted(self._entries_by_mac.keys()):
            entry = self._entries_by_mac[mac]
            data = entry.to_dict()

            # Order keys inside the entry according to STATE_KEY_ORDER
            ordered_entry: Dict[str, Any] = {}
            for key in STATE_KEY_ORDER:
                if key in data:
                    ordered_entry[key] = data[key]
            # Any extra keys (future fields) go at the end
            for key, value in data.items():
                if key not in ordered_entry:
                    ordered_entry[key] = value

            ordered_state[mac] = ordered_entry

        with self._path.open("w", encoding="utf-8") as f:
            json.dump(ordered_state, f, indent=2, sort_keys=False)

    # ------------------------------------------------------------------
    # Lookups
    # ------------------------------------------------------------------

    def get_entry_by_mac(self, mac: str) -> Optional[IpStateEntry]:
        """Return the entry for the given MAC, if any."""
        return self._entries_by_mac.get(mac)

    def get_entry_by_ip(self, ip: str) -> Optional[IpStateEntry]:
        """Return the entry for the given IP, if any."""
        for entry in self._entries_by_mac.values():
            if entry.ip == ip:
                return entry
        return None

    def all_entries(self) -> Dict[str, IpStateEntry]:
        """Return a copy of all entries keyed by MAC."""
        return dict(self._entries_by_mac)

    # ------------------------------------------------------------------
    # Mutations
    # ------------------------------------------------------------------

    def upsert_entry(
        self,
        mac: str,
        *,
        ip: Optional[str] = None,
        model: Optional[str] = None,
        hw_model: Optional[str] = None,
        hostname: Optional[str] = None,
        room: Optional[str] = None,
        location: Optional[str] = None,
        friendly_name: Optional[str] = None,
        fw: Optional[str] = None,
        touch_assigned_at: bool = False,
        touch_last_seen: bool = True,
        extra_updates: Optional[Dict[str, Any]] = None,
    ) -> IpStateEntry:
        """Create or update an entry for the given MAC.

        This helper mirrors the behavior from legacy shelly_stage2.py, but
        makes the semantics explicit and testable.
        """
        existing = self._entries_by_mac.get(mac)
        if existing is None:
            existing = IpStateEntry(mac=mac)

        entry = IpStateEntry.from_dict(mac, existing.to_dict())

        if ip is not None:
            entry.ip = ip
        if model is not None:
            entry.model = model
        if hw_model is not None:
            entry.hw_model = hw_model
        if hostname is not None:
            entry.hostname = hostname
        if room is not None:
            entry.room = room
        if location is not None:
            entry.location = location
        if friendly_name is not None:
            entry.friendly_name = friendly_name
        if fw is not None:
            entry.fw = fw

        now_iso = datetime.now(timezone.utc).isoformat()
        if touch_assigned_at and not entry.assigned_at:
            entry.assigned_at = now_iso
        if touch_last_seen:
            entry.last_seen = now_iso

        if extra_updates:
            if entry.extra is None:
                entry.extra = {}
            entry.extra.update(extra_updates)

        self._entries_by_mac[mac] = entry
        return entry
