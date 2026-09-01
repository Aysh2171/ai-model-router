"""
Unit Tests for Provider Availability Policy and Rank Fallback.
Verifies that models without active credentials are automatically skipped,
allowing the highest-ranked available candidate model to be approved.
"""

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT_DIR = Path(__file__).resolve().parent.parent
ROUTER_DIR = ROOT_DIR.parent

sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(ROUTER_DIR))

from model_registry.src import ModelInfo
from capability_matcher.src import CandidateModel
from ranking_engine.src import RankedModel, RankingResult
from policy_engine.src import PolicyEngine, PolicyContext, UsageState, DecisionState, FailureReason
from policy_engine.src.policies.availability import ProviderAvailabilityPolicy


def create_candidate(model_id: str, provider: str, rank: int, score: float = 0.9) -> RankedModel:
    info = ModelInfo(
        provider=provider,
        family="TestFamily",
        model_id=model_id,
        display_name=model_id,
        description="Test model",
        cost_tier="low",
        latency_tier="fast"
    )
    cand = CandidateModel(
        model_id=model_id,
        provider=provider,
        family="TestFamily",
        model_info=info,
        context_headroom=120000
    )
    return RankedModel(
        model_id=model_id,
        provider=provider,
        family="TestFamily",
        candidate=cand,
        overall_score=score,
        rank_position=rank,
        component_scores={"cost": 0.9, "latency": 0.9, "suitability": 0.9, "headroom": 0.9},
        scoring_explanation="Test ranking score"
    )


class TestProviderAvailabilityPolicy(unittest.TestCase):

    def test_provider_availability_detection(self):
        """Test detection of configured vs unconfigured provider API keys."""
        with patch.dict(os.environ, {"GEMINI_API_KEY": "AIzaSyTestKey1234567890", "ANTHROPIC_API_KEY": ""}, clear=False):
            policy = ProviderAvailabilityPolicy()
            self.assertTrue(policy.is_provider_available("Google"))
            self.assertFalse(policy.is_provider_available("Anthropic"))

    def test_availability_policy_evaluation_pass(self):
        """Test that configured provider passes availability policy."""
        with patch.dict(os.environ, {"GROQ_API_KEY": "gsk_TestSecretKey1234567890"}, clear=False):
            policy = ProviderAvailabilityPolicy()
            model = create_candidate("llama-3.3-70b-versatile", "Groq", 1)
            ctx = PolicyContext(require_available_credentials=True)
            usage = UsageState()
            outcome = policy.evaluate(model, ctx, usage)
            self.assertTrue(outcome.passed)
            self.assertIsNone(outcome.failure_reason)

    def test_availability_policy_evaluation_fail(self):
        """Test that unconfigured provider fails availability policy with PROVIDER_UNAVAILABLE."""
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": ""}, clear=False):
            policy = ProviderAvailabilityPolicy()
            model = create_candidate("claude-3.5-sonnet", "Anthropic", 1)
            ctx = PolicyContext(require_available_credentials=True)
            usage = UsageState()
            outcome = policy.evaluate(model, ctx, usage)
            self.assertFalse(outcome.passed)
            self.assertEqual(outcome.failure_reason, FailureReason.PROVIDER_UNAVAILABLE.value)

    def test_end_to_end_availability_fallback(self):
        """
        Scenario:
          Rank #1: Claude 3.5 Sonnet (Anthropic) — Unconfigured -> Skipped
          Rank #2: GPT-4o (OpenAI)             — Unconfigured -> Skipped
          Rank #3: Gemini 1.5 Flash (Google)   — Configured   -> APPROVED_WITH_FALLBACK
        """
        env_override = {
            "ANTHROPIC_API_KEY": "",
            "OPENAI_API_KEY": "",
            "GEMINI_API_KEY": "AIzaSyActiveGeminiKey123456",
        }
        with patch.dict(os.environ, env_override, clear=False):
            c1 = create_candidate("claude-3.5-sonnet", "Anthropic", 1, 0.95)
            c2 = create_candidate("gpt-4o", "OpenAI", 2, 0.90)
            c3 = create_candidate("gemini-1.5-flash", "Google", 3, 0.85)

            ranking = RankingResult(
                request_id="REQ-AVAIL-TEST",
                is_satisfiable=True,
                selected_model=c1,
                ranked_candidates=[c1, c2, c3],
                total_candidates=3
            )

            engine = PolicyEngine()
            ctx = PolicyContext(require_available_credentials=True)
            decision = engine.evaluate(ranking, context=ctx)

            self.assertEqual(decision.decision, DecisionState.APPROVED_WITH_FALLBACK)
            self.assertEqual(decision.selected_model.model_id, "gemini-1.5-flash")
            self.assertEqual(decision.selected_model.provider, "Google")
            self.assertEqual(decision.selected_rank, 3)
            self.assertTrue(decision.fallback_used)
            self.assertEqual(decision.fallback_attempts, 2)


if __name__ == "__main__":
    unittest.main()
