"""
Ranking Result and Telemetry Data Models.
Defines RankedModel and RankingResult dataclasses for ordered model candidates and selection metadata.
"""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
from capability_matcher.src import CandidateModel


@dataclass
class RankedModel:
    """Represents an allowed candidate model scored and ordered by the Ranking Engine."""

    model_id: str
    provider: str
    family: str
    candidate: CandidateModel
    overall_score: float
    rank_position: int
    component_scores: Dict[str, float] = field(default_factory=dict)
    scoring_explanation: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert RankedModel instance into dictionary payload."""
        return {
            "model_id": self.model_id,
            "provider": self.provider,
            "family": self.family,
            "rank_position": self.rank_position,
            "overall_score": round(self.overall_score, 4),
            "component_scores": {k: round(v, 4) for k, v in self.component_scores.items()},
            "scoring_explanation": self.scoring_explanation,
            "candidate": self.candidate.to_dict(),
        }


@dataclass
class RankingResult:
    """Top-level container object returned by RankingEngine."""

    request_id: str
    is_satisfiable: bool
    selected_model: Optional[RankedModel]
    ranked_candidates: List[RankedModel] = field(default_factory=list)
    total_candidates: int = 0
    ranking_policy_applied: Dict[str, Any] = field(default_factory=dict)
    complexity_profile: Dict[str, Any] = field(default_factory=dict)
    policy_excluded_count: int = 0
    capability_excluded_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert RankingResult into structured dictionary payload."""
        return {
            "request_id": self.request_id,
            "is_satisfiable": self.is_satisfiable,
            "total_candidates": self.total_candidates,
            "selected_model": self.selected_model.to_dict() if self.selected_model else None,
            "ranked_candidates": [r.to_dict() for r in self.ranked_candidates],
            "ranking_policy_applied": self.ranking_policy_applied,
            "complexity_profile": self.complexity_profile,
            "policy_excluded_count": self.policy_excluded_count,
            "capability_excluded_count": self.capability_excluded_count,
        }
