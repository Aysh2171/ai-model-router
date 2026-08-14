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

        Raises:
            ValueError: If raw_request is not a dictionary or prompt is missing/non-string.
        """
        # M1 Change 1: Root Request Validation
        if not isinstance(raw_request, dict):
            raise ValueError("Request payload must be a dictionary.")

        # M1 Change 2: Prompt Validation
        if "prompt" not in raw_request:
            raise ValueError("Request 'prompt' must be a valid string.")
        
        raw_prompt = raw_request.get("prompt")
        if not isinstance(raw_prompt, str):
            raise ValueError("Request 'prompt' must be a valid string.")
        prompt = raw_prompt  # Empty string "" is valid

        # M1 Change 4: Attachment Normalization
        raw_attachments = raw_request.get("attachments")
        attachments: List[Dict[str, Any]] = []

        if isinstance(raw_attachments, list):
            for item in raw_attachments:
                if isinstance(item, dict):
                    raw_type = item.get("type") or item.get("file_type")
                    att_type = str(raw_type) if raw_type is not None and str(raw_type).strip() else "unknown"
                    raw_size = item.get("size_mb", 0.0)
                    try:
                        att_size = float(raw_size)
                    except (ValueError, TypeError):
                        att_size = 0.0
                    attachments.append({
                        "type": att_type,
                        "file_type": att_type,
                        "size_mb": att_size
                    })
        elif raw_request.get("attachment_type", "none") != "none":
            flat_type = str(raw_request.get("attachment_type", "unknown"))
            try:
                flat_size = float(raw_request.get("attachment_size_mb", 1.0))
            except (ValueError, TypeError):
                flat_size = 1.0
            attachments = [{
                "type": flat_type,
                "file_type": flat_type,
                "size_mb": flat_size
            }]

        # M1 Change 5: Conversation Context Normalization
        raw_context = raw_request.get("conversation_context")
        conversation_context: Dict[str, Any] = {}
        if isinstance(raw_context, dict):
            raw_turns = raw_context.get("turns", 0)
            try:
                turns = int(raw_turns)
            except (ValueError, TypeError):
                turns = 0
            conversation_context = {"turns": max(0, turns)}
        elif "conversation_length" in raw_request:
            raw_turns = raw_request.get("conversation_length", 0)
            try:
                turns = int(raw_turns)
            except (ValueError, TypeError):
                turns = 0
            conversation_context = {"turns": max(0, turns)}

        # M1 Change 3: Metadata Normalization
        raw_meta = raw_request.get("metadata")
        metadata: Dict[str, Any] = dict(raw_meta) if isinstance(raw_meta, dict) else {}
        if "task_category" in raw_request and "task_category" not in metadata:
            metadata["task_category"] = str(raw_request.get("task_category", "General Prompting"))

        # M1 Change 6: Expected Output Normalization
        raw_output = raw_request.get("expected_output")
        expected_output: Dict[str, Any] = {}
        if isinstance(raw_output, dict):
            raw_fmt = raw_output.get("format", "text")
            expected_output = {"format": str(raw_fmt) if raw_fmt is not None else "text"}
        elif isinstance(raw_output, str):
            expected_output = {"format": raw_output}
        elif "expected_output_format" in raw_request:
            flat_fmt = raw_request.get("expected_output_format", "text")
            expected_output = {"format": str(flat_fmt) if flat_fmt is not None else "text"}
        else:
            expected_output = {"format": "text"}

        return StructuredRequest(
            prompt=prompt,
            attachments=attachments,
            conversation_context=conversation_context,
            metadata=metadata,
            expected_output=expected_output
        )
