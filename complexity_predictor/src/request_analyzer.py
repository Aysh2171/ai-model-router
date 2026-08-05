"""
Request Analysis module for the Complexity Predictor.
Parses raw AI Requests and organizes them into a Structured Request domain representation.
Performs no feature engineering, word counting, or token estimation.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List


@dataclass
class StructuredRequest:
    """Domain representation organizing the components of a raw AI Request."""
    prompt: str = ""
    attachments: List[Dict[str, Any]] = field(default_factory=list)
    conversation_context: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    expected_output: Dict[str, Any] = field(default_factory=dict)


class RequestAnalyzer:
    """Identifies and organizes components of raw incoming AI Requests."""

    def analyze(self, raw_request: Dict[str, Any]) -> StructuredRequest:
        """
        Analyze a raw request payload and organize its components into a StructuredRequest.

        Args:
            raw_request: Dictionary containing raw request fields.

        Returns:
            StructuredRequest domain object.
        """
        prompt = raw_request.get("prompt", "")

        # Extract attachments list or construct from flat fields if provided
        attachments = raw_request.get("attachments", [])
        if not attachments and raw_request.get("attachment_type", "none") != "none":
            attachments = [{
                "type": raw_request.get("attachment_type", "none"),
                "size_mb": float(raw_request.get("attachment_size_mb", 1.0))
            }]

        # Extract conversation context or construct from flat turn count
        conversation_context = raw_request.get("conversation_context", {})
        if not conversation_context and "conversation_length" in raw_request:
            conversation_context = {"turns": int(raw_request.get("conversation_length", 0))}

        # Extract metadata or gather task category
        metadata = raw_request.get("metadata", {})
        if "task_category" in raw_request and "task_category" not in metadata:
            metadata["task_category"] = raw_request.get("task_category", "General Prompting")

        # Extract expected output or format string
        expected_output = raw_request.get("expected_output", {})
        if isinstance(expected_output, str):
            expected_output = {"format": expected_output}
        elif not expected_output and "expected_output_format" in raw_request:
            expected_output = {"format": raw_request.get("expected_output_format", "text")}

        return StructuredRequest(
            prompt=prompt,
            attachments=attachments,
            conversation_context=conversation_context,
            metadata=metadata,
            expected_output=expected_output
        )
