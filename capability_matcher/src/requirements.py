"""
Requirement Extraction and Match Requirements Data Model.
Derives structured technical matching constraints from normalized AI request representations.
"""

from dataclasses import dataclass, field, asdict
from typing import Set, Dict, Any, Optional, List


@dataclass
class MatchRequirements:
    """Dataclass encapsulating mandatory technical matching constraints derived from a normalized request."""

    required_modalities: Set[str] = field(default_factory=lambda: {"text"})
    min_context_window: int = 4096
    min_max_output_tokens: int = 1024
    required_use_cases: Set[str] = field(default_factory=set)
    required_capabilities: Dict[str, bool] = field(default_factory=dict)
    allow_preview: bool = True
    allow_deprecated: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert requirements instance into a dictionary payload."""
        data = asdict(self)
        data["required_modalities"] = sorted(list(self.required_modalities))
        data["required_use_cases"] = sorted(list(self.required_use_cases))
        return data


class RequirementExtractor:
    """Consumes a normalized AI request representation and derives technical matching constraints for the Capability Matcher."""

    @staticmethod
    def extract(
        request_payload: Dict[str, Any],
        complexity_profile: Optional[Dict[str, Any]] = None,
        **overrides: Any
    ) -> MatchRequirements:
        """
        Derive a MatchRequirements constraint object from a normalized request representation and optional complexity context.
        """
        required_modalities: Set[str] = {"text"}
        required_capabilities: Dict[str, bool] = {}
        required_use_cases: Set[str] = set()

        # 1. Extract Task Category -> Use Case Mapping
        metadata = request_payload.get("metadata", {})
        task_cat = metadata.get("task_category") or request_payload.get("task_category")
        if task_cat and isinstance(task_cat, str):
            category = task_cat.strip()
            if category not in ["General Question Answering", "General Prompting"]:
                required_use_cases.add(category)

        # 2. Extract Attachment Requirements & Modalities
        attachments = request_payload.get("attachments", [])
        total_attachment_bytes = 0
        if isinstance(attachments, list):
            for att in attachments:
                if isinstance(att, dict):
                    att_type = att.get("file_type", "").lower()
                    att_size = att.get("size_mb", 0)
                    total_attachment_bytes += int(att_size * 1024 * 1024)

                    if att_type in ["image", "jpg", "jpeg", "png", "gif", "bmp"]:
                        required_modalities.add("image")
                        required_capabilities["supports_vision"] = True
                        required_capabilities["supports_multimodal"] = True
                    elif att_type in ["audio", "mp3", "wav", "m4a"]:
                        required_modalities.add("audio")
                        required_capabilities["supports_audio"] = True
                        required_capabilities["supports_multimodal"] = True
                    elif att_type in ["video", "mp4", "mov", "avi"]:
                        required_modalities.add("video")
                        required_capabilities["supports_multimodal"] = True

        # 3. Compute Minimum Context Window Tokens
        prompt = request_payload.get("prompt", "")
        prompt_char_len = len(prompt) if isinstance(prompt, str) else 0
        estimated_prompt_tokens = max(100, prompt_char_len // 4)

        attachment_token_estimate = len(attachments) * 800 + (total_attachment_bytes // 200)

        conv_context = request_payload.get("conversation_context", {})
        turns = conv_context.get("turns", 0) if isinstance(conv_context, dict) else 0
        history_token_estimate = turns * 500

        total_input_tokens = estimated_prompt_tokens + attachment_token_estimate + history_token_estimate
        min_context = max(4096, int(total_input_tokens * 1.25))

        # 4. Output Format Requirements
        expected_output = request_payload.get("expected_output", {})
        output_format = expected_output.get("format", "").lower() if isinstance(expected_output, dict) else ""
        
        min_output_tokens = 1024
        if output_format in ["json", "json_object"]:
            required_capabilities["supports_json"] = True
        elif output_format in ["code", "script"]:
            required_capabilities["supports_code"] = True
            required_use_cases.add("Programming")
        elif output_format in ["comparative_report", "summary", "markdown"]:
            min_output_tokens = 2048

        # 5. Functions & Tools Support
        tools = request_payload.get("tools") or request_payload.get("functions")
        if tools:
            required_capabilities["supports_function_calling"] = True
            required_capabilities["supports_tools"] = True
            required_use_cases.add("Tool Use")

        # 6. Incorporate Complexity Context
        if complexity_profile and isinstance(complexity_profile, dict):
            comp_tier = complexity_profile.get("complexity", "").upper()
            if comp_tier == "HIGH":
                min_output_tokens = max(min_output_tokens, 4096)
                min_context = max(min_context, 16384)

        # Apply explicit overrides if supplied
        if "required_modalities" in overrides:
            required_modalities = set(overrides["required_modalities"])
        if "min_context_window" in overrides:
            min_context = int(overrides["min_context_window"])
        if "min_max_output_tokens" in overrides:
            min_output_tokens = int(overrides["min_max_output_tokens"])
        if "required_use_cases" in overrides:
            required_use_cases = set(overrides["required_use_cases"])
        if "allow_preview" in overrides:
            allow_preview = bool(overrides["allow_preview"])
        else:
            allow_preview = True
        if "allow_deprecated" in overrides:
            allow_deprecated = bool(overrides["allow_deprecated"])
        else:
            allow_deprecated = False

        return MatchRequirements(
            required_modalities=required_modalities,
            min_context_window=min_context,
            min_max_output_tokens=min_output_tokens,
            required_use_cases=required_use_cases,
            required_capabilities=required_capabilities,
            allow_preview=allow_preview,
            allow_deprecated=allow_deprecated,
        )
