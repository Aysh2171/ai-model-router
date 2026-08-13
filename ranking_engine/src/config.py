"""
Ranking Configuration and Weights Specification.
Defines RankingConfig dataclass with deterministic weight validation and normalization rules.
"""

from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional


@dataclass
class RankingConfig:
    """Dataclass encapsulating ranking criteria weights and operational preference flags."""

    cost_weight: float = 0.30
    latency_weight: float = 0.25
    suitability_weight: float = 0.25
    headroom_weight: float = 0.20
    prefer_lower_cost: bool = True
    prefer_lower_latency: bool = True

    def __post_init__(self) -> None:
        """Validate and normalize weights deterministically upon instantiation."""
        self.validate_and_normalize()

    def validate_and_normalize(self) -> None:
        """Validate non-negative weight constraint and normalize sum to 1.0."""
        weights = {
            "cost_weight": self.cost_weight,
            "latency_weight": self.latency_weight,
            "suitability_weight": self.suitability_weight,
            "headroom_weight": self.headroom_weight,
        }

        for name, val in weights.items():
            if not isinstance(val, (int, float)):
                raise ValueError(f"Ranking weight '{name}' must be a numeric value, got {type(val).__name__}.")
            if val < 0.0:
                raise ValueError(f"Ranking weight '{name}' cannot be negative ({val}).")

        total = sum(weights.values())
        if total <= 0.0:
            raise ValueError("Sum of ranking weights must be strictly greater than zero.")

        # Normalize weights if total does not equal 1.0 (with 1e-4 tolerance)
        if abs(total - 1.0) > 1e-4:
            self.cost_weight = round(self.cost_weight / total, 4)
            self.latency_weight = round(self.latency_weight / total, 4)
            self.suitability_weight = round(self.suitability_weight / total, 4)
            self.headroom_weight = round(self.headroom_weight / total, 4)

            new_total = round(self.cost_weight + self.latency_weight + self.suitability_weight + self.headroom_weight, 4)
            diff = round(1.0 - new_total, 4)
            if abs(diff) > 0.0:
                weight_pairs = [
                    ("cost_weight", self.cost_weight),
                    ("latency_weight", self.latency_weight),
                    ("suitability_weight", self.suitability_weight),
                    ("headroom_weight", self.headroom_weight),
                ]
                non_zero_pairs = [p for p in weight_pairs if p[1] > 0.0]
                if non_zero_pairs:
                    largest_name = max(non_zero_pairs, key=lambda p: p[1])[0]
                    current_val = getattr(self, largest_name)
                    setattr(self, largest_name, round(current_val + diff, 4))

    def to_dict(self) -> Dict[str, Any]:
        """Convert RankingConfig instance into dictionary payload."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RankingConfig":
        """Instantiate RankingConfig from dictionary."""
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered_data)
