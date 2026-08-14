"""
Integration Tests for Module 8 Feedback Pipeline with Modules 1–7.
"""

import sys
import unittest
from pathlib import Path

# Ensure project modules are resolvable
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PROJECT_ROOT / "complexity_predictor") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "complexity_predictor"))

from gateway_router.src.orchestrator import PipelineRouter
from gateway_router.src.models import ExecutionStatus
from rule_engine.src import PolicyContext as RulePolicyContext
from ranking_engine.src import RankingConfig
from policy_engine.src import PolicyContext as RuntimePolicyContext

from feedback_pipeline.src.config import FeedbackConfig
from feedback_pipeline.src.repository import SQLAlchemyFeedbackRepository
from feedback_pipeline.src.service import FeedbackService
from feedback_pipeline.src.analytics import FeedbackAnalytics


class TestFeedbackPipelineIntegration(unittest.TestCase):
    """Integration test suite connecting Modules 1–7 with Module 8."""

    def setUp(self):
        """Initialize PipelineRouter (M1–M7) and FeedbackPipeline (M8)."""
        self.pipeline = PipelineRouter()
        self.config = FeedbackConfig(database_url="sqlite:///:memory:")
        self.repo = SQLAlchemyFeedbackRepository(database_url=self.config.database_url)
        self.service = FeedbackService(repository=self.repo, config=self.config)
        self.analytics = FeedbackAnalytics(repository=self.repo)

    def test_end_to_end_m1_to_m8_pipeline(self):
        """
        Verify complete trajectory:
        Raw Request -> M1 (Complexity) -> M2/M3 (Match) -> M4 (Rules) -> M5 (Ranking) ->
        M6 (Policy) -> M7 (Gateway) -> M8 (Feedback Ingestion -> DB -> Analytics).
        """
        raw_request = {
            "request_id": "REQ-INT-001",
            "prompt": "Write a Python function to compute the Fibonacci sequence using memoization.",
            "metadata": {"task_category": "Programming"},
            "expected_output": {"format": "code"}
        }

        # 1. Execute M1–M7
        response = self.pipeline.route_and_execute(raw_request=raw_request)
        self.assertEqual(response.status, ExecutionStatus.SUCCESS)
        self.assertIsNotNone(response.model_id)

        # 2. Ingest into Module 8
        event = self.service.record_gateway_response(
            response=response,
            request_prompt=raw_request["prompt"],
            task_category="Programming"
        )
        self.assertIsNotNone(event.event_id)
        self.assertEqual(event.request_id, "REQ-INT-001")
        self.assertEqual(event.model_id, response.model_id)
        self.assertEqual(event.task_category, "Programming")
        self.assertEqual(event.execution_status, "SUCCESS")

        # 3. Attach User Quality Feedback
        fb = self.service.submit_feedback(
            event_id=event.event_id,
            rating=5,
            quality_category="accurate",
            comment="Generated working memoized code."
        )
        self.assertEqual(fb.rating, 5)

        # 4. Query Analytics
        summary = self.analytics.get_summary_metrics()
        self.assertEqual(summary["total_requests"], 1)
        self.assertEqual(summary["successful_requests"], 1)
        self.assertEqual(summary["success_rate_pct"], 100.0)

        quality = self.analytics.get_quality_metrics()
        self.assertEqual(quality["total_feedback_count"], 1)
        self.assertEqual(quality["average_rating"], 5.0)

    def test_policy_fallback_event_ingestion(self):
        """
        Verify policy-governed fallback dispatch is captured with fallback_used=True and reflected in analytics.
        """
        raw_request = {
            "request_id": "REQ-INT-FALLBACK",
            "prompt": "Write a Python script to calculate prime numbers.",
            "metadata": {"task_category": "Programming"},
            "expected_output": {"format": "code"}
        }
        rule_ctx = RulePolicyContext(allowed_providers={"Anthropic"})
        ranking_cfg = RankingConfig(prefer_lower_cost=False)
        runtime_ctx = RuntimePolicyContext(
            tenant_id="budget_tenant",
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

        event = self.service.record_gateway_response(
            response=response,
            request_prompt=raw_request["prompt"],
            task_category="Programming"
        )
        self.assertTrue(event.fallback_used)
        self.assertEqual(event.model_id, "claude-3.5-haiku")

        dist = self.analytics.get_routing_distribution()
        self.assertEqual(dist["total_requests"], 1)
        self.assertEqual(dist["fallback_count"], 1)
        self.assertEqual(dist["fallback_rate_pct"], 100.0)


if __name__ == "__main__":
    unittest.main()
