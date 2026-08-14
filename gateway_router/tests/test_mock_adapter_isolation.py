"""
Unit and Integration Tests for MockProviderAdapter Request-Scoped State Isolation in Gateway Router.
"""

import unittest
from unittest.mock import Mock
from gateway_router.src.models import GatewayRequest, ExecutionStatus
from gateway_router.src.adapters.mock import MockProviderAdapter
from gateway_router.src.gateway import GatewayRouter
from gateway_router.src.adapters.registry import AdapterRegistry
from gateway_router.src.orchestrator import PipelineRouter
from ranking_engine.src import RankedModel
from model_registry.src import ModelInfo
from capability_matcher.src import CandidateModel


class TestMockAdapterIsolation(unittest.TestCase):
    """Test suite verifying request-scoped attempt isolation and fault simulation in MockProviderAdapter."""

    def setUp(self):
        self.adapter = MockProviderAdapter(provider="OpenAI")
        self.info = ModelInfo(
            provider="OpenAI",
            family="GPT-4",
            model_id="gpt-4o",
            display_name="GPT-4o",
            description="Test",
        )
        self.candidate = CandidateModel(
            model_id="gpt-4o",
            provider="OpenAI",
            family="GPT-4",
            model_info=self.info,
            context_headroom=100000,
        )
        self.model = RankedModel(
            model_id="gpt-4o",
            provider="OpenAI",
            family="GPT-4",
            candidate=self.candidate,
            overall_score=0.95,
            rank_position=1,
        )

    def test_repeat_transient_simulation_isolation(self):
        """Verify consecutive requests with transient fault simulation both independently trigger failures and retries."""
        req_1 = GatewayRequest(
            request_id="REQ-001",
            prompt="Hello 1",
            simulation_options={"fail_mode": "transient_then_success", "fail_count_before_success": 1}
        )
        # Attempt 1 for REQ-001 fails
        with self.assertRaises(Exception):
            self.adapter.execute(req_1, self.model)
        # Attempt 2 for REQ-001 succeeds
        res_1 = self.adapter.execute(req_1, self.model)
        self.assertIn("Simulated response", res_1.content)

        # NEW Request REQ-002 on SAME adapter must NOT succeed immediately
        req_2 = GatewayRequest(
            request_id="REQ-002",
            prompt="Hello 2",
            simulation_options={"fail_mode": "transient_then_success", "fail_count_before_success": 1}
        )
        # Attempt 1 for REQ-002 fails (isolated state!)
        with self.assertRaises(Exception):
            self.adapter.execute(req_2, self.model)
        # Attempt 2 for REQ-002 succeeds
        res_2 = self.adapter.execute(req_2, self.model)
        self.assertIn("Simulated response", res_2.content)

    def test_different_thresholds_isolation(self):
        """Verify requests with different fail_count_before_success thresholds follow their own counts."""
        req_a = GatewayRequest(
            request_id="REQ-A",
            prompt="A",
            simulation_options={"fail_mode": "transient_then_success", "fail_count_before_success": 1}
        )
        req_b = GatewayRequest(
            request_id="REQ-B",
            prompt="B",
            simulation_options={"fail_mode": "transient_then_success", "fail_count_before_success": 2}
        )

        # REQ-A: 1 fail, then success
        with self.assertRaises(Exception):
            self.adapter.execute(req_a, self.model)
        res_a = self.adapter.execute(req_a, self.model)
        self.assertIsNotNone(res_a)

        # REQ-B: 2 fails, then success
        with self.assertRaises(Exception):
            self.adapter.execute(req_b, self.model)
        with self.assertRaises(Exception):
            self.adapter.execute(req_b, self.model)
        res_b = self.adapter.execute(req_b, self.model)
        self.assertIsNotNone(res_b)

    def test_streaming_simulation_attempt_parity(self):
        """Verify execute_stream adheres to request-scoped attempt counts and simulation fault triggers."""
        req_stream = GatewayRequest(
            request_id="REQ-STREAM-001",
            prompt="Stream",
            simulation_options={"fail_mode": "transient_then_success", "fail_count_before_success": 1}
        )
        # Attempt 1 for REQ-STREAM-001 raises TransientExecutionError
        with self.assertRaises(Exception):
            list(self.adapter.execute_stream(req_stream, self.model))

        # Attempt 2 for REQ-STREAM-001 yields chunks successfully
        chunks = list(self.adapter.execute_stream(req_stream, self.model))
        self.assertGreater(len(chunks), 0)
        self.assertTrue(chunks[-1].is_final)

    def test_consecutive_pipeline_requests_with_fault_injection(self):
        """Verify 10 consecutive pipeline executions with transient fault injection all produce retry_count=1 and SUCCESS."""
        pipeline = PipelineRouter()
        for i in range(10):
            req_payload = {
                "request_id": f"REQ-CONSEC-{i:03d}",
                "prompt": "Test fault injection",
                "metadata": {"task_category": "Programming"}
            }
            resp = pipeline.route_and_execute(
                raw_request=req_payload,
                simulation_options={"fail_mode": "transient_then_success", "fail_count_before_success": 1}
            )
            self.assertEqual(resp.status, ExecutionStatus.SUCCESS)
            self.assertEqual(resp.retry_count, 1)

    def test_concurrent_multithreaded_requests_isolation(self):
        """Verify 20 concurrent threads running distinct requests on the same adapter experience isolated retry attempts."""
        import concurrent.futures

        def worker(req_id: str):
            req = GatewayRequest(
                request_id=req_id,
                prompt=f"Prompt for {req_id}",
                simulation_options={"fail_mode": "transient_then_success", "fail_count_before_success": 1}
            )
            # Attempt 1: MUST fail
            attempt_1_failed = False
            try:
                self.adapter.execute(req, self.model)
            except Exception:
                attempt_1_failed = True

            # Attempt 2: MUST succeed
            attempt_2_succeeded = False
            try:
                res = self.adapter.execute(req, self.model)
                if res and res.content:
                    attempt_2_succeeded = True
            except Exception:
                attempt_2_succeeded = False

            return (req_id, attempt_1_failed, attempt_2_succeeded)

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(worker, f"REQ-THREAD-{i:03d}") for i in range(20)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        for req_id, att1_fail, att2_succ in results:
            self.assertTrue(att1_fail, f"{req_id} attempt 1 should have failed")
            self.assertTrue(att2_succ, f"{req_id} attempt 2 should have succeeded")

        # Verify state is cleaned up after all threads finish
        self.assertEqual(len(self.adapter._request_attempts), 0)


if __name__ == "__main__":
    unittest.main()
