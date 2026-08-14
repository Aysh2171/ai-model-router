"""
Unit tests for Gateway Router streaming chunk generation.
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

from gateway_router.src.gateway import GatewayRouter
from gateway_router.src.models import GatewayRequest, StreamChunk, ExecutionMode
from gateway_router.src.adapters.mock import MockProviderAdapter
from gateway_router.src.adapters.registry import AdapterRegistry

from policy_engine.src import PolicyDecision, DecisionState
from ranking_engine.src import RankedModel
from capability_matcher.src import CandidateModel
from model_registry.src import ModelInfo


def create_test_decision(model_id: str = "gpt-4o", provider: str = "OpenAI", rejected: bool = False) -> PolicyDecision:
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
    ranked = RankedModel(
        model_id=model_id,
        provider=provider,
        family="GPT",
        candidate=cand,
        overall_score=0.90,
        rank_position=1,
    )
    if rejected:
        return PolicyDecision(
            request_id="REQ-STREAM-REJ",
            decision=DecisionState.REJECTED,
            selected_model=None,
            selected_rank=None,
            fallback_used=False
        )
    return PolicyDecision(
        request_id="REQ-STREAM",
        decision=DecisionState.APPROVED,
        selected_model=ranked,
        selected_rank=1,
        fallback_used=False
    )


class TestGatewayStreaming(unittest.TestCase):
    """Test suite verifying GatewayRouter streaming chunk generation and error chunk handling."""

    def setUp(self):
        self.router = GatewayRouter()

    def test_mock_streaming_chunks_generation(self):
        """Verify streaming generation yields multiple ordered StreamChunk objects."""
        decision = create_test_decision("gpt-4o", "OpenAI")
        req = GatewayRequest(request_id="REQ-STR-1", prompt="Explain quantum computing.", policy_decision=decision, stream=True)

        chunks = list(self.router.execute_stream(req))

        self.assertGreater(len(chunks), 1)
        self.assertEqual(chunks[0].chunk_index, 0)
        self.assertEqual(chunks[0].execution_mode, ExecutionMode.MOCK.value)
        self.assertEqual(chunks[0].model_id, "gpt-4o")
        self.assertEqual(chunks[0].provider, "OpenAI")

    def test_streaming_final_chunk_flag(self):
        """Verify strictly the last stream chunk sets is_final=True."""
        decision = create_test_decision("claude-3.5-sonnet", "Anthropic")
        req = GatewayRequest(request_id="REQ-STR-2", prompt="Write a poem.", policy_decision=decision, stream=True)

        chunks = list(self.router.execute_stream(req))

        for chunk in chunks[:-1]:
            self.assertFalse(chunk.is_final)
        self.assertTrue(chunks[-1].is_final)

    def test_streaming_policy_rejection_error_chunk(self):
        """Verify rejected policy decision yields a single error stream chunk with is_final=True."""
        decision = create_test_decision(rejected=True)
        req = GatewayRequest(request_id="REQ-STR-3", prompt="Heavy task", policy_decision=decision, stream=True)

        chunks = list(self.router.execute_stream(req))

        self.assertEqual(len(chunks), 1)
        self.assertTrue(chunks[0].is_final)
        self.assertIn("[STREAM ERROR]", chunks[0].content)

    def test_streaming_missing_adapter_error_chunk(self):
        """Verify missing provider adapter yields a single error stream chunk."""
        decision = create_test_decision("custom-model", "NonExistentProvider")
        req = GatewayRequest(request_id="REQ-STR-4", prompt="Test", policy_decision=decision, stream=True)

        chunks = list(self.router.execute_stream(req))

        self.assertEqual(len(chunks), 1)
        self.assertTrue(chunks[0].is_final)
        self.assertIn("No provider adapter registered", chunks[0].content)


if __name__ == "__main__":
    unittest.main()
