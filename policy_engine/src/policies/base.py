"""
Base Runtime Policy Abstraction and Evaluation Outcome.
Defines abstract BasePolicy class and PolicyEvaluationOutcome dataclass for runtime governance policies.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
from ranking_engine.src import RankedModel
from ..context import PolicyContext
from ..usage import UsageState


@dataclass
class PolicyEvaluationOutcome:
    """Dataclass capturing the outcome of evaluating a runtime policy against a candidate model."""

    passed: bool
    policy_name: str
    failure_reason: Optional[str] = None
    explanation: Optional[str] = None
    estimated_cost: float = 0.0


class BasePolicy(ABC):
    """Abstract base class for all runtime governance policies."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier for the policy."""
        pass

    @abstractmethod
    def evaluate(self, ranked_model: RankedModel, context: PolicyContext, usage: UsageState) -> PolicyEvaluationOutcome:
        """
        Evaluate runtime policy against a ranked candidate model under current context and usage state.

        Args:
            ranked_model: RankedModel instance from Module 5.
            context: PolicyContext containing runtime limits.
            usage: UsageState tracking tenant consumption metrics.

        Returns:
            PolicyEvaluationOutcome instance indicating pass/fail status and audit telemetry.
        """
        pass
