"""
Live NVIDIA NIM Provider Adapter Implementation.
Connects to NVIDIA NIM OpenAI-compatible API (https://integrate.api.nvidia.com/v1) for real model execution.
"""

import os
import time
from typing import Generator, Optional, Dict, Any
from openai import OpenAI, RateLimitError, APIError
from ranking_engine.src import RankedModel
from .base import BaseProviderAdapter
from ..models import GatewayRequest, GatewayExecutionResult, StreamChunk, ExecutionMode
from ..exceptions import (
    TransientExecutionError,
    TimeoutExecutionError,
    PermanentExecutionError,
)

DEFAULT_NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"
DEFAULT_NVIDIA_API_KEY = os.environ.get("NVIDIA_API_KEY", "").strip()


class NvidiaProviderAdapter(BaseProviderAdapter):
    """Concrete live provider adapter executing requests against NVIDIA NIM / API endpoints."""

    def __init__(
        self, 
        provider: str = "NVIDIA", 
        name: Optional[str] = None,
        base_url: str = DEFAULT_NVIDIA_BASE_URL,
        api_key: Optional[str] = None,
        default_live_model: str = "nvidia/nemotron-3-nano-30b-a3b",
        max_retries: int = 1,
        retry_delay: float = 2.0,
    ):
        self._provider = provider
        self._name = name or f"nvidia_{provider.lower()}_adapter"
        self._base_url = base_url
        self._api_key = api_key or os.environ.get("NVIDIA_API_KEY", "").strip()
        self._default_live_model = default_live_model
        self._max_retries = max_retries
        self._retry_delay = retry_delay
        self._client: Optional[OpenAI] = None

    @property
    def name(self) -> str:
        return self._name

    @property
    def provider(self) -> str:
        return self._provider

    @property
    def execution_mode(self) -> str:
        return ExecutionMode.LIVE.value

    @property
    def is_configured(self) -> bool:
        key = self._api_key or os.environ.get("NVIDIA_API_KEY", "").strip()
        return bool(key and len(key) > 5)

    @property
    def is_available(self) -> bool:
        return self.is_configured

    def _get_client(self) -> OpenAI:
        """Lazily initialize OpenAI client configured for NVIDIA NIM."""
        key = self._api_key or os.environ.get("NVIDIA_API_KEY", "").strip()
        if not key:
            raise PermanentExecutionError("NVIDIA_API_KEY is not configured in server environment.")
        if self._client is None:
            self._client = OpenAI(base_url=self._base_url, api_key=key, max_retries=0)
        return self._client

    def _resolve_model_id(self, model: RankedModel) -> str:
        """Resolve the model ID, falling back to verified live model if requested model is abstract."""
        if model and model.model_id:
            # Map router catalog model name to verified live NIM model ID if needed
            if model.model_id in ("nemotron-4-340b", "nvidia/nemotron-4-340b", "default"):
                return "nvidia/nemotron-3-nano-30b-a3b"
            return model.model_id
        return self._default_live_model




    def execute(self, request: GatewayRequest, model: RankedModel) -> GatewayExecutionResult:
        client = self._get_client()
        live_model = self._resolve_model_id(model)
        
        start_time = time.perf_counter()
        
        messages = [
            {"role": "user", "content": request.prompt}
        ]
        
        delay = self._retry_delay
        max_retries = self._max_retries
        
        for attempt in range(1, max_retries + 1):
            try:
                completion = client.chat.completions.create(
                    model=live_model,
                    messages=messages,
                    temperature=0.7,
                    max_tokens=512,
                    timeout=30.0,
                )
                
                elapsed_ms = (time.perf_counter() - start_time) * 1000.0
                content = completion.choices[0].message.content or ""
                
                usage_info = {
                    "prompt_tokens": getattr(completion.usage, "prompt_tokens", len(request.prompt.split())),
                    "completion_tokens": getattr(completion.usage, "completion_tokens", len(content.split())),
                    "total_tokens": getattr(completion.usage, "total_tokens", len(request.prompt.split()) + len(content.split())),
                }
                
                return GatewayExecutionResult(
                    content=content,
                    model_id=live_model,
                    provider=self.provider,
                    execution_mode=ExecutionMode.LIVE.value,
                    latency_ms=elapsed_ms,
                    usage=usage_info,
                    metadata={
                        "adapter_name": self.name,
                        "base_url": self._base_url,
                        "live_model": live_model,
                        "rank_position": model.rank_position if model else 1,
                    }
                )
                
            except (RateLimitError, APIError) as err:
                err_msg = str(err)
                if "429" in err_msg or isinstance(err, RateLimitError):
                    if attempt < max_retries:
                        time.sleep(delay)
                        delay += 4.0
                        continue
                    raise TransientExecutionError(f"NVIDIA API rate limit exceeded: {err}")
                elif "404" in err_msg:
                    # Model not found on account, fallback to verified default
                    if live_model != self._default_live_model:
                        live_model = self._default_live_model
                        continue
                    raise PermanentExecutionError(f"NVIDIA API model not found: {err}")
                else:
                    raise PermanentExecutionError(f"NVIDIA API error: {err}")
            except Exception as e:
                raise TransientExecutionError(f"NVIDIA API request failed: {e}")

    def execute_stream(self, request: GatewayRequest, model: RankedModel) -> Generator[StreamChunk, None, None]:
        client = self._get_client()
        live_model = self._resolve_model_id(model)
        
        response = client.chat.completions.create(
            model=live_model,
            messages=[{"role": "user", "content": request.prompt}],
            stream=True,
            temperature=0.7,
            max_tokens=512,
        )
        
        index = 0
        for chunk in response:
            delta = chunk.choices[0].delta.content or ""
            if delta:
                yield StreamChunk(
                    request_id=request.request_id,
                    chunk_index=index,
                    delta=delta,
                    is_final=False,
                    model_id=live_model,
                    provider=self.provider,
                    execution_mode=ExecutionMode.LIVE.value
                )
                index += 1
                
        yield StreamChunk(
            request_id=request.request_id,
            chunk_index=index,
            delta="",
            is_final=True,
            model_id=live_model,
            provider=self.provider,
            execution_mode=ExecutionMode.LIVE.value
        )

