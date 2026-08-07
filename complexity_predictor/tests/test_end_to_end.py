"""
End-to-End tests and schema contract validation for the Complexity Predictor.
"""

import unittest
import sys
from pathlib import Path

# Add complexity_predictor root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.model import ComplexityPredictorModel
from tests.fixtures.requests import SIMPLE_TEXT_REQUEST, CODE_REQUEST, DOCUMENT_REQUEST, MULTIMODAL_REQUEST
from tests.fixtures.expected_profiles import EXPECTED_PROFILE_KEYS, VALID_COMPLEXITY_CLASSES

DEFAULT_MODEL_PATH = Path(__file__).resolve().parent.parent / "models" / "predictor_pipeline.joblib"


class TestEndToEnd(unittest.TestCase):
    """End-to-end testing suite for prediction outputs and JSON profiles."""

    @classmethod
    def setUpClass(cls):
        cls.predictor = ComplexityPredictorModel.load_pipeline(str(DEFAULT_MODEL_PATH))

    def test_schema_contract(self):
        """Assert output dictionary strictly contains keys: complexity, complexity_score, and confidence."""
        payloads = [SIMPLE_TEXT_REQUEST, CODE_REQUEST, DOCUMENT_REQUEST, MULTIMODAL_REQUEST]
        for p in payloads:
            profile = self.predictor.predict_complexity(p)
            self.assertEqual(set(profile.keys()), EXPECTED_PROFILE_KEYS)

    def test_value_bounds(self):
        """Assert complexity in {'Low', 'Medium', 'High'}, score in [0, 100], confidence in [0.0, 1.0]."""
        payloads = [SIMPLE_TEXT_REQUEST, CODE_REQUEST, DOCUMENT_REQUEST, MULTIMODAL_REQUEST]
        for p in payloads:
            profile = self.predictor.predict_complexity(p)
            self.assertIn(profile["complexity"], VALID_COMPLEXITY_CLASSES)
            self.assertTrue(0 <= profile["complexity_score"] <= 100)
            self.assertTrue(0.0 <= profile["confidence"] <= 1.0)

    def test_unambiguous_baseline_labels(self):
        """Verify unambiguous reference prompts produce expected baseline classification bounds."""
        simple_profile = self.predictor.predict_complexity(SIMPLE_TEXT_REQUEST)
        doc_profile = self.predictor.predict_complexity(DOCUMENT_REQUEST)

        self.assertIn(simple_profile["complexity"], ["Low", "Medium"])
        self.assertEqual(doc_profile["complexity"], "High")


if __name__ == "__main__":
    unittest.main()
