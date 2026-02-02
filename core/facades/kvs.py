# core/facades/kvs.py
#
# Simple facade for Shelly Gen2 KVS RPC.
# Uses generic RpcClient from core.rpc and exposes a small helper API:
#
#   - list_keys(client) -> list[str]
#   - get_value(client, key) -> Any | None
#   - set_value(client, key, value) -> dict (raw RPC result)
#
# The exact method names are based on the Shelly Gen2 KVS API.
# If the device does not support KVS, calls will raise RpcError.

from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..rpc import RpcClient
from ..errors import RpcError


def list_keys(client: RpcClient) -> List[str]:
    """
    Return a list of available KVS keys on the device.

    RPC: KVS.List or Kvs.List (depends on firmware; we try both).
    """
    # Some firmwares use "KVS." prefix, some "Kvs."
    for method in ("KVS.List", "Kvs.List"):
        try:
            res: Dict[str, Any] = client.call(method, {})
            keys = res.get("keys") or res.get("items") or []
            # Normalise to list of strings
            return [str(k) for k in keys]
        except RpcError as e:
            # Try next variant if method not supported
            if "not found" in str(e).lower() or "not exist" in str(e).lower():
                continue
            raise
    raise RpcError("KVS list method not supported by this device")


def get_value(client: RpcClient, key: str) -> Optional[Any]:
    """
    Get a single KVS value by key.

    RPC: KVS.Get / Kvs.Get
    Expected response: { "key": "<key>", "value": <any> } or {} if missing.
    """
    params = {"key": key}
    for method in ("KVS.Get", "Kvs.Get"):
        try:
            res: Dict[str, Any] = client.call(method, params)
            # Some firmwares may omit "value" if key does not exist
            if "value" not in res:
                return None
            return res["value"]
        except RpcError as e:
            if "not found" in str(e).lower() or "not exist" in str(e).lower():
                continue
            raise
    raise RpcError("KVS get method not supported by this device")


def set_value(client: RpcClient, key: str, value: Any) -> Dict[str, Any]:
    """
    Set a KVS value.

    RPC: KVS.Set / Kvs.Set
    Expected request: { "key": "<key>", "value": <any> }
    """
    params = {"key": key, "value": value}
    last_error: Optional[Exception] = None
    for method in ("KVS.Set", "Kvs.Set"):
        try:
            res: Dict[str, Any] = client.call(method, params)
            return res
        except RpcError as e:
            last_error = e
            if "not found" in str(e).lower() or "not exist" in str(e).lower():
                continue
            raise
    if last_error:
        raise last_error
    raise RpcError("KVS set method not supported by this device")
