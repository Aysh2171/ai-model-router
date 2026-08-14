"""
Gateway Router Exceptions and Failure Model.
Defines strongly typed exception classes categorizing retryable vs non-retryable execution errors.
"""


class GatewayError(Exception):
    """Base exception for all Gateway Router failures."""
    pass


class AdapterNotFoundError(GatewayError):
    """Raised when no registered provider adapter exists for the requested provider."""
    pass


class InvalidRequestError(GatewayError):
    """Raised when request payload or execution configuration is invalid."""
    pass


class ExecutionError(GatewayError):
    """Base class for provider execution failures."""
    pass


class TransientExecutionError(ExecutionError):
    """Raised when a transient/recoverable failure occurs (e.g. simulated 503, connection reset).
    Eligible for gateway-level retry."""
    pass


class TimeoutExecutionError(ExecutionError):
    """Raised when request execution times out. Eligible for gateway-level retry."""
    pass


class PermanentExecutionError(ExecutionError):
    """Raised when an unrecoverable failure occurs (e.g. 400 Bad Request, payload format error).
    Not eligible for gateway retry."""
    pass
