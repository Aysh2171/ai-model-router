"""
Unit tests for ComplexityPredictorModel loading, saving, and serialization consistency.
"""

import unittest
import tempfile
import os
import sys
from pathlib import Path

# Add complexity_predictor root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.model import ComplexityPredictorModel
from tests.fixtures.requests import CODE_REQUEST

DEFAULT_MODEL_PATH = Path(__file__).resolve().parent.parent / "models" / "predictor_pipeline.joblib"


class TestModelLoading(unittest.TestCase):
    """Unit test cases for ComplexityPredictorModel persistence and loading."""

    def test_load_production_model(self):
        """Verify loading existing production trained pipeline artifact models/predictor_pipeline.joblib."""
        predictor = ComplexityPredictorModel.load_pipeline(str(DEFAULT_MODEL_PATH))

        self.assertIsNotNone(predictor.model)
        self.assertIsNotNone(predictor.preprocessor)
        self.assertTrue(predictor.preprocessor.is_fitted)

    def test_missing_model_file(self):
        """Verify appropriate exception raised when loading non-existent file path."""
        with self.assertRaises(Exception):
            ComplexityPredictorModel.load_pipeline("non_existent_model_file_xyz.joblib")

    def test_corrupt_model_file(self):
        """Verify appropriate exception raised when loading a corrupted binary artifact."""
        with tempfile.NamedTemporaryFile(suffix=".joblib", delete=False) as tmp:
            tmp.write(b"CORRUPTED_BINARY_HEADER_DATA_12345")
            tmp_path = tmp.name

        try:
            with self.assertRaises(Exception):
                ComplexityPredictorModel.load_pipeline(tmp_path)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_serialization_consistency(self):
        """Verify prediction output is 100% identical before saving and after reloading pipeline."""
        predictor1 = ComplexityPredictorModel.load_pipeline(str(DEFAULT_MODEL_PATH))
        profile1 = predictor1.predict_complexity(CODE_REQUEST)

        # Save to temporary joblib artifact
        with tempfile.NamedTemporaryFile(suffix=".joblib", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            predictor1.save_pipeline(tmp_path)
            predictor2 = ComplexityPredictorModel.load_pipeline(tmp_path)
            profile2 = predictor2.predict_complexity(CODE_REQUEST)

            self.assertEqual(profile1["complexity"], profile2["complexity"])
            self.assertEqual(profile1["complexity_score"], profile2["complexity_score"])
            self.assertEqual(profile1["confidence"], profile2["confidence"])
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)


if __name__ == "__main__":
    unittest.main()
