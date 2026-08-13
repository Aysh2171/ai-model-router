"""
Unit tests for QuotaPolicy runtime governance.
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
from src.policies import QuotaPolicy


class TestQuotaPolicy(unittest.TestCase):
    """Unit tests for QuotaPolicy."""

    def setUp(self):
        self.policy = QuotaPolicy()
        self.info = ModelInfo(provider="OpenAI", family="GPT", model_id="gpt-4o-mini", display_name="M", description="")
        self.cand = CandidateModel(model_id="gpt-4o-mini", provider="OpenAI", family="GPT", model_info=self.info, context_headroom=10000)
        self.ranked = RankedModel(model_id="gpt-4o-mini", provider="OpenAI", family="GPT", candidate=self.cand, overall_score=0.9, rank_position=1)

    def test_request_token_bound_pass(self):
        """Verify request within max_tokens_per_request passes."""
        ctx = PolicyContext(max_tokens_per_request=4000, requested_tokens=2000)
        usage = UsageState()

        outcome = self.policy.evaluate(self.ranked, ctx, usage)
        self.assertTrue(outcome.passed)

    def test_request_token_bound_exceeded(self):
        """Verify request exceeding max_tokens_per_request fails."""
        ctx = PolicyContext(max_tokens_per_request=2000, requested_tokens=5000)
        usage = UsageState()

        outcome = self.policy.evaluate(self.ranked, ctx, usage)
        self.assertFalse(outcome.passed)
        self.assertEqual(outcome.failure_reason, FailureReason.TOKEN_QUOTA_EXCEEDED.value)

    def test_daily_request_limit_exceeded(self):
        """Verify daily request quota exhaustion fails."""
        ctx = PolicyContext(daily_request_limit=10)
        usage = UsageState(daily_requests_used=10)

        outcome = self.policy.evaluate(self.ranked, ctx, usage)
        self.assertFalse(outcome.passed)
        self.assertEqual(outcome.failure_reason, FailureReason.REQUEST_QUOTA_EXCEEDED.value)

    def test_monthly_request_limit_exceeded(self):
        """Verify monthly request quota exhaustion fails."""
        ctx = PolicyContext(monthly_request_limit=100)
        usage = UsageState(monthly_requests_used=100)

        outcome = self.policy.evaluate(self.ranked, ctx, usage)
        self.assertFalse(outcome.passed)
        self.assertEqual(outcome.failure_reason, FailureReason.REQUEST_QUOTA_EXCEEDED.value)

    def test_monthly_token_limit_exceeded(self):
        """Verify monthly token quota exhaustion fails."""
        ctx = PolicyContext(monthly_token_limit=100000, requested_tokens=5000)
        usage = UsageState(monthly_tokens_used=98000)

        outcome = self.policy.evaluate(self.ranked, ctx, usage)
        self.assertFalse(outcome.passed)
        self.assertEqual(outcome.failure_reason, FailureReason.TOKEN_QUOTA_EXCEEDED.value)


if __name__ == "__main__":
    unittest.main()
