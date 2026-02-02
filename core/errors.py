# errors.py — central error types for RPC & Core

class RpcError(Exception):
    """Generic RPC error returned by the device."""
    def __init__(self, message: str, code: int | None = None, data=None):
        super().__init__(message)
        self.code = code
        self.data = data


class TimeoutError(RpcError):
    """Request timed out."""


class AuthError(RpcError):
    """Authentication/authorization error."""


class UnsupportedMethodError(RpcError):
    """RPC method is not supported by the device."""


class NetworkError(RpcError):
    """Transport-level error (connection, DNS, etc.)."""


class ValidationError(RpcError):
    """Input/output validation failed in core layer."""
