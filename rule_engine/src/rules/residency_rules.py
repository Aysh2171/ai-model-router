"""
Organizational Data Residency Governance Policy Rule.
Evaluates data residency compatibility against model catalog tags and metadata attributes.
"""

from capability_matcher.src import CandidateModel
from .base import BaseRule, RuleOutcome
from ..context import PolicyContext


class DataResidencyRule(BaseRule):
    """Enforces data residency compliance policies based on model metadata tags and attributes."""

    @property
    def name(self) -> str:
        return "DataResidencyRule"

    def evaluate(self, candidate: CandidateModel, context: PolicyContext) -> RuleOutcome:
        if not context.data_residency_region:
            return RuleOutcome(passed=True, rule_name=self.name)

        req_region = context.data_residency_region.upper()
        model_tags = {tag.lower() for tag in candidate.model_info.tags}

        # Check for explicit region restriction tags (e.g., 'us-only', 'eu-only')
        conflicting_regions = []
        if req_region == "EU" and "us-only" in model_tags:
            conflicting_regions.append("Model is restricted to US region ('us-only')")
        elif req_region == "US" and "eu-only" in model_tags:
            conflicting_regions.append("Model is restricted to EU region ('eu-only')")

        # Check if requested region requires explicit compliance tag (e.g., 'eu-hosted', 'us-hosted', 'global')
        required_tag = f"{req_region.lower()}-hosted"
        is_region_compatible = (
            "global" in model_tags or
            "global-residency" in model_tags or
            required_tag in model_tags or
            not any(t.endswith("-only") or t.endswith("-hosted") for t in model_tags)
        )

        if conflicting_regions:
            return RuleOutcome(
                passed=False,
                rule_name=self.name,
                reason=f"Data residency constraint '{req_region}' violated: {'; '.join(conflicting_regions)}"
            )

        if not is_region_compatible:
            return RuleOutcome(
                passed=False,
                rule_name=self.name,
                reason=f"Model '{candidate.model_id}' lacks required data residency tag '{required_tag}' for region '{req_region}'"
            )

        return RuleOutcome(passed=True, rule_name=self.name)
