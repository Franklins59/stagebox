from typing import Any, Dict, Optional
import requests
from .errors import RpcError, TimeoutError, AuthError, NetworkError

class RpcClient:
    """
    Minimal HTTP RPC client for Shelly Gen2+ devices.
    """

    def __init__(self, host: str, *,
                 username: Optional[str] = None,
                 password: Optional[str] = None,
                 timeout_s: float = 3.0):
        self.host = host
        self.username = username
        self.password = password
        self.timeout = timeout_s
        self._rpc_id = 1

    @property
    def base_url(self) -> str:
        return f"http://{self.host}/rpc"

    def call(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        payload = {"id": self._rpc_id, "method": method}
        if params:
            payload["params"] = params
        self._rpc_id += 1

        try:
            auth = (self.username, self.password) if self.username or self.password else None
            resp = requests.post(self.base_url, json=payload, timeout=self.timeout, auth=auth)
        except requests.exceptions.Timeout as e:
            raise TimeoutError(f"RPC timeout calling {method} on {self.host}") from e
        except requests.exceptions.RequestException as e:
            raise NetworkError(f"RPC network error calling {method} on {self.host}: {e}") from e

        if resp.status_code in (401, 403):
            raise AuthError(f"RPC auth error ({resp.status_code}) on {self.host}")
        if resp.status_code >= 400:
            raise RpcError(f"HTTP {resp.status_code} for {method} on {self.host}")

        try:
            data = resp.json()
        except ValueError as e:
            raise RpcError(f"Invalid JSON response for {method} on {self.host}") from e

        if "error" in data and data["error"]:
            err = data["error"]
            raise RpcError(
                message=f"RPC error {err.get('code')}: {err.get('message')}",
                code=err.get("code"),
                data=err.get("data"),
            )

        return data.get("result", {})
