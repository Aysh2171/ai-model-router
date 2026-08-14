"""
Unit Tests for RequirementExtractor and MatchRequirements in Capability Matcher.
"""

import unittest
from capability_matcher.src.requirements import (
    RequirementExtractor,
    MatchRequirements,
    TASK_CATEGORY_ALIAS_MAP,
)


class TestRequirementExtractor(unittest.TestCase):
    """Test suite verifying requirement extraction and task category alias resolution."""

    def test_extract_canonical_use_cases(self):
        """Verify canonical categories are extracted directly."""
        req1 = RequirementExtractor.extract({"prompt": "code", "metadata": {"task_category": "Programming"}})
        self.assertEqual(req1.required_use_cases, {"Programming"})

        req2 = RequirementExtractor.extract({"prompt": "design", "metadata": {"task_category": "System Design"}})
        self.assertEqual(req2.required_use_cases, {"System Design"})

        req3 = RequirementExtractor.extract({"prompt": "translate", "metadata": {"task_category": "Translation"}})
        self.assertEqual(req3.required_use_cases, {"Translation"})

    def test_extract_m1_dataset_aliases(self):
        """Verify M1 dataset categories resolve to canonical catalog use cases."""
        req_ar = RequirementExtractor.extract({"prompt": "audit", "metadata": {"task_category": "Analysis & Review"}})
        self.assertEqual(req_ar.required_use_cases, {"Reasoning"})

        req_dp = RequirementExtractor.extract({"prompt": "etl", "metadata": {"task_category": "Data Processing"}})
        self.assertEqual(req_dp.required_use_cases, {"Data Extraction"})

        req_doc = RequirementExtractor.extract({"prompt": "pdf", "metadata": {"task_category": "Document Processing"}})
        self.assertEqual(req_doc.required_use_cases, {"Document Analysis"})

    def test_extract_industry_synonyms(self):
        """Verify synonyms and aliases resolve correctly."""
        req_sa = RequirementExtractor.extract({"prompt": "arch", "metadata": {"task_category": "System Architecture"}})
        self.assertEqual(req_sa.required_use_cases, {"Software Architecture"})

        req_mm = RequirementExtractor.extract({"prompt": "vision", "metadata": {"task_category": "Multimodal"}})
        self.assertEqual(req_mm.required_use_cases, {"Vision Analysis"})

        req_vis = RequirementExtractor.extract({"prompt": "vision", "metadata": {"task_category": "Vision"}})
        self.assertEqual(req_vis.required_use_cases, {"Vision Analysis"})

        req_math = RequirementExtractor.extract({"prompt": "solve", "metadata": {"task_category": "Math"}})
        self.assertEqual(req_math.required_use_cases, {"Mathematical Reasoning"})

        req_cr = RequirementExtractor.extract({"prompt": "review", "metadata": {"task_category": "Code Reviewing"}})
        self.assertEqual(req_cr.required_use_cases, {"Code Review"})

    def test_extract_general_categories_empty_constraints(self):
        """Verify general categories produce empty use case constraints."""
        for cat in ["General", "General Prompting", "General Question Answering"]:
            req = RequirementExtractor.extract({"prompt": "hi", "metadata": {"task_category": cat}})
            self.assertEqual(req.required_use_cases, set())

    def test_extract_unsupported_category_preserved(self):
        """Verify genuinely unsupported categories remain strict requirements."""
        req = RequirementExtractor.extract({"prompt": "quantum", "metadata": {"task_category": "QuantumTeleportation"}})
        self.assertEqual(req.required_use_cases, {"QuantumTeleportation"})

    def test_extract_attachments_modalities(self):
        """Verify image, audio, and video attachments set appropriate modalities and flags."""
        req_img = RequirementExtractor.extract({
            "prompt": "describe",
            "attachments": [{"file_type": "png", "size_mb": 2}]
        })
        self.assertIn("image", req_img.required_modalities)
        self.assertTrue(req_img.required_capabilities.get("supports_vision"))

        req_aud = RequirementExtractor.extract({
            "prompt": "transcribe",
            "attachments": [{"file_type": "mp3", "size_mb": 5}]
        })
        self.assertIn("audio", req_aud.required_modalities)
        self.assertTrue(req_aud.required_capabilities.get("supports_audio"))

    def test_extract_context_window_estimation(self):
        """Verify large prompts increase required context window."""
        long_prompt = "word " * 10000  # ~50,000 chars -> ~12,500 tokens
        req = RequirementExtractor.extract({"prompt": long_prompt})
        self.assertGreater(req.min_context_window, 10000)

    def test_extract_expected_output_formats(self):
        """Verify JSON and code output expectations set capability requirements."""
        req_json = RequirementExtractor.extract({
            "prompt": "output json",
            "expected_output": {"format": "json"}
        })
        self.assertTrue(req_json.required_capabilities.get("supports_json"))

        req_code = RequirementExtractor.extract({
            "prompt": "write code",
            "expected_output": {"format": "code"}
        })
        self.assertTrue(req_code.required_capabilities.get("supports_code"))
        self.assertIn("Programming", req_code.required_use_cases)


if __name__ == "__main__":
    unittest.main()
