"""
Unit tests for Gateway Router FastAPI transport endpoints using TestClient.
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

from fastapi.testclient import TestClient
from gateway_router.src.api import create_app
from gateway_router.src.gateway import GatewayRouter
from gateway_router.src.orchestrator import PipelineRouter


class TestGatewayAPI(unittest.TestCase):
    """Test suite verifying FastAPI transport layer endpoints."""

    def setUp(self):
        self.app = create_app()
        self.client = TestClient(self.app)

    def test_health_endpoint(self):
        """Verify GET /health returns 200 OK and valid health metadata."""
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "healthy")
        self.assertEqual(data["execution_mode"], "mock")
        self.assertIn("OpenAI", data["registered_providers"])

    def test_chat_completions_endpoint(self):
        """Verify POST /v1/chat/completions executes routing and returns valid response payload."""
        payload = {
            "messages": [{"role": "user", "content": "What is Python?"}],
            "temperature": 0.7,
            "metadata": {"task_category": "General Question Answering"}
        }
        resp = self.client.post("/v1/chat/completions", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "SUCCESS")
        self.assertEqual(data["execution_mode"], "mock")
        self.assertIsNotNone(data["model_id"])
        self.assertIn("[MOCK EXECUTION]", data["content"])

    def test_streaming_completions_endpoint(self):
        """Verify POST /v1/chat/completions/stream yields Server-Sent Events (SSE)."""
        payload = {
            "messages": [{"role": "user", "content": "Tell me a joke."}],
            "model": "OpenAI/gpt-4o",
            "stream": True
        }
        resp = self.client.post("/v1/chat/completions/stream", json=payload)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("text/event-stream", resp.headers["content-type"])

        content = resp.text
        self.assertIn("data:", content)
        self.assertIn("[DONE]", content)


if __name__ == "__main__":
    unittest.main()
