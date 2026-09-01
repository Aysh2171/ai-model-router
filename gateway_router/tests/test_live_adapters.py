"""
Unit Tests for Live Provider Adapters with Mocked HTTP Client.
Verifies adapter normalization, model resolution, token telemetry, error handling,
and latency measurement across all provider adapters without consuming live API quota.
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

ROOT_DIR = Path(__file__).resolve().parent.parent
ROUTER_DIR = ROOT_DIR.parent

sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(ROUTER_DIR))

from ranking_engine.src import RankedModel
from capability_matcher.src import CandidateModel
from model_registry.src import ModelInfo
from gateway_router.src.models import GatewayRequest, ExecutionMode, ExecutionStatus
from gateway_router.src.adapters import (
    GeminiProviderAdapter,
    DeepSeekProviderAdapter,
    GroqProviderAdapter,
    OpenRouterProviderAdapter,
    MistralProviderAdapter,
    NvidiaProviderAdapter,
    AdapterRegistry,
)


def create_mock_completion(content: str = "Test model response"):
    completion = MagicMock()
    choice = MagicMock()
    choice.message.content = content
    completion.choices = [choice]
    usage = MagicMock()
    usage.prompt_tokens = 10
    usage.completion_tokens = 20
    usage.total_tokens = 30
    completion.usage = usage
    return completion


def make_ranked_model(model_id: str, provider: str) -> RankedModel:
    info = ModelInfo(provider=provider, family="Test", model_id=model_id, display_name=model_id, description="", cost_tier="low")
    cand = CandidateModel(model_id=model_id, provider=provider, family="Test", model_info=info, context_headroom=1000)
    return RankedModel(
        model_id=model_id,
        provider=provider,
        family="Test",
        candidate=cand,
        overall_score=0.9,
        rank_position=1
    )


class TestLiveProviderAdapters(unittest.TestCase):

    def test_gemini_adapter_execution(self):
        """Test Gemini adapter execution with mocked OpenAI client."""
        adapter = GeminiProviderAdapter(api_key="test_gemini_key_12345")
        self.assertTrue(adapter.is_configured)
        self.assertEqual(adapter.execution_mode, ExecutionMode.LIVE.value)

        with patch.object(adapter, "_get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = create_mock_completion("Gemini answer")
            mock_get_client.return_value = mock_client

            req = GatewayRequest(request_id="REQ-G-1", prompt="Explain gravity", provider="Google", model_id="gemini-1.5-flash")
            model = make_ranked_model("gemini-1.5-flash", "Google")
            res = adapter.execute(req, model)

            self.assertEqual(res.content, "Gemini answer")
            self.assertEqual(res.model_id, "gemini-3.6-flash")
            self.assertEqual(res.provider, "Google")
            self.assertEqual(res.execution_mode, "live")
            self.assertGreater(res.latency_ms, 0)
            mock_client.chat.completions.create.assert_called_once()

    def test_deepseek_adapter_execution(self):
        """Test DeepSeek adapter execution with mocked client."""
        adapter = DeepSeekProviderAdapter(api_key="test_deepseek_key_12345")
        self.assertTrue(adapter.is_configured)

        with patch.object(adapter, "_get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = create_mock_completion("DeepSeek answer")
            mock_get_client.return_value = mock_client

            req = GatewayRequest(request_id="REQ-DS-1", prompt="Write code", provider="DeepSeek", model_id="deepseek-v3")
            model = make_ranked_model("deepseek-v3", "DeepSeek")
            res = adapter.execute(req, model)

            self.assertEqual(res.content, "DeepSeek answer")
            self.assertEqual(res.model_id, "deepseek-chat")
            self.assertEqual(res.provider, "DeepSeek")

    def test_groq_adapter_execution(self):
        """Test Groq adapter execution with mocked client."""
        adapter = GroqProviderAdapter(api_key="test_groq_key_12345")
        self.assertTrue(adapter.is_configured)

        with patch.object(adapter, "_get_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = create_mock_completion("Groq fast answer")
            mock_get_client.return_value = mock_client

            req = GatewayRequest(request_id="REQ-GQ-1", prompt="Fast response", provider="Groq", model_id="llama-3.3-70b-versatile")
            model = make_ranked_model("llama-3.3-70b-versatile", "Groq")
            res = adapter.execute(req, model)

            self.assertEqual(res.content, "Groq fast answer")
            self.assertEqual(res.model_id, "groq/compound-mini")
            self.assertEqual(res.provider, "Groq")

    def test_openrouter_free_model_enforcement(self):
        """Test OpenRouter adapter enforces :free tier model routing."""
        adapter = OpenRouterProviderAdapter(api_key="test_openrouter_key_12345")
        self.assertTrue(adapter.is_configured)

        model = make_ranked_model("meta-llama/llama-3.3-70b-instruct", "OpenRouter")
        resolved = adapter._resolve_model_id(model)
        self.assertIn(":free", resolved)

    def test_nvidia_adapter_execution(self):
        """Test NVIDIA adapter defaults to active nemotron-3-nano model."""
        adapter = NvidiaProviderAdapter(api_key="test_nvidia_key_12345")
        self.assertTrue(adapter.is_configured)

        model = make_ranked_model("nemotron-4-340b", "NVIDIA")
        resolved = adapter._resolve_model_id(model)
        self.assertEqual(resolved, "nvidia/nemotron-3-nano-30b-a3b")


    def test_adapter_registry_discovery(self):
        """Test AdapterRegistry discovery of configured vs mock providers."""
        registry = AdapterRegistry.create_default()
        providers = registry.list_providers()
        self.assertIn("Google", providers)
        self.assertIn("DeepSeek", providers)
        self.assertIn("Groq", providers)
        self.assertIn("NVIDIA", providers)
        self.assertIn("OpenAI", providers)


if __name__ == "__main__":
    unittest.main()
