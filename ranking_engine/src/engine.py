"""
Ranking Engine Orchestrator.
Evaluates criteria scoring algorithms, performs deterministic tie-breaking, and produces ranked candidate lists.
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from rule_engine.src import RuleEvaluationResult
from capability_matcher.src import CandidateModel
from .config import RankingConfig
from .result import RankedModel, RankingResult
from .scoring import ComponentScorer

DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "default_ranking_policy.json"


class RankingEngine:
    """Core evaluation engine performing preference scoring and deterministic model candidate ranking."""

    def __init__(self, config: Optional[RankingConfig] = None, default_config_path: Optional[Path] = None):
        """Initialize RankingEngine with custom or default ranking configuration."""
        self.default_config_path = default_config_path or DEFAULT_CONFIG_PATH
        self._default_config_data = self._load_default_config()

        if config is not None:
            self.config = config
        elif self._default_config_data:
            self.config = RankingConfig.from_dict(self._default_config_data)
        else:
            self.config = RankingConfig()

    def _load_default_config(self) -> Dict[str, Any]:
        """Load default declarative ranking policy dictionary from JSON configuration file."""
        if self.default_config_path.exists():
            try:
                with open(self.default_config_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def get_default_config(self) -> RankingConfig:
        """Construct RankingConfig instance from default declarative JSON file."""
        if self._default_config_data:
            return RankingConfig.from_dict(self._default_config_data)
        return RankingConfig()

    def rank(
        self,
        rule_evaluation_result: RuleEvaluationResult,
        config: Optional[RankingConfig] = None,
        **config_overrides: Any
    ) -> RankingResult:
        """
        Rank allowed candidate models produced by Rule Engine (Module 4).

        Args:
            rule_evaluation_result: RuleEvaluationResult from Module 4.
            config: Optional RankingConfig override.
            **config_overrides: Optional key-value overrides for RankingConfig parameters.

        Returns:
            RankingResult container with ordered candidates and selection metadata.
        """
        # Resolve effective ranking config
        effective_config = config or self.config
        if config_overrides:
            config_dict = effective_config.to_dict()
            config_dict.update(config_overrides)
            effective_config = RankingConfig.from_dict(config_dict)

        return self.rank_candidates(
            candidates=rule_evaluation_result.allowed_candidates,
            config=effective_config,
            request_id=rule_evaluation_result.request_id,
            complexity_profile=rule_evaluation_result.complexity_profile,
            policy_excluded_count=rule_evaluation_result.policy_excluded_count,
            capability_excluded_count=len(rule_evaluation_result.capability_excluded_models),
        )

    def rank_candidates(
        self,
        candidates: List[CandidateModel],
        config: RankingConfig,
        request_id: str = "REQ-000",
        complexity_profile: Optional[Dict[str, Any]] = None,
        policy_excluded_count: int = 0,
        capability_excluded_count: int = 0
    ) -> RankingResult:
        """
        Score and rank a list of CandidateModel objects deterministically.
        Uses primary score, secondary headroom, and tertiary model_id for deterministic tie-breaking.
        """
        profile = complexity_profile or {}

        # Handle empty candidate list
        if not candidates:
            return RankingResult(
                request_id=request_id,
                is_satisfiable=False,
                selected_model=None,
                ranked_candidates=[],
                total_candidates=0,
                ranking_policy_applied=config.to_dict(),
                complexity_profile=profile,
                policy_excluded_count=policy_excluded_count,
                capability_excluded_count=capability_excluded_count,
            )

        # Batch max headroom calculation for relative normalization
        batch_max_headroom = max((c.context_headroom for c in candidates), default=0)

        scored_tuples = []
        for candidate in candidates:
            overall_score, component_scores, explanation = ComponentScorer.compute_candidate_score(
                candidate=candidate,
                config=config,
                complexity_profile=profile,
                batch_max_headroom=batch_max_headroom
            )
            scored_tuples.append((candidate, overall_score, component_scores, explanation))

        # Deterministic Sort:
        # 1. -overall_score (descending)
        # 2. -context_headroom (descending)
        # 3. model_id (ascending)
        scored_tuples.sort(
            key=lambda item: (-item[1], -item[0].context_headroom, item[0].model_id)
        )

        ranked_models: List[RankedModel] = []
        for position, (cand, score, comp_scores, exp) in enumerate(scored_tuples, start=1):
            ranked_models.append(
                RankedModel(
                    model_id=cand.model_id,
                    provider=cand.provider,
                    family=cand.family,
                    candidate=cand,
                    overall_score=score,
                    rank_position=position,
                    component_scores=comp_scores,
                    scoring_explanation=exp,
                )
            )

        selected_model = ranked_models[0] if ranked_models else None

        return RankingResult(
            request_id=request_id,
            is_satisfiable=True,
            selected_model=selected_model,
            ranked_candidates=ranked_models,
            total_candidates=len(ranked_models),
            ranking_policy_applied=config.to_dict(),
            complexity_profile=profile,
            policy_excluded_count=policy_excluded_count,
            capability_excluded_count=capability_excluded_count,
        )
