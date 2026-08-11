"""
Organizational Provider Governance Policy Rules.
Implements AllowedProvidersRule and DisallowedProvidersRule.
"""

from capability_matcher.src import CandidateModel
from .base import BaseRule, RuleOutcome
from ..context import PolicyContext


class AllowedProvidersRule(BaseRule):
    """Enforces organizational provider whitelist policies."""

    @property
    def name(self) -> str:
        return "AllowedProvidersRule"

    def evaluate(self, candidate: CandidateModel, context: PolicyContext) -> RuleOutcome:
        if context.allowed_providers is None:
            return RuleOutcome(passed=True, rule_name=self.name)

        allowed_lower = {p.lower() for p in context.allowed_providers}
        if candidate.provider.lower() not in allowed_lower:
            return RuleOutcome(
                passed=False,
                rule_name=self.name,
                reason=f"Provider '{candidate.provider}' is not in allowed_providers whitelist {sorted(list(context.allowed_providers))}"
            )
        return RuleOutcome(passed=True, rule_name=self.name)


class DisallowedProvidersRule(BaseRule):
    """Enforces organizational provider blacklist policies."""

    @property
    def name(self) -> str:
        return "DisallowedProvidersRule"

    def evaluate(self, candidate: CandidateModel, context: PolicyContext) -> RuleOutcome:
        if not context.disallowed_providers:
            return RuleOutcome(passed=True, rule_name=self.name)

        disallowed_lower = {p.lower() for p in context.disallowed_providers}
        if candidate.provider.lower() in disallowed_lower:
            return RuleOutcome(
                passed=False,
                rule_name=self.name,
                reason=f"Provider '{candidate.provider}' is in disallowed_providers blacklist {sorted(list(context.disallowed_providers))}"
            )
        return RuleOutcome(passed=True, rule_name=self.name)
