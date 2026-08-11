"""
Base Rule Abstraction and Evaluation Outcome.
Defines abstract BaseRule class and RuleOutcome dataclass for all organizational policy rules.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
from capability_matcher.src import CandidateModel
from ..context import PolicyContext


@dataclass
class RuleOutcome:
    """Dataclass capturing the outcome of evaluating a single rule against a candidate model."""

    passed: bool
    rule_name: str
    reason: Optional[str] = None


class BaseRule(ABC):
    """Abstract base class for all organizational policy rules."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier for the rule."""
        pass

    @abstractmethod
    def evaluate(self, candidate: CandidateModel, context: PolicyContext) -> RuleOutcome:
        """
        Evaluate organizational policy rule against a candidate model.

        Args:
            candidate: CandidateModel instance from Module 3.
            context: PolicyContext containing tenant metadata and policies.

        Returns:
            RuleOutcome instance indicating pass/fail status and violation details.
        """
        pass
