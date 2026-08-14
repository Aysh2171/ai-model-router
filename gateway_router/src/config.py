"""
Gateway Router Configuration Specification.
Defines GatewayConfig dataclass with validation and serialization rules.
"""

from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional
from pathlib import Path
import json


DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "default_gateway_config.json"


@dataclass
class GatewayConfig:
    """Dataclass encapsulating execution parameters, retry bounds, and simulation options."""

    max_retries: int = 2
    retry_delay_ms: float = 0.0
    timeout_seconds: float = 30.0
    execution_mode: str = "mock"
    enable_streaming: bool = True
    default_simulated_latency_ms: float = 15.0

    def __post_init__(self) -> None:
        """Validate configuration parameters upon instantiation."""
        self.validate()

    def validate(self) -> None:
        """Validate numeric bounds to prevent invalid gateway execution configurations."""
        if self.max_retries < 0:
            raise ValueError(f"max_retries cannot be negative ({self.max_retries}).")
        if self.retry_delay_ms < 0:
            raise ValueError(f"retry_delay_ms cannot be negative ({self.retry_delay_ms}).")
        if self.timeout_seconds <= 0:
            raise ValueError(f"timeout_seconds must be strictly positive ({self.timeout_seconds}).")
        if self.default_simulated_latency_ms < 0:
            raise ValueError(f"default_simulated_latency_ms cannot be negative ({self.default_simulated_latency_ms}).")

    def to_dict(self) -> Dict[str, Any]:
        """Convert GatewayConfig instance into dictionary payload."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GatewayConfig":
        """Instantiate GatewayConfig from dictionary."""
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered_data)

    @classmethod
    def load_default(cls, config_path: Optional[Path] = None) -> "GatewayConfig":
        """Load GatewayConfig from JSON file or fall back to defaults."""
        path = config_path or DEFAULT_CONFIG_PATH
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return cls.from_dict(json.load(f))
            except Exception:
                pass
        return cls()
