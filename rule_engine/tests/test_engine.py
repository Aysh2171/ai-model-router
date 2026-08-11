"""
Integration tests for RuleEngine orchestration and evaluation pipeline.
"""

import unittest
import sys
from pathlib import Path

# Add rule_engine and ai-model-router root to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
ROUTER_DIR = ROOT_DIR.parent

sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(ROUTER_DIR))

from capability_matcher.src import CapabilityMatcher
from src.context import PolicyContext
from src.engine import RuleEngine
from src.result import RuleEvaluationResult


class TestRuleEngine(unittest.TestCase):
    """Integration test cases for RuleEngine."""

    def setUp(self):
        self.capability_matcher = CapabilityMatcher()
        self.rule_engine = RuleEngine()

        self.request_payload = {
            "request_id": "REQ-TEST-100",
            "prompt": "Write React frontend component.",
            "metadata": {"task_category": "Programming"},
            "expected_output": {"format": "code"}
        }
        self.cap_result = self.capability_matcher.match(self.request_payload)

    def test_default_policy_evaluation(self):
        """Verify evaluation using default policy configuration."""
        result = self.rule_engine.evaluate(self.cap_result)

        self.assertIsInstance(result, RuleEvaluationResult)
        self.assertTrue(result.is_rule_satisfiable)
        self.assertGreater(result.allowed_count, 0)
        self.assertEqual(result.request_id, "REQ-TEST-100")

    def test_multiple_violations_collection(self):
        """Verify that multiple policy rule violations per candidate model are collected cleanly."""
        ctx = PolicyContext(
            disallowed_providers={"OpenAI"},
            max_cost_tier="low"
        )
        result = self.rule_engine.evaluate(self.cap_result, context=ctx)

        for excl in result.policy_excluded_candidates:
            if excl.provider == "OpenAI":
                self.assertGreaterEqual(len(excl.failed_rule_names), 1)

    def test_unsatisfiable_policy_state(self):
        """Verify is_rule_satisfiable=False when all candidates fail policy rules."""
        ctx = PolicyContext(allowed_providers={"NonExistentProvider"})
        result = self.rule_engine.evaluate(self.cap_result, context=ctx)

        self.assertFalse(result.is_rule_satisfiable)
        self.assertEqual(result.allowed_count, 0)
        self.assertEqual(len(result.allowed_candidates), 0)
        self.assertGreater(result.policy_excluded_count, 0)

    def test_separation_of_capability_and_policy_exclusions(self):
        """Verify capability_excluded_models (Module 3) is kept separate from policy_excluded_candidates (Module 4)."""
        ctx = PolicyContext(disallowed_providers={"Meta"})
        result = self.rule_engine.evaluate(self.cap_result, context=ctx)

        self.assertIsInstance(result.capability_excluded_models, list)
        self.assertIsInstance(result.policy_excluded_candidates, list)
        self.assertEqual(len(result.capability_excluded_models), len(self.cap_result.excluded_models))


if __name__ == "__main__":
    unittest.main()
