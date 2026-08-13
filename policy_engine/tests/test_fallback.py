"""
Unit tests for Fallback governance and Ranking Order Preservation Invariant.
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
from ranking_engine.src import RankedModel, RankingResult
from src.context import PolicyContext
from src.usage import UsageState
from src.decisions import DecisionState, FailureReason
from src.engine import PolicyEngine


class TestFallbackGovernance(unittest.TestCase):
    """Unit tests verifying fallback governance and strict ranking order preservation invariant."""

    def setUp(self):
        self.engine = PolicyEngine()

        # Model A: High cost (7.0 units) -> Rank #1
        self.info_a = ModelInfo(provider="OpenAI", family="GPT", model_id="model-a", display_name="A", description="", cost_tier="high")
        self.cand_a = CandidateModel(model_id="model-a", provider="OpenAI", family="GPT", model_info=self.info_a, context_headroom=10000)
        self.ranked_a = RankedModel(model_id="model-a", provider="OpenAI", family="GPT", candidate=self.cand_a, overall_score=0.90, rank_position=1)

        # Model B: Low cost (1.0 units) -> Rank #2
        self.info_b = ModelInfo(provider="OpenAI", family="GPT", model_id="model-b", display_name="B", description="", cost_tier="low")
        self.cand_b = CandidateModel(model_id="model-b", provider="OpenAI", family="GPT", model_info=self.info_b, context_headroom=5000)
        self.ranked_b = RankedModel(model_id="model-b", provider="OpenAI", family="GPT", candidate=self.cand_b, overall_score=0.80, rank_position=2)

        # Model C: Low cost (1.0 units) -> Rank #3
        self.info_c = ModelInfo(provider="OpenAI", family="GPT", model_id="model-c", display_name="C", description="", cost_tier="low")
        self.cand_c = CandidateModel(model_id="model-c", provider="OpenAI", family="GPT", model_info=self.info_c, context_headroom=2000)
        self.ranked_c = RankedModel(model_id="model-c", provider="OpenAI", family="GPT", candidate=self.cand_c, overall_score=0.70, rank_position=3)

        self.ranking_result = RankingResult(
            request_id="REQ-FALLBACK-01",
            is_satisfiable=True,
            selected_model=self.ranked_a,
            ranked_candidates=[self.ranked_a, self.ranked_b, self.ranked_c],
            total_candidates=3
        )

    def test_ranking_order_preservation_invariant(self):
        """CRITICAL INVARIANT TEST: Verify Policy Engine NEVER changes ranking order A > B > C during fallback."""
        ctx = PolicyContext(budget_limit=5.0, fallback_enabled=True, max_fallback_attempts=3) # Rank A (7.0) exceeds budget, Rank B (1.0) succeeds

        decision = self.engine.evaluate(self.ranking_result, context=ctx)

        self.assertEqual(decision.decision, DecisionState.APPROVED_WITH_FALLBACK)
        self.assertTrue(decision.fallback_used)
        self.assertEqual(decision.selected_rank, 2)
        self.assertEqual(decision.selected_model.model_id, "model-b")

        # Verify evaluation list preserves exact original rank order A -> B
        eval_ranks = [e.rank_position for e in decision.evaluated_candidates]
        self.assertEqual(eval_ranks, [1, 2])
        self.assertEqual(decision.evaluated_candidates[0].model_id, "model-a")
        self.assertEqual(decision.evaluated_candidates[1].model_id, "model-b")

        # Verify original scores and rank positions on candidates were NOT modified
        self.assertEqual(self.ranked_a.rank_position, 1)
        self.assertEqual(self.ranked_b.rank_position, 2)
        self.assertEqual(self.ranked_c.rank_position, 3)

    def test_fallback_disabled(self):
        """Verify fallback disabled stops after Rank #1 fails policy."""
        ctx = PolicyContext(budget_limit=5.0, fallback_enabled=False)

        decision = self.engine.evaluate(self.ranking_result, context=ctx)

        self.assertEqual(decision.decision, DecisionState.REJECTED)
        self.assertFalse(decision.fallback_used)
        self.assertEqual(len(decision.evaluated_candidates), 1) # Only Rank #1 evaluated

    def test_max_fallback_attempts_allows_rank_2_evaluation(self):
        """Verify max_fallback_attempts = 1 permits Rank #1 to fail and Rank #2 to be evaluated."""
        # Rank A (7.0 units) exceeds budget limit (5.0 units). Rank B (1.0 unit) is affordable.
        # max_fallback_attempts = 1 allows evaluating Rank #2.
        ctx = PolicyContext(budget_limit=5.0, fallback_enabled=True, max_fallback_attempts=1)

        decision = self.engine.evaluate(self.ranking_result, context=ctx)

        self.assertEqual(decision.decision, DecisionState.APPROVED_WITH_FALLBACK)
        self.assertTrue(decision.fallback_used)
        self.assertEqual(decision.selected_rank, 2)
        self.assertEqual(decision.selected_model.model_id, "model-b")
        self.assertEqual(decision.fallback_attempts, 1)
        self.assertEqual(len(decision.evaluated_candidates), 2)

    def test_request_level_failure_short_circuits_fallback(self):
        """Verify request/tenant-level failures (e.g. RATE_LIMIT_EXCEEDED) terminate fallback immediately."""
        ctx = PolicyContext(max_requests_per_window=5, fallback_enabled=True, max_fallback_attempts=3)
        usage = UsageState(requests_in_window=5)

        decision = self.engine.evaluate(self.ranking_result, context=ctx, usage_state=usage)

        self.assertEqual(decision.decision, DecisionState.REJECTED)
        self.assertFalse(decision.fallback_used)
        self.assertEqual(decision.fallback_attempts, 1)
        # Verify that ONLY Candidate #1 was evaluated before short-circuiting
        self.assertEqual(len(decision.evaluated_candidates), 1)
        self.assertEqual(decision.evaluated_candidates[0].failure_reasons, [FailureReason.RATE_LIMIT_EXCEEDED.value])


if __name__ == "__main__":
    unittest.main()
