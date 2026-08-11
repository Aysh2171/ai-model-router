"""
Organizational Cost Governance Policy Rule.
Enforces max allowed model cost tiers using deterministic cost order comparisons.
"""

from capability_matcher.src import CandidateModel
from .base import BaseRule, RuleOutcome
from ..context import PolicyContext, COST_TIER_ORDER


class MaxCostTierRule(BaseRule):
    """Enforces maximum allowable model cost tier policies using deterministic cost order."""

    @property
    def name(self) -> str:
        return "MaxCostTierRule"

    def evaluate(self, candidate: CandidateModel, context: PolicyContext) -> RuleOutcome:
        if not context.max_cost_tier:
            return RuleOutcome(passed=True, rule_name=self.name)

        max_cap_lower = context.max_cost_tier.lower()
        candidate_cost_lower = candidate.model_info.cost_tier.lower()

        max_cap_rank = COST_TIER_ORDER.get(max_cap_lower, 4)
        candidate_rank = COST_TIER_ORDER.get(candidate_cost_lower, 4)

        if candidate_rank > max_cap_rank:
            return RuleOutcome(
                passed=False,
                rule_name=self.name,
                reason=f"Model cost tier '{candidate.model_info.cost_tier}' exceeds tenant max_cost_tier cap '{context.max_cost_tier}'"
            )

        return RuleOutcome(passed=True, rule_name=self.name)
