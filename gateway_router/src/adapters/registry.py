"""
Provider Adapter Registry.
Manages provider adapter registrations and explicit provider-to-adapter resolution.
"""

from typing import Dict, Optional, List
from .base import BaseProviderAdapter
from .mock import MockProviderAdapter


KNOWN_CATALOG_PROVIDERS = [
    "OpenAI",
    "Anthropic",
    "Google",
    "Meta",
    "Mistral",
    "DeepSeek",
    "Cohere",
    "xAI",
    "MiniMax",
    "NVIDIA",
]


class AdapterRegistry:
    """Central registry resolving provider names to registered ProviderAdapter instances."""

    def __init__(self):
        self._adapters: Dict[str, BaseProviderAdapter] = {}

    def register(self, adapter: BaseProviderAdapter) -> None:
        """Register a provider adapter instance."""
        key = adapter.provider.strip().lower()
        self._adapters[key] = adapter

    def get(self, provider: str) -> Optional[BaseProviderAdapter]:
        """Look up registered adapter for a provider (case-insensitive). Returns None if not registered."""
        if not provider:
            return None
        key = provider.strip().lower()
        return self._adapters.get(key)

    def has_provider(self, provider: str) -> bool:
        """Check if an adapter is registered for the specified provider."""
        if not provider:
            return False
        return provider.strip().lower() in self._adapters

    def list_providers(self) -> List[str]:
        """List distinct provider names currently registered."""
        return sorted([a.provider for a in self._adapters.values()])

    def unregister(self, provider: str) -> None:
        """Remove registered adapter for a provider."""
        key = provider.strip().lower()
        if key in self._adapters:
            del self._adapters[key]

    @classmethod
    def create_default(cls) -> "AdapterRegistry":
        """
        Instantiate and populate an AdapterRegistry with explicit mock adapters
        for all 10 supported foundation model catalog providers.
        """
        registry = cls()
        for provider in KNOWN_CATALOG_PROVIDERS:
            registry.register(MockProviderAdapter(provider=provider))
        return registry
