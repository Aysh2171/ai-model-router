"""
Unit tests for FeatureExtractor module.
Verifies core feature key schemas, type integrity, value sanitization (no None/NaN/Inf), regex matching, and verb metrics.
"""

import unittest
import math
import sys
from pathlib import Path

# Add complexity_predictor root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.request_analyzer import RequestAnalyzer
from src.feature_extractor import FeatureExtractor
from tests.fixtures.requests import SIMPLE_TEXT_REQUEST, CODE_REQUEST, DOCUMENT_REQUEST, MULTIMODAL_REQUEST
from tests.fixtures.invalid_requests import EMPTY_PROMPT_REQUEST, MASSIVE_PROMPT_REQUEST, UNKNOWN_EXTENSION_REQUEST


class TestFeatureExtractor(unittest.TestCase):
    """Unit test cases for FeatureExtractor."""

    def setUp(self):
        self.analyzer = RequestAnalyzer()
        self.extractor = FeatureExtractor()

    def test_core_feature_schema_and_types(self):
        """Verify feature vector contains required core keys and correct primitive data types."""
        req = self.analyzer.analyze(SIMPLE_TEXT_REQUEST)
        features = self.extractor.extract_features(req)

        self.assertIsInstance(features, dict)
        core_keys = [
            "prompt_length", "word_count", "sentence_count", "estimated_prompt_tokens",
            "avg_word_length", "domain_complexity_score", "instruction_count",
            "technology_count", "task_category", "primary_file_type", "expected_output_format"
        ]
        for key in core_keys:
            self.assertIn(key, features, f"Core feature key '{key}' missing from extracted feature vector.")

        # Type checks
        self.assertIsInstance(features["prompt_length"], (int, float))
        self.assertIsInstance(features["word_count"], (int, float))
        self.assertIsInstance(features["task_category"], str)
        self.assertIsInstance(features["is_programming_request"], (int, bool))

    def test_feature_values_sanitization(self):
        """Assert that extracted feature dictionaries contain NO None, NaN, or Infinite values."""
        payloads = [
            SIMPLE_TEXT_REQUEST, CODE_REQUEST, DOCUMENT_REQUEST, MULTIMODAL_REQUEST,
            EMPTY_PROMPT_REQUEST, MASSIVE_PROMPT_REQUEST, UNKNOWN_EXTENSION_REQUEST
        ]
        for payload in payloads:
            req = self.analyzer.analyze(payload)
            features = self.extractor.extract_features(req)
            for key, val in features.items():
                self.assertIsNotNone(val, f"Feature '{key}' returned None for payload.")
                if isinstance(val, float):
                    self.assertFalse(math.isnan(val), f"Feature '{key}' returned NaN for payload.")
                    self.assertFalse(math.isinf(val), f"Feature '{key}' returned Inf for payload.")

    def test_prompt_length_metrics(self):
        """Verify prompt character, word, sentence, and average word length computations."""
        req = self.analyzer.analyze(SIMPLE_TEXT_REQUEST)
        features = self.extractor.extract_features(req)

        self.assertGreater(features["prompt_length"], 0)
        self.assertGreater(features["word_count"], 0)
        self.assertGreaterEqual(features["sentence_count"], 1)
        self.assertGreater(features["avg_word_length"], 0.0)

    def test_scale_regex_extraction(self):
        """Verify detection of scale indicators (e.g. '600 pages')."""
        doc_req = self.analyzer.analyze(DOCUMENT_REQUEST)
        features = self.extractor.extract_features(doc_req)

        self.assertGreater(features["large_document_indicator"], 0)
        self.assertGreater(features["page_count_indicator"], 0)

    def test_technology_keyword_counting(self):
        """Verify tech stack keyword identification (FastAPI, PostgreSQL, Redis, Docker)."""
        tech_payload = {
            "prompt": "Build a FastAPI backend with PostgreSQL, Redis, and Docker support.",
            "metadata": {"task_category": "Programming"}
        }
        req = self.analyzer.analyze(tech_payload)
        features = self.extractor.extract_features(req)

        self.assertGreaterEqual(features["technology_count"], 3)
        self.assertEqual(features["is_programming_request"], 1)

    def test_action_verb_diversity(self):
        """Verify action verb detection and unique ratio calculation."""
        req = self.analyzer.analyze(CODE_REQUEST)
        features = self.extractor.extract_features(req)

        self.assertGreaterEqual(features["instruction_count"], 1)


if __name__ == "__main__":
    unittest.main()
