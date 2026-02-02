"""Stagebox Services"""

from web.services.device_manager import DeviceManager, device_manager, get_device_manager
from web.services.job_queue import JobQueue, job_queue, get_job_queue
from web.services.building_manager import (
    discover_buildings,
    activate_building,
    deactivate_building,
    get_active_building,
    is_building_active,
)

__all__ = [
    'DeviceManager',
    'device_manager',
    'get_device_manager',
    'JobQueue',
    'job_queue',
    'get_job_queue',
    'discover_buildings',
    'activate_building',
    'deactivate_building',
    'get_active_building',
    'is_building_active',
]
