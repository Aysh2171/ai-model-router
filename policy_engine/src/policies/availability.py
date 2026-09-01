"""
Provider Availability Runtime Policy Implementation.
Evaluates candidate models against active provider credentials configured in the server environment.
Skips candidate models if their underlying provider lacks active credentials, enabling automatic fallback.
"""

import os
from typing import Dict, Optional, Set
from ranking_engine.src import RankedModel
from ..context import PolicyContext
from ..usage import UsageState
from ..decisions import FailureReason
from .base import BasePolicy, PolicyEvaluationOutcome

PROVIDER_ENV_KEY_MAP: Dict[str, list[str]] = {
    "google": ["GEMINI_API_KEY", "GOOGLE_API_KEY"],
    "deepseek": ["DEEPSEEK_API_KEY"],
    "groq": ["GROQ_API_KEY"],
    "openrouter": ["OPENROUTER_API_KEY"],
    "mistral": ["MISTRAL_API_KEY"],
    "nvidia": ["NVIDIA_API_KEY"],
    "meta": ["GROQ_API_KEY", "OPENROUTER_API_KEY", "META_API_KEY"],
    "openai": ["OPENAI_API_KEY"],
    "anthropic": ["ANTHROPIC_API_KEY"],
    "cohere": ["COHERE_API_KEY"],
    "xai": ["XAI_API_KEY", "GROK_API_KEY"],
    "minimax": ["MINIMAX_API_KEY"],
}


class ProviderAvailabilityPolicy(BasePolicy):
    """
    Policy ensuring only models from providers with verified, configured credentials are selected for dispatch.
    Unconfigured providers fail this policy with PROVIDER_UNAVAILABLE, triggering automatic rank fallback.
    """

    def __init__(self, name: str = "provider_availability_policy"):
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    @staticmethod
    def is_provider_available(provider_name: str) -> bool:
        """Check if provider has any non-empty credential configured in the environment."""
        if not provider_name:
            return False
        p_key = provider_name.strip().lower()
        env_vars = PROVIDER_ENV_KEY_MAP.get(p_key, [f"{provider_name.upper()}_API_KEY"])
        for var_name in env_vars:
            val = os.environ.get(var_name, "").strip()
            if val and len(val) > 5:
                return True
        return False

    def evaluate(self, ranked_model: RankedModel, context: PolicyContext, usage: UsageState) -> PolicyEvaluationOutcome:
        # If policy context explicitly disables availability filtering (e.g. for pure simulation / offline audits)
        if hasattr(context, "require_available_credentials") and not context.require_available_credentials:
            return PolicyEvaluationOutcome(
                passed=True,
                policy_name=self.name,
                explanation="Availability check bypassed by policy context."
            )

        provider = ranked_model.provider
        if not self.is_provider_available(provider):
            return PolicyEvaluationOutcome(
                passed=False,
                policy_name=self.name,
                failure_reason=FailureReason.PROVIDER_UNAVAILABLE.value,
                explanation=f"Provider '{provider}' is not configured with active API credentials in server environment."
            )

        return PolicyEvaluationOutcome(
            passed=True,
            policy_name=self.name,
            explanation=f"Provider '{provider}' has verified active API credentials."
        )
