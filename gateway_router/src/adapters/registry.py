"""
Provider Adapter Registry.
Manages provider adapter registrations and explicit provider-to-adapter resolution.
Dynamically resolves live provider adapters when credentials exist in the server environment.
"""

import os
from typing import Dict, Optional, List
from .base import BaseProviderAdapter
from .mock import MockProviderAdapter
from .gemini import GeminiProviderAdapter
from .deepseek import DeepSeekProviderAdapter
from .groq import GroqProviderAdapter
from .openrouter import OpenRouterProviderAdapter
from .mistral import MistralProviderAdapter
from .nvidia import NvidiaProviderAdapter


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
    "Groq",
    "OpenRouter",
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

    def is_provider_available(self, provider: str) -> bool:
        """Check if provider has an active, configured, and available adapter."""
        adapter = self.get(provider)
        if not adapter:
            return False
        return adapter.is_available and adapter.is_configured

    def list_providers(self) -> List[str]:
        """List distinct provider names currently registered."""
        return sorted([a.provider for a in self._adapters.values()])

    def list_available_providers(self) -> List[str]:
        """List provider names that are configured with working live credentials."""
        available = []
        for p in self.list_providers():
            if self.is_provider_available(p):
                available.append(p)
        return available

    def unregister(self, provider: str) -> None:
        """Remove registered adapter for a provider."""
        key = provider.strip().lower()
        if key in self._adapters:
            del self._adapters[key]

    @classmethod
    def create_default(cls) -> "AdapterRegistry":
        """
        Instantiate and populate an AdapterRegistry:
        - Real live adapters for providers with active credentials (Google/Gemini, DeepSeek, Groq, OpenRouter, Mistral, NVIDIA)
        - MockProviderAdapter for testing or unconfigured providers (OpenAI, Anthropic, Cohere, xAI, MiniMax)
        """
        registry = cls()

        # 1. Google / Gemini
        gemini_adapter = GeminiProviderAdapter(provider="Google")
        if gemini_adapter.is_configured:
            registry.register(gemini_adapter)
        else:
            registry.register(MockProviderAdapter(provider="Google"))

        # 2. DeepSeek
        deepseek_adapter = DeepSeekProviderAdapter(provider="DeepSeek")
        if deepseek_adapter.is_configured:
            registry.register(deepseek_adapter)
        else:
            registry.register(MockProviderAdapter(provider="DeepSeek"))

        # 3. Groq
        groq_adapter = GroqProviderAdapter(provider="Groq")
        if groq_adapter.is_configured:
            registry.register(groq_adapter)
        else:
            registry.register(MockProviderAdapter(provider="Groq"))

        # 4. OpenRouter
        openrouter_adapter = OpenRouterProviderAdapter(provider="OpenRouter")
        if openrouter_adapter.is_configured:
            registry.register(openrouter_adapter)
        else:
            registry.register(MockProviderAdapter(provider="OpenRouter"))

        # 5. Mistral
        mistral_adapter = MistralProviderAdapter(provider="Mistral")
        if mistral_adapter.is_configured:
            registry.register(mistral_adapter)
        else:
            registry.register(MockProviderAdapter(provider="Mistral"))

        # 6. NVIDIA
        registry.register(NvidiaProviderAdapter(provider="NVIDIA"))

        # 7. Meta (If Groq is configured, route Meta requests via GroqProviderAdapter or Mock)
        if groq_adapter.is_configured:
            registry.register(GroqProviderAdapter(provider="Meta", default_live_model="llama-3.3-70b-versatile"))
        else:
            registry.register(MockProviderAdapter(provider="Meta"))

        # 8. Remaining Catalog Providers without API keys (OpenAI, Anthropic, Cohere, xAI, MiniMax)
        for provider in ["OpenAI", "Anthropic", "Cohere", "xAI", "MiniMax"]:
            registry.register(MockProviderAdapter(provider=provider))

        return registry

    @classmethod
    def create_mock_only(cls) -> "AdapterRegistry":
        """Instantiate pure mock registry for automated unit tests."""
        registry = cls()
        for provider in KNOWN_CATALOG_PROVIDERS:
            registry.register(MockProviderAdapter(provider=provider))
        return registry
