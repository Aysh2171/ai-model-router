"""
Policy Context and Configuration Data Models.
Defines PolicyContext and PolicyConfig dataclasses encapsulating tenant governance parameters.
"""

from dataclasses import dataclass, field
from typing import Set, Optional, Dict, Any, List


COST_TIER_ORDER: Dict[str, int] = {
    "low": 1,
    "medium": 2,
    "high": 3,
    "premium": 4
}


@dataclass
class PolicyContext:
    """Dataclass encapsulating tenant metadata, security compliance tags, and organizational constraints."""

    tenant_id: str = "default_tenant"
    tenant_tier: str = "standard"
    environment: str = "production"
    allowed_providers: Optional[Set[str]] = None
    disallowed_providers: Optional[Set[str]] = None
    data_residency_region: Optional[str] = None
    required_compliance_tags: Set[str] = field(default_factory=set)
    max_cost_tier: Optional[str] = None
    allowed_model_statuses: Set[str] = field(default_factory=lambda: {"available"})

    def to_dict(self) -> Dict[str, Any]:
        """Convert PolicyContext instance into dictionary payload."""
        return {
            "tenant_id": self.tenant_id,
            "tenant_tier": self.tenant_tier,
            "environment": self.environment,
            "allowed_providers": sorted(list(self.allowed_providers)) if self.allowed_providers is not None else None,
            "disallowed_providers": sorted(list(self.disallowed_providers)) if self.disallowed_providers is not None else None,
            "data_residency_region": self.data_residency_region,
            "required_compliance_tags": sorted(list(self.required_compliance_tags)),
            "max_cost_tier": self.max_cost_tier,
            "allowed_model_statuses": sorted(list(self.allowed_model_statuses)),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PolicyContext":
        """Instantiate PolicyContext from dictionary, handling set conversions cleanly."""
        allowed_prov = set(data["allowed_providers"]) if data.get("allowed_providers") is not None else None
        disallowed_prov = set(data["disallowed_providers"]) if data.get("disallowed_providers") is not None else None
        compliance_tags = set(data.get("required_compliance_tags", []))
        statuses = set(data.get("allowed_model_statuses", ["available"]))

        return cls(
            tenant_id=data.get("tenant_id", "default_tenant"),
            tenant_tier=data.get("tenant_tier", "standard"),
            environment=data.get("environment", "production"),
            allowed_providers=allowed_prov,
            disallowed_providers=disallowed_prov,
            data_residency_region=data.get("data_residency_region"),
            required_compliance_tags=compliance_tags,
            max_cost_tier=data.get("max_cost_tier"),
            allowed_model_statuses=statuses,
        )
