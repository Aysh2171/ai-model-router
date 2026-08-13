"""
Unit tests for BudgetPolicy runtime governance.
"""

import unittest
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
ROUTER_DIR = ROOT_DIR.parent

sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(ROUTER_DIR))

from model_registry.src import ModelInfo
from capability_matcher.src import CandidateModel
from ranking_engine.src import RankedModel
from src.context import PolicyContext
from src.usage import UsageState
from src.decisions import FailureReason
from src.policies import BudgetPolicy


class TestBudgetPolicy(unittest.TestCase):
    """Unit tests for BudgetPolicy."""

    def setUp(self):
        self.policy = BudgetPolicy()

        self.info_low = ModelInfo(provider="OpenAI", family="GPT", model_id="gpt-4o-mini", display_name="M", description="", cost_tier="low")
        self.cand_low = CandidateModel(model_id="gpt-4o-mini", provider="OpenAI", family="GPT", model_info=self.info_low, context_headroom=10000)
        self.ranked_low = RankedModel(model_id="gpt-4o-mini", provider="OpenAI", family="GPT", candidate=self.cand_low, overall_score=0.9, rank_position=1)

        self.info_high = ModelInfo(provider="OpenAI", family="GPT", model_id="gpt-4o", display_name="H", description="", cost_tier="high")
        self.cand_high = CandidateModel(model_id="gpt-4o", provider="OpenAI", family="GPT", model_info=self.info_high, context_headroom=10000)
        self.ranked_high = RankedModel(model_id="gpt-4o", provider="OpenAI", family="GPT", candidate=self.cand_high, overall_score=0.8, rank_position=2)

    def test_within_budget(self):
        """Verify candidate within budget passes policy."""
        ctx = PolicyContext(budget_limit=10.0)
        usage = UsageState(budget_consumed=2.0)

        outcome = self.policy.evaluate(self.ranked_low, ctx, usage)
        self.assertTrue(outcome.passed)
        self.assertEqual(outcome.estimated_cost, 1.0)

    def test_exceeds_budget(self):
        """Verify candidate exceeding budget limit fails with BUDGET_EXCEEDED."""
        ctx = PolicyContext(budget_limit=5.0)
        usage = UsageState(budget_consumed=0.0)

        outcome = self.policy.evaluate(self.ranked_high, ctx, usage) # high cost = 7.0 units
        self.assertFalse(outcome.passed)
        self.assertEqual(outcome.failure_reason, FailureReason.BUDGET_EXCEEDED.value)
        self.assertIn("Budget limit exceeded", outcome.explanation)

    def test_exact_budget_boundary(self):
        """Verify candidate on exact budget boundary passes."""
        ctx = PolicyContext(budget_limit=5.0)
        usage = UsageState(budget_consumed=4.0)

        outcome = self.policy.evaluate(self.ranked_low, ctx, usage) # 4.0 + 1.0 = 5.0
        self.assertTrue(outcome.passed)


if __name__ == "__main__":
    unittest.main()
