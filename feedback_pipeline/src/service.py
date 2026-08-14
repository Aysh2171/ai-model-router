"""
Feedback Service Layer.
Coordinates telemetry ingestion from GatewayResponse, user feedback submission, and event correlation.
"""

from typing import Optional, Dict, Any, List

from gateway_router.src import GatewayResponse
from .models import RoutingEvent, FeedbackRecord
from .repository import FeedbackRepository, SQLAlchemyFeedbackRepository
from .config import FeedbackConfig


class FeedbackService:
    """
    Central service coordinating routing telemetry recording and quality feedback attachment.
    """

    def __init__(
        self,
        repository: Optional[FeedbackRepository] = None,
        config: Optional[FeedbackConfig] = None
    ):
        self.config = config or FeedbackConfig.load_default()
        self.repository = repository or SQLAlchemyFeedbackRepository(database_url=self.config.database_url)

    def record_gateway_response(
        self,
        response: GatewayResponse,
        request_prompt: str = "",
        task_category: Optional[str] = None
    ) -> RoutingEvent:
        """
        Convert an executed GatewayResponse into a persistent RoutingEvent.

        Args:
            response: GatewayResponse emitted by Module 7 GatewayRouter.
            request_prompt: Original client prompt text for summary extraction.
            task_category: Optional categorical task label.

        Returns:
            The persisted RoutingEvent instance.
        """
        event = RoutingEvent.from_gateway_response(
            response=response,
            request_prompt=request_prompt,
            task_category=task_category,
            max_prompt_length=self.config.max_prompt_summary_length
        )
        self.repository.record_event(event)
        return event

    def record_event(self, event: RoutingEvent) -> RoutingEvent:
        """Persist a pre-constructed RoutingEvent directly."""
        self.repository.record_event(event)
        return event

    def submit_feedback(
        self,
        event_id: str,
        rating: int,
        quality_category: Optional[str] = None,
        comment: Optional[str] = None,
        evaluator_id: Optional[str] = None
    ) -> FeedbackRecord:
        """
        Submit a qualitative evaluation rating for a recorded routing event.

        Args:
            event_id: Target event_id linking to a recorded RoutingEvent.
            rating: Integer score from 1 to 5.
            quality_category: Optional qualitative label (e.g. 'accurate', 'slow', 'hallucination').
            comment: Optional descriptive feedback string.
            evaluator_id: Optional identifier for client user or evaluation agent.

        Returns:
            The persisted FeedbackRecord instance.
        """
        if not self.config.enable_feedback_collection:
            raise ValueError("Feedback collection is currently disabled in configuration.")

        event = self.repository.get_event(event_id)
        if event is None:
            raise KeyError(f"Cannot attach feedback: No RoutingEvent found with event_id '{event_id}'.")

        feedback = FeedbackRecord(
            event_id=event_id,
            rating=rating,
            quality_category=quality_category,
            comment=comment,
            evaluator_id=evaluator_id
        )
        self.repository.record_feedback(feedback)
        return feedback

    def get_event_with_feedback(self, event_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a specific RoutingEvent bundled with all associated feedback records."""
        event = self.repository.get_event(event_id)
        if event is None:
            return None
        feedback_list = self.repository.get_feedback_for_event(event_id)
        return {
            "event": event.to_dict(),
            "feedback": [f.to_dict() for f in feedback_list]
        }

    def list_recent_events(self, limit: int = 100) -> List[RoutingEvent]:
        """Retrieve recent routing telemetry events."""
        return self.repository.list_events(limit=limit)
