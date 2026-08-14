"""
Gateway Router Module (Module 7).
Core execution layer executing authorized model dispatches via provider adapters.
"""

from .models import (
    ExecutionMode,
    ExecutionStatus,
    GatewayRequest,
    GatewayResponse,
    StreamChunk,
    GatewayExecutionResult,
)
from .config import GatewayConfig
from .exceptions import (
    GatewayError,
    AdapterNotFoundError,
    InvalidRequestError,
    ExecutionError,
    TransientExecutionError,
    TimeoutExecutionError,
    PermanentExecutionError,
)
from .adapters import (
    BaseProviderAdapter,
    MockProviderAdapter,
    AdapterRegistry,
)
from .gateway import GatewayRouter
from .orchestrator import PipelineRouter

__all__ = [
    "ExecutionMode",
    "ExecutionStatus",
    "GatewayRequest",
    "GatewayResponse",
    "StreamChunk",
    "GatewayExecutionResult",
    "GatewayConfig",
    "GatewayError",
    "AdapterNotFoundError",
    "InvalidRequestError",
    "ExecutionError",
    "TransientExecutionError",
    "TimeoutExecutionError",
    "PermanentExecutionError",
    "BaseProviderAdapter",
    "MockProviderAdapter",
    "AdapterRegistry",
    "GatewayRouter",
    "PipelineRouter",
]
