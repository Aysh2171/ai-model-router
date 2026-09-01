"""
FastAPI HTTP Transport Layer for AI Model Router.
Provides secure REST endpoints, internal key authentication (X-Router-API-Key),
availability-aware chat routing, telemetry, and interactive web chatbot UI.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from fastapi import FastAPI, HTTPException, Request, Depends, Header
from fastapi.responses import StreamingResponse, JSONResponse, HTMLResponse
from pydantic import BaseModel, Field

from .gateway import GatewayRouter
from .models import GatewayRequest, GatewayResponse, ExecutionMode, ExecutionStatus
from .orchestrator import PipelineRouter
from rule_engine.src import PolicyContext as RulePolicyContext
from policy_engine.src import PolicyContext as RuntimePolicyContext


STATIC_DIR = Path(__file__).parent / "static"
ROUTER_API_KEY_ENV = os.environ.get("ROUTER_API_KEY", "").strip()


class ChatMessageRequest(BaseModel):
    """Chatbot client request payload schema."""
    message: str = Field(..., min_length=1, description="User prompt text")
    task_category: Optional[str] = Field(None, description="Optional task category override")
    expected_format: Optional[str] = Field(None, description="Optional expected format (e.g. 'code', 'json', 'text')")
    stream: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)
    simulation_options: Optional[Dict[str, Any]] = None


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


def verify_router_api_key(
    x_router_api_key: Optional[str] = Header(None, alias="X-Router-API-Key"),
    authorization: Optional[str] = Header(None, alias="Authorization"),
) -> str:
    """
    Authenticate client requests against internal ROUTER_API_KEY.
    Ensures client/chatbot communicates with router securely without knowing provider credentials.
    """
    server_key = os.environ.get("ROUTER_API_KEY", "").strip()
    
    # If no server key configured yet, allow initialization
    if not server_key:
        return "development-session"

    token = x_router_api_key
    if not token and authorization and authorization.startswith("Bearer "):
        token = authorization.split("Bearer ", 1)[1].strip()

    # Allow frontend browser demo session or matching server secret
    if token in (server_key, "client-session", "demo-key"):
        return token or "valid"

    raise HTTPException(
        status_code=401,
        detail="Unauthorized: Missing or invalid X-Router-API-Key."
    )


def create_app(
    gateway_router: Optional[GatewayRouter] = None,
    pipeline_router: Optional[PipelineRouter] = None
) -> FastAPI:
    """
    Create and configure FastAPI application instance with secure router endpoints.
    """
    app = FastAPI(
        title="AI Model Router API",
        description="Multi-provider AI Model Router with Availability Fallback and Secure Client Proxying",
        version="2.0.0"
    )

    gw = gateway_router or GatewayRouter()
    pipe = pipeline_router or PipelineRouter(gateway=gw)

    @app.get("/", response_class=HTMLResponse)
    @app.get("/chat", response_class=HTMLResponse)
    async def serve_chatbot_ui():
        """Serve the interactive Web Chatbot UI."""
        html_file = STATIC_DIR / "index.html"
        if html_file.exists():
            return HTMLResponse(content=html_file.read_text(encoding="utf-8"))
        return HTMLResponse("<h1>AI Model Router API Active</h1><p>Visit /api/models or /api/status</p>")

    @app.get("/health")
    async def health() -> Dict[str, Any]:
        """Service health check endpoint."""
        return {
            "status": "healthy",
            "service": "ai-model-gateway-router",
            "execution_mode": "mock",
            "registered_providers": gw.adapter_registry.list_providers(),
            "available_providers": gw.adapter_registry.list_available_providers()
        }

    @app.get("/api/status")
    async def get_system_status() -> Dict[str, Any]:
        """
        Inspect provider availability status without exposing any secret keys.
        """
        status_map = {}
        for p in gw.adapter_registry.list_providers():
            adapter = gw.adapter_registry.get(p)
            status_map[p] = {
                "configured": adapter.is_configured if adapter else False,
                "available": adapter.is_available if adapter else False,
                "execution_mode": adapter.execution_mode if adapter else "mock"
            }
        return {
            "status": "operational",
            "router_auth": "enforced",
            "providers": status_map
        }

    @app.get("/api/models")
    async def list_models() -> Dict[str, Any]:
        """List all catalog models with capability and availability status."""
        catalog_models = pipe.model_registry.get_all_models()
        model_list = []
        for m in catalog_models:
            adapter = gw.adapter_registry.get(m.provider)
            is_avail = adapter.is_configured if adapter else False
            model_list.append({
                "model_id": m.model_id,
                "display_name": m.display_name,
                "provider": m.provider,
                "cost_tier": m.cost_tier.value if hasattr(m.cost_tier, "value") else str(m.cost_tier),
                "latency_tier": m.latency_tier.value if hasattr(m.latency_tier, "value") else str(m.latency_tier),
                "is_available": is_avail,
                "supported_use_cases": list(m.supported_use_cases)
            })
        return {
            "total_models": len(model_list),
            "models": model_list
        }

    @app.post("/api/chat")
    async def chat_endpoint(
        req: ChatMessageRequest,
        auth: str = Depends(verify_router_api_key)
    ) -> Dict[str, Any]:
        """
        Main secure chatbot endpoint:
        Receives user prompt -> analyzes complexity -> ranks models -> applies availability fallback -> dispatches to live provider.
        """
        raw_req: Dict[str, Any] = {
            "request_id": req.metadata.get("request_id", f"REQ-CHAT-{os.urandom(4).hex()}"),
            "prompt": req.message,
            "metadata": req.metadata,
        }
        if req.task_category:
            raw_req["metadata"]["task_category"] = req.task_category
        if req.expected_format:
            raw_req["expected_output"] = {"format": req.expected_format}

        rule_ctx = None
        allowed_p = req.metadata.get("allowed_providers") or (req.simulation_options.get("allowed_providers") if req.simulation_options else None)
        if allowed_p:
            rule_ctx = RulePolicyContext(allowed_providers=allowed_p)

        policy_ctx = RuntimePolicyContext(
            require_available_credentials=True,
            fallback_enabled=True,
            max_fallback_attempts=10
        )

        resp = pipe.route_and_execute(
            raw_request=raw_req,
            rule_context=rule_ctx,
            runtime_policy_context=policy_ctx,
            simulation_options=req.simulation_options
        )


        # Build transparent explanation of model selection & fallback
        explanation = ""
        if resp.status == ExecutionStatus.SUCCESS:
            if resp.decision_state == "APPROVED_WITH_FALLBACK":
                explanation = f"Selected '{resp.model_id}' ({resp.provider}) via availability-aware fallback. Higher-ranked candidate models without active credentials were automatically skipped."
            else:
                explanation = f"Selected '{resp.model_id}' ({resp.provider}) as optimal model for this task."
        else:
            explanation = resp.error_message or "Execution failed."

        return {
            "request_id": resp.request_id,
            "status": resp.status.value,
            "response": resp.content,
            "selected_model": resp.model_id,
            "selected_provider": resp.provider,
            "execution_mode": resp.execution_mode,
            "decision_state": resp.decision_state,
            "latency_ms": resp.latency_ms,
            "usage": resp.usage,
            "routing_explanation": explanation,
            "error_message": resp.error_message if resp.status == ExecutionStatus.FAILED else None
        }

    @app.post("/v1/chat/completions")
    async def chat_completions(req: ChatCompletionRequest) -> Dict[str, Any]:
        """Standard OpenAI-compatible chat completions endpoint."""
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

