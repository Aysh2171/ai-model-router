"""
Request and Token Quotas Governance Policy.
Enforces request token bounds, daily/monthly request quotas, and token consumption limits.
"""

from ranking_engine.src import RankedModel
from .base import BasePolicy, PolicyEvaluationOutcome
from ..context import PolicyContext
from ..usage import UsageState
from ..decisions import FailureReason


class QuotaPolicy(BasePolicy):
    """Enforces request-level token bounds and tenant daily/monthly quotas."""

    @property
    def name(self) -> str:
        return "QuotaPolicy"

    def evaluate(self, ranked_model: RankedModel, context: PolicyContext, usage: UsageState) -> PolicyEvaluationOutcome:
        req_tokens = context.requested_tokens

        # 1. Single Request Max Token Limit
        if context.max_tokens_per_request is not None and req_tokens > context.max_tokens_per_request:
            return PolicyEvaluationOutcome(
                passed=False,
                policy_name=self.name,
                failure_reason=FailureReason.TOKEN_QUOTA_EXCEEDED.value,
                explanation=f"Requested tokens ({req_tokens:,}) exceed max_tokens_per_request limit ({context.max_tokens_per_request:,})."
            )

        # 2. Daily Request Limit
        if context.daily_request_limit is not None and usage.daily_requests_used >= context.daily_request_limit:
            return PolicyEvaluationOutcome(
                passed=False,
                policy_name=self.name,
                failure_reason=FailureReason.REQUEST_QUOTA_EXCEEDED.value,
                explanation=f"Daily request quota limit reached ({usage.daily_requests_used}/{context.daily_request_limit})."
            )

        # 3. Daily Token Limit
        if context.daily_token_limit is not None and (usage.daily_tokens_used + req_tokens) > context.daily_token_limit:
            return PolicyEvaluationOutcome(
                passed=False,
                policy_name=self.name,
                failure_reason=FailureReason.TOKEN_QUOTA_EXCEEDED.value,
                explanation=f"Projected daily tokens ({usage.daily_tokens_used + req_tokens:,}) exceed daily_token_limit ({context.daily_token_limit:,})."
            )

        # 4. Monthly Request Limit
        if context.monthly_request_limit is not None and usage.monthly_requests_used >= context.monthly_request_limit:
            return PolicyEvaluationOutcome(
                passed=False,
                policy_name=self.name,
                failure_reason=FailureReason.REQUEST_QUOTA_EXCEEDED.value,
                explanation=f"Monthly request quota limit reached ({usage.monthly_requests_used}/{context.monthly_request_limit})."
            )

        # 5. Monthly Token Limit
        if context.monthly_token_limit is not None and (usage.monthly_tokens_used + req_tokens) > context.monthly_token_limit:
            return PolicyEvaluationOutcome(
                passed=False,
                policy_name=self.name,
                failure_reason=FailureReason.TOKEN_QUOTA_EXCEEDED.value,
                explanation=f"Projected monthly tokens ({usage.monthly_tokens_used + req_tokens:,}) exceed monthly_token_limit ({context.monthly_token_limit:,})."
            )

        return PolicyEvaluationOutcome(passed=True, policy_name=self.name)
