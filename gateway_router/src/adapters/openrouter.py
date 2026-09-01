"""
Live OpenRouter Provider Adapter Implementation.
Connects to OpenRouter Gateway API (https://openrouter.ai/api/v1) for real model execution.
Enforces strict zero-cost free-tier models (:free) to eliminate any risk of paid usage.
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

DEFAULT_OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_OPENROUTER_FREE_MODEL = "nvidia/nemotron-3.5-lightning:free"


class OpenRouterProviderAdapter(BaseProviderAdapter):
    """Concrete live provider adapter executing free-tier requests against OpenRouter."""

    def __init__(
        self,
        provider: str = "OpenRouter",
        name: Optional[str] = None,
        base_url: str = DEFAULT_OPENROUTER_BASE_URL,
        api_key: Optional[str] = None,
        default_live_model: str = DEFAULT_OPENROUTER_FREE_MODEL,
        max_retries: int = 1,
        retry_delay: float = 2.0,
    ):
        self._provider = provider
        self._name = name or f"openrouter_{provider.lower()}_adapter"
        self._base_url = base_url
        self._api_key = api_key or os.environ.get("OPENROUTER_API_KEY", "").strip()
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
        key = self._api_key or os.environ.get("OPENROUTER_API_KEY", "").strip()
        return bool(key and len(key) > 5)

    @property
    def is_available(self) -> bool:
        return self.is_configured

    def _get_client(self) -> OpenAI:
        key = self._api_key or os.environ.get("OPENROUTER_API_KEY", "").strip()
        if not key:
            raise PermanentExecutionError("OPENROUTER_API_KEY is not configured in server environment.")
        if self._client is None:
            self._client = OpenAI(
                base_url=self._base_url,
                api_key=key,
                default_headers={
                    "HTTP-Referer": "https://github.com/ai-model-router",
                    "X-Title": "AI Model Router Prototype",
                },
                max_retries=0
            )
        return self._client

    def _resolve_model_id(self, model: RankedModel) -> str:
        """Map model to verified free model, always appending :free if not already present."""
        if model and model.model_id:
            mid = model.model_id
            if ":free" in mid:
                return mid
            if "llama" in mid.lower():
                return "meta-llama/llama-3.3-70b-instruct:free"
            if "deepseek" in mid.lower():
                return "deepseek/deepseek-r1:free"
            if "gemini" in mid.lower():
                return "google/gemini-2.0-flash-exp:free"
            if "mistral" in mid.lower():
                return "mistralai/mistral-7b-instruct:free"
            if "qwen" in mid.lower():
                return "qwen/qwen-2.5-72b-instruct:free"
            return f"{mid}:free"
        return self._default_live_model

    def execute(self, request: GatewayRequest, model: RankedModel) -> GatewayExecutionResult:
        client = self._get_client()
        live_model = self._resolve_model_id(model)
        start_time = time.perf_counter()

        messages = [{"role": "user", "content": request.prompt}]
        delay = self._retry_delay
        max_retries = self._max_retries

        for attempt in range(1, max_retries + 1):
            try:
                completion = client.chat.completions.create(
                    model=live_model,
                    messages=messages,
                    temperature=request.temperature if request.temperature is not None else 0.7,
                    max_tokens=request.max_tokens or 512,
                    timeout=25.0,
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
                        delay += 3.0
                        continue
                    raise TransientExecutionError(f"OpenRouter API rate limit reached: {err}")
                elif "404" in err_msg:
                    raise PermanentExecutionError(f"OpenRouter model not found: {err}")
                else:
                    raise PermanentExecutionError(f"OpenRouter API error: {err}")
            except Exception as e:
                err_str = str(e).lower()
                if "timeout" in err_str:
                    raise TimeoutExecutionError(f"OpenRouter API request timed out: {e}")
                raise TransientExecutionError(f"OpenRouter API request failed: {e}")

        raise TransientExecutionError("OpenRouter execution retries exhausted.")

    def execute_stream(self, request: GatewayRequest, model: RankedModel) -> Generator[StreamChunk, None, None]:
        client = self._get_client()
        live_model = self._resolve_model_id(model)
        messages = [{"role": "user", "content": request.prompt}]

        try:
            stream_resp = client.chat.completions.create(
                model=live_model,
                messages=messages,
                temperature=request.temperature if request.temperature is not None else 0.7,
                max_tokens=request.max_tokens or 512,
                stream=True,
                timeout=25.0,
            )

            idx = 0
            for chunk in stream_resp:
                if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                    delta_content = chunk.choices[0].delta.content
                    yield StreamChunk(
                        request_id=request.request_id,
                        chunk_index=idx,
                        content=delta_content,
                        model_id=live_model,
                        provider=self.provider,
                        is_final=False,
                        execution_mode=ExecutionMode.LIVE.value
                    )
                    idx += 1

            yield StreamChunk(
                request_id=request.request_id,
                chunk_index=idx,
                content="",
                model_id=live_model,
                provider=self.provider,
                is_final=True,
                execution_mode=ExecutionMode.LIVE.value
            )

        except Exception as e:
            raise TransientExecutionError(f"OpenRouter streaming failed: {e}")
