"""
Data model representation for AI foundation models inside the Model Registry.
Defines the ModelInfo dataclass containing structured provider metadata, use cases, modalities, and capability flags.
"""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional


VALID_STATUSES = {"available", "preview", "deprecated"}
VALID_COST_TIERS = {"low", "medium", "high", "premium"}
VALID_LATENCY_TIERS = {"fast", "medium", "slow"}
VALID_MODALITIES = {"text", "image", "audio", "video"}


@dataclass
class ModelInfo:
    """Dataclass representing structured metadata, routing hints, and capabilities of an AI model."""

    provider: str
    family: str
    model_id: str
    display_name: str
    description: str
    status: str = "available"
    is_default: bool = False
    tags: List[str] = field(default_factory=list)
    context_window: int = 128000
    max_output_tokens: int = 4096
    cost_tier: str = "medium"
    latency_tier: str = "medium"
    supported_modalities: List[str] = field(default_factory=lambda: ["text"])
    supported_use_cases: List[str] = field(default_factory=list)

    # Capability Flags
    supports_function_calling: bool = False
    supports_json: bool = False
    supports_streaming: bool = True
    supports_code: bool = False
    supports_tools: bool = False
    supports_audio: bool = False
    supports_vision: bool = False
    supports_multimodal: bool = False
    supports_reasoning: bool = False
    supports_long_context: bool = False
    supports_structured_output: bool = False
    notes: str = ""

    def validate(self) -> None:
        """Validate metadata fields to ensure integrity and prevent invalid routing inputs."""
        if not self.model_id or not isinstance(self.model_id, str):
            raise ValueError("ModelInfo model_id must be a non-empty string.")
        if not self.provider or not isinstance(self.provider, str):
            raise ValueError(f"ModelInfo provider for '{self.model_id}' must be a non-empty string.")
        if not self.family or not isinstance(self.family, str):
            raise ValueError(f"ModelInfo family for '{self.model_id}' must be a non-empty string.")
        if self.status not in VALID_STATUSES:
            raise ValueError(f"Invalid status '{self.status}' for '{self.model_id}'. Expected one of {VALID_STATUSES}.")
        if self.cost_tier not in VALID_COST_TIERS:
            raise ValueError(f"Invalid cost_tier '{self.cost_tier}' for '{self.model_id}'. Expected one of {VALID_COST_TIERS}.")
        if self.latency_tier not in VALID_LATENCY_TIERS:
            raise ValueError(f"Invalid latency_tier '{self.latency_tier}' for '{self.model_id}'. Expected one of {VALID_LATENCY_TIERS}.")
        if self.context_window <= 0:
            raise ValueError(f"Context window for '{self.model_id}' must be positive.")

    def to_dict(self) -> Dict[str, Any]:
        """Convert dataclass instance into a dictionary payload."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ModelInfo":
        """Instantiate ModelInfo from dictionary, enforcing lightweight validation."""
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}

        model_info = cls(**filtered_data)
        model_info.validate()
        return model_info
