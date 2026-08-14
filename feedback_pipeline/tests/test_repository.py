"""
Tests for Feedback Pipeline Repository and SQLAlchemy Operations.
"""

import unittest
from feedback_pipeline.src.models import RoutingEvent, FeedbackRecord
from feedback_pipeline.src.repository import SQLAlchemyFeedbackRepository


class TestFeedbackRepository(unittest.TestCase):
    """Test suite verifying persistence operations on in-memory SQLite database."""

    def setUp(self):
        """Initialize fresh in-memory SQLAlchemy repository for each test."""
        self.repo = SQLAlchemyFeedbackRepository(database_url="sqlite:///:memory:")

    def test_record_and_get_event(self):
        """Verify persisting and retrieving a RoutingEvent."""
        event = RoutingEvent(
            request_id="REQ-DB-001",
            task_category="Reasoning",
            complexity_tier="High",
            complexity_score=85,
            model_id="claude-3.5-sonnet",
            provider="Anthropic",
            execution_status="SUCCESS",
            latency_ms=25.4,
            prompt_tokens=50,
            completion_tokens=120,
            total_tokens=170,
            prompt_summary="Solve logic puzzle."
        )

        self.repo.record_event(event)
        retrieved = self.repo.get_event(event.event_id)

        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.event_id, event.event_id)
        self.assertEqual(retrieved.request_id, "REQ-DB-001")
        self.assertEqual(retrieved.model_id, "claude-3.5-sonnet")
        self.assertEqual(retrieved.provider, "Anthropic")
        self.assertEqual(retrieved.complexity_score, 85)
        self.assertEqual(retrieved.total_tokens, 170)

    def test_get_events_by_request_id(self):
        """Verify retrieving multiple attempts sharing the same request_id."""
        ev1 = RoutingEvent(request_id="REQ-MULTI", model_id="model-a", execution_status="FAILED")
        ev2 = RoutingEvent(request_id="REQ-MULTI", model_id="model-b", execution_status="SUCCESS")

        self.repo.record_event(ev1)
        self.repo.record_event(ev2)

        results = self.repo.get_events_by_request_id("REQ-MULTI")
        self.assertEqual(len(results), 2)
        model_ids = [e.model_id for e in results]
        self.assertIn("model-a", model_ids)
        self.assertIn("model-b", model_ids)

    def test_list_events_and_count(self):
        """Verify listing events with limit and total event count."""
        for i in range(5):
            ev = RoutingEvent(request_id=f"REQ-LIST-{i}", model_id=f"model-{i}")
            self.repo.record_event(ev)

        self.assertEqual(self.repo.count_events(), 5)
        events = self.repo.list_events(limit=3)
        self.assertEqual(len(events), 3)

    def test_record_and_get_feedback_for_event(self):
        """Verify persisting and querying feedback records linked to an event_id."""
        event = RoutingEvent(request_id="REQ-FB-01", model_id="gpt-4o")
        self.repo.record_event(event)

        fb1 = FeedbackRecord(event_id=event.event_id, rating=5, comment="Great result!")
        fb2 = FeedbackRecord(event_id=event.event_id, rating=4, comment="Good formatting.")
        self.repo.record_feedback(fb1)
        self.repo.record_feedback(fb2)

        fb_list = self.repo.get_feedback_for_event(event.event_id)
        self.assertEqual(len(fb_list), 2)
        ratings = [f.rating for f in fb_list]
        self.assertIn(5, ratings)
        self.assertIn(4, ratings)


if __name__ == "__main__":
    unittest.main()
