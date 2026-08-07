"""
Test Fixtures Package Initializer.
Exposes valid payloads, invalid payloads, and schema contracts for unit/integration/E2E testing.
"""

from tests.fixtures.requests import (
    SIMPLE_TEXT_REQUEST,
    CODE_REQUEST,
    DOCUMENT_REQUEST,
    MULTIMODAL_REQUEST,
)
from tests.fixtures.invalid_requests import (
    EMPTY_PROMPT_REQUEST,
    WHITESPACE_PROMPT_REQUEST,
    NON_STRING_PROMPT_REQUEST,
    MASSIVE_PROMPT_REQUEST,
    UNKNOWN_EXTENSION_REQUEST,
    UNKNOWN_CATEGORY_REQUEST,
)
from tests.fixtures.expected_profiles import (
    EXPECTED_PROFILE_KEYS,
    VALID_COMPLEXITY_CLASSES,
)

__all__ = [
    "SIMPLE_TEXT_REQUEST",
    "CODE_REQUEST",
    "DOCUMENT_REQUEST",
    "MULTIMODAL_REQUEST",
    "EMPTY_PROMPT_REQUEST",
    "WHITESPACE_PROMPT_REQUEST",
    "NON_STRING_PROMPT_REQUEST",
    "MASSIVE_PROMPT_REQUEST",
    "UNKNOWN_EXTENSION_REQUEST",
    "UNKNOWN_CATEGORY_REQUEST",
    "EXPECTED_PROFILE_KEYS",
    "VALID_COMPLEXITY_CLASSES",
]
