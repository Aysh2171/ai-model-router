"""
Runtime Governance Policy Context and Limits Configuration.
Defines PolicyContext dataclass encapsulating tenant runtime limits, quota thresholds, and fallback parameters.
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional


DEFAULT_COST_TIER_UNITS: Dict[str, float] = {
    "low": 1.0,
    "medium": 3.0,
    "high": 7.0,
    "premium": 12.0,
}


@dataclass
class PolicyContext:
    """Dataclass encapsulating tenant runtime governance limits and fallback configuration."""

    tenant_id: str = "default_tenant"
    environment: str = "production"

    # Budget Governance Limits
    budget_limit: Optional[float] = None
    cost_tier_units: Dict[str, float] = field(default_factory=lambda: dict(DEFAULT_COST_TIER_UNITS))

    # Quota Limits
    max_tokens_per_request: Optional[int] = None
    requested_tokens: int = 1000
    daily_request_limit: Optional[int] = None
    daily_token_limit: Optional[int] = None
    monthly_request_limit: Optional[int] = None
    monthly_token_limit: Optional[int] = None

    # Rate Limiting Limits
    max_requests_per_window: Optional[int] = None

    # Fallback Governance
    fallback_enabled: bool = True
    max_fallback_attempts: int = 3

    def __post_init__(self) -> None:
        """Validate numeric limits upon instantiation."""
        self.validate()

    def validate(self) -> None:
        """Validate runtime limits and fallback parameters to prevent invalid policy configurations."""
        if self.budget_limit is not None and self.budget_limit < 0.0:
            raise ValueError(f"budget_limit cannot be negative ({self.budget_limit}).")

        if self.requested_tokens < 0:
            raise ValueError(f"requested_tokens cannot be negative ({self.requested_tokens}).")

        int_limits = {
            "max_tokens_per_request": self.max_tokens_per_request,
            "daily_request_limit": self.daily_request_limit,
            "daily_token_limit": self.daily_token_limit,
            "monthly_request_limit": self.monthly_request_limit,
            "monthly_token_limit": self.monthly_token_limit,
            "max_requests_per_window": self.max_requests_per_window,
        }

        for name, val in int_limits.items():
            if val is not None and val < 0:
                raise ValueError(f"Limit '{name}' cannot be negative ({val}).")

        if self.max_fallback_attempts < 0:
            raise ValueError(f"max_fallback_attempts cannot be negative ({self.max_fallback_attempts}).")

    def to_dict(self) -> Dict[str, Any]:
        """Convert PolicyContext instance into dictionary payload."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PolicyContext":
        """Instantiate PolicyContext from dictionary."""
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered_data)
