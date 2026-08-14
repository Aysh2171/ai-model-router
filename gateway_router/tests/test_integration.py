"""
Integration tests verifying end-to-end chaining of Modules 1 through 7 via PipelineRouter.
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

from gateway_router.src.orchestrator import PipelineRouter
from gateway_router.src.models import ExecutionStatus, ExecutionMode
from ranking_engine.src import RankingConfig
from rule_engine.src import PolicyContext as RuleContext
from policy_engine.src import PolicyContext as RuntimeContext, UsageState


class TestPipelineIntegration(unittest.TestCase):
    """Test suite verifying end-to-end integration across all seven modules."""

    def setUp(self):
        self.pipeline = PipelineRouter()

    def test_end_to_end_pipeline_success(self):
        """Verify standard request flows through M1->M2->M3->M4->M5->M6->M7 to successful mock execution."""
        raw_request = {
            "request_id": "REQ-INT-001",
            "prompt": "Write a Python script to sort numbers.",
            "metadata": {"task_category": "Programming"},
            "expected_output": {"format": "code"}
        }

        response = self.pipeline.route_and_execute(raw_request)

        self.assertEqual(response.status, ExecutionStatus.SUCCESS)
        self.assertIsNotNone(response.model_id)
        self.assertIsNotNone(response.provider)
        self.assertEqual(response.execution_mode, ExecutionMode.MOCK.value)
        self.assertIn("[MOCK EXECUTION]", response.content)
        self.assertIn("complexity_profile", response.metadata)
        self.assertGreater(response.metadata["feasible_candidate_count"], 0)

    def test_end_to_end_pipeline_policy_fallback_execution(self):
        """
        Verify that when Module 6 Policy Engine selects a fallback candidate due to budget limits,
        GatewayRouter executes the policy-selected fallback model without altering the decision.
        """
        raw_request = {
            "request_id": "REQ-INT-FALLBACK",
            "prompt": "Write a Python script to calculate prime numbers.",
            "metadata": {"task_category": "Programming"},
            "expected_output": {"format": "code"}
        }

        # Constrain to Anthropic models (claude-3.5-sonnet High Cost, claude-3.5-haiku Low Cost)
        rule_ctx = RuleContext(allowed_providers={"Anthropic"})
        ranking_cfg = RankingConfig(prefer_lower_cost=False)

        # Set budget limit to 2.0 units with current spend 0.0 units.
        # Rank #1 (claude-3.5-sonnet: 7.0 units) will fail budget.
        # Rank #2 (claude-3.5-haiku: 1.0 unit) will succeed as fallback!
        runtime_ctx = RuntimeContext(
            tenant_id="fallback_tenant",
            budget_limit=2.0,
            fallback_enabled=True,
            max_fallback_attempts=3
        )

        response = self.pipeline.route_and_execute(
            raw_request=raw_request,
            rule_context=rule_ctx,
            ranking_config=ranking_cfg,
            runtime_policy_context=runtime_ctx
        )

        self.assertEqual(response.status, ExecutionStatus.SUCCESS)
        self.assertTrue(response.fallback_used)
        self.assertEqual(response.model_id, "claude-3.5-haiku")
        self.assertEqual(response.provider, "Anthropic")
        self.assertIn("[MOCK EXECUTION]", response.content)

    def test_end_to_end_pipeline_policy_rejection(self):
        """Verify that when Module 6 Policy Engine rejects a request, GatewayRouter returns REJECTED status."""
        raw_request = {
            "request_id": "REQ-INT-REJECT",
            "prompt": "Summarize text.",
            "metadata": {"task_category": "General Prompting"}
        }

        # Set daily request limit to 0 to force immediate request-level policy rejection
        runtime_ctx = RuntimeContext(
            tenant_id="exhausted_tenant",
            daily_request_limit=0
        )
        usage = UsageState(tenant_id="exhausted_tenant", daily_requests_used=0)

        response = self.pipeline.route_and_execute(
            raw_request=raw_request,
            runtime_policy_context=runtime_ctx,
            usage_state=usage
        )

        self.assertEqual(response.status, ExecutionStatus.REJECTED)
        self.assertIsNone(response.content)
        self.assertIn("Execution blocked", response.error_message)


if __name__ == "__main__":
    unittest.main()
