"""
Integration tests for RankingEngine orchestrator and pipeline execution.
Covering Refinement 3 (Weight normalization preserving zero weights).
"""

import unittest
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
ROUTER_DIR = ROOT_DIR.parent

sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(ROUTER_DIR))

from capability_matcher.src import CapabilityMatcher, CandidateModel
from rule_engine.src import RuleEngine, PolicyContext
from model_registry.src import ModelInfo
from src.config import RankingConfig
from src.result import RankingResult
from src.engine import RankingEngine


class TestRankingEngine(unittest.TestCase):
    """Integration test cases for RankingEngine."""

    def setUp(self):
        self.capability_matcher = CapabilityMatcher()
        self.rule_engine = RuleEngine()
        self.ranking_engine = RankingEngine()

        self.request_payload = {
            "request_id": "REQ-RANK-TEST",
            "prompt": "Build React dashboard component.",
            "metadata": {"task_category": "Programming"},
            "expected_output": {"format": "code"}
        }
        self.cap_result = self.capability_matcher.match(self.request_payload)
        self.rule_result = self.rule_engine.evaluate(self.cap_result)

    def test_rank_integration(self):
        """Verify successful ranking execution consuming RuleEngine output."""
        result = self.ranking_engine.rank(self.rule_result)

        self.assertIsInstance(result, RankingResult)
        self.assertTrue(result.is_satisfiable)
        self.assertIsNotNone(result.selected_model)
        self.assertEqual(result.selected_model.rank_position, 1)
        self.assertGreater(result.total_candidates, 0)
        self.assertEqual(len(result.ranked_candidates), result.total_candidates)

    def test_weight_auto_normalization(self):
        """Verify that weights not summing to 1.0 are auto-normalized cleanly."""
        cfg = RankingConfig(cost_weight=2.0, latency_weight=2.0, suitability_weight=2.0, headroom_weight=2.0)
        self.assertEqual(cfg.cost_weight, 0.25)
        self.assertEqual(cfg.latency_weight, 0.25)

    def test_zero_weights_preserved_during_normalization(self):
        """Refinement 3: Verify that explicit zero-weight parameters remain strictly zero after normalization residual adjustments."""
        cfg = RankingConfig(cost_weight=0.0, latency_weight=0.5, suitability_weight=0.5, headroom_weight=0.0)

        self.assertEqual(cfg.cost_weight, 0.0)
        self.assertEqual(cfg.latency_weight, 0.5)
        self.assertEqual(cfg.suitability_weight, 0.5)
        self.assertEqual(cfg.headroom_weight, 0.0)
        self.assertAlmostEqual(cfg.cost_weight + cfg.latency_weight + cfg.suitability_weight + cfg.headroom_weight, 1.0, places=4)

    def test_invalid_negative_weight(self):
        """Verify that negative weights raise ValueError."""
        with self.assertRaises(ValueError):
            RankingConfig(cost_weight=-0.50)

    def test_empty_candidates_handling(self):
        """Verify graceful handling when candidates list is empty."""
        strict_pol = PolicyContext(allowed_providers={"NonExistentProvider"})
        empty_rule_result = self.rule_engine.evaluate(self.cap_result, context=strict_pol)

        result = self.ranking_engine.rank(empty_rule_result)

        self.assertFalse(result.is_satisfiable)
        self.assertIsNone(result.selected_model)
        self.assertEqual(result.total_candidates, 0)
        self.assertEqual(len(result.ranked_candidates), 0)

    def test_deterministic_tie_breaking(self):
        """Verify tie-breaking using context_headroom and model_id."""
        info1 = ModelInfo(provider="OpenAI", family="GPT", model_id="model-b", display_name="B", description="B", cost_tier="medium", latency_tier="medium")
        info2 = ModelInfo(provider="OpenAI", family="GPT", model_id="model-a", display_name="A", description="A", cost_tier="medium", latency_tier="medium")

        cand1 = CandidateModel(model_id="model-b", provider="OpenAI", family="GPT", model_info=info1, context_headroom=50000)
        cand2 = CandidateModel(model_id="model-a", provider="OpenAI", family="GPT", model_info=info2, context_headroom=50000)

        cfg = RankingConfig(cost_weight=0.25, latency_weight=0.25, suitability_weight=0.25, headroom_weight=0.25)
        result = self.ranking_engine.rank_candidates([cand1, cand2], config=cfg)

        # identical scores and identical headroom -> model-a wins due to alphabetical model_id
        self.assertEqual(result.selected_model.model_id, "model-a")


if __name__ == "__main__":
    unittest.main()
