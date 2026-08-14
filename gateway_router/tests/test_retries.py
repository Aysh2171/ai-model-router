"""
Unit tests for Gateway Router bounded retry behavior and error classification.
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
from gateway_router.src.config import GatewayConfig
from gateway_router.src.models import GatewayRequest, ExecutionStatus
from gateway_router.src.adapters.mock import MockProviderAdapter
from gateway_router.src.adapters.registry import AdapterRegistry

from policy_engine.src import PolicyDecision, DecisionState
from ranking_engine.src import RankedModel
from capability_matcher.src import CandidateModel
from model_registry.src import ModelInfo


def create_test_decision(model_id: str = "gpt-4o", provider: str = "OpenAI") -> PolicyDecision:
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
    return PolicyDecision(
        request_id="REQ-RETRY",
        decision=DecisionState.APPROVED,
        selected_model=ranked,
        selected_rank=1,
        fallback_used=False,
    )


class TestGatewayRetries(unittest.TestCase):
    """Test suite verifying bounded retry semantics and failure classification."""

    def test_transient_error_retries_and_succeeds(self):
        """Verify transient failure on attempt 1 triggers retry and succeeds on attempt 2."""
        config = GatewayConfig(max_retries=2, retry_delay_ms=0.0)
        router = GatewayRouter(config=config)
        decision = create_test_decision("gpt-4o", "OpenAI")

        req = GatewayRequest(
            request_id="REQ-RETRY-1",
            prompt="Hello world",
            policy_decision=decision,
            simulation_options={
                "fail_mode": "transient_then_success",
                "fail_count_before_success": 1
            }
        )

        response = router.execute(req)

        self.assertEqual(response.status, ExecutionStatus.SUCCESS)
        self.assertEqual(response.retry_count, 1)
        self.assertIn("[MOCK EXECUTION]", response.content)

    def test_retries_exhausted_on_continuous_transient_failures(self):
        """Verify continuous transient failures exhaust configured retry limit."""
        config = GatewayConfig(max_retries=2, retry_delay_ms=0.0)
        router = GatewayRouter(config=config)
        decision = create_test_decision("gpt-4o", "OpenAI")

        req = GatewayRequest(
            request_id="REQ-RETRY-2",
            prompt="Hello world",
            policy_decision=decision,
            simulation_options={"fail_mode": "transient"}
        )

        response = router.execute(req)

        self.assertEqual(response.status, ExecutionStatus.RETRY_EXHAUSTED)
        self.assertEqual(response.retry_count, 2)
        self.assertIsNone(response.content)
        self.assertIn("retries exhausted", response.error_message.lower())

    def test_timeout_error_retries_and_records_status(self):
        """Verify timeout failures trigger retries and return TIMEOUT status upon exhaustion."""
        config = GatewayConfig(max_retries=1, retry_delay_ms=0.0)
        router = GatewayRouter(config=config)
        decision = create_test_decision("claude-3.5-sonnet", "Anthropic")

        req = GatewayRequest(
            request_id="REQ-TIMEOUT-1",
            prompt="Heavy reasoning task",
            policy_decision=decision,
            simulation_options={"fail_mode": "timeout"}
        )

        response = router.execute(req)

        self.assertEqual(response.status, ExecutionStatus.TIMEOUT)
        self.assertEqual(response.retry_count, 1)
        self.assertIn("timeout", response.error_message.lower())

    def test_permanent_error_aborts_immediately_without_retry(self):
        """Verify non-retryable permanent errors abort immediately with retry_count=0."""
        config = GatewayConfig(max_retries=3, retry_delay_ms=0.0)
        router = GatewayRouter(config=config)
        decision = create_test_decision("gpt-4o", "OpenAI")

        req = GatewayRequest(
            request_id="REQ-PERM-1",
            prompt="Malformed prompt",
            policy_decision=decision,
            simulation_options={"fail_mode": "permanent"}
        )

        response = router.execute(req)

        self.assertEqual(response.status, ExecutionStatus.FAILED)
        self.assertEqual(response.retry_count, 0)
        self.assertIn("Permanent execution failure", response.error_message)


if __name__ == "__main__":
    unittest.main()
