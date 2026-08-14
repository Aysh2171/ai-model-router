"""
Unit tests for GatewayRouter core execution logic and PolicyDecision handling.
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
from gateway_router.src.models import GatewayRequest, ExecutionStatus, ExecutionMode
from gateway_router.src.adapters.registry import AdapterRegistry
from gateway_router.src.adapters.mock import MockProviderAdapter

from policy_engine.src import PolicyDecision, DecisionState, PolicyEvaluation
from ranking_engine.src import RankedModel
from capability_matcher.src import CandidateModel
from model_registry.src import ModelInfo


def create_test_decision(
    state: DecisionState,
    model_id: str = "gpt-4o",
    provider: str = "OpenAI",
    fallback_used: bool = False
) -> PolicyDecision:
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
        rank_position=2 if fallback_used else 1,
    )

    if state in (DecisionState.APPROVED, DecisionState.APPROVED_WITH_FALLBACK):
        return PolicyDecision(
            request_id="REQ-TEST",
            decision=state,
            selected_model=ranked,
            selected_rank=ranked.rank_position,
            fallback_used=fallback_used,
            fallback_attempts=1 if fallback_used else 0,
            applied_policies=["BudgetPolicy"]
        )
    elif state == DecisionState.REJECTED:
        eval_fail = PolicyEvaluation(
            model_id=model_id,
            provider=provider,
            rank_position=1,
            allowed=False,
            failure_reasons=["BUDGET_EXCEEDED"],
            explanations=["Budget exceeded limit."]
        )
        return PolicyDecision(
            request_id="REQ-TEST",
            decision=DecisionState.REJECTED,
            selected_model=None,
            selected_rank=None,
            fallback_used=False,
            fallback_attempts=1,
            evaluated_candidates=[eval_fail],
            applied_policies=["BudgetPolicy"]
        )
    else:  # NO_CANDIDATE
        return PolicyDecision(
            request_id="REQ-TEST",
            decision=DecisionState.NO_CANDIDATE,
            selected_model=None,
            selected_rank=None,
            fallback_used=False,
            fallback_attempts=0
        )


class TestGatewayRouter(unittest.TestCase):
    """Test suite verifying GatewayRouter execution paths and decision state handling."""

    def setUp(self):
        self.router = GatewayRouter()

    def test_approved_decision_execution(self):
        """Verify executing an APPROVED PolicyDecision returns success response with mock output."""
        decision = create_test_decision(DecisionState.APPROVED, "gpt-4o", "OpenAI")
        req = GatewayRequest(request_id="REQ-APP-1", prompt="Explain recursion.", policy_decision=decision)

        response = self.router.execute(req)

        self.assertEqual(response.status, ExecutionStatus.SUCCESS)
        self.assertEqual(response.decision_state, DecisionState.APPROVED.value)
        self.assertEqual(response.model_id, "gpt-4o")
        self.assertEqual(response.provider, "OpenAI")
        self.assertEqual(response.execution_mode, ExecutionMode.MOCK.value)
        self.assertFalse(response.fallback_used)
        self.assertIn("[MOCK EXECUTION]", response.content)

    def test_approved_fallback_decision_execution(self):
        """Verify executing an APPROVED_WITH_FALLBACK PolicyDecision executes the policy-selected model."""
        decision = create_test_decision(DecisionState.APPROVED_WITH_FALLBACK, "claude-3.5-sonnet", "Anthropic", fallback_used=True)
        req = GatewayRequest(request_id="REQ-FALL-1", prompt="Write a quicksort.", policy_decision=decision)

        response = self.router.execute(req)

        self.assertEqual(response.status, ExecutionStatus.SUCCESS)
        self.assertEqual(response.decision_state, DecisionState.APPROVED_WITH_FALLBACK.value)
        self.assertEqual(response.model_id, "claude-3.5-sonnet")
        self.assertEqual(response.provider, "Anthropic")
        self.assertTrue(response.fallback_used)
        self.assertIn("[MOCK EXECUTION]", response.content)

    def test_policy_rejection_blocks_execution(self):
        """Verify that a REJECTED PolicyDecision blocks adapter execution and returns REJECTED status."""
        decision = create_test_decision(DecisionState.REJECTED)
        req = GatewayRequest(request_id="REQ-REJ-1", prompt="Process 500GB log file.", policy_decision=decision)

        response = self.router.execute(req)

        self.assertEqual(response.status, ExecutionStatus.REJECTED)
        self.assertEqual(response.decision_state, DecisionState.REJECTED.value)
        self.assertIsNone(response.content)
        self.assertIn("Execution blocked", response.error_message)

    def test_no_candidate_blocks_execution(self):
        """Verify that a NO_CANDIDATE PolicyDecision blocks adapter execution."""
        decision = create_test_decision(DecisionState.NO_CANDIDATE)
        req = GatewayRequest(request_id="REQ-NOCAND-1", prompt="Unsatisfiable prompt", policy_decision=decision)

        response = self.router.execute(req)

        self.assertEqual(response.status, ExecutionStatus.NO_CANDIDATE)
        self.assertEqual(response.decision_state, DecisionState.NO_CANDIDATE.value)
        self.assertIsNone(response.content)

    def test_missing_adapter_returns_adapter_not_found(self):
        """Verify that a provider without a registered adapter returns ADAPTER_NOT_FOUND rather than generic fallback."""
        decision = create_test_decision(DecisionState.APPROVED, "custom-model", "UnregisteredProvider")
        req = GatewayRequest(request_id="REQ-NOADAPT-1", prompt="Test prompt", policy_decision=decision)

        response = self.router.execute(req)

        self.assertEqual(response.status, ExecutionStatus.ADAPTER_NOT_FOUND)
        self.assertEqual(response.provider, "UnregisteredProvider")
        self.assertIn("No provider adapter registered", response.error_message)


if __name__ == "__main__":
    unittest.main()
