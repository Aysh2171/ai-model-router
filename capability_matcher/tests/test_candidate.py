"""
Unit Tests for CandidateModel and CapabilityMatchResult in Capability Matcher.
"""

import unittest
from model_registry.src.model import ModelInfo
from capability_matcher.src.requirements import MatchRequirements
from capability_matcher.src.candidate import (
    CandidateModel,
    ExcludedModel,
    CapabilityMatchResult,
)


class TestCandidateModels(unittest.TestCase):
    """Test suite verifying CandidateModel, ExcludedModel, and CapabilityMatchResult serialization."""

    def test_candidate_model_serialization(self):
        """Verify CandidateModel serialization to dict."""
        info = ModelInfo(
            provider="OpenAI",
            family="GPT-4",
            model_id="gpt-4o",
            display_name="GPT-4o",
            description="Test",
        )
        cand = CandidateModel(
            model_id="gpt-4o",
            provider="OpenAI",
            family="GPT-4",
            model_info=info,
            context_headroom=120000,
            matched_constraints=["Vision supported"],
            matched_constraint_count=1,
        )
        data = cand.to_dict()
        self.assertEqual(data["model_id"], "gpt-4o")
        self.assertEqual(data["context_headroom"], 120000)
        self.assertEqual(data["matched_constraint_count"], 1)

    def test_excluded_model_serialization(self):
        """Verify ExcludedModel serialization."""
        exc = ExcludedModel(
            model_id="claude-3.5-haiku",
            provider="Anthropic",
            exclusion_reasons=["Insufficient context window"],
        )
        data = exc.to_dict()
        self.assertEqual(data["model_id"], "claude-3.5-haiku")
        self.assertEqual(len(data["exclusion_reasons"]), 1)

    def test_capability_match_result_serialization(self):
        """Verify CapabilityMatchResult structure and serialization."""
        reqs = MatchRequirements(required_modalities={"text"})
        result = CapabilityMatchResult(
            request_id="REQ-001",
            is_satisfiable=True,
            complexity_profile={"complexity": "Medium", "complexity_score": 50},
            requirements=reqs,
            eligible_candidates=[],
            excluded_models=[],
            total_registered=17,
            eligible_count=0,
            excluded_count=17,
        )
        data = result.to_dict()
        self.assertEqual(data["request_id"], "REQ-001")
        self.assertTrue(data["is_satisfiable"])
        self.assertEqual(data["total_registered"], 17)


if __name__ == "__main__":
    unittest.main()
