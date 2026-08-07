"""
Integration tests for the Complexity Predictor pipeline.
Verifies multi-module flow across Analyzer -> Extractor -> Preprocessor -> Model Inference -> Complexity Profile.
"""

import unittest
import sys
from pathlib import Path

# Add complexity_predictor root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.model import ComplexityPredictorModel
from tests.fixtures.requests import SIMPLE_TEXT_REQUEST, CODE_REQUEST, DOCUMENT_REQUEST
from tests.fixtures.expected_profiles import EXPECTED_PROFILE_KEYS, VALID_COMPLEXITY_CLASSES

DEFAULT_MODEL_PATH = Path(__file__).resolve().parent.parent / "models" / "predictor_pipeline.joblib"


class TestIntegration(unittest.TestCase):
    """Integration test cases for multi-module pipeline execution."""

    @classmethod
    def setUpClass(cls):
        cls.predictor = ComplexityPredictorModel.load_pipeline(str(DEFAULT_MODEL_PATH))

    def test_full_pipeline_flow(self):
        """Pass payload through analyzer, feature extractor, preprocessor, and model to generate profile."""
        profile = self.predictor.predict_complexity(CODE_REQUEST)

        self.assertIsInstance(profile, dict)
        self.assertEqual(set(profile.keys()), EXPECTED_PROFILE_KEYS)
        self.assertIn(profile["complexity"], VALID_COMPLEXITY_CLASSES)

    def test_prediction_output_values(self):
        """Verify continuous score (0-100) and confidence (0.0-1.0) adhere to valid range bounds."""
        payloads = [SIMPLE_TEXT_REQUEST, CODE_REQUEST, DOCUMENT_REQUEST]
        for p in payloads:
            profile = self.predictor.predict_complexity(p)
            score = profile["complexity_score"]
            conf = profile["confidence"]

            self.assertIsInstance(score, (int, float))
            self.assertGreaterEqual(score, 0)
            self.assertLessEqual(score, 100)

            self.assertIsInstance(conf, float)
            self.assertGreaterEqual(conf, 0.0)
            self.assertLessEqual(conf, 1.0)


if __name__ == "__main__":
    unittest.main()
