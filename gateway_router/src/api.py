"""
FastAPI HTTP Transport Layer for Gateway Router.
Provides a thin REST and Server-Sent Events (SSE) streaming transport interface delegating to GatewayRouter.
"""

from typing import Dict, Any, Optional
import json
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field

from .gateway import GatewayRouter
from .models import GatewayRequest, GatewayResponse, ExecutionMode, ExecutionStatus
from .orchestrator import PipelineRouter


class ChatCompletionRequest(BaseModel):
    """OpenAI-compatible request body schema."""
    model: Optional[str] = None
    messages: list[Dict[str, Any]] = Field(default_factory=list)
    prompt: Optional[str] = None
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    stream: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)
    simulation_options: Optional[Dict[str, Any]] = None


def create_app(
    gateway_router: Optional[GatewayRouter] = None,
    pipeline_router: Optional[PipelineRouter] = None
) -> FastAPI:
    """
    Create and configure FastAPI application instance.
    Acts as a thin transport layer calling the core GatewayRouter or PipelineRouter.
    """
    app = FastAPI(
        title="AI Model Router Gateway API",
        description="Unified execution layer for the AI Model Router (Local Simulation Mode)",
        version="1.0.0"
    )

    gw = gateway_router or GatewayRouter()
    pipe = pipeline_router or PipelineRouter(gateway=gw)

    @app.get("/health")
    async def health() -> Dict[str, Any]:
        """Service health check endpoint."""
        return {
            "status": "healthy",
            "service": "ai-model-gateway-router",
            "execution_mode": ExecutionMode.MOCK.value,
            "registered_providers": gw.adapter_registry.list_providers()
        }

    @app.post("/v1/chat/completions")
    async def chat_completions(req: ChatCompletionRequest) -> Dict[str, Any]:
        """Standard chat completions endpoint."""
        extracted_prompt = req.prompt or ""
        if not extracted_prompt and req.messages:
            extracted_prompt = req.messages[-1].get("content", "")

        raw_req = {
            "request_id": req.metadata.get("request_id", "REQ-HTTP"),
            "prompt": extracted_prompt,
            "metadata": req.metadata,
        }

        # Delegate execution to PipelineRouter or GatewayRouter
        if req.model and "/" in req.model:
            parts = req.model.split("/", 1)
            gw_req = GatewayRequest(
                request_id=raw_req["request_id"],
                prompt=extracted_prompt,
                provider=parts[0],
                model_id=parts[1],
                temperature=req.temperature,
                max_tokens=req.max_tokens,
                simulation_options=req.simulation_options,
            )
            resp = gw.execute(gw_req)
        else:
            resp = pipe.route_and_execute(
                raw_request=raw_req,
                simulation_options=req.simulation_options
            )

        return resp.to_dict()

    @app.post("/v1/chat/completions/stream")
    async def stream_chat_completions(req: ChatCompletionRequest) -> StreamingResponse:
        """Server-Sent Events (SSE) streaming endpoint."""
        extracted_prompt = req.prompt or ""
        if not extracted_prompt and req.messages:
            extracted_prompt = req.messages[-1].get("content", "")

        provider = "OpenAI"
        model_id = req.model or "gpt-4o"
        if "/" in model_id:
            provider, model_id = model_id.split("/", 1)

        gw_req = GatewayRequest(
            request_id=req.metadata.get("request_id", "REQ-STREAM"),
            prompt=extracted_prompt,
            provider=provider,
            model_id=model_id,
            stream=True,
            simulation_options=req.simulation_options
        )

        def event_generator():
            for chunk in gw.execute_stream(gw_req):
                payload = {
                    "id": chunk.request_id,
                    "object": "chat.completion.chunk",
                    "model": chunk.model_id,
                    "provider": chunk.provider,
                    "choices": [{
                        "index": chunk.chunk_index,
                        "delta": {"content": chunk.content},
                        "finish_reason": "stop" if chunk.is_final else None
                    }]
                }
                yield f"data: {json.dumps(payload)}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(event_generator(), media_type="text/event-stream")

    return app
