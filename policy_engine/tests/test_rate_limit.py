"""
Unit tests for RateLimitPolicy runtime governance.
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
from src.policies import RateLimitPolicy


class TestRateLimitPolicy(unittest.TestCase):
    """Unit tests for RateLimitPolicy."""

    def setUp(self):
        self.policy = RateLimitPolicy()
        self.info = ModelInfo(provider="OpenAI", family="GPT", model_id="gpt-4o-mini", display_name="M", description="")
        self.cand = CandidateModel(model_id="gpt-4o-mini", provider="OpenAI", family="GPT", model_info=self.info, context_headroom=10000)
        self.ranked = RankedModel(model_id="gpt-4o-mini", provider="OpenAI", family="GPT", candidate=self.cand, overall_score=0.9, rank_position=1)

    def test_rate_limit_within_window(self):
        """Verify request within rate limit window passes."""
        ctx = PolicyContext(max_requests_per_window=10)
        usage = UsageState(requests_in_window=5)

        outcome = self.policy.evaluate(self.ranked, ctx, usage)
        self.assertTrue(outcome.passed)

    def test_rate_limit_exceeded(self):
        """Verify request exceeding window cap fails."""
        ctx = PolicyContext(max_requests_per_window=5)
        usage = UsageState(requests_in_window=5)

        outcome = self.policy.evaluate(self.ranked, ctx, usage)
        self.assertFalse(outcome.passed)
        self.assertEqual(outcome.failure_reason, FailureReason.RATE_LIMIT_EXCEEDED.value)


if __name__ == "__main__":
    unittest.main()
