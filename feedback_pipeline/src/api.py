"""
FastAPI HTTP Transport Layer for Feedback Pipeline.
Exposes thin REST endpoints for telemetry ingestion, feedback attachment, and analytical querying.
"""

from typing import Optional, Dict, Any, List
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

from .service import FeedbackService
from .analytics import FeedbackAnalytics
from .models import RoutingEvent


class IngestEventRequest(BaseModel):
    """Payload schema for manually submitting a telemetry event."""
    request_id: str
    execution_status: str = "SUCCESS"
    task_category: str = "General Prompting"
    complexity_tier: Optional[str] = None
    complexity_score: Optional[int] = None
    model_id: Optional[str] = None
    provider: Optional[str] = None
    decision_state: Optional[str] = None
    execution_mode: str = "mock"
    latency_ms: float = 0.0
    retry_count: int = 0
    fallback_used: bool = False
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    error_message: Optional[str] = None
    prompt_summary: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SubmitFeedbackRequest(BaseModel):
    """Payload schema for submitting user or evaluator feedback."""
    rating: int = Field(..., ge=1, le=5, description="Integer evaluation rating between 1 and 5")
    quality_category: Optional[str] = Field(None, description="E.g. accurate, slow, hallucination")
    comment: Optional[str] = Field(None, description="Qualitative feedback comments")
    evaluator_id: Optional[str] = Field(None, description="Identifier for client user or evaluator")


def create_app(
    service: Optional[FeedbackService] = None,
    analytics: Optional[FeedbackAnalytics] = None
) -> FastAPI:
    """
    Factory creating a FastAPI instance with configured FeedbackService and FeedbackAnalytics.
    """
    app = FastAPI(
        title="AI Model Router — Module 8: Feedback Pipeline API",
        version="1.0.0",
        description="Lightweight REST transport layer for telemetry ingestion, feedback capture, and analytics."
    )

    srv = service or FeedbackService()
    ana = analytics or FeedbackAnalytics(repository=srv.repository)

    @app.get("/health", status_code=status.HTTP_200_OK)
    def health_check() -> Dict[str, Any]:
        """Check API operational health status."""
        return {
            "status": "ok",
            "module": "feedback_pipeline",
            "version": "1.0.0",
            "database_url": srv.config.database_url
        }

    @app.post("/events", status_code=status.HTTP_201_CREATED)
    def ingest_event(payload: IngestEventRequest) -> Dict[str, Any]:
        """Ingest and persist a routing execution telemetry event."""
        event = RoutingEvent(
            request_id=payload.request_id,
            task_category=payload.task_category,
            complexity_tier=payload.complexity_tier,
            complexity_score=payload.complexity_score,
            model_id=payload.model_id,
            provider=payload.provider,
            decision_state=payload.decision_state,
            execution_status=payload.execution_status,
            execution_mode=payload.execution_mode,
            latency_ms=payload.latency_ms,
            retry_count=payload.retry_count,
            fallback_used=payload.fallback_used,
            prompt_tokens=payload.prompt_tokens,
            completion_tokens=payload.completion_tokens,
            total_tokens=payload.total_tokens,
            error_message=payload.error_message,
            prompt_summary=payload.prompt_summary,
            metadata=payload.metadata
        )
        persisted = srv.record_event(event)
        return {
            "status": "recorded",
            "event": persisted.to_dict()
        }

    @app.get("/events/{event_id}", status_code=status.HTTP_200_OK)
    def get_event(event_id: str) -> Dict[str, Any]:
        """Retrieve a specific telemetry event bundled with its feedback submissions."""
        data = srv.get_event_with_feedback(event_id)
        if data is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"RoutingEvent with event_id '{event_id}' not found."
            )
        return data

    @app.post("/events/{event_id}/feedback", status_code=status.HTTP_201_CREATED)
    def submit_feedback(event_id: str, payload: SubmitFeedbackRequest) -> Dict[str, Any]:
        """Attach user or evaluator quality feedback to an existing telemetry event."""
        try:
            fb = srv.submit_feedback(
                event_id=event_id,
                rating=payload.rating,
                quality_category=payload.quality_category,
                comment=payload.comment,
                evaluator_id=payload.evaluator_id
            )
            return {
                "status": "recorded",
                "feedback": fb.to_dict()
            }
        except KeyError as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    @app.get("/analytics", status_code=status.HTTP_200_OK)
    def get_full_analytics() -> Dict[str, Any]:
        """Retrieve unified summary, routing distribution, quality, and per-model metrics."""
        return ana.get_full_dashboard_summary()

    @app.get("/analytics/summary", status_code=status.HTTP_200_OK)
    def get_summary_analytics() -> Dict[str, Any]:
        """Retrieve high-level health and volume summary metrics."""
        return ana.get_summary_metrics()

    @app.get("/analytics/models", status_code=status.HTTP_200_OK)
    def get_model_analytics() -> List[Dict[str, Any]]:
        """Retrieve performance breakdown by model."""
        return ana.get_model_performance_summary()

    return app
