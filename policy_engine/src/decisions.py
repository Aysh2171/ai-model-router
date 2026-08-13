"""
Decision States and Failure Reasons Enum Definitions.
Defines DecisionState and FailureReason constants for structured, machine-readable governance audit logs.
"""

from enum import Enum


class DecisionState(str, Enum):
    """Final operational dispatch governance decision states."""

    APPROVED = "APPROVED"
    APPROVED_WITH_FALLBACK = "APPROVED_WITH_FALLBACK"
    REJECTED = "REJECTED"
    NO_CANDIDATE = "NO_CANDIDATE"


class FailureReason(str, Enum):
    """Structured machine-readable runtime policy failure reasons."""

    BUDGET_EXCEEDED = "BUDGET_EXCEEDED"
    REQUEST_QUOTA_EXCEEDED = "REQUEST_QUOTA_EXCEEDED"
    TOKEN_QUOTA_EXCEEDED = "TOKEN_QUOTA_EXCEEDED"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    FALLBACK_DISABLED = "FALLBACK_DISABLED"
    MAX_FALLBACK_ATTEMPTS_EXCEEDED = "MAX_FALLBACK_ATTEMPTS_EXCEEDED"
    NO_RANKED_CANDIDATES = "NO_RANKED_CANDIDATES"
