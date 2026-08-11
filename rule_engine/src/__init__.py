"""
Rule Engine Package Initializer.
Exposes RuleEngine, PolicyContext, PolicyExcludedModel, RuleEvaluationResult, BaseRule, and built-in rules.
"""

from .context import PolicyContext, COST_TIER_ORDER
from .result import PolicyExcludedModel, RuleEvaluationResult
from .rules import (
    BaseRule,
    RuleOutcome,
    AllowedProvidersRule,
    DisallowedProvidersRule,
    DataResidencyRule,
    SecurityComplianceRule,
    TenantAccessTierRule,
    MaxCostTierRule,
    DEFAULT_RULES,
)
from .engine import RuleEngine

__all__ = [
    "PolicyContext",
    "COST_TIER_ORDER",
    "PolicyExcludedModel",
    "RuleEvaluationResult",
    "BaseRule",
    "RuleOutcome",
    "AllowedProvidersRule",
    "DisallowedProvidersRule",
    "DataResidencyRule",
    "SecurityComplianceRule",
    "TenantAccessTierRule",
    "MaxCostTierRule",
    "DEFAULT_RULES",
    "RuleEngine",
]
