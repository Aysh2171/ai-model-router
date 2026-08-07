"""
Unit tests for DataPreprocessor module.
Verifies column transformer setup, feature scaling, label encoding, and unseen category handling.
"""

import unittest
import pandas as pd
import numpy as np
import sys
from pathlib import Path

# Add complexity_predictor root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.request_analyzer import RequestAnalyzer
from src.feature_extractor import FeatureExtractor
from src.preprocessor import DataPreprocessor
from tests.fixtures.requests import SIMPLE_TEXT_REQUEST, CODE_REQUEST, DOCUMENT_REQUEST


class TestDataPreprocessor(unittest.TestCase):
    """Unit test cases for DataPreprocessor."""

    def setUp(self):
        self.analyzer = RequestAnalyzer()
        self.extractor = FeatureExtractor()
        self.preprocessor = DataPreprocessor()

        # Build synthetic training DataFrame for fitting
        f1 = self.extractor.extract_features(self.analyzer.analyze(SIMPLE_TEXT_REQUEST))
        f2 = self.extractor.extract_features(self.analyzer.analyze(CODE_REQUEST))
        f3 = self.extractor.extract_features(self.analyzer.analyze(DOCUMENT_REQUEST))

        f1["complexity"] = "Low"
        f2["complexity"] = "Medium"
        f3["complexity"] = "High"

        self.df_train = pd.DataFrame([f1, f2, f3])

    def test_fit_transform(self):
        """Verify fitting preprocessor on feature DataFrame and returning matrix X and target y."""
        X, y = self.preprocessor.fit_transform(self.df_train)

        self.assertTrue(self.preprocessor.is_fitted)
        self.assertIsInstance(X, np.ndarray)
        self.assertEqual(X.shape[0], 3)
        self.assertEqual(len(y), 3)
        self.assertTrue(np.issubdtype(y.dtype, np.integer))

    def test_unseen_category_handling(self):
        """Verify preprocessor transforms single feature vector with unseen categorical features without error."""
        self.preprocessor.fit_transform(self.df_train)

        unseen_f = self.extractor.extract_features(self.analyzer.analyze({
            "prompt": "Test prompt",
            "metadata": {"task_category": "UnseenCategory999"}
        }))

        X_single = self.preprocessor.transform_single(unseen_f)
        self.assertIsInstance(X_single, np.ndarray)
        self.assertEqual(X_single.shape[0], 1)
        self.assertFalse(np.isnan(X_single).any())


if __name__ == "__main__":
    unittest.main()
