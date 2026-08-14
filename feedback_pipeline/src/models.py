"""
Feedback Pipeline Domain Models.
Defines RoutingEvent and FeedbackRecord dataclasses representing telemetry traces and quality feedback.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import uuid

from gateway_router.src import GatewayResponse, ExecutionStatus


@dataclass
class RoutingEvent:
    """Represents an immutable operational telemetry record captured from Gateway execution."""

    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    request_id: str = "REQ-000"
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    task_category: str = "General Prompting"
    complexity_tier: Optional[str] = None
    complexity_score: Optional[int] = None
    complexity_confidence: Optional[float] = None
    model_id: Optional[str] = None
    provider: Optional[str] = None
    decision_state: Optional[str] = None
    execution_status: str = "SUCCESS"
    execution_mode: str = "mock"
    latency_ms: float = 0.0
    retry_count: int = 0
    fallback_used: bool = False
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost_tier: Optional[str] = None
    latency_tier: Optional[str] = None
    selected_rank: Optional[int] = None
    feasible_candidate_count: Optional[int] = None
    allowed_candidate_count: Optional[int] = None
    ranked_candidate_count: Optional[int] = None
    error_message: Optional[str] = None
    prompt_summary: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_success(self) -> bool:
        """Helper property evaluating whether execution concluded successfully."""
        return self.execution_status.upper() == "SUCCESS"

    @classmethod
    def from_gateway_response(
        cls,
        response: GatewayResponse,
        request_prompt: str = "",
        task_category: Optional[str] = None,
        max_prompt_length: int = 200
    ) -> "RoutingEvent":
        """
        Construct a RoutingEvent instance from an upstream GatewayResponse and optional prompt context.
        """
        meta = response.metadata or {}
        comp_profile = meta.get("complexity_profile") or {}

        # Extract Complexity Profile metadata if present
        comp_tier = str(comp_profile.get("complexity")) if comp_profile.get("complexity") is not None else None
        comp_score = int(comp_profile.get("complexity_score")) if comp_profile.get("complexity_score") is not None else None
        comp_conf = float(comp_profile.get("confidence")) if comp_profile.get("confidence") is not None else None

        # Extract Task Category from argument, metadata, or default
        category = task_category or meta.get("task_category") or "General Prompting"

        # Sanitize / Truncate prompt summary for data privacy
        prompt_snippet = None
        if request_prompt:
            prompt_snippet = request_prompt[:max_prompt_length]

        usage = response.usage or {}
        p_tokens = usage.get("prompt_tokens", 0)
        c_tokens = usage.get("completion_tokens", 0)
        t_tokens = usage.get("total_tokens", p_tokens + c_tokens)

        status_str = response.status.value if hasattr(response.status, "value") else str(response.status)

        return cls(
            request_id=response.request_id,
            task_category=category,
            complexity_tier=comp_tier,
            complexity_score=comp_score,
            complexity_confidence=comp_conf,
            model_id=response.model_id,
            provider=response.provider,
            decision_state=response.decision_state,
            execution_status=status_str,
            execution_mode=response.execution_mode,
            latency_ms=round(response.latency_ms, 2),
            retry_count=response.retry_count,
            fallback_used=response.fallback_used,
            prompt_tokens=p_tokens,
            completion_tokens=c_tokens,
            total_tokens=t_tokens,
            cost_tier=meta.get("cost_tier"),
            latency_tier=meta.get("latency_tier"),
            selected_rank=meta.get("selected_rank"),
            feasible_candidate_count=meta.get("feasible_candidate_count"),
            allowed_candidate_count=meta.get("allowed_candidate_count"),
            ranked_candidate_count=meta.get("ranked_candidate_count"),
            error_message=response.error_message,
            prompt_summary=prompt_snippet,
            metadata=meta
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert RoutingEvent instance into a serializable dictionary."""
        return {
            "event_id": self.event_id,
            "request_id": self.request_id,
            "timestamp": self.timestamp.isoformat() if isinstance(self.timestamp, datetime) else str(self.timestamp),
            "task_category": self.task_category,
            "complexity_tier": self.complexity_tier,
            "complexity_score": self.complexity_score,
            "complexity_confidence": self.complexity_confidence,
            "model_id": self.model_id,
            "provider": self.provider,
            "decision_state": self.decision_state,
            "execution_status": self.execution_status,
            "execution_mode": self.execution_mode,
            "latency_ms": round(self.latency_ms, 2),
            "retry_count": self.retry_count,
            "fallback_used": self.fallback_used,
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
            "cost_tier": self.cost_tier,
            "latency_tier": self.latency_tier,
            "selected_rank": self.selected_rank,
            "feasible_candidate_count": self.feasible_candidate_count,
            "allowed_candidate_count": self.allowed_candidate_count,
            "ranked_candidate_count": self.ranked_candidate_count,
            "error_message": self.error_message,
            "prompt_summary": self.prompt_summary,
            "metadata": self.metadata,
        }


@dataclass
class FeedbackRecord:
    """Represents qualitative user or evaluator evaluation linked to a routing event."""

    event_id: str
    rating: int
    feedback_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    quality_category: Optional[str] = None
    comment: Optional[str] = None
    evaluator_id: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        """Validate rating bounds (must be an integer between 1 and 5)."""
        if not isinstance(self.rating, int) or self.rating < 1 or self.rating > 5:
            raise ValueError(f"Rating must be an integer between 1 and 5 (got {self.rating}).")

    def to_dict(self) -> Dict[str, Any]:
        """Convert FeedbackRecord into a serializable dictionary."""
        return {
            "feedback_id": self.feedback_id,
            "event_id": self.event_id,
            "rating": self.rating,
            "quality_category": self.quality_category,
            "comment": self.comment,
            "evaluator_id": self.evaluator_id,
            "created_at": self.created_at.isoformat() if isinstance(self.created_at, datetime) else str(self.created_at),
        }
