"""
Gateway Router Core Engine.
Executes dispatch requests against resolved provider adapters with bounded retries and streaming support.
"""

import time
from typing import Optional, Generator
from policy_engine.src import PolicyDecision, DecisionState
from ranking_engine.src import RankedModel
from capability_matcher.src import CandidateModel
from model_registry.src import ModelInfo

from .models import (
    GatewayRequest,
    GatewayResponse,
    StreamChunk,
    ExecutionStatus,
    ExecutionMode,
)
from .config import GatewayConfig
from .exceptions import (
    TransientExecutionError,
    TimeoutExecutionError,
    PermanentExecutionError,
)
from .adapters.registry import AdapterRegistry


class GatewayRouter:
    """
    Core execution layer routing authorized decisions to concrete provider adapters.
    Maintains bounded retries on the selected model without re-ranking or altering policy decisions.
    """

    def __init__(
        self,
        adapter_registry: Optional[AdapterRegistry] = None,
        config: Optional[GatewayConfig] = None
    ):
        self.adapter_registry = adapter_registry or AdapterRegistry.create_default()
        self.config = config or GatewayConfig.load_default()

    def _create_synthetic_ranked_model(self, model_id: str, provider: str) -> RankedModel:
        """Create a minimal RankedModel wrapper when executing direct requests without upstream pipeline."""
        info = ModelInfo(
            provider=provider,
            family=provider,
            model_id=model_id,
            display_name=model_id,
            description="Direct execution model specification",
            status="available",
            is_default=False,
            tags=["direct-dispatch"],
            context_window=128000,
            max_output_tokens=4096,
            cost_tier="medium",
            latency_tier="fast",
            supported_modalities=["text"],
            supported_use_cases=["General Prompting"],
        )
        cand = CandidateModel(
            model_id=model_id,
            provider=provider,
            family=provider,
            model_info=info,
            context_headroom=120000,
        )
        return RankedModel(
            model_id=model_id,
            provider=provider,
            family=provider,
            candidate=cand,
            overall_score=1.0,
            rank_position=1,
        )

    def execute(self, request: GatewayRequest) -> GatewayResponse:
        """
        Execute an authorized request against the selected provider adapter.

        Args:
            request: GatewayRequest containing prompt and optional PolicyDecision.

        Returns:
            GatewayResponse containing execution status, generated content, and telemetry.
        """
        start_time = time.perf_counter()
        req_id = request.request_id
        decision = request.policy_decision

        # 1. Handle Policy Engine rejection states without executing adapters
        if decision is not None:
            dec_state = decision.decision
            if dec_state == DecisionState.REJECTED:
                rejection_reasons = []
                for eval_item in decision.evaluated_candidates:
                    rejection_reasons.extend(eval_item.failure_reasons)
                reason_str = "; ".join(rejection_reasons) if rejection_reasons else "Tenant runtime limits exceeded"
                return GatewayResponse(
                    request_id=req_id,
                    status=ExecutionStatus.REJECTED,
                    decision_state=DecisionState.REJECTED.value,
                    execution_mode=ExecutionMode.MOCK.value,
                    error_message=f"Execution blocked: Request rejected by Policy Engine ({reason_str}).",
                    fallback_used=False,
                    metadata={"policy_decision": decision.to_dict()}
                )
            elif dec_state == DecisionState.NO_CANDIDATE:
                return GatewayResponse(
                    request_id=req_id,
                    status=ExecutionStatus.NO_CANDIDATE,
                    decision_state=DecisionState.NO_CANDIDATE.value,
                    execution_mode=ExecutionMode.MOCK.value,
                    error_message="Execution blocked: No eligible candidates available for dispatch.",
                    fallback_used=False,
                    metadata={"policy_decision": decision.to_dict()}
                )

        # 2. Resolve Selected Model and Provider
        selected_model: Optional[RankedModel] = None
        fallback_used = False
        decision_state_val: Optional[str] = None

        if decision is not None and decision.selected_model is not None:
            selected_model = decision.selected_model
            fallback_used = decision.fallback_used
            decision_state_val = decision.decision.value if isinstance(decision.decision, DecisionState) else str(decision.decision)
        elif request.model_id and request.provider:
            selected_model = self._create_synthetic_ranked_model(request.model_id, request.provider)
            decision_state_val = "DIRECT_DISPATCH"
        else:
            return GatewayResponse(
                request_id=req_id,
                status=ExecutionStatus.FAILED,
                decision_state=decision_state_val,
                execution_mode=ExecutionMode.MOCK.value,
                error_message="Invalid request: No selected_model found in PolicyDecision and no direct model_id/provider supplied.",
            )

        provider_name = selected_model.provider
        model_id = selected_model.model_id

        # 3. Resolve Provider Adapter
        adapter = self.adapter_registry.get(provider_name)
        if adapter is None:
            return GatewayResponse(
                request_id=req_id,
                status=ExecutionStatus.ADAPTER_NOT_FOUND,
                decision_state=decision_state_val,
                model_id=model_id,
                provider=provider_name,
                execution_mode=ExecutionMode.MOCK.value,
                error_message=f"No provider adapter registered for provider '{provider_name}'.",
                fallback_used=fallback_used,
                metadata={"rank_position": selected_model.rank_position}
            )

        # 4. Bounded Retry Execution Loop for the SAME selected model
        retry_count = 0
        max_retries = self.config.max_retries

        while retry_count <= max_retries:
            try:
                exec_result = adapter.execute(request, selected_model)
                elapsed_ms = (time.perf_counter() - start_time) * 1000.0

                return GatewayResponse(
                    request_id=req_id,
                    status=ExecutionStatus.SUCCESS,
                    decision_state=decision_state_val,
                    model_id=model_id,
                    provider=provider_name,
                    content=exec_result.content,
                    execution_mode=ExecutionMode.MOCK.value,
                    latency_ms=exec_result.latency_ms if exec_result.latency_ms > 0 else elapsed_ms,
                    retry_count=retry_count,
                    fallback_used=fallback_used,
                    usage=exec_result.usage,
                    metadata={
                        **request.metadata,
                        **exec_result.metadata,
                        "adapter_name": adapter.name,
                        "selected_rank": selected_model.rank_position,
                    }
                )

            except (TransientExecutionError, TimeoutExecutionError) as transient_err:
                if retry_count < max_retries:
                    retry_count += 1
                    if self.config.retry_delay_ms > 0:
                        time.sleep(self.config.retry_delay_ms / 1000.0)
                    continue
                else:
                    adapter.cleanup_request(request)
                    elapsed_ms = (time.perf_counter() - start_time) * 1000.0
                    status_val = (
                        ExecutionStatus.TIMEOUT
                        if isinstance(transient_err, TimeoutExecutionError)
                        else ExecutionStatus.RETRY_EXHAUSTED
                    )
                    return GatewayResponse(
                        request_id=req_id,
                        status=status_val,
                        decision_state=decision_state_val,
                        model_id=model_id,
                        provider=provider_name,
                        execution_mode=ExecutionMode.MOCK.value,
                        latency_ms=elapsed_ms,
                        retry_count=retry_count,
                        fallback_used=fallback_used,
                        error_message=f"Execution retries exhausted ({retry_count}/{max_retries}): {str(transient_err)}",
                        metadata={"adapter_name": adapter.name, "last_error": str(transient_err)}
                    )

            except PermanentExecutionError as perm_err:
                adapter.cleanup_request(request)
                elapsed_ms = (time.perf_counter() - start_time) * 1000.0
                return GatewayResponse(
                    request_id=req_id,
                    status=ExecutionStatus.FAILED,
                    decision_state=decision_state_val,
                    model_id=model_id,
                    provider=provider_name,
                    execution_mode=ExecutionMode.MOCK.value,
                    latency_ms=elapsed_ms,
                    retry_count=retry_count,
                    fallback_used=fallback_used,
                    error_message=f"Permanent execution failure (non-retryable): {str(perm_err)}",
                    metadata={"adapter_name": adapter.name}
                )

            except Exception as unhandled_err:
                adapter.cleanup_request(request)
                elapsed_ms = (time.perf_counter() - start_time) * 1000.0
                return GatewayResponse(
                    request_id=req_id,
                    status=ExecutionStatus.FAILED,
                    decision_state=decision_state_val,
                    model_id=model_id,
                    provider=provider_name,
                    execution_mode=ExecutionMode.MOCK.value,
                    latency_ms=elapsed_ms,
                    retry_count=retry_count,
                    fallback_used=fallback_used,
                    error_message=f"Unhandled execution error: {str(unhandled_err)}",
                    metadata={"adapter_name": adapter.name}
                )

        # Catch-all fallback
        return GatewayResponse(
            request_id=req_id,
            status=ExecutionStatus.FAILED,
            error_message="Execution loop terminated unexpectedly."
        )

    def execute_stream(self, request: GatewayRequest) -> Generator[StreamChunk, None, None]:
        """
        Execute request with streaming token chunks.

        Args:
            request: GatewayRequest payload.

        Yields:
            StreamChunk objects incrementally.
        """
        req_id = request.request_id
        decision = request.policy_decision

        # 1. Handle Policy Engine rejection states
        if decision is not None:
            if decision.decision in (DecisionState.REJECTED, DecisionState.NO_CANDIDATE):
                yield StreamChunk(
                    request_id=req_id,
                    chunk_index=0,
                    content=f"[STREAM ERROR] Execution rejected by Policy Engine ({decision.decision.value}).",
                    model_id="none",
                    provider="none",
                    is_final=True,
                    execution_mode=ExecutionMode.MOCK.value
                )
                return

        # 2. Resolve Selected Model and Provider
        if decision is not None and decision.selected_model is not None:
            selected_model = decision.selected_model
        elif request.model_id and request.provider:
            selected_model = self._create_synthetic_ranked_model(request.model_id, request.provider)
        else:
            yield StreamChunk(
                request_id=req_id,
                chunk_index=0,
                content="[STREAM ERROR] No selected model available for streaming.",
                model_id="none",
                provider="none",
                is_final=True,
                execution_mode=ExecutionMode.MOCK.value
            )
            return

        provider_name = selected_model.provider
        model_id = selected_model.model_id

        # 3. Resolve Provider Adapter
        adapter = self.adapter_registry.get(provider_name)
        if adapter is None:
            yield StreamChunk(
                request_id=req_id,
                chunk_index=0,
                content=f"[STREAM ERROR] No provider adapter registered for '{provider_name}'.",
                model_id=model_id,
                provider=provider_name,
                is_final=True,
                execution_mode=ExecutionMode.MOCK.value
            )
            return

        # 4. Stream execution chunks
        try:
            for chunk in adapter.execute_stream(request, selected_model):
                yield chunk
        except Exception as stream_err:
            adapter.cleanup_request(request)
            yield StreamChunk(
                request_id=req_id,
                chunk_index=999,
                content=f"[STREAM ERROR] Streaming generation failed: {str(stream_err)}",
                model_id=model_id,
                provider=provider_name,
                is_final=True,
                execution_mode=ExecutionMode.MOCK.value
            )
