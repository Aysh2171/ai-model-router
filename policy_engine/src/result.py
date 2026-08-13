"""
Policy Evaluation Result and Telemetry Data Models.
Defines PolicyEvaluation and PolicyDecision dataclasses capturing runtime governance audit traces.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from ranking_engine.src import RankedModel
from .decisions import DecisionState


@dataclass
class PolicyEvaluation:
    """Captures runtime policy evaluation for a specific ranked model candidate."""

    model_id: str
    provider: str
    rank_position: int
    allowed: bool
    failure_reasons: List[str] = field(default_factory=list)
    explanations: List[str] = field(default_factory=list)
    estimated_cost: float = 0.0
    fallback_eligible: bool = True
    ranked_model: Optional[RankedModel] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert PolicyEvaluation instance into dictionary payload."""
        return {
            "model_id": self.model_id,
            "provider": self.provider,
            "rank_position": self.rank_position,
            "allowed": self.allowed,
            "failure_reasons": self.failure_reasons,
            "explanations": self.explanations,
            "estimated_cost": round(self.estimated_cost, 4),
            "fallback_eligible": self.fallback_eligible,
            "ranked_model": self.ranked_model.to_dict() if self.ranked_model else None,
        }


@dataclass
class PolicyDecision:
    """Top-level operational governance dispatch decision object returned by PolicyEngine."""

    request_id: str
    decision: DecisionState
    selected_model: Optional[RankedModel] = None
    selected_rank: Optional[int] = None
    fallback_used: bool = False
    fallback_attempts: int = 0
    evaluated_candidates: List[PolicyEvaluation] = field(default_factory=list)
    applied_policies: List[str] = field(default_factory=list)
    usage_state_snapshot: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert PolicyDecision into structured dictionary payload."""
        return {
            "request_id": self.request_id,
            "decision": self.decision.value if isinstance(self.decision, DecisionState) else str(self.decision),
            "selected_rank": self.selected_rank,
            "selected_model": self.selected_model.to_dict() if self.selected_model else None,
            "fallback_used": self.fallback_used,
            "fallback_attempts": self.fallback_attempts,
            "applied_policies": self.applied_policies,
            "usage_state_snapshot": self.usage_state_snapshot,
            "evaluated_candidates": [e.to_dict() for e in self.evaluated_candidates],
        }
