"""
Unit Tests for M1 Malformed Input Validation and Safe Normalization in Complexity Predictor.
"""

import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.request_analyzer import RequestAnalyzer, StructuredRequest
from src.model import ComplexityPredictorModel

DEFAULT_MODEL_PATH = Path(__file__).resolve().parent.parent / "models" / "predictor_pipeline.joblib"


class TestInputValidation(unittest.TestCase):
    """Test suite verifying controlled validation failures and safe normalizations in M1."""

    def setUp(self):
        self.analyzer = RequestAnalyzer()
        self.predictor = ComplexityPredictorModel.load_pipeline(str(DEFAULT_MODEL_PATH))

    def test_non_dict_root_payload_raises_value_error(self):
        """Verify non-dictionary root payloads raise ValueError."""
        with self.assertRaises(ValueError) as ctx:
            self.analyzer.analyze("invalid string payload")
        self.assertIn("must be a dictionary", str(ctx.exception))

        with self.assertRaises(ValueError) as ctx:
            self.analyzer.analyze(None)
        self.assertIn("must be a dictionary", str(ctx.exception))

        with self.assertRaises(ValueError) as ctx:
            self.analyzer.analyze([1, 2, 3])
        self.assertIn("must be a dictionary", str(ctx.exception))

    def test_missing_or_non_string_prompt_raises_value_error(self):
        """Verify missing, None, or non-string prompt raises ValueError."""
        with self.assertRaises(ValueError):
            self.analyzer.analyze({})
        with self.assertRaises(ValueError):
            self.analyzer.analyze({"prompt": None})
        with self.assertRaises(ValueError):
            self.analyzer.analyze({"prompt": 12345})
        with self.assertRaises(ValueError):
            self.analyzer.analyze({"prompt": ["hello", "world"]})
        with self.assertRaises(ValueError):
            self.analyzer.analyze({"prompt": {"text": "hi"}})

    def test_empty_prompt_string_succeeds(self):
        """Verify empty string prompt produces valid StructuredRequest and executes cleanly."""
        req = self.analyzer.analyze({"prompt": ""})
        self.assertIsInstance(req, StructuredRequest)
        self.assertEqual(req.prompt, "")

        profile = self.predictor.predict_complexity({"prompt": ""})
        self.assertIn(profile["complexity"], ["Low", "Medium", "High"])
        self.assertGreaterEqual(profile["complexity_score"], 0)
        self.assertLessEqual(profile["complexity_score"], 100)

    def test_malformed_metadata_safe_normalization(self):
        """Verify non-dict metadata normalizes safely to empty dict."""
        for bad_meta in ["invalid", [1, 2], 123, None]:
            req = self.analyzer.analyze({"prompt": "test", "metadata": bad_meta})
            self.assertEqual(req.metadata, {})

    def test_malformed_attachments_safe_normalization(self):
        """Verify non-list attachments and corrupted attachment items normalize safely."""
        # Non-list attachments normalize to []
        req_non_list = self.analyzer.analyze({"prompt": "test", "attachments": "file.png"})
        self.assertEqual(req_non_list.attachments, [])

        req_none = self.analyzer.analyze({"prompt": "test", "attachments": None})
        self.assertEqual(req_none.attachments, [])

        # List with malformed items filters out non-dicts and coerces types
        malformed_list = [
            None,
            "corrupted_entry.txt",
            123,
            {"type": 456, "size_mb": "bad_size"},
            {"type": "image", "size_mb": "12.5"}
        ]
        req = self.analyzer.analyze({"prompt": "test", "attachments": malformed_list})
        self.assertEqual(len(req.attachments), 2)
        self.assertEqual(req.attachments[0]["type"], "456")
        self.assertEqual(req.attachments[0]["size_mb"], 0.0)
        self.assertEqual(req.attachments[1]["type"], "image")
        self.assertEqual(req.attachments[1]["size_mb"], 12.5)

    def test_malformed_conversation_context_safe_normalization(self):
        """Verify conversation context turns parse safely, negative turns clamp to 0."""
        req_bad = self.analyzer.analyze({"prompt": "test", "conversation_context": "turn 1"})
        self.assertEqual(req_bad.conversation_context, {})

        req_str_turns = self.analyzer.analyze({"prompt": "test", "conversation_context": {"turns": "5"}})
        self.assertEqual(req_str_turns.conversation_context["turns"], 5)

        req_inv_turns = self.analyzer.analyze({"prompt": "test", "conversation_context": {"turns": "invalid"}})
        self.assertEqual(req_inv_turns.conversation_context["turns"], 0)

        req_neg_turns = self.analyzer.analyze({"prompt": "test", "conversation_context": {"turns": -10}})
        self.assertEqual(req_neg_turns.conversation_context["turns"], 0)

    def test_malformed_expected_output_safe_normalization(self):
        """Verify expected output normalizes cleanly."""
        req_inv = self.analyzer.analyze({"prompt": "test", "expected_output": 123})
        self.assertEqual(req_inv.expected_output, {"format": "text"})

        req_shorthand = self.analyzer.analyze({"prompt": "test", "expected_output": "json"})
        self.assertEqual(req_shorthand.expected_output, {"format": "json"})

        req_int_fmt = self.analyzer.analyze({"prompt": "test", "expected_output": {"format": 999}})
        self.assertEqual(req_int_fmt.expected_output, {"format": "999"})


if __name__ == "__main__":
    unittest.main()
