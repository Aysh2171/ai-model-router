"""
Resilience and edge-case tests for the Complexity Predictor.
Verifies graceful handling of empty prompts, whitespace inputs, massive prompts, unknown extensions, and unseen categories.
"""

import unittest
import sys
from pathlib import Path

# Add complexity_predictor root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.model import ComplexityPredictorModel
from tests.fixtures.invalid_requests import (
    EMPTY_PROMPT_REQUEST,
    WHITESPACE_PROMPT_REQUEST,
    MASSIVE_PROMPT_REQUEST,
    UNKNOWN_EXTENSION_REQUEST,
    UNKNOWN_CATEGORY_REQUEST,
)
from tests.fixtures.expected_profiles import EXPECTED_PROFILE_KEYS, VALID_COMPLEXITY_CLASSES

DEFAULT_MODEL_PATH = Path(__file__).resolve().parent.parent / "models" / "predictor_pipeline.joblib"


class TestEdgeCases(unittest.TestCase):
    """Resilience test suite for malformed and boundary payloads."""

    @classmethod
    def setUpClass(cls):
        cls.predictor = ComplexityPredictorModel.load_pipeline(str(DEFAULT_MODEL_PATH))

    def test_empty_prompt(self):
        """Verify empty string prompt executes without crashing."""
        profile = self.predictor.predict_complexity(EMPTY_PROMPT_REQUEST)
        self.assertEqual(set(profile.keys()), EXPECTED_PROFILE_KEYS)
        self.assertIn(profile["complexity"], VALID_COMPLEXITY_CLASSES)

    def test_whitespace_only_prompt(self):
        """Verify whitespace prompt handles gracefully."""
        profile = self.predictor.predict_complexity(WHITESPACE_PROMPT_REQUEST)
        self.assertEqual(set(profile.keys()), EXPECTED_PROFILE_KEYS)
        self.assertIn(profile["complexity"], VALID_COMPLEXITY_CLASSES)

    def test_extremely_long_prompt(self):
        """Verify massive prompt (500k+ chars) executes without memory errors or crashing."""
        profile = self.predictor.predict_complexity(MASSIVE_PROMPT_REQUEST)
        self.assertEqual(set(profile.keys()), EXPECTED_PROFILE_KEYS)
        self.assertIn(profile["complexity"], VALID_COMPLEXITY_CLASSES)

    def test_unsupported_attachment_extensions(self):
        """Verify unsupported file extension handles gracefully without exceptions."""
        profile = self.predictor.predict_complexity(UNKNOWN_EXTENSION_REQUEST)
        self.assertEqual(set(profile.keys()), EXPECTED_PROFILE_KEYS)
        self.assertIn(profile["complexity"], VALID_COMPLEXITY_CLASSES)

    def test_unknown_task_category(self):
        """Verify unseen task category is ignored by preprocessor without error."""
        profile = self.predictor.predict_complexity(UNKNOWN_CATEGORY_REQUEST)
        self.assertEqual(set(profile.keys()), EXPECTED_PROFILE_KEYS)
        self.assertIn(profile["complexity"], VALID_COMPLEXITY_CLASSES)


if __name__ == "__main__":
    unittest.main()
