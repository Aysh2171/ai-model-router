"""
Mock Provider Adapter Implementation.
Provides deterministic, local simulated execution without requiring external network calls or credentials.
"""

import threading
import uuid
from collections import defaultdict
from typing import Generator, Optional, Dict, Any
from ranking_engine.src import RankedModel
from .base import BaseProviderAdapter
from ..models import GatewayRequest, GatewayExecutionResult, StreamChunk, ExecutionMode
from ..exceptions import (
    TransientExecutionError,
    TimeoutExecutionError,
    PermanentExecutionError,
)


class MockProviderAdapter(BaseProviderAdapter):
    """Deterministic local mock provider adapter for simulated routing execution."""

    def __init__(self, provider: str = "MockGeneric", name: Optional[str] = None):
        self._provider = provider
        self._name = name or f"mock_{provider.lower()}_adapter"
        self.call_count = 0
        self._request_attempts: Dict[str, int] = defaultdict(int)
        self._lock = threading.Lock()

    @property
    def name(self) -> str:
        return self._name

    @property
    def provider(self) -> str:
        return self._provider

    def _get_request_key(self, request: GatewayRequest) -> str:
        """Resolve request-specific state key, generating and binding a unique key if empty."""
        if request and request.request_id and request.request_id.strip():
            return request.request_id.strip()
        if request and not hasattr(request, "_mock_gen_id"):
            setattr(request, "_mock_gen_id", f"gen-{uuid.uuid4()}")
        return getattr(request, "_mock_gen_id", f"gen-{uuid.uuid4()}")

    def _increment_request_attempt(self, request: GatewayRequest) -> int:
        """Atomically increment call_count and request-scoped attempt counter."""
        req_key = self._get_request_key(request)
        with self._lock:
            self.call_count += 1
            self._request_attempts[req_key] += 1
            return self._request_attempts[req_key]

    def _cleanup_request_attempt(self, request: GatewayRequest) -> None:
        """Clean up request-scoped attempt state upon reaching terminal outcome."""
        req_key = self._get_request_key(request)
        with self._lock:
            self._request_attempts.pop(req_key, None)

    def cleanup_request(self, request: GatewayRequest) -> None:
        """Public hook to clean up request-scoped attempt state upon reaching terminal outcome."""
        self._cleanup_request_attempt(request)

    def _check_simulation_faults(self, request: GatewayRequest, attempt_count: int) -> None:
        """Inspect simulation options to inject controllable faults for deterministic testing."""
        sim_opts = request.simulation_options or {}
        fail_mode = sim_opts.get("fail_mode")

        if fail_mode == "transient":
            raise TransientExecutionError(f"Simulated transient network glitch for provider '{self.provider}'.")
        elif fail_mode == "timeout":
            raise TimeoutExecutionError(f"Simulated execution timeout (30s exceeded) for provider '{self.provider}'.")
        elif fail_mode == "permanent":
            raise PermanentExecutionError(f"Simulated permanent 400 Bad Request error for provider '{self.provider}'.")
        elif fail_mode == "transient_then_success":
            fail_threshold = int(sim_opts.get("fail_count_before_success", 1))
            if attempt_count <= fail_threshold:
                raise TransientExecutionError(f"Simulated transient failure (attempt {attempt_count}/{fail_threshold}).")

    def execute(self, request: GatewayRequest, model: RankedModel) -> GatewayExecutionResult:
        attempt_count = self._increment_request_attempt(request)
        try:
            self._check_simulation_faults(request, attempt_count)
        except Exception:
            sim_opts = request.simulation_options or {}
            if sim_opts.get("fail_mode") == "permanent":
                self._cleanup_request_attempt(request)
            raise

        # Clean up request-scoped state upon successful completion
        self._cleanup_request_attempt(request)

        sim_opts = request.simulation_options or {}
        custom_content = sim_opts.get("custom_response")
        sim_latency = float(sim_opts.get("simulated_latency_ms", 15.0))

        prompt_snippet = request.prompt[:60] + "..." if len(request.prompt) > 60 else request.prompt

        if custom_content:
            content = custom_content
        else:
            content = (
                f"[MOCK EXECUTION] Simulated response from provider '{self.provider}' for model '{model.model_id}'. "
                f"Prompt summary: '{prompt_snippet}'. Execution completed in local simulation mode."
            )

        prompt_tokens = max(1, len(request.prompt.split()))
        completion_tokens = max(1, len(content.split()))

        return GatewayExecutionResult(
            content=content,
            model_id=model.model_id,
            provider=self.provider,
            execution_mode=ExecutionMode.MOCK.value,
            latency_ms=sim_latency,
            usage={
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens,
            },
            metadata={
                "adapter_name": self.name,
                "rank_position": model.rank_position,
                "cost_tier": model.candidate.model_info.cost_tier,
                "latency_tier": model.candidate.model_info.latency_tier,
            }
        )

    def execute_stream(self, request: GatewayRequest, model: RankedModel) -> Generator[StreamChunk, None, None]:
        attempt_count = self._increment_request_attempt(request)
        try:
            self._check_simulation_faults(request, attempt_count)
        except Exception:
            sim_opts = request.simulation_options or {}
            if sim_opts.get("fail_mode") == "permanent":
                self._cleanup_request_attempt(request)
            raise

        self._cleanup_request_attempt(request)

        prompt_snippet = request.prompt[:40] + "..." if len(request.prompt) > 40 else request.prompt

        chunks = [
            f"[MOCK STREAM] Simulated stream for model '{model.model_id}'",
            f" | Provider: '{self.provider}'",
            f" | Prompt: '{prompt_snippet}'",
            " | Execution completed successfully."
        ]

        for idx, chunk_text in enumerate(chunks):
            is_final = (idx == len(chunks) - 1)
            yield StreamChunk(
                request_id=request.request_id,
                chunk_index=idx,
                content=chunk_text,
                model_id=model.model_id,
                provider=self.provider,
                is_final=is_final,
                execution_mode=ExecutionMode.MOCK.value
            )
