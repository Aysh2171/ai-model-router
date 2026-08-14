"""
Unit Tests for CapabilityMatcher in Capability Matcher.
"""

import unittest
from capability_matcher.src.matcher import CapabilityMatcher


class TestCapabilityMatcher(unittest.TestCase):
    """Test suite verifying CapabilityMatcher 5-stage feasibility filtering."""

    def setUp(self):
        self.matcher = CapabilityMatcher()

    def test_matcher_general_request_matches_all_text_models(self):
        """Verify general prompt request matches all available text models."""
        res = self.matcher.match({"prompt": "Hello world", "metadata": {"task_category": "General Prompting"}})
        self.assertTrue(res.is_satisfiable)
        self.assertEqual(res.eligible_count, 17)
        self.assertEqual(res.excluded_count, 0)

    def test_matcher_modality_filtering(self):
        """Verify image attachment filters strictly to vision-capable models."""
        res = self.matcher.match({
            "prompt": "Describe image",
            "attachments": [{"file_type": "image", "size_mb": 2}]
        })
        self.assertTrue(res.is_satisfiable)
        self.assertGreater(res.eligible_count, 0)
        # All eligible candidates must support vision
        for cand in res.eligible_candidates:
            self.assertIn("image", [m.lower() for m in cand.model_info.supported_modalities])
            self.assertTrue(cand.model_info.supports_vision)

    def test_matcher_context_window_filtering(self):
        """Verify extremely large context requirement excludes small-context models."""
        # Request requiring 3,000,000 tokens (only minimax-text-01 with 4M context satisfies this)
        res = self.matcher.match({
            "prompt": "Large dataset analysis",
            "metadata": {"estimated_tokens": 3000000}
        }, min_context_window=3000000)
        self.assertTrue(res.is_satisfiable)
        self.assertEqual(res.eligible_count, 1)
        self.assertEqual(res.eligible_candidates[0].model_id, "minimax-text-01")

    def test_matcher_alias_task_categories(self):
        """Verify M1 dataset categories and synonyms resolve to correct candidate sets."""
        # 1. Document Processing -> Document Analysis (6 models)
        res_doc = self.matcher.match({"prompt": "pdf", "metadata": {"task_category": "Document Processing"}})
        self.assertTrue(res_doc.is_satisfiable)
        self.assertEqual(res_doc.eligible_count, 6)

        # 2. Data Processing -> Data Extraction (9 models)
        res_data = self.matcher.match({"prompt": "etl", "metadata": {"task_category": "Data Processing"}})
        self.assertTrue(res_data.is_satisfiable)
        self.assertEqual(res_data.eligible_count, 9)

        # 3. System Architecture -> Software Architecture (6 models)
        res_sa = self.matcher.match({"prompt": "arch", "metadata": {"task_category": "System Architecture"}})
        self.assertTrue(res_sa.is_satisfiable)
        self.assertEqual(res_sa.eligible_count, 6)

        # 4. Multimodal -> Vision Analysis (5 models)
        res_mm = self.matcher.match({"prompt": "vision", "metadata": {"task_category": "Multimodal"}})
        self.assertTrue(res_mm.is_satisfiable)
        self.assertEqual(res_mm.eligible_count, 5)

    def test_matcher_unsupported_category_returns_zero_eligible(self):
        """Verify genuinely unsupported task category results in is_satisfiable=False."""
        res = self.matcher.match({"prompt": "quantum", "metadata": {"task_category": "QuantumTeleportation"}})
        self.assertFalse(res.is_satisfiable)
        self.assertEqual(res.eligible_count, 0)
        self.assertEqual(res.excluded_count, 17)

    def test_matcher_exclusion_trace_identifies_missing_use_case(self):
        """Verify exclusion trace explicitly documents missing use case."""
        res = self.matcher.match({"prompt": "quantum", "metadata": {"task_category": "QuantumPhysicsSimulation"}})
        self.assertFalse(res.is_satisfiable)
        self.assertGreater(len(res.excluded_models), 0)
        for exc in res.excluded_models:
            self.assertTrue(any("Missing required use case: 'QuantumPhysicsSimulation'" in r for r in exc.exclusion_reasons))

    def test_matcher_preview_filtering(self):
        """Verify allow_preview=False filters preview status models."""
        res = self.matcher.match({"prompt": "test"}, allow_preview=False)
        self.assertTrue(res.is_satisfiable)
        for cand in res.eligible_candidates:
            self.assertNotEqual(cand.model_info.status, "preview")


if __name__ == "__main__":
    unittest.main()
