"""
Unit tests for ComponentScorer criteria algorithms and deterministic tie-breaking logic.
Covering Refinement 1 (Inversion symmetry), Refinement 2 (Status independence), Refinement 4 (Profile resilience), Refinement 5 (Headroom consistency).
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
from src.config import RankingConfig
from src.scoring import ComponentScorer


class TestComponentScorer(unittest.TestCase):
    """Unit tests for individual criteria scoring functions."""

    def setUp(self):
        self.model_info_low = ModelInfo(
            provider="OpenAI",
            family="GPT",
            model_id="gpt-4o-mini",
            display_name="GPT-4o Mini",
            description="Fast low cost model",
            status="available",
            tags=["fast", "lightweight"],
            cost_tier="low",
            latency_tier="fast"
        )
        self.cand_low = CandidateModel(
            model_id="gpt-4o-mini",
            provider="OpenAI",
            family="GPT",
            model_info=self.model_info_low,
            context_headroom=120000
        )

        self.model_info_high = ModelInfo(
            provider="Anthropic",
            family="Claude",
            model_id="claude-3.5-sonnet",
            display_name="Claude 3.5 Sonnet",
            description="High capacity model",
            status="available",
            tags=["multimodal", "coding", "reasoning"],
            cost_tier="high",
            latency_tier="fast",
            supports_code=True,
            supports_reasoning=True
        )
        self.cand_high = CandidateModel(
            model_id="claude-3.5-sonnet",
            provider="Anthropic",
            family="Claude",
            model_info=self.model_info_high,
            context_headroom=180000
        )

    def test_cost_scoring(self):
        """Verify cost scoring mapping for low vs high cost models."""
        score_low = ComponentScorer.score_cost(self.cand_low, prefer_lower_cost=True)
        score_high = ComponentScorer.score_cost(self.cand_high, prefer_lower_cost=True)

        self.assertEqual(score_low, 1.00)
        self.assertEqual(score_high, 0.35)
        self.assertGreater(score_low, score_high)

    def test_cost_preference_inversion_symmetry(self):
        """Refinement 1: Verify cost preference inversion is mathematically symmetric (1.0 - base)."""
        score_normal = ComponentScorer.score_cost(self.cand_high, prefer_lower_cost=True)
        score_inverted = ComponentScorer.score_cost(self.cand_high, prefer_lower_cost=False)

        self.assertEqual(score_normal, 0.35)
        self.assertEqual(score_inverted, 0.65)
        self.assertAlmostEqual(score_normal + score_inverted, 1.00, places=4)

        score_low_norm = ComponentScorer.score_cost(self.cand_low, prefer_lower_cost=True)
        score_low_inv = ComponentScorer.score_cost(self.cand_low, prefer_lower_cost=False)
        self.assertEqual(score_low_norm, 1.00)
        self.assertEqual(score_low_inv, 0.00)

    def test_latency_preference_inversion_symmetry(self):
        """Refinement 1: Verify latency preference inversion is mathematically symmetric (1.0 - base)."""
        info_slow = ModelInfo(provider="Test", family="Test", model_id="test-slow", display_name="Slow", description="", latency_tier="slow")
        cand_slow = CandidateModel(model_id="test-slow", provider="Test", family="Test", model_info=info_slow, context_headroom=1000)

        score_fast_norm = ComponentScorer.score_latency(self.cand_low, prefer_lower_latency=True)
        score_fast_inv = ComponentScorer.score_latency(self.cand_low, prefer_lower_latency=False)
        self.assertEqual(score_fast_norm, 1.00)
        self.assertEqual(score_fast_inv, 0.00)

        score_slow_norm = ComponentScorer.score_latency(cand_slow, prefer_lower_latency=True)
        score_slow_inv = ComponentScorer.score_latency(cand_slow, prefer_lower_latency=False)
        self.assertEqual(score_slow_norm, 0.20)
        self.assertEqual(score_slow_inv, 0.80)
        self.assertAlmostEqual(score_slow_norm + score_slow_inv, 1.00, places=4)

    def test_lifecycle_status_does_not_affect_suitability(self):
        """Refinement 2: Verify candidate lifecycle status (e.g. preview) does not alter suitability scoring."""
        info_preview = ModelInfo(
            provider="OpenAI",
            family="GPT",
            model_id="gpt-4o-mini-preview",
            display_name="GPT-4o Mini Preview",
            description="Preview model",
            status="preview",
            tags=["fast", "lightweight"],
            cost_tier="low",
            latency_tier="fast"
        )
        cand_preview = CandidateModel(
            model_id="gpt-4o-mini-preview",
            provider="OpenAI",
            family="GPT",
            model_info=info_preview,
            context_headroom=120000
        )

        profile_low = {"complexity": "LOW"}
        score_available = ComponentScorer.score_suitability(self.cand_low, profile_low)
        score_preview = ComponentScorer.score_suitability(cand_preview, profile_low)

        self.assertEqual(score_available, 1.00)
        self.assertEqual(score_preview, 1.00)
        self.assertEqual(score_available, score_preview)

    def test_complexity_profile_resilience(self):
        """Refinement 4: Verify resilience across string complexity labels, numeric scores, boundaries, and fallbacks."""
        # Explicit label takes precedence
        self.assertEqual(ComponentScorer.score_suitability(self.cand_high, {"complexity": "HIGH", "complexity_score": 10}), 1.00)
        self.assertEqual(ComponentScorer.score_suitability(self.cand_low, {"complexity": "LOW", "complexity_score": 90}), 1.00)

        # Numeric score fallback (boundaries: <=30 -> LOW, 31-70 -> MEDIUM, >=71 -> HIGH)
        self.assertEqual(ComponentScorer.score_suitability(self.cand_high, {"complexity_score": 85}), 1.00)
        self.assertEqual(ComponentScorer.score_suitability(self.cand_high, {"complexity_score": 71}), 1.00)
        self.assertEqual(ComponentScorer.score_suitability(self.cand_low, {"complexity_score": 30}), 1.00)

        # Malformed & missing profile fallback to MEDIUM safely
        self.assertEqual(ComponentScorer.score_suitability(self.cand_low, {"complexity_score": "invalid"}), 1.00)
        self.assertEqual(ComponentScorer.score_suitability(self.cand_low, {}), 1.00)
        self.assertEqual(ComponentScorer.score_suitability(self.cand_low, None), 1.00)

    def test_headroom_scoring_standardized(self):
        """Refinement 5: Verify standardized headroom scoring, score bounds [0.0, 1.0], and monotonicity."""
        # Batch relative mode
        s1 = ComponentScorer.score_headroom(self.cand_low, batch_max_headroom=200000)
        s2 = ComponentScorer.score_headroom(self.cand_high, batch_max_headroom=200000)
        self.assertEqual(s1, 0.60)
        self.assertEqual(s2, 0.90)
        self.assertLess(s1, s2)

        # Zero and negative headroom
        cand_zero = CandidateModel(model_id="z", provider="P", family="F", model_info=self.model_info_low, context_headroom=0)
        cand_neg = CandidateModel(model_id="n", provider="P", family="F", model_info=self.model_info_low, context_headroom=-500)
        self.assertEqual(ComponentScorer.score_headroom(cand_zero, batch_max_headroom=200000), 0.0)
        self.assertEqual(ComponentScorer.score_headroom(cand_neg, batch_max_headroom=200000), 0.0)

        # Standalone mode
        s_standalone = ComponentScorer.score_headroom(self.cand_low, batch_max_headroom=0)
        self.assertEqual(s_standalone, 0.60)
        self.assertGreaterEqual(s_standalone, 0.0)
        self.assertLessEqual(s_standalone, 1.0)

    def test_compute_candidate_score(self):
        """Verify overall weighted score computation."""
        cfg = RankingConfig(cost_weight=0.50, latency_weight=0.50, suitability_weight=0.0, headroom_weight=0.0)
        overall, comp_scores, exp = ComponentScorer.compute_candidate_score(
            candidate=self.cand_low,
            config=cfg,
            complexity_profile={"complexity": "LOW"},
            batch_max_headroom=120000
        )

        self.assertEqual(overall, 1.00)
        self.assertEqual(comp_scores["cost"], 1.00)
        self.assertEqual(comp_scores["latency"], 1.00)
        self.assertIn("Overall: 1.0000", exp)


if __name__ == "__main__":
    unittest.main()
