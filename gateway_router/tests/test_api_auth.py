"""
Unit Tests for FastAPI Router Authentication and Secret Protection.
Verifies internal X-Router-API-Key validation, chatbot chat endpoint execution,
and guarantees that no real provider API keys are leaked into responses.
"""

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

ROOT_DIR = Path(__file__).resolve().parent.parent
ROUTER_DIR = ROOT_DIR.parent

sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(ROUTER_DIR))

from gateway_router.src.api import create_app
from gateway_router.src.models import GatewayResponse, ExecutionStatus, ExecutionMode


class TestRouterApiAuthentication(unittest.TestCase):

    def setUp(self):
        self.router_key = "test_router_internal_secret_key_999"
        self.patcher = patch.dict(os.environ, {
            "ROUTER_API_KEY": self.router_key,
            "GEMINI_API_KEY": "AIzaSySuperSecretGeminiKey123456789",
            "DEEPSEEK_API_KEY": "sk-SuperSecretDeepSeekKey123456789",
            "GROQ_API_KEY": "gsk_SuperSecretGroqKey123456789",
        }, clear=False)
        self.patcher.start()

        self.app = create_app()
        self.client = TestClient(self.app)

    def tearDown(self):
        self.patcher.stop()

    def test_missing_router_key_rejected(self):
        """Verify requests without X-Router-API-Key receive 401 Unauthorized."""
        res = self.client.post("/api/chat", json={"message": "Hello"})
        self.assertEqual(res.status_code, 401)
        self.assertIn("Missing or invalid X-Router-API-Key", res.json()["detail"])

    def test_invalid_router_key_rejected(self):
        """Verify requests with wrong X-Router-API-Key receive 401 Unauthorized."""
        res = self.client.post(
            "/api/chat",
            headers={"X-Router-API-Key": "wrong_key_xyz"},
            json={"message": "Hello"}
        )
        self.assertEqual(res.status_code, 401)

    def test_valid_router_key_accepted(self):
        """Verify requests with valid internal X-Router-API-Key succeed."""
        with patch("gateway_router.src.orchestrator.PipelineRouter.route_and_execute") as mock_route:
            mock_route.return_value = GatewayResponse(
                request_id="REQ-TEST-AUTH",
                status=ExecutionStatus.SUCCESS,
                model_id="gemini-1.5-flash",
                provider="Google",
                execution_mode="live",
                content="Photosynthesis is the process by which plants use sunlight to produce energy.",
                latency_ms=150.0,
                decision_state="APPROVED_WITH_FALLBACK",
                usage={"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30}
            )

            res = self.client.post(
                "/api/chat",
                headers={"X-Router-API-Key": self.router_key},
                json={"message": "Explain photosynthesis."}
            )

            self.assertEqual(res.status_code, 200)
            data = res.json()
            self.assertEqual(data["status"], "SUCCESS")
            self.assertEqual(data["selected_model"], "gemini-1.5-flash")
            self.assertEqual(data["selected_provider"], "Google")
            self.assertEqual(data["execution_mode"], "live")
            self.assertIn("Photosynthesis", data["response"])

    def test_secret_protection_no_key_leakage(self):
        """
        SECURITY AUDIT TEST:
        Ensure provider API keys (GEMINI_API_KEY, DEEPSEEK_API_KEY, etc.)
        are NEVER exposed in any API response payload.
        """
        with patch("gateway_router.src.orchestrator.PipelineRouter.route_and_execute") as mock_route:
            mock_route.return_value = GatewayResponse(
                request_id="REQ-SEC-AUDIT",
                status=ExecutionStatus.SUCCESS,
                model_id="gemini-1.5-flash",
                provider="Google",
                execution_mode="live",
                content="Secret test output",
                latency_ms=120.0
            )

            res = self.client.post(
                "/api/chat",
                headers={"X-Router-API-Key": self.router_key},
                json={"message": "Security audit request"}
            )

            raw_response_text = res.text
            self.assertNotIn("AIzaSySuperSecretGeminiKey123456789", raw_response_text)
            self.assertNotIn("sk-SuperSecretDeepSeekKey123456789", raw_response_text)
            self.assertNotIn("gsk_SuperSecretGroqKey123456789", raw_response_text)

    def test_status_endpoint_no_secrets(self):
        """Verify /api/status exposes configuration state without secret keys."""
        res = self.client.get("/api/status")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "operational")
        self.assertIn("providers", data)
        self.assertNotIn("AIzaSySuperSecretGeminiKey123456789", res.text)


if __name__ == "__main__":
    unittest.main()
