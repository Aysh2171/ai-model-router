"""
Rules Package Initializer.
Exposes BaseRule, RuleOutcome, and all built-in organizational policy rule implementations.
"""

from .base import BaseRule, RuleOutcome
from .provider_rules import AllowedProvidersRule, DisallowedProvidersRule
from .residency_rules import DataResidencyRule
from .compliance_rules import SecurityComplianceRule, TenantAccessTierRule
from .cost_rules import MaxCostTierRule

DEFAULT_RULES = [
    AllowedProvidersRule(),
    DisallowedProvidersRule(),
    DataResidencyRule(),
    SecurityComplianceRule(),
    TenantAccessTierRule(),
    MaxCostTierRule(),
]

__all__ = [
    "BaseRule",
    "RuleOutcome",
    "AllowedProvidersRule",
    "DisallowedProvidersRule",
    "DataResidencyRule",
    "SecurityComplianceRule",
    "TenantAccessTierRule",
    "MaxCostTierRule",
    "DEFAULT_RULES",
]
