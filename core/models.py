from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Set

@dataclass
class DeviceInfo:
    id: str
    ip: str
    model: str
    fw: str
    gen: int
    methods: Set[str] = field(default_factory=set)
    extra: Dict[str, Any] = field(default_factory=dict)

@dataclass
class SwitchState:
    channel: int
    is_on: bool
    power_w: Optional[float] = None
    voltage_v: Optional[float] = None
    current_a: Optional[float] = None
    raw: Dict[str, Any] = field(default_factory=dict)

@dataclass
class OTAStatus:
    status: str
    progress: Optional[int] = None
    version: Optional[str] = None
    raw: Dict[str, Any] = field(default_factory=dict)

@dataclass
class State:
    """Typed view of data/ip_state.json.
    devices is a mapping: device_id -> arbitrary metadata dict.
    path stores the file path this state was loaded from (for saving).
    """
    version: int
    devices: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    path: Optional[str] = None