"""
Rule Engine Evaluation Result and Telemetry Data Structures.
Defines PolicyExcludedModel and RuleEvaluationResult dataclasses for audit traces and downstream routers.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from capability_matcher.src import CandidateModel, ExcludedModel
from .context import PolicyContext


@dataclass
class PolicyExcludedModel:
    """Captures a candidate model that passed technical capability match but was rejected by organizational rules."""

    model_id: str
    provider: str
    failed_rule_names: List[str] = field(default_factory=list)
    violation_details: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert PolicyExcludedModel instance into dictionary payload."""
        return {
            "model_id": self.model_id,
            "provider": self.provider,
            "failed_rule_names": self.failed_rule_names,
            "violation_details": self.violation_details,
        }


@dataclass
class RuleEvaluationResult:
    """Top-level container object returned by RuleEngine."""

    request_id: str
    is_rule_satisfiable: bool
    policy_context: PolicyContext
    allowed_candidates: List[CandidateModel] = field(default_factory=list)
    policy_excluded_candidates: List[PolicyExcludedModel] = field(default_factory=list)
    capability_excluded_models: List[ExcludedModel] = field(default_factory=list)
    complexity_profile: Dict[str, Any] = field(default_factory=dict)
    applied_policies: List[str] = field(default_factory=list)
    total_feasible_input: int = 0
    allowed_count: int = 0
    policy_excluded_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert RuleEvaluationResult into structured dictionary payload."""
        return {
            "request_id": self.request_id,
            "is_rule_satisfiable": self.is_rule_satisfiable,
            "total_feasible_input": self.total_feasible_input,
            "allowed_count": self.allowed_count,
            "policy_excluded_count": self.policy_excluded_count,
            "policy_context": self.policy_context.to_dict(),
            "applied_policies": self.applied_policies,
            "complexity_profile": self.complexity_profile,
            "allowed_candidates": [c.to_dict() for c in self.allowed_candidates],
            "policy_excluded_candidates": [p.to_dict() for p in self.policy_excluded_candidates],
            "capability_excluded_models": [e.to_dict() for e in self.capability_excluded_models],
        }
