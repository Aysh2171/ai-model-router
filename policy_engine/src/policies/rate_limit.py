"""
Rate Limiting Governance Policy.
Enforces window-based request rate limits.
"""

from ranking_engine.src import RankedModel
from .base import BasePolicy, PolicyEvaluationOutcome
from ..context import PolicyContext
from ..usage import UsageState
from ..decisions import FailureReason


class RateLimitPolicy(BasePolicy):
    """Enforces request rate limits within the current time window."""

    @property
    def name(self) -> str:
        return "RateLimitPolicy"

    def evaluate(self, ranked_model: RankedModel, context: PolicyContext, usage: UsageState) -> PolicyEvaluationOutcome:
        if context.max_requests_per_window is None:
            return PolicyEvaluationOutcome(passed=True, policy_name=self.name)

        if usage.requests_in_window >= context.max_requests_per_window:
            return PolicyEvaluationOutcome(
                passed=False,
                policy_name=self.name,
                failure_reason=FailureReason.RATE_LIMIT_EXCEEDED.value,
                explanation=f"Rate limit exceeded: Requests in window ({usage.requests_in_window}) >= Max allowed ({context.max_requests_per_window})."
            )

        return PolicyEvaluationOutcome(passed=True, policy_name=self.name)
