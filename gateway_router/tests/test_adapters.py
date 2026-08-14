"""
Unit tests for Provider Adapter abstraction and MockProviderAdapter.
"""

import sys
import unittest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
ROUTER_DIR = ROOT_DIR.parent
COMPLEXITY_DIR = ROUTER_DIR / "complexity_predictor"

sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(ROUTER_DIR))
if str(COMPLEXITY_DIR) not in sys.path:
    sys.path.insert(0, str(COMPLEXITY_DIR))

from gateway_router.src.adapters.mock import MockProviderAdapter
from gateway_router.src.adapters.registry import AdapterRegistry
from gateway_router.src.models import GatewayRequest, ExecutionMode
from gateway_router.src.exceptions import (
    TransientExecutionError,
    TimeoutExecutionError,
    PermanentExecutionError,
)
from model_registry.src import ModelInfo
from capability_matcher.src import CandidateModel
from ranking_engine.src import RankedModel


def create_test_ranked_model(model_id: str = "gpt-4o", provider: str = "OpenAI") -> RankedModel:
    info = ModelInfo(
        provider=provider,
        family="GPT",
        model_id=model_id,
        display_name=model_id,
        description="Test model",
        status="available",
        is_default=True,
        tags=["test"],
        context_window=128000,
        max_output_tokens=4096,
        cost_tier="high",
        latency_tier="fast",
        supported_modalities=["text"],
        supported_use_cases=["General Prompting"],
    )
    cand = CandidateModel(
        model_id=model_id,
        provider=provider,
        family="GPT",
        model_info=info,
        context_headroom=120000,
    )
    return RankedModel(
        model_id=model_id,
        provider=provider,
        family="GPT",
        candidate=cand,
        overall_score=0.95,
        rank_position=1,
    )


class TestProviderAdapters(unittest.TestCase):
    """Test suite verifying adapter execution, simulation modes, and registry operations."""

    def test_mock_adapter_execution(self):
        """Verify normal mock adapter execution produces clean simulated output."""
        adapter = MockProviderAdapter(provider="OpenAI")
        req = GatewayRequest(request_id="REQ-001", prompt="What is Python?")
        model = create_test_ranked_model("gpt-4o", "OpenAI")

        result = adapter.execute(req, model)

        self.assertEqual(result.model_id, "gpt-4o")
        self.assertEqual(result.provider, "OpenAI")
        self.assertEqual(result.execution_mode, ExecutionMode.MOCK.value)
        self.assertIn("[MOCK EXECUTION]", result.content)
        self.assertIn("gpt-4o", result.content)
        self.assertGreater(result.usage["total_tokens"], 0)

    def test_mock_adapter_custom_response(self):
        """Verify simulation options can supply custom deterministic responses."""
        adapter = MockProviderAdapter(provider="Anthropic")
        req = GatewayRequest(
            request_id="REQ-002",
            prompt="Hello",
            simulation_options={"custom_response": "Custom deterministic output"}
        )
        model = create_test_ranked_model("claude-3.5-sonnet", "Anthropic")

        result = adapter.execute(req, model)
        self.assertEqual(result.content, "Custom deterministic output")

    def test_mock_adapter_fault_injection(self):
        """Verify controllable fault injection raises expected strongly typed exceptions."""
        adapter = MockProviderAdapter(provider="OpenAI")
        model = create_test_ranked_model("gpt-4o", "OpenAI")

        # Transient failure
        req_transient = GatewayRequest(request_id="R1", prompt="test", simulation_options={"fail_mode": "transient"})
        with self.assertRaises(TransientExecutionError):
            adapter.execute(req_transient, model)

        # Timeout failure
        req_timeout = GatewayRequest(request_id="R2", prompt="test", simulation_options={"fail_mode": "timeout"})
        with self.assertRaises(TimeoutExecutionError):
            adapter.execute(req_timeout, model)

        # Permanent failure
        req_perm = GatewayRequest(request_id="R3", prompt="test", simulation_options={"fail_mode": "permanent"})
        with self.assertRaises(PermanentExecutionError):
            adapter.execute(req_perm, model)

    def test_adapter_registry_registration_and_lookup(self):
        """Verify AdapterRegistry registers and resolves adapters case-insensitively."""
        registry = AdapterRegistry()
        adapter = MockProviderAdapter(provider="Cohere")
        registry.register(adapter)

        self.assertTrue(registry.has_provider("cohere"))
        self.assertTrue(registry.has_provider("COHERE"))
        self.assertEqual(registry.get("cohere"), adapter)
        self.assertEqual(registry.get("Cohere"), adapter)

    def test_adapter_registry_missing_provider_returns_none(self):
        """Verify lookup for an unregistered provider returns None rather than silent fallback."""
        registry = AdapterRegistry()
        self.assertFalse(registry.has_provider("UnknownProvider"))
        self.assertIsNone(registry.get("UnknownProvider"))


if __name__ == "__main__":
    unittest.main()
