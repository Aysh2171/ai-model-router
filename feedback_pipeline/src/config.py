"""
Feedback Pipeline Configuration.
Defines FeedbackConfig dataclass managing database connection URLs and telemetry retention parameters.
"""

from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional
from pathlib import Path
import json
import os


DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "default_feedback_config.json"


@dataclass
class FeedbackConfig:
    """Dataclass encapsulating database settings, prompt retention policy, and feedback collection rules."""

    database_url: str = "sqlite:///:memory:"
    store_full_prompt: bool = False
    max_prompt_summary_length: int = 200
    enable_feedback_collection: bool = True
    analytics_cache_ttl_seconds: int = 60

    def __post_init__(self) -> None:
        """Validate numeric limits upon initialization."""
        self.validate()

    def validate(self) -> None:
        """Validate configuration properties."""
        if self.max_prompt_summary_length < 0:
            raise ValueError(f"max_prompt_summary_length cannot be negative ({self.max_prompt_summary_length}).")
        if self.analytics_cache_ttl_seconds < 0:
            raise ValueError(f"analytics_cache_ttl_seconds cannot be negative ({self.analytics_cache_ttl_seconds}).")

    def to_dict(self) -> Dict[str, Any]:
        """Convert FeedbackConfig into dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FeedbackConfig":
        """Instantiate FeedbackConfig from dictionary."""
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered_data)

    @classmethod
    def load_default(cls, config_path: Optional[Path] = None) -> "FeedbackConfig":
        """
        Load FeedbackConfig from JSON file or environment variables, falling back to defaults.
        Environment variable FEEDBACK_DB_URL takes precedence over file settings if present.
        """
        path = config_path or DEFAULT_CONFIG_PATH
        config_data = {}
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    config_data = json.load(f)
            except Exception:
                pass

        instance = cls.from_dict(config_data)

        # Environment variable override for production PostgreSQL deployments
        env_db_url = os.environ.get("FEEDBACK_DB_URL")
        if env_db_url:
            instance.database_url = env_db_url

        return instance
