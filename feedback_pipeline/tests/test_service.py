"""
Tests for FeedbackService Orchestration Layer.
"""

import unittest
from gateway_router.src import GatewayResponse, ExecutionStatus
from feedback_pipeline.src.config import FeedbackConfig
from feedback_pipeline.src.repository import SQLAlchemyFeedbackRepository
from feedback_pipeline.src.service import FeedbackService


class TestFeedbackService(unittest.TestCase):
    """Test suite for FeedbackService operations."""

    def setUp(self):
        """Initialize fresh repository and service for each test."""
        self.config = FeedbackConfig(database_url="sqlite:///:memory:")
        self.repo = SQLAlchemyFeedbackRepository(database_url=self.config.database_url)
        self.service = FeedbackService(repository=self.repo, config=self.config)

    def test_record_gateway_response(self):
        """Verify recording a GatewayResponse produces a persisted RoutingEvent."""
        gw_resp = GatewayResponse(
            request_id="REQ-SRV-001",
            status=ExecutionStatus.SUCCESS,
            decision_state="APPROVED",
            model_id="minimax-text-01",
            provider="MiniMax",
            latency_ms=18.2,
            usage={"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
            metadata={"cost_tier": "medium", "task_category": "Coding"}
        )

        event = self.service.record_gateway_response(
            response=gw_resp,
            request_prompt="Write a Python decorator.",
            task_category="Coding"
        )

        self.assertIsNotNone(event.event_id)
        self.assertEqual(event.request_id, "REQ-SRV-001")
        self.assertEqual(event.model_id, "minimax-text-01")
        self.assertEqual(event.provider, "MiniMax")
        self.assertEqual(event.total_tokens, 30)

        # Verify query from repository
        stored = self.repo.get_event(event.event_id)
        self.assertIsNotNone(stored)
        self.assertEqual(stored.request_id, "REQ-SRV-001")

    def test_submit_feedback_success(self):
        """Verify submitting feedback links to an existing event."""
        gw_resp = GatewayResponse(
            request_id="REQ-SRV-002",
            status=ExecutionStatus.SUCCESS,
            model_id="gpt-4o",
            provider="OpenAI"
        )
        event = self.service.record_gateway_response(gw_resp)

        fb = self.service.submit_feedback(
            event_id=event.event_id,
            rating=5,
            quality_category="accurate",
            comment="Code was optimal and ran cleanly.",
            evaluator_id="qa_tester"
        )

        self.assertEqual(fb.event_id, event.event_id)
        self.assertEqual(fb.rating, 5)
        self.assertEqual(fb.evaluator_id, "qa_tester")

    def test_submit_feedback_nonexistent_event_raises_key_error(self):
        """Verify submitting feedback for unknown event raises KeyError."""
        with self.assertRaises(KeyError):
            self.service.submit_feedback(
                event_id="NON-EXISTENT-UUID",
                rating=4
            )

    def test_get_event_with_feedback(self):
        """Verify retrieving event with all associated feedback items bundled."""
        gw_resp = GatewayResponse(
            request_id="REQ-SRV-003",
            status=ExecutionStatus.SUCCESS,
            model_id="claude-3.5-haiku",
            provider="Anthropic"
        )
        event = self.service.record_gateway_response(gw_resp)
        self.service.submit_feedback(event.event_id, rating=4, comment="Good speed.")
        self.service.submit_feedback(event.event_id, rating=5, comment="Correct answer.")

        bundled = self.service.get_event_with_feedback(event.event_id)
        self.assertIsNotNone(bundled)
        self.assertEqual(bundled["event"]["model_id"], "claude-3.5-haiku")
        self.assertEqual(len(bundled["feedback"]), 2)

    def test_feedback_disabled_raises_value_error(self):
        """Verify attempting to submit feedback when disabled raises ValueError."""
        cfg_disabled = FeedbackConfig(database_url="sqlite:///:memory:", enable_feedback_collection=False)
        srv_disabled = FeedbackService(repository=self.repo, config=cfg_disabled)

        gw_resp = GatewayResponse(request_id="REQ-004", status=ExecutionStatus.SUCCESS)
        event = srv_disabled.record_gateway_response(gw_resp)

        with self.assertRaises(ValueError):
            srv_disabled.submit_feedback(event.event_id, rating=5)


if __name__ == "__main__":
    unittest.main()
