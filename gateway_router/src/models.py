"""
Gateway Router Data Models and Representations.
Defines GatewayRequest, GatewayResponse, StreamChunk, and Execution Enums for the execution layer.
"""

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Dict, Any, Optional, List
from policy_engine.src import PolicyDecision, DecisionState
from ranking_engine.src import RankedModel


class ExecutionMode(str, Enum):
    """Execution mode indicator for gateway dispatches."""
    MOCK = "mock"


class ExecutionStatus(str, Enum):
    """Gateway request execution outcome states."""
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    TIMEOUT = "TIMEOUT"
    RETRY_EXHAUSTED = "RETRY_EXHAUSTED"
    REJECTED = "REJECTED"
    NO_CANDIDATE = "NO_CANDIDATE"
    ADAPTER_NOT_FOUND = "ADAPTER_NOT_FOUND"


@dataclass
class GatewayRequest:
    """Encapsulates client payload and routing decision for gateway execution."""

    request_id: str = "REQ-000"
    prompt: str = ""
    policy_decision: Optional[PolicyDecision] = None
    model_id: Optional[str] = None
    provider: Optional[str] = None
    stream: bool = False
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    simulation_options: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert GatewayRequest into dictionary payload."""
        return {
            "request_id": self.request_id,
            "prompt": self.prompt,
            "model_id": self.model_id,
            "provider": self.provider,
            "stream": self.stream,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "metadata": self.metadata,
            "simulation_options": self.simulation_options,
            "policy_decision": self.policy_decision.to_dict() if self.policy_decision else None,
        }


@dataclass
class StreamChunk:
    """Represents an incremental streaming token chunk emitted during response generation."""

    request_id: str
    chunk_index: int
    content: str
    model_id: str
    provider: str
    is_final: bool = False
    execution_mode: str = ExecutionMode.MOCK.value

    def to_dict(self) -> Dict[str, Any]:
        """Convert StreamChunk into dictionary payload."""
        return asdict(self)


@dataclass
class GatewayExecutionResult:
    """Internal result returned by a Provider Adapter execution."""

    content: str
    model_id: str
    provider: str
    execution_mode: str = ExecutionMode.MOCK.value
    latency_ms: float = 0.0
    usage: Dict[str, int] = field(default_factory=lambda: {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0})
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert GatewayExecutionResult into dictionary payload."""
        return asdict(self)


@dataclass
class GatewayResponse:
    """Top-level unified response returned by the Gateway Router."""

    request_id: str
    status: ExecutionStatus
    decision_state: Optional[str] = None
    model_id: Optional[str] = None
    provider: Optional[str] = None
    content: Optional[str] = None
    execution_mode: str = ExecutionMode.MOCK.value
    latency_ms: float = 0.0
    retry_count: int = 0
    fallback_used: bool = False
    error_message: Optional[str] = None
    usage: Dict[str, int] = field(default_factory=lambda: {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0})
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert GatewayResponse into structured dictionary payload."""
        return {
            "request_id": self.request_id,
            "status": self.status.value if isinstance(self.status, ExecutionStatus) else str(self.status),
            "decision_state": self.decision_state,
            "model_id": self.model_id,
            "provider": self.provider,
            "content": self.content,
            "execution_mode": self.execution_mode,
            "latency_ms": round(self.latency_ms, 2),
            "retry_count": self.retry_count,
            "fallback_used": self.fallback_used,
            "error_message": self.error_message,
            "usage": self.usage,
            "metadata": self.metadata,
        }
