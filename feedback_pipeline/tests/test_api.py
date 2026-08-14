"""
Tests for Feedback Pipeline FastAPI REST Transport Layer.
"""

import unittest
from fastapi.testclient import TestClient

from feedback_pipeline.src.config import FeedbackConfig
from feedback_pipeline.src.repository import SQLAlchemyFeedbackRepository
from feedback_pipeline.src.service import FeedbackService
from feedback_pipeline.src.analytics import FeedbackAnalytics
from feedback_pipeline.src.api import create_app


class TestFeedbackAPI(unittest.TestCase):
    """Test suite verifying FastAPI transport endpoints."""

    def setUp(self):
        """Initialize in-memory service and FastAPI TestClient."""
        self.config = FeedbackConfig(database_url="sqlite:///:memory:")
        self.repo = SQLAlchemyFeedbackRepository(database_url=self.config.database_url)
        self.service = FeedbackService(repository=self.repo, config=self.config)
        self.analytics = FeedbackAnalytics(repository=self.repo)
        self.app = create_app(service=self.service, analytics=self.analytics)
        self.client = TestClient(self.app)

    def test_health_endpoint(self):
        """Verify GET /health returns operational status 200 OK."""
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["module"], "feedback_pipeline")

    def test_ingest_and_get_event_endpoint(self):
        """Verify POST /events ingests telemetry and GET /events/{id} retrieves it."""
        payload = {
            "request_id": "REQ-API-001",
            "execution_status": "SUCCESS",
            "task_category": "Coding",
            "model_id": "gpt-4o",
            "provider": "OpenAI",
            "latency_ms": 14.5,
            "prompt_tokens": 12,
            "completion_tokens": 24,
            "total_tokens": 36
        }
        post_resp = self.client.post("/events", json=payload)
        self.assertEqual(post_resp.status_code, 201)
        data = post_resp.json()
        self.assertEqual(data["status"], "recorded")
        event_id = data["event"]["event_id"]

        get_resp = self.client.get(f"/events/{event_id}")
        self.assertEqual(get_resp.status_code, 200)
        evt_data = get_resp.json()
        self.assertEqual(evt_data["event"]["request_id"], "REQ-API-001")
        self.assertEqual(evt_data["event"]["model_id"], "gpt-4o")
        self.assertEqual(evt_data["feedback"], [])

    def test_submit_feedback_endpoint(self):
        """Verify POST /events/{event_id}/feedback attaches feedback."""
        # 1. Ingest event
        post_resp = self.client.post("/events", json={"request_id": "REQ-API-002", "model_id": "claude-3.5-haiku"})
        event_id = post_resp.json()["event"]["event_id"]

        # 2. Attach feedback
        fb_payload = {
            "rating": 5,
            "quality_category": "accurate",
            "comment": "Quick and correct answer.",
            "evaluator_id": "user_bob"
        }
        fb_resp = self.client.post(f"/events/{event_id}/feedback", json=fb_payload)
        self.assertEqual(fb_resp.status_code, 201)
        fb_data = fb_resp.json()
        self.assertEqual(fb_data["status"], "recorded")
        self.assertEqual(fb_data["feedback"]["rating"], 5)

        # 3. Retrieve event and verify feedback is attached
        get_resp = self.client.get(f"/events/{event_id}")
        self.assertEqual(len(get_resp.json()["feedback"]), 1)

    def test_analytics_endpoints(self):
        """Verify GET /analytics and GET /analytics/summary return computed metrics."""
        self.client.post("/events", json={"request_id": "REQ-ANA-01", "model_id": "gpt-4o", "latency_ms": 10.0})
        self.client.post("/events", json={"request_id": "REQ-ANA-02", "model_id": "minimax-text-01", "latency_ms": 20.0})

        resp_full = self.client.get("/analytics")
        self.assertEqual(resp_full.status_code, 200)
        full_data = resp_full.json()
        self.assertEqual(full_data["summary"]["total_requests"], 2)
        self.assertEqual(full_data["summary"]["avg_latency_ms"], 15.0)

        resp_summary = self.client.get("/analytics/summary")
        self.assertEqual(resp_summary.status_code, 200)
        self.assertEqual(resp_summary.json()["total_requests"], 2)


if __name__ == "__main__":
    unittest.main()
