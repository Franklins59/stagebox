from typing import Set
from .rpc import RpcClient
from .models import DeviceInfo

def list_methods(client: RpcClient) -> Set[str]:
    res = client.call("Shelly.ListMethods", {})
    return set(res.get("methods", []) or [])

def get_device_info(client: RpcClient) -> DeviceInfo:
    res = client.call("Shelly.GetDeviceInfo", {})
    dev_id = str(res.get("id", "unknown"))
    model = str(res.get("model", "unknown"))
    gen = int(res.get("gen", 2))
    fw = str(res.get("fw", res.get("ver", res.get("fw_id", "unknown"))))
    methods = list_methods(client)

    info = DeviceInfo(
        id=dev_id,
        ip="",
        model=model,
        fw=fw,
        gen=gen,
        methods=methods,
        extra=res,
    )
    return info
