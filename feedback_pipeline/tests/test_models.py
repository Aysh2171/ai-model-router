"""
Tests for Feedback Pipeline Domain Models and Conversions.
"""

import unittest
from datetime import datetime, timezone
from gateway_router.src import GatewayResponse, ExecutionStatus
from feedback_pipeline.src.models import RoutingEvent, FeedbackRecord


class TestFeedbackModels(unittest.TestCase):
    """Test suite for RoutingEvent and FeedbackRecord dataclasses."""

    def test_routing_event_from_gateway_response(self):
        """Verify constructing a RoutingEvent from GatewayResponse extracts all relevant fields."""
        gw_resp = GatewayResponse(
            request_id="REQ-TEST-001",
            status=ExecutionStatus.SUCCESS,
            decision_state="APPROVED",
            model_id="gpt-4o",
            provider="OpenAI",
            content="[MOCK EXECUTION] Test response",
            execution_mode="mock",
            latency_ms=12.5,
            retry_count=1,
            fallback_used=False,
            usage={"prompt_tokens": 15, "completion_tokens": 30, "total_tokens": 45},
            metadata={
                "task_category": "Coding",
                "cost_tier": "high",
                "latency_tier": "fast",
                "selected_rank": 1,
                "complexity_profile": {
                    "complexity": "Medium",
                    "complexity_score": 55,
                    "confidence": 0.92
                }
            }
        )

        event = RoutingEvent.from_gateway_response(
            response=gw_resp,
            request_prompt="Write a binary search algorithm in Python."
        )

        self.assertEqual(event.request_id, "REQ-TEST-001")
        self.assertEqual(event.execution_status, "SUCCESS")
        self.assertEqual(event.decision_state, "APPROVED")
        self.assertEqual(event.model_id, "gpt-4o")
        self.assertEqual(event.provider, "OpenAI")
        self.assertEqual(event.task_category, "Coding")
        self.assertEqual(event.complexity_tier, "Medium")
        self.assertEqual(event.complexity_score, 55)
        self.assertEqual(event.complexity_confidence, 0.92)
        self.assertEqual(event.retry_count, 1)
        self.assertFalse(event.fallback_used)
        self.assertEqual(event.prompt_tokens, 15)
        self.assertEqual(event.completion_tokens, 30)
        self.assertEqual(event.total_tokens, 45)
        self.assertTrue(event.is_success)
        self.assertEqual(event.prompt_summary, "Write a binary search algorithm in Python.")

    def test_routing_event_prompt_truncation(self):
        """Verify long prompts are sanitized/truncated in prompt_summary according to max_prompt_length."""
        gw_resp = GatewayResponse(
            request_id="REQ-TEST-LONG",
            status=ExecutionStatus.SUCCESS,
            model_id="gemini-1.5-pro",
            provider="Google"
        )
        long_prompt = "A" * 500

        event = RoutingEvent.from_gateway_response(
            response=gw_resp,
            request_prompt=long_prompt,
            max_prompt_length=50
        )

        self.assertEqual(len(event.prompt_summary), 50)
        self.assertEqual(event.prompt_summary, "A" * 50)

    def test_routing_event_is_success_property(self):
        """Verify is_success property reflects execution status correctly."""
        event_ok = RoutingEvent(execution_status="SUCCESS")
        event_rej = RoutingEvent(execution_status="REJECTED")
        event_fail = RoutingEvent(execution_status="FAILED")

        self.assertTrue(event_ok.is_success)
        self.assertFalse(event_rej.is_success)
        self.assertFalse(event_fail.is_success)

    def test_feedback_record_valid(self):
        """Verify creating a valid FeedbackRecord within rating bounds 1-5."""
        fb = FeedbackRecord(
            event_id="EVT-12345",
            rating=5,
            quality_category="accurate",
            comment="Excellent response, perfectly solved.",
            evaluator_id="user_alice"
        )

        self.assertEqual(fb.event_id, "EVT-12345")
        self.assertEqual(fb.rating, 5)
        self.assertEqual(fb.quality_category, "accurate")
        self.assertEqual(fb.comment, "Excellent response, perfectly solved.")
        self.assertEqual(fb.evaluator_id, "user_alice")

        d = fb.to_dict()
        self.assertIn("feedback_id", d)
        self.assertEqual(d["rating"], 5)

    def test_feedback_record_invalid_rating(self):
        """Verify FeedbackRecord raises ValueError on rating < 1 or > 5 or invalid types."""
        with self.assertRaises(ValueError):
            FeedbackRecord(event_id="EVT-1", rating=0)

        with self.assertRaises(ValueError):
            FeedbackRecord(event_id="EVT-1", rating=6)

        with self.assertRaises(ValueError):
            FeedbackRecord(event_id="EVT-1", rating="5")  # type: ignore


if __name__ == "__main__":
    unittest.main()
