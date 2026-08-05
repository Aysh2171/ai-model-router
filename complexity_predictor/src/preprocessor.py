"""
Data Preprocessing module for the Complexity Predictor.
Handles feature scaling, categorical encoding, missing value imputation, and matrix formatting.
"""

import pandas as pd
from typing import Tuple, List, Dict, Any
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler, LabelEncoder


class DataPreprocessor:
    """Preprocesses Feature Vectors into encoded, scaled feature matrices for model training and inference."""

    NUMERICAL_FEATURES: List[str] = [
        "prompt_length",
        "word_count",
        "sentence_count",
        "estimated_prompt_tokens",
        "avg_word_length",
        "avg_sentence_length",
        "question_count",
        "special_char_count",
        "punctuation_density",
        "newline_count",
        "bullet_count",
        "numbered_list_count",
        "contains_code_block",
        "contains_json",
        "contains_markdown",
        "contains_table_like_structure",
        "contains_urls",
        "domain_complexity_score",
        "contains_large_numeric_quantity",
        "page_count_indicator",
        "large_document_indicator",
        "large_dataset_indicator",
        "large_codebase_indicator",
        "instruction_count",
        "objective_diversity",
        "multi_step_request",
        "high_complexity_domain_terms",
        "technology_count",
        "technology_diversity",
        "is_programming_request",
        "attachment_count",
        "total_attachment_size_mb",
        "conversation_turns",
        "has_context",
        "component_count",
        "is_structured_output"
    ]

    CATEGORICAL_FEATURES: List[str] = [
        "task_category",
        "primary_file_type",
        "expected_output_format"
    ]

    COMPLEXITY_CLASSES: List[str] = ["Low", "Medium", "High"]

    def __init__(self):
        self.column_transformer = ColumnTransformer(
            transformers=[
                ("num", StandardScaler(), self.NUMERICAL_FEATURES),
                ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), self.CATEGORICAL_FEATURES)
            ]
        )
        self.label_encoder = LabelEncoder()
        self.label_encoder.fit(self.COMPLEXITY_CLASSES)
        self.is_fitted = False

    def fit_transform(self, df: pd.DataFrame) -> Tuple[Any, Any]:
        """
        Fit preprocessor pipeline on feature DataFrame and return transformed X matrix and target vector y.

        Args:
            df: DataFrame containing Feature Vector columns and target 'complexity' column.

        Returns:
            Tuple of (X_transformed, y_encoded)
        """
        X = df[self.NUMERICAL_FEATURES + self.CATEGORICAL_FEATURES]
        X_transformed = self.column_transformer.fit_transform(X)

        y = df["complexity"]
        y_encoded = self.label_encoder.transform(y)

        self.is_fitted = True
        return X_transformed, y_encoded

    def transform_single(self, feature_vector: Dict[str, Any]) -> Any:
        """
        Transform a single Feature Vector dictionary into a model-ready 2D array.

        Args:
            feature_vector: Dictionary containing extracted features.

        Returns:
            2D numpy array formatted for model inference.
        """
        if not self.is_fitted:
            raise RuntimeError("DataPreprocessor must be fitted before transforming feature vectors.")

        df_single = pd.DataFrame([feature_vector])
        X_single = df_single[self.NUMERICAL_FEATURES + self.CATEGORICAL_FEATURES]
        return self.column_transformer.transform(X_single)
