"""
Integration tests for PolicyEngine orchestrator and execution pipeline.
"""

import unittest
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
ROUTER_DIR = ROOT_DIR.parent

sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(ROUTER_DIR))

from capability_matcher.src import CapabilityMatcher
from rule_engine.src import RuleEngine
from ranking_engine.src import RankingEngine, RankingResult
from src.context import PolicyContext
from src.usage import UsageState
from src.decisions import DecisionState
from src.engine import PolicyEngine


class TestPolicyEngine(unittest.TestCase):
    """Integration test cases for PolicyEngine."""

    def setUp(self):
        self.capability_matcher = CapabilityMatcher()
        self.rule_engine = RuleEngine()
        self.ranking_engine = RankingEngine()
        self.policy_engine = PolicyEngine()

        self.request_payload = {
            "request_id": "REQ-INTEG-POL",
            "prompt": "Write React component.",
            "metadata": {"task_category": "Programming"},
            "expected_output": {"format": "code"}
        }
        self.cap_result = self.capability_matcher.match(self.request_payload)
        self.rule_result = self.rule_engine.evaluate(self.cap_result)
        self.ranking_result = self.ranking_engine.rank(self.rule_result)

    def test_evaluate_normal_approval(self):
        """Verify successful policy evaluation approving top-ranked model."""
        ctx = PolicyContext(tenant_id="test_tenant")
        decision = self.policy_engine.evaluate(self.ranking_result, context=ctx)

        self.assertEqual(decision.decision, DecisionState.APPROVED)
        self.assertFalse(decision.fallback_used)
        self.assertEqual(decision.selected_rank, 1)
        self.assertIsNotNone(decision.selected_model)
        self.assertEqual(decision.request_id, "REQ-INTEG-POL")

    def test_evaluate_empty_ranking_result(self):
        """Verify graceful NO_CANDIDATE decision when RankingResult is empty."""
        empty_ranking = RankingResult(request_id="REQ-EMPTY", is_satisfiable=False, selected_model=None, ranked_candidates=[])
        decision = self.policy_engine.evaluate(empty_ranking)

        self.assertEqual(decision.decision, DecisionState.NO_CANDIDATE)
        self.assertIsNone(decision.selected_model)
        self.assertEqual(len(decision.evaluated_candidates), 0)

    def test_invalid_negative_config(self):
        """Verify negative budget_limit or fallback attempts raises ValueError."""
        with self.assertRaises(ValueError):
            PolicyContext(budget_limit=-10.0)

        with self.assertRaises(ValueError):
            PolicyContext(max_fallback_attempts=-1)

    def test_usage_state_record_dispatch(self):
        """Verify successful dispatch records cost and tokens into usage state snapshot."""
        usage = UsageState(budget_consumed=0.0)
        ctx = PolicyContext(requested_tokens=1500)

        decision = self.policy_engine.evaluate(self.ranking_result, context=ctx, usage_state=usage)

        self.assertEqual(decision.decision, DecisionState.APPROVED)
        self.assertGreater(usage.budget_consumed, 0.0)
        self.assertEqual(usage.daily_tokens_used, 1500)
        self.assertEqual(usage.daily_requests_used, 1)

    def test_multiple_simultaneous_policy_failures(self):
        """Verify multiple policy violations (e.g. Budget & RateLimit) are collected on a candidate."""
        ctx = PolicyContext(budget_limit=0.1, max_requests_per_window=5)
        usage = UsageState(requests_in_window=5)

        decision = self.policy_engine.evaluate(self.ranking_result, context=ctx, usage_state=usage)

        self.assertEqual(decision.decision, DecisionState.REJECTED)
        self.assertGreaterEqual(len(decision.evaluated_candidates), 1)
        eval_item = decision.evaluated_candidates[0]
        self.assertIn("BUDGET_EXCEEDED", eval_item.failure_reasons)
        self.assertIn("RATE_LIMIT_EXCEEDED", eval_item.failure_reasons)


if __name__ == "__main__":
    unittest.main()
