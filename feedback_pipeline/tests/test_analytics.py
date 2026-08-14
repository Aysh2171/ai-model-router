"""
Tests for FeedbackAnalytics Engine.
"""

import unittest
from feedback_pipeline.src.models import RoutingEvent, FeedbackRecord
from feedback_pipeline.src.repository import SQLAlchemyFeedbackRepository
from feedback_pipeline.src.analytics import FeedbackAnalytics


class TestFeedbackAnalytics(unittest.TestCase):
    """Test suite verifying mathematical correctness of aggregated telemetry metrics."""

    def setUp(self):
        """Initialize fresh repository and analytics engine."""
        self.repo = SQLAlchemyFeedbackRepository(database_url="sqlite:///:memory:")
        self.analytics = FeedbackAnalytics(repository=self.repo)

    def test_empty_analytics(self):
        """Verify summary on empty repository returns valid zeroed dictionary."""
        summary = self.analytics.get_summary_metrics()
        self.assertEqual(summary["total_requests"], 0)
        self.assertEqual(summary["success_rate_pct"], 0.0)

        dist = self.analytics.get_routing_distribution()
        self.assertEqual(dist["total_requests"], 0)
        self.assertEqual(dist["fallback_rate_pct"], 0.0)

        quality = self.analytics.get_quality_metrics()
        self.assertEqual(quality["total_feedback_count"], 0)
        self.assertEqual(quality["average_rating"], 0.0)

    def test_summary_metrics_calculation(self):
        """Verify summary metrics compute correct sums and averages across events."""
        # 3 Successful events (latencies: 10, 20, 30; tokens: 10, 20, 30; retries: 0, 1, 2)
        # 1 Failed event (latency: 40; tokens: 0; retries: 0)
        e1 = RoutingEvent(request_id="R1", execution_status="SUCCESS", latency_ms=10.0, retry_count=0, total_tokens=10)
        e2 = RoutingEvent(request_id="R2", execution_status="SUCCESS", latency_ms=20.0, retry_count=1, total_tokens=20)
        e3 = RoutingEvent(request_id="R3", execution_status="SUCCESS", latency_ms=30.0, retry_count=2, total_tokens=30)
        e4 = RoutingEvent(request_id="R4", execution_status="FAILED", latency_ms=40.0, retry_count=0, total_tokens=0)

        for e in [e1, e2, e3, e4]:
            self.repo.record_event(e)

        summary = self.analytics.get_summary_metrics()
        self.assertEqual(summary["total_requests"], 4)
        self.assertEqual(summary["successful_requests"], 3)
        self.assertEqual(summary["failed_requests"], 1)
        self.assertEqual(summary["success_rate_pct"], 75.0)
        self.assertEqual(summary["avg_latency_ms"], 25.0)  # (10+20+30+40)/4 = 25.0
        self.assertEqual(summary["avg_retry_count"], 0.75)  # (0+1+2+0)/4 = 0.75
        self.assertEqual(summary["total_tokens"], 60)

    def test_routing_distribution(self):
        """Verify model, provider, fallback rate, and complexity breakdowns."""
        e1 = RoutingEvent(model_id="gpt-4o", provider="OpenAI", fallback_used=False, complexity_tier="High")
        e2 = RoutingEvent(model_id="gpt-4o", provider="OpenAI", fallback_used=True, complexity_tier="High")
        e3 = RoutingEvent(model_id="claude-3.5-haiku", provider="Anthropic", fallback_used=False, complexity_tier="Low")

        for e in [e1, e2, e3]:
            self.repo.record_event(e)

        dist = self.analytics.get_routing_distribution()
        self.assertEqual(dist["total_requests"], 3)
        self.assertEqual(dist["fallback_count"], 1)
        self.assertEqual(dist["fallback_rate_pct"], 33.33)
        self.assertEqual(dist["model_usage"]["gpt-4o"], 2)
        self.assertEqual(dist["model_usage"]["claude-3.5-haiku"], 1)
        self.assertEqual(dist["provider_usage"]["OpenAI"], 2)
        self.assertEqual(dist["provider_usage"]["Anthropic"], 1)
        self.assertEqual(dist["complexity_distribution"]["High"], 2)
        self.assertEqual(dist["complexity_distribution"]["Low"], 1)

    def test_quality_metrics_calculation(self):
        """Verify average ratings and satisfaction percentages."""
        ev = RoutingEvent(request_id="R-QUAL")
        self.repo.record_event(ev)

        # Ratings: 5, 4, 3 -> sum=12, count=3, avg=4.0; ratings >= 4: 2/3 (66.67%)
        fb1 = FeedbackRecord(event_id=ev.event_id, rating=5, quality_category="accurate")
        fb2 = FeedbackRecord(event_id=ev.event_id, rating=4, quality_category="accurate")
        fb3 = FeedbackRecord(event_id=ev.event_id, rating=3, quality_category="slow")

        for f in [fb1, fb2, fb3]:
            self.repo.record_feedback(f)

        quality = self.analytics.get_quality_metrics()
        self.assertEqual(quality["total_feedback_count"], 3)
        self.assertEqual(quality["average_rating"], 4.0)
        self.assertEqual(quality["satisfaction_rate_pct"], 66.67)
        self.assertEqual(quality["rating_distribution"][5], 1)
        self.assertEqual(quality["rating_distribution"][4], 1)
        self.assertEqual(quality["rating_distribution"][3], 1)
        self.assertEqual(quality["quality_category_counts"]["accurate"], 2)
        self.assertEqual(quality["quality_category_counts"]["slow"], 1)

    def test_model_performance_summary(self):
        """Verify per-model performance and rating aggregation."""
        ev1 = RoutingEvent(model_id="gpt-4o", provider="OpenAI", execution_status="SUCCESS", latency_ms=10.0, total_tokens=100)
        ev2 = RoutingEvent(model_id="gpt-4o", provider="OpenAI", execution_status="SUCCESS", latency_ms=20.0, total_tokens=200)
        ev3 = RoutingEvent(model_id="claude-3.5-haiku", provider="Anthropic", execution_status="SUCCESS", latency_ms=5.0, total_tokens=50)

        for e in [ev1, ev2, ev3]:
            self.repo.record_event(e)

        fb1 = FeedbackRecord(event_id=ev1.event_id, rating=5)
        fb2 = FeedbackRecord(event_id=ev2.event_id, rating=3)
        self.repo.record_feedback(fb1)
        self.repo.record_feedback(fb2)

        perf = self.analytics.get_model_performance_summary()
        self.assertEqual(len(perf), 2)

        gpt_perf = next(p for p in perf if p["model_id"] == "gpt-4o")
        self.assertEqual(gpt_perf["request_count"], 2)
        self.assertEqual(gpt_perf["success_rate_pct"], 100.0)
        self.assertEqual(gpt_perf["avg_latency_ms"], 15.0)
        self.assertEqual(gpt_perf["avg_rating"], 4.0)  # (5+3)/2 = 4.0

        claude_perf = next(p for p in perf if p["model_id"] == "claude-3.5-haiku")
        self.assertEqual(claude_perf["request_count"], 1)
        self.assertIsNone(claude_perf["avg_rating"])


if __name__ == "__main__":
    unittest.main()
