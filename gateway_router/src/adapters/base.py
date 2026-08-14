"""
Base Provider Adapter Abstraction.
Defines abstract BaseProviderAdapter defining standardized interface for all provider integrations.
"""

from abc import ABC, abstractmethod
from typing import Generator, Any
from ranking_engine.src import RankedModel
from ..models import GatewayRequest, GatewayExecutionResult, StreamChunk


class BaseProviderAdapter(ABC):
    """Abstract base class establishing provider execution contract."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier for this adapter instance."""
        pass

    @property
    @abstractmethod
    def provider(self) -> str:
        """Canonical provider name handled by this adapter (e.g. 'OpenAI', 'Anthropic')."""
        pass

    @abstractmethod
    def execute(self, request: GatewayRequest, model: RankedModel) -> GatewayExecutionResult:
        """
        Execute request against provider model.

        Args:
            request: GatewayRequest payload.
            model: Selected RankedModel metadata from upstream router.

        Returns:
            GatewayExecutionResult containing generated content and execution telemetry.
        """
        pass

    @abstractmethod
    def execute_stream(self, request: GatewayRequest, model: RankedModel) -> Generator[StreamChunk, None, None]:
        """
        Execute request with streaming token generation.

        Args:
            request: GatewayRequest payload.
            model: Selected RankedModel metadata.

        Yields:
            StreamChunk objects incrementally.
        """
        pass

    def cleanup_request(self, request: GatewayRequest) -> None:
        """
        Optional hook to clean up request-scoped simulation or connection state upon reaching terminal outcome.
        Default implementation is a no-op.
        """
        pass
