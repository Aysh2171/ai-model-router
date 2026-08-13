"""
Policy Engine Core Orchestrator.
Evaluates runtime governance policies across pre-ranked candidate models in strict rank order without re-ranking.
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from ranking_engine.src import RankingResult, RankedModel
from .context import PolicyContext
from .usage import UsageState
from .result import PolicyEvaluation, PolicyDecision
from .decisions import DecisionState, FailureReason
from .policies import BasePolicy, DEFAULT_POLICIES, BudgetPolicy

DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "default_policy.json"


REQUEST_LEVEL_FAILURES = {
    FailureReason.RATE_LIMIT_EXCEEDED.value,
    FailureReason.REQUEST_QUOTA_EXCEEDED.value,
    FailureReason.TOKEN_QUOTA_EXCEEDED.value,
}


class PolicyEngine:
    """Core runtime governance decision engine executing policy evaluation and ordered fallback dispatch."""

    def __init__(self, policies: Optional[List[BasePolicy]] = None, default_config_path: Optional[Path] = None):
        """Initialize PolicyEngine with custom or default runtime policy evaluators."""
        self.policies: List[BasePolicy] = policies if policies is not None else list(DEFAULT_POLICIES)
        self.default_config_path = default_config_path or DEFAULT_CONFIG_PATH
        self._default_policy_data = self._load_default_config()

    def _load_default_config(self) -> Dict[str, Any]:
        """Load default declarative policy configuration dictionary from JSON file."""
        if self.default_config_path.exists():
            try:
                with open(self.default_config_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def get_default_context(self) -> PolicyContext:
        """Construct PolicyContext instance from default declarative policy JSON."""
        if self._default_policy_data:
            return PolicyContext.from_dict(self._default_policy_data)
        return PolicyContext()

    def evaluate(
        self,
        ranking_result: RankingResult,
        context: Optional[PolicyContext] = None,
        usage_state: Optional[UsageState] = None,
        **context_overrides: Any
    ) -> PolicyDecision:
        """
        Evaluate runtime governance policies on the pre-ranked candidates inside RankingResult.

        Args:
            ranking_result: RankingResult from Module 5 (Ranking Engine).
            context: Optional PolicyContext instance. If omitted, constructed from default_policy.json.
            usage_state: Optional UsageState instance. If omitted, initialized as a fresh in-memory state.
            **context_overrides: Optional key-value overrides for PolicyContext parameters.

        Returns:
            PolicyDecision object containing final dispatch state, selected model, fallback metadata, and audit trace.
        """
        # Resolve effective policy context
        if context is None:
            if self._default_policy_data:
                effective_context = PolicyContext.from_dict(self._default_policy_data)
            else:
                effective_context = PolicyContext()
        else:
            effective_context = context

        if context_overrides:
            ctx_dict = effective_context.to_dict()
            ctx_dict.update(context_overrides)
            effective_context = PolicyContext.from_dict(ctx_dict)

        # Resolve usage state
        effective_usage = usage_state if usage_state is not None else UsageState(tenant_id=effective_context.tenant_id)
        applied_policies = [p.name for p in self.policies]

        # Handle empty/unsatisfiable ranking result
        if not ranking_result or not ranking_result.is_satisfiable or not ranking_result.ranked_candidates:
            return PolicyDecision(
                request_id=ranking_result.request_id if ranking_result else "REQ-000",
                decision=DecisionState.NO_CANDIDATE,
                selected_model=None,
                selected_rank=None,
                fallback_used=False,
                fallback_attempts=0,
                evaluated_candidates=[],
                applied_policies=applied_policies,
                usage_state_snapshot=effective_usage.to_dict(),
            )

        evaluated_candidates: List[PolicyEvaluation] = []
        fallback_attempts = 0
        budget_policy_ref = next((p for p in self.policies if isinstance(p, BudgetPolicy)), BudgetPolicy())

        # Iterate through pre-ranked candidates in STRICT rank order (Rank #1 -> Rank #2 -> Rank #3...)
        for rank_idx, candidate in enumerate(ranking_result.ranked_candidates):
            est_cost = budget_policy_ref.estimate_cost(candidate, effective_context)

            # Fallback policy governance checks if this is a fallback attempt
            if rank_idx > 0:
                if not effective_context.fallback_enabled:
                    break
                if fallback_attempts > effective_context.max_fallback_attempts:
                    break

            # Evaluate each runtime policy against the candidate model
            candidate_failures: List[str] = []
            candidate_explanations: List[str] = []

            for policy in self.policies:
                outcome = policy.evaluate(candidate, effective_context, effective_usage)
                if not outcome.passed:
                    if outcome.failure_reason:
                        candidate_failures.append(outcome.failure_reason)
                    if outcome.explanation:
                        candidate_explanations.append(outcome.explanation)

            if not candidate_failures:
                # Candidate passed ALL policies!
                is_fallback = (rank_idx > 0)
                decision_state = DecisionState.APPROVED_WITH_FALLBACK if is_fallback else DecisionState.APPROVED

                evaluated_candidates.append(
                    PolicyEvaluation(
                        model_id=candidate.model_id,
                        provider=candidate.provider,
                        rank_position=candidate.rank_position,
                        allowed=True,
                        failure_reasons=[],
                        explanations=["All runtime governance policies satisfied."],
                        estimated_cost=est_cost,
                        fallback_eligible=True,
                        ranked_model=candidate,
                    )
                )

                # Record successful dispatch in usage state
                effective_usage.record_dispatch(est_cost, effective_context.requested_tokens)

                return PolicyDecision(
                    request_id=ranking_result.request_id,
                    decision=decision_state,
                    selected_model=candidate,
                    selected_rank=candidate.rank_position,
                    fallback_used=is_fallback,
                    fallback_attempts=fallback_attempts,
                    evaluated_candidates=evaluated_candidates,
                    applied_policies=applied_policies,
                    usage_state_snapshot=effective_usage.to_dict(),
                )
            else:
                # Candidate failed 1 or more runtime policies
                evaluated_candidates.append(
                    PolicyEvaluation(
                        model_id=candidate.model_id,
                        provider=candidate.provider,
                        rank_position=candidate.rank_position,
                        allowed=False,
                        failure_reasons=candidate_failures,
                        explanations=candidate_explanations,
                        estimated_cost=est_cost,
                        fallback_eligible=True,
                        ranked_model=candidate,
                    )
                )
                fallback_attempts += 1

                # Short-circuit fallback evaluation immediately if failure is request/tenant-level
                if any(f in REQUEST_LEVEL_FAILURES for f in candidate_failures):
                    break

        # All candidates failed runtime policy checks
        return PolicyDecision(
            request_id=ranking_result.request_id,
            decision=DecisionState.REJECTED,
            selected_model=None,
            selected_rank=None,
            fallback_used=False,
            fallback_attempts=fallback_attempts,
            evaluated_candidates=evaluated_candidates,
            applied_policies=applied_policies,
            usage_state_snapshot=effective_usage.to_dict(),
        )
