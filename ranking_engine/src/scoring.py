"""
Component Scorer and Criteria Algorithms.
Defines ComponentScorer implementing transparent normalized criteria scoring algorithms [0.0 to 1.0].
"""

from typing import Dict, Any, Tuple
from capability_matcher.src import CandidateModel
from .config import RankingConfig


class ComponentScorer:
    """Computes normalized criteria scores [0.0 - 1.0] and weighted overall scores for candidate models."""

    @staticmethod
    def score_cost(candidate: CandidateModel, prefer_lower_cost: bool = True) -> float:
        """
        Score model cost efficiency based on cost_tier metadata.
        Returns a float between 0.0 and 1.0.
        """
        cost_tier = (candidate.model_info.cost_tier or "medium").lower()
        tier_scores = {
            "low": 1.00,
            "medium": 0.70,
            "high": 0.35,
            "premium": 0.10,
        }
        base_score = tier_scores.get(cost_tier, 0.50)

        if not prefer_lower_cost:
            base_score = round(1.0 - base_score, 4)

        return min(1.0, max(0.0, base_score))

    @staticmethod
    def score_latency(candidate: CandidateModel, prefer_lower_latency: bool = True) -> float:
        """
        Score model latency efficiency based on latency_tier metadata.
        Returns a float between 0.0 and 1.0.
        """
        latency_tier = (candidate.model_info.latency_tier or "medium").lower()
        tier_scores = {
            "fast": 1.00,
            "medium": 0.60,
            "slow": 0.20,
        }
        base_score = tier_scores.get(latency_tier, 0.50)

        if not prefer_lower_latency:
            base_score = round(1.0 - base_score, 4)

        return min(1.0, max(0.0, base_score))

    @staticmethod
    def score_suitability(candidate: CandidateModel, complexity_profile: Dict[str, Any]) -> float:
        """
        Score capability/complexity alignment between model metadata and request complexity profile.
        Returns a float between 0.0 and 1.0.
        """
        raw_tier = complexity_profile.get("complexity") if isinstance(complexity_profile, dict) else None
        tier = None

        if isinstance(raw_tier, str) and raw_tier.strip():
            tier = raw_tier.strip().upper()
        elif isinstance(complexity_profile, dict) and "complexity_score" in complexity_profile:
            try:
                score_val = float(complexity_profile["complexity_score"])
                if score_val <= 30:
                    tier = "LOW"
                elif score_val >= 71:
                    tier = "HIGH"
                else:
                    tier = "MEDIUM"
            except (ValueError, TypeError):
                tier = "MEDIUM"

        if not tier or tier not in {"LOW", "MEDIUM", "HIGH"}:
            tier = "MEDIUM"

        info = candidate.model_info

        if tier == "LOW":
            # For low complexity, lightweight fast models are optimal (1.00), premium cost models are over-provisioned (0.40)
            if info.cost_tier == "low" and info.latency_tier == "fast":
                return 1.00
            elif info.cost_tier in ["low", "medium"]:
                return 0.85
            elif info.cost_tier == "premium":
                return 0.40
            return 0.70

        elif tier == "HIGH":
            # For high complexity, reasoning/high-capacity models are optimal (1.00), low-capacity models are penalized (0.40)
            if info.supports_reasoning or (info.cost_tier in ["high", "premium"] and info.supports_code):
                return 1.00
            elif info.context_window >= 128000 and (info.supports_code or info.supports_tools):
                return 0.85
            elif info.cost_tier == "low":
                return 0.40
            return 0.70

        else:  # MEDIUM complexity
            if info.cost_tier in ["low", "medium"] or info.supports_code:
                return 1.00
            return 0.75

    @staticmethod
    def score_headroom(candidate: CandidateModel, batch_max_headroom: int = 0) -> float:
        """
        Score remaining context headroom tokens using standardized relative scale.
        Returns a float between 0.0 and 1.0.
        """
        headroom = getattr(candidate, "context_headroom", 0)
        if headroom <= 0:
            return 0.0

        if batch_max_headroom > 0:
            ratio = headroom / batch_max_headroom
        else:
            # Standalone evaluation using 200,000 token reference scale
            ratio = headroom / 200000

        return round(min(1.0, max(0.0, ratio)), 4)

    @classmethod
    def compute_candidate_score(
        cls,
        candidate: CandidateModel,
        config: RankingConfig,
        complexity_profile: Dict[str, Any],
        batch_max_headroom: int = 0
    ) -> Tuple[float, Dict[str, float], str]:
        """
        Calculate weighted overall score and component scores breakdown.

        Returns:
            Tuple of (overall_score, component_scores_dict, explanation_str)
        """
        s_cost = cls.score_cost(candidate, prefer_lower_cost=config.prefer_lower_cost)
        s_lat = cls.score_latency(candidate, prefer_lower_latency=config.prefer_lower_latency)
        s_suit = cls.score_suitability(candidate, complexity_profile)
        s_head = cls.score_headroom(candidate, batch_max_headroom=batch_max_headroom)

        overall = (
            (s_cost * config.cost_weight) +
            (s_lat * config.latency_weight) +
            (s_suit * config.suitability_weight) +
            (s_head * config.headroom_weight)
        )
        overall = round(min(1.0, max(0.0, overall)), 4)

        component_scores = {
            "cost": round(s_cost, 4),
            "latency": round(s_lat, 4),
            "suitability": round(s_suit, 4),
            "headroom": round(s_head, 4),
        }

        explanation = (
            f"Overall: {overall:.4f} [Cost={s_cost:.2f} (w={config.cost_weight:.2f}), "
            f"Latency={s_lat:.2f} (w={config.latency_weight:.2f}), "
            f"Suitability={s_suit:.2f} (w={config.suitability_weight:.2f}), "
            f"Headroom={s_head:.2f} (w={config.headroom_weight:.2f})]"
        )

        return overall, component_scores, explanation
