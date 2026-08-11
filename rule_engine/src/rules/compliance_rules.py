"""
Security Compliance and Tenant Access Tier Policy Rules.
Implements SecurityComplianceRule and TenantAccessTierRule.
"""

from capability_matcher.src import CandidateModel
from .base import BaseRule, RuleOutcome
from ..context import PolicyContext


class SecurityComplianceRule(BaseRule):
    """Enforces organizational security and regulatory compliance tag policies."""

    @property
    def name(self) -> str:
        return "SecurityComplianceRule"

    def evaluate(self, candidate: CandidateModel, context: PolicyContext) -> RuleOutcome:
        if not context.required_compliance_tags:
            return RuleOutcome(passed=True, rule_name=self.name)

        model_tags = {tag.lower() for tag in candidate.model_info.tags}
        missing_tags = [
            req_tag for req_tag in context.required_compliance_tags
            if req_tag.lower() not in model_tags
        ]

        if missing_tags:
            return RuleOutcome(
                passed=False,
                rule_name=self.name,
                reason=f"Model '{candidate.model_id}' lacks required security/compliance tags: {sorted(missing_tags)}"
            )

        return RuleOutcome(passed=True, rule_name=self.name)


class TenantAccessTierRule(BaseRule):
    """Enforces tenant tier access policies and status restrictions."""

    @property
    def name(self) -> str:
        return "TenantAccessTierRule"

    def evaluate(self, candidate: CandidateModel, context: PolicyContext) -> RuleOutcome:
        # Check model status against allowed statuses in context
        if candidate.model_info.status not in context.allowed_model_statuses:
            return RuleOutcome(
                passed=False,
                rule_name=self.name,
                reason=f"Model status '{candidate.model_info.status}' is not in tenant allowed_model_statuses {sorted(list(context.allowed_model_statuses))}"
            )

        # Restricted features (preview models or premium cost tier) require enterprise tenant tier
        if candidate.model_info.status == "preview" and context.tenant_tier.lower() != "enterprise":
            return RuleOutcome(
                passed=False,
                rule_name=self.name,
                reason=f"Preview model '{candidate.model_id}' requires 'enterprise' tenant tier (current tenant_tier: '{context.tenant_tier}')"
            )

        if candidate.model_info.cost_tier == "premium" and context.tenant_tier.lower() == "standard":
            return RuleOutcome(
                passed=False,
                rule_name=self.name,
                reason=f"Premium cost tier model '{candidate.model_id}' requires 'premium' or 'enterprise' tenant tier (current tenant_tier: '{context.tenant_tier}')"
            )

        return RuleOutcome(passed=True, rule_name=self.name)
