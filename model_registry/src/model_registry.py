"""
Model Registry Core Catalog Service.
Maintains structured metadata for representative AI models and exposes extensible programmatic query APIs.
"""

import json
from pathlib import Path
from typing import List, Dict, Optional, Any
from .model import ModelInfo


DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "models.json"


class ModelRegistry:
    """Central catalog service providing query, filtering, and lookup access for AI foundation model metadata."""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize ModelRegistry and automatically load configured model catalog."""
        self._models: Dict[str, ModelInfo] = {}
        self.load_models(config_path or str(DEFAULT_CONFIG_PATH))

    def load_models(self, config_path: str) -> None:
        """Load and validate model metadata JSON file into memory."""
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"Model Registry configuration file not found at '{config_path}'.")

        with open(path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        if not isinstance(raw_data, list):
            raise ValueError("Invalid configuration format: Expected a JSON array of model objects.")

        loaded_models: Dict[str, ModelInfo] = {}
        for entry in raw_data:
            model_info = ModelInfo.from_dict(entry)
            if model_info.model_id in loaded_models:
                raise ValueError(f"Duplicate model_id '{model_info.model_id}' found in configuration.")
            loaded_models[model_info.model_id] = model_info

        self._models = loaded_models

    def get_all_models(self) -> List[ModelInfo]:
        """Retrieve list of all registered foundation models."""
        return list(self._models.values())

    def get_model(self, model_id: str) -> Optional[ModelInfo]:
        """Retrieve specific model metadata by model_id."""
        return self._models.get(model_id)

    def get_models_by_provider(self, provider: str) -> List[ModelInfo]:
        """Retrieve models belonging to a specific provider (case-insensitive)."""
        target = provider.strip().lower()
        return [m for m in self._models.values() if m.provider.lower() == target]

    def get_models_by_family(self, family: str) -> List[ModelInfo]:
        """Retrieve models belonging to a specific model family (case-insensitive)."""
        target = family.strip().lower()
        return [m for m in self._models.values() if m.family.lower() == target]

    def get_default_model(self, provider: Optional[str] = None, family: Optional[str] = None) -> Optional[ModelInfo]:
        """Retrieve designated default model for a provider or family."""
        candidates = self.get_all_models()
        if provider:
            candidates = [m for m in candidates if m.provider.lower() == provider.strip().lower()]
        if family:
            candidates = [m for m in candidates if m.family.lower() == family.strip().lower()]

        for m in candidates:
            if m.is_default:
                return m
        return candidates[0] if candidates else None

    def get_models_by_cost_tier(self, tier: str) -> List[ModelInfo]:
        """Retrieve models matching a target cost tier ('low', 'medium', 'high', 'premium')."""
        target = tier.strip().lower()
        return [m for m in self._models.values() if m.cost_tier == target]

    def get_models_by_latency_tier(self, tier: str) -> List[ModelInfo]:
        """Retrieve models matching a target latency tier ('fast', 'medium', 'slow')."""
        target = tier.strip().lower()
        return [m for m in self._models.values() if m.latency_tier == target]

    def get_models_supporting(self, modality: str) -> List[ModelInfo]:
        """Retrieve models supporting a specific content modality ('text', 'image', 'audio', 'video')."""
        target = modality.strip().lower()
        return [m for m in self._models.values() if target in [mod.lower() for mod in m.supported_modalities]]

    def get_models_for_use_case(self, use_case: str) -> List[ModelInfo]:
        """Retrieve models supporting a specific workload use case (case-insensitive)."""
        target = use_case.strip().lower()
        return [m for m in self._models.values() if any(target == uc.lower() for uc in m.supported_use_cases)]

    def search_models(self, query: str) -> List[ModelInfo]:
        """Perform case-insensitive substring search across model_id, display_name, provider, family, and tags."""
        q = query.strip().lower()
        if not q:
            return self.get_all_models()

        results = []
        for m in self._models.values():
            if (
                q in m.model_id.lower()
                or q in m.display_name.lower()
                or q in m.provider.lower()
                or q in m.family.lower()
                or any(q in tag.lower() for tag in m.tags)
            ):
                results.append(m)
        return results

    def filter_models(self, **criteria: Any) -> List[ModelInfo]:
        """
        Extensible keyword filtering for complex model queries.
        
        Supported criteria:
        - provider: str
        - family: str
        - status: str
        - is_default: bool
        - cost_tier: str or List[str]
        - latency_tier: str or List[str]
        - min_context_window: int
        - min_max_output_tokens: int
        - required_modalities: List[str]
        - required_use_cases: List[str]
        - tags: List[str]
        - Boolean capability flags (e.g. supports_vision=True, supports_function_calling=True)
        """
        results = self.get_all_models()

        if "provider" in criteria and criteria["provider"] is not None:
            target = criteria["provider"].strip().lower()
            results = [m for m in results if m.provider.lower() == target]

        if "family" in criteria and criteria["family"] is not None:
            target = criteria["family"].strip().lower()
            results = [m for m in results if m.family.lower() == target]

        if "status" in criteria and criteria["status"] is not None:
            target = criteria["status"].strip().lower()
            results = [m for m in results if m.status.lower() == target]

        if "is_default" in criteria and criteria["is_default"] is not None:
            target = bool(criteria["is_default"])
            results = [m for m in results if m.is_default == target]

        if "cost_tier" in criteria and criteria["cost_tier"] is not None:
            tiers = criteria["cost_tier"]
            if isinstance(tiers, str):
                tiers = [tiers]
            tier_set = {t.strip().lower() for t in tiers}
            results = [m for m in results if m.cost_tier in tier_set]

        if "latency_tier" in criteria and criteria["latency_tier"] is not None:
            tiers = criteria["latency_tier"]
            if isinstance(tiers, str):
                tiers = [tiers]
            tier_set = {t.strip().lower() for t in tiers}
            results = [m for m in results if m.latency_tier in tier_set]

        if "min_context_window" in criteria and criteria["min_context_window"] is not None:
            min_cw = int(criteria["min_context_window"])
            results = [m for m in results if m.context_window >= min_cw]

        if "min_max_output_tokens" in criteria and criteria["min_max_output_tokens"] is not None:
            min_out = int(criteria["min_max_output_tokens"])
            results = [m for m in results if m.max_output_tokens >= min_out]

        if "required_modalities" in criteria and criteria["required_modalities"]:
            req_mods = {m.strip().lower() for m in criteria["required_modalities"]}
            results = [
                m for m in results
                if req_mods.issubset({mod.lower() for mod in m.supported_modalities})
            ]

        if "required_use_cases" in criteria and criteria["required_use_cases"]:
            req_cases = {c.strip().lower() for c in criteria["required_use_cases"]}
            results = [
                m for m in results
                if req_cases.issubset({uc.lower() for uc in m.supported_use_cases})
            ]

        if "tags" in criteria and criteria["tags"]:
            req_tags = {t.strip().lower() for t in criteria["tags"]}
            results = [
                m for m in results
                if req_tags.issubset({t.lower() for t in m.tags})
            ]

        # Process boolean capability flags
        capability_flags = [
            "supports_function_calling", "supports_json", "supports_streaming",
            "supports_code", "supports_tools", "supports_audio", "supports_vision",
            "supports_multimodal", "supports_reasoning", "supports_long_context",
            "supports_structured_output"
        ]
        for flag in capability_flags:
            if flag in criteria and criteria[flag] is not None:
                val = bool(criteria[flag])
                results = [m for m in results if getattr(m, flag) == val]

        return results

    def list_providers(self) -> List[str]:
        """List distinct providers in alphabetical order."""
        return sorted(list({m.provider for m in self._models.values()}))

    def list_families(self) -> List[str]:
        """List distinct model families in alphabetical order."""
        return sorted(list({m.family for m in self._models.values()}))

    def list_models(self) -> List[str]:
        """List distinct model_id identifiers in alphabetical order."""
        return sorted(list(self._models.keys()))

    def count_models(self) -> int:
        """Return total count of registered models."""
        return len(self._models)
