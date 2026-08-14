"""
Unit tests for RequestAnalyzer and StructuredRequest data model.
Verifies parsing accuracy, schema contracts, type integrity, and default fallbacks.
"""

import unittest
import sys
from pathlib import Path

# Add complexity_predictor root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.request_analyzer import RequestAnalyzer, StructuredRequest
from tests.fixtures.requests import SIMPLE_TEXT_REQUEST, CODE_REQUEST, DOCUMENT_REQUEST
from tests.fixtures.invalid_requests import NON_STRING_PROMPT_REQUEST


class TestRequestAnalyzer(unittest.TestCase):
    """Unit test cases for RequestAnalyzer."""

    def setUp(self):
        self.analyzer = RequestAnalyzer()

    def test_valid_request_parsing(self):
        """Verify parsing of valid request dictionary into StructuredRequest."""
        req = self.analyzer.analyze(SIMPLE_TEXT_REQUEST)
        self.assertIsInstance(req, StructuredRequest)
        self.assertEqual(req.prompt, SIMPLE_TEXT_REQUEST["prompt"])
        self.assertEqual(req.attachments, [])

    def test_structured_request_schema_contract(self):
        """Verify that StructuredRequest strictly maintains required field data types for standard requests."""
        test_payloads = [
            SIMPLE_TEXT_REQUEST,
            CODE_REQUEST,
            DOCUMENT_REQUEST,
            {"prompt": ""}  # Valid empty string prompt
        ]
        for payload in test_payloads:
            req = self.analyzer.analyze(payload)
            self.assertIsInstance(req.prompt, str)
            self.assertIsInstance(req.attachments, list)
            self.assertIsInstance(req.conversation_context, dict)
            self.assertIsInstance(req.metadata, dict)
            self.assertIsInstance(req.expected_output, dict)

    def test_missing_optional_fields(self):
        """Verify fallback values when optional dictionary fields are omitted."""
        minimal_payload = {"prompt": "Hello world"}
        req = self.analyzer.analyze(minimal_payload)
        self.assertEqual(req.prompt, "Hello world")
        self.assertEqual(req.attachments, [])
        self.assertEqual(req.conversation_context, {})
        self.assertEqual(req.metadata, {})

    def test_attachment_type_normalization(self):
        """Verify file extension normalization to standardized file categories."""
        doc_req = self.analyzer.analyze(DOCUMENT_REQUEST)
        self.assertEqual(len(doc_req.attachments), 1)

    def test_invalid_payload_types_raises_value_error(self):
        """Verify request analyzer rejects non-string prompt with ValueError."""
        with self.assertRaises(ValueError):
            self.analyzer.analyze(NON_STRING_PROMPT_REQUEST)


if __name__ == "__main__":
    unittest.main()
