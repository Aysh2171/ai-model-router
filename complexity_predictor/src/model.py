"""
Machine learning model management module for the Complexity Predictor.
Handles model training, evaluation, persistence (save/load), and runtime complexity prediction.
Reuses the exact same processing flow (Request Analysis -> Feature Extraction -> Preprocessing -> Model).
"""

import os
import joblib
import numpy as np
from typing import Dict, Any, Tuple, Optional
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score
from src.request_analyzer import RequestAnalyzer
from src.feature_extractor import FeatureExtractor
from src.preprocessor import DataPreprocessor


class ComplexityPredictorModel:
    """Wrapper class managing the supervised ML classifier lifecycle and inference engine."""

    def __init__(self, model_instance: Optional[Any] = None):
        self.analyzer = RequestAnalyzer()
        self.extractor = FeatureExtractor()
        self.preprocessor = DataPreprocessor()
        if model_instance is not None:
            self.model = model_instance
        else:
            self.model = RandomForestClassifier(n_estimators=200, random_state=42)

    def train(self, X_train: Any, y_train: Any) -> None:
        """Train the supervised machine learning classifier."""
        self.model.fit(X_train, y_train)

    def evaluate(self, X_test: Any, y_test: Any) -> Dict[str, float]:
        """
        Evaluate model performance on test set.

        Returns:
            Dictionary containing accuracy and F1 score.
        """
        y_pred = self.model.predict(X_test)
        acc = float(accuracy_score(y_test, y_pred))
        f1 = float(f1_score(y_test, y_pred, average="macro"))
        return {"accuracy": round(acc, 4), "f1_score": round(f1, 4)}

    def save_pipeline(self, file_path: str) -> None:
        """Save the fitted preprocessor and trained model to disk as a single joblib artifact."""
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        pipeline_data = {
            "preprocessor": self.preprocessor,
            "model": self.model
        }
        joblib.dump(pipeline_data, file_path)

    @classmethod
    def load_pipeline(cls, file_path: str) -> "ComplexityPredictorModel":
        """Load a saved pipeline artifact from disk and return an initialized predictor instance."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Saved pipeline artifact not found at: {file_path}")

        pipeline_data = joblib.load(file_path)
        instance = cls(model_instance=pipeline_data["model"])
        instance.preprocessor = pipeline_data["preprocessor"]
        return instance

    def predict_complexity(self, raw_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predict AI Request complexity and return structured Complexity Profile.
        Executes the exact same processing flow:
        Raw Request -> Request Analysis -> Structured Request -> Feature Extraction -> Feature Vector -> Preprocessing -> Model.

        Args:
            raw_request: Raw request dictionary.

        Returns:
            Complexity Profile dictionary with 'complexity', 'complexity_score', and 'confidence'.
        """
        # 1. Request Analysis
        structured_req = self.analyzer.analyze(raw_request)

        # 2. Feature Extraction
        feature_vector = self.extractor.extract_features(structured_req)

        # 3. Data Preprocessing
        X_vec = self.preprocessor.transform_single(feature_vector)

        # 4. Machine Learning Model Inference
        if hasattr(self.model, "predict_proba"):
            probs = self.model.predict_proba(X_vec)[0]
            top_class_idx = int(np.argmax(probs))
            complexity_label = self.preprocessor.label_encoder.classes_[top_class_idx]
            confidence = float(probs[top_class_idx])

            # Map class probabilities to 0-100 complexity score scale
            classes_list = list(self.preprocessor.label_encoder.classes_)
            low_idx = classes_list.index("Low") if "Low" in classes_list else 0
            med_idx = classes_list.index("Medium") if "Medium" in classes_list else 0
            high_idx = classes_list.index("High") if "High" in classes_list else 0

            raw_score = (probs[low_idx] * 15) + (probs[med_idx] * 50) + (probs[high_idx] * 85)
            complexity_score = int(round(clamp(raw_score, 0, 100)))
        else:
            y_pred_enc = self.model.predict(X_vec)[0]
            complexity_label = self.preprocessor.label_encoder.classes_[y_pred_enc]
            confidence = 1.0
            score_map = {"Low": 15, "Medium": 45, "High": 75}
            complexity_score = score_map.get(complexity_label, 50)

        return {
            "complexity": complexity_label,
            "complexity_score": complexity_score,
            "confidence": round(confidence, 2)
        }


def clamp(val: float, min_val: float, max_val: float) -> float:
    """Utility to bound a score value between min and max."""
    return max(min_val, min(max_val, val))
