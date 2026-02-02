from ..rpc import RpcClient
from ..capabilities import get_device_info as _get_info
from ..models import DeviceInfo

def get_info(client: RpcClient, *, known_ip: str | None = None) -> DeviceInfo:
    info = _get_info(client)
    info.ip = known_ip or client.host
    return info

def reboot(client: RpcClient) -> None:
    client.call("Shelly.Reboot", {})
