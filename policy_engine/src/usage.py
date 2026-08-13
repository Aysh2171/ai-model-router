"""
Runtime Usage State Tracking Data Model.
Defines in-memory UsageState dataclass for tracking tenant budget consumption, quotas, and rate limits.
"""

from dataclasses import dataclass, asdict
from typing import Dict, Any


@dataclass
class UsageState:
    """In-memory representation of tenant runtime usage state for policy evaluation."""

    tenant_id: str = "default_tenant"
    budget_consumed: float = 0.0
    requests_in_window: int = 0
    tokens_in_window: int = 0
    daily_requests_used: int = 0
    daily_tokens_used: int = 0
    monthly_requests_used: int = 0
    monthly_tokens_used: int = 0

    def record_dispatch(self, cost: float, tokens: int) -> None:
        """Record successful request dispatch consumption into in-memory usage state."""
        self.budget_consumed = round(self.budget_consumed + max(0.0, cost), 4)
        self.requests_in_window += 1
        self.tokens_in_window += max(0, tokens)
        self.daily_requests_used += 1
        self.daily_tokens_used += max(0, tokens)
        self.monthly_requests_used += 1
        self.monthly_tokens_used += max(0, tokens)

    def to_dict(self) -> Dict[str, Any]:
        """Convert UsageState instance into dictionary payload."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UsageState":
        """Instantiate UsageState from dictionary."""
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered_data)
