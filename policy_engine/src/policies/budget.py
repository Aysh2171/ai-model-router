"""
Runtime Budget Governance Policy.
Enforces tenant runtime spending and budget limits using prototype simulation cost units.
"""

from ranking_engine.src import RankedModel
from .base import BasePolicy, PolicyEvaluationOutcome
from ..context import PolicyContext, DEFAULT_COST_TIER_UNITS
from ..usage import UsageState
from ..decisions import FailureReason


class BudgetPolicy(BasePolicy):
    """Enforces tenant budget limits against estimated request execution cost."""

    @property
    def name(self) -> str:
        return "BudgetPolicy"

    def estimate_cost(self, ranked_model: RankedModel, context: PolicyContext) -> float:
        """Estimate request cost units from model cost_tier metadata."""
        cost_tier = (ranked_model.candidate.model_info.cost_tier or "medium").lower()
        cost_map = context.cost_tier_units or DEFAULT_COST_TIER_UNITS
        return float(cost_map.get(cost_tier, 3.0))

    def evaluate(self, ranked_model: RankedModel, context: PolicyContext, usage: UsageState) -> PolicyEvaluationOutcome:
        est_cost = self.estimate_cost(ranked_model, context)

        if context.budget_limit is None:
            return PolicyEvaluationOutcome(passed=True, policy_name=self.name, estimated_cost=est_cost)

        projected_total = usage.budget_consumed + est_cost
        if projected_total > context.budget_limit:
            return PolicyEvaluationOutcome(
                passed=False,
                policy_name=self.name,
                failure_reason=FailureReason.BUDGET_EXCEEDED.value,
                explanation=(
                    f"Budget limit exceeded: Projected total {projected_total:.2f} units "
                    f"(Current {usage.budget_consumed:.2f} + Est {est_cost:.2f}) > Limit {context.budget_limit:.2f} units"
                ),
                estimated_cost=est_cost
            )

        return PolicyEvaluationOutcome(passed=True, policy_name=self.name, estimated_cost=est_cost)
