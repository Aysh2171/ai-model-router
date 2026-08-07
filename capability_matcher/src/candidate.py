"""
Candidate Model and Match Result Output Representations.
Defines CandidateModel, ExcludedModel, and CapabilityMatchResult data structures passed to downstream router engines.
"""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
from model_registry.src import ModelInfo
from .requirements import MatchRequirements


@dataclass
class CandidateModel:
    """Represents an eligible foundation model that satisfies all technical hard constraints."""

    model_id: str
    provider: str
    family: str
    model_info: ModelInfo
    context_headroom: int
    matched_constraints: List[str] = field(default_factory=list)
    matched_constraint_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert CandidateModel into dictionary payload."""
        return {
            "model_id": self.model_id,
            "provider": self.provider,
            "family": self.family,
            "context_headroom": self.context_headroom,
            "matched_constraint_count": self.matched_constraint_count,
            "matched_constraints": self.matched_constraints,
            "model_info": self.model_info.to_dict(),
        }


@dataclass
class ExcludedModel:
    """Captures granular audit trace for models disqualified during feasibility matching."""

    model_id: str
    provider: str
    exclusion_reasons: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert ExcludedModel into dictionary payload."""
        return {
            "model_id": self.model_id,
            "provider": self.provider,
            "exclusion_reasons": self.exclusion_reasons,
        }


@dataclass
class CapabilityMatchResult:
    """Top-level container object returned by CapabilityMatcher."""

    request_id: str
    is_satisfiable: bool
    complexity_profile: Dict[str, Any]
    requirements: MatchRequirements
    eligible_candidates: List[CandidateModel] = field(default_factory=list)
    excluded_models: List[ExcludedModel] = field(default_factory=list)
    total_registered: int = 0
    eligible_count: int = 0
    excluded_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert CapabilityMatchResult into structured dictionary payload."""
        return {
            "request_id": self.request_id,
            "is_satisfiable": self.is_satisfiable,
            "total_registered": self.total_registered,
            "eligible_count": self.eligible_count,
            "excluded_count": self.excluded_count,
            "complexity_profile": self.complexity_profile,
            "requirements": self.requirements.to_dict(),
            "eligible_candidates": [c.to_dict() for c in self.eligible_candidates],
            "excluded_models": [e.to_dict() for e in self.excluded_models],
        }
