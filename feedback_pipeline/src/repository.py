"""
Repository Abstraction and SQLAlchemy Implementation.
Provides clean persistence operations isolating database interactions from core business logic.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from contextlib import contextmanager
from datetime import datetime, timezone
import json

from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from .models import RoutingEvent, FeedbackRecord
from .schema import Base, RoutingEventModel, FeedbackRecordModel


class FeedbackRepository(ABC):
    """Abstract interface defining persistence operations for the Feedback Pipeline."""

    @abstractmethod
    def record_event(self, event: RoutingEvent) -> None:
        """Persist a RoutingEvent telemetry record."""
        pass

    @abstractmethod
    def record_feedback(self, feedback: FeedbackRecord) -> None:
        """Persist a qualitative FeedbackRecord."""
        pass

    @abstractmethod
    def get_event(self, event_id: str) -> Optional[RoutingEvent]:
        """Retrieve a specific RoutingEvent by its unique event_id."""
        pass

    @abstractmethod
    def get_events_by_request_id(self, request_id: str) -> List[RoutingEvent]:
        """Retrieve all RoutingEvents sharing a correlation request_id."""
        pass

    @abstractmethod
    def list_events(self, limit: int = 100, offset: int = 0) -> List[RoutingEvent]:
        """List telemetry events ordered by timestamp descending."""
        pass

    @abstractmethod
    def get_feedback_for_event(self, event_id: str) -> List[FeedbackRecord]:
        """Retrieve all feedback submissions linked to an event_id."""
        pass

    @abstractmethod
    def list_all_feedback(self, limit: int = 100) -> List[FeedbackRecord]:
        """List recent feedback submissions."""
        pass

    @abstractmethod
    def count_events(self) -> int:
        """Return total count of recorded routing events."""
        pass


class SQLAlchemyFeedbackRepository(FeedbackRepository):
    """
    SQLAlchemy-backed implementation of FeedbackRepository.
    Supports PostgreSQL for production and SQLite (in-memory/file) for deterministic testing.
    """

    def __init__(self, database_url: str = "sqlite:///:memory:", echo: bool = False):
        self.database_url = database_url
        engine_kwargs = {"echo": echo}
        if database_url.startswith("sqlite"):
            engine_kwargs["connect_args"] = {"check_same_thread": False}
            if ":memory:" in database_url:
                engine_kwargs["poolclass"] = StaticPool
        self.engine = create_engine(database_url, **engine_kwargs)
        self.SessionLocal = sessionmaker(bind=self.engine, expire_on_commit=False)
        Base.metadata.create_all(self.engine)

    @contextmanager
    def _get_session(self):
        """Provide a transactional session context."""
        session: Session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def _model_to_event(self, m: RoutingEventModel) -> RoutingEvent:
        """Convert ORM model to domain RoutingEvent dataclass."""
        meta_dict = {}
        if m.metadata_json:
            try:
                meta_dict = json.loads(m.metadata_json)
            except Exception:
                pass

        return RoutingEvent(
            event_id=m.event_id,
            request_id=m.request_id,
            timestamp=m.timestamp if isinstance(m.timestamp, datetime) else datetime.now(timezone.utc),
            task_category=m.task_category,
            complexity_tier=m.complexity_tier,
            complexity_score=m.complexity_score,
            complexity_confidence=m.complexity_confidence,
            model_id=m.model_id,
            provider=m.provider,
            decision_state=m.decision_state,
            execution_status=m.execution_status,
            execution_mode=m.execution_mode,
            latency_ms=m.latency_ms,
            retry_count=m.retry_count,
            fallback_used=m.fallback_used,
            prompt_tokens=m.prompt_tokens,
            completion_tokens=m.completion_tokens,
            total_tokens=m.total_tokens,
            cost_tier=m.cost_tier,
            latency_tier=m.latency_tier,
            selected_rank=m.selected_rank,
            feasible_candidate_count=m.feasible_candidate_count,
            allowed_candidate_count=m.allowed_candidate_count,
            ranked_candidate_count=m.ranked_candidate_count,
            error_message=m.error_message,
            prompt_summary=m.prompt_summary,
            metadata=meta_dict
        )

    def _model_to_feedback(self, f: FeedbackRecordModel) -> FeedbackRecord:
        """Convert ORM model to domain FeedbackRecord dataclass."""
        return FeedbackRecord(
            feedback_id=f.feedback_id,
            event_id=f.event_id,
            rating=f.rating,
            quality_category=f.quality_category,
            comment=f.comment,
            evaluator_id=f.evaluator_id,
            created_at=f.created_at if isinstance(f.created_at, datetime) else datetime.now(timezone.utc)
        )

    def record_event(self, event: RoutingEvent) -> None:
        meta_str = json.dumps(event.metadata) if event.metadata else None
        m = RoutingEventModel(
            event_id=event.event_id,
            request_id=event.request_id,
            timestamp=event.timestamp,
            task_category=event.task_category,
            complexity_tier=event.complexity_tier,
            complexity_score=event.complexity_score,
            complexity_confidence=event.complexity_confidence,
            model_id=event.model_id,
            provider=event.provider,
            decision_state=event.decision_state,
            execution_status=event.execution_status,
            execution_mode=event.execution_mode,
            latency_ms=event.latency_ms,
            retry_count=event.retry_count,
            fallback_used=event.fallback_used,
            prompt_tokens=event.prompt_tokens,
            completion_tokens=event.completion_tokens,
            total_tokens=event.total_tokens,
            cost_tier=event.cost_tier,
            latency_tier=event.latency_tier,
            selected_rank=event.selected_rank,
            feasible_candidate_count=event.feasible_candidate_count,
            allowed_candidate_count=event.allowed_candidate_count,
            ranked_candidate_count=event.ranked_candidate_count,
            error_message=event.error_message,
            prompt_summary=event.prompt_summary,
            metadata_json=meta_str
        )
        with self._get_session() as session:
            session.add(m)

    def record_feedback(self, feedback: FeedbackRecord) -> None:
        f = FeedbackRecordModel(
            feedback_id=feedback.feedback_id,
            event_id=feedback.event_id,
            rating=feedback.rating,
            quality_category=feedback.quality_category,
            comment=feedback.comment,
            evaluator_id=feedback.evaluator_id,
            created_at=feedback.created_at
        )
        with self._get_session() as session:
            session.add(f)

    def get_event(self, event_id: str) -> Optional[RoutingEvent]:
        with self._get_session() as session:
            stmt = select(RoutingEventModel).where(RoutingEventModel.event_id == event_id)
            res = session.execute(stmt).scalars().first()
            return self._model_to_event(res) if res else None

    def get_events_by_request_id(self, request_id: str) -> List[RoutingEvent]:
        with self._get_session() as session:
            stmt = select(RoutingEventModel).where(RoutingEventModel.request_id == request_id).order_by(RoutingEventModel.timestamp.asc())
            results = session.execute(stmt).scalars().all()
            return [self._model_to_event(m) for m in results]

    def list_events(self, limit: int = 100, offset: int = 0) -> List[RoutingEvent]:
        with self._get_session() as session:
            stmt = select(RoutingEventModel).order_by(RoutingEventModel.timestamp.desc()).offset(offset).limit(limit)
            results = session.execute(stmt).scalars().all()
            return [self._model_to_event(m) for m in results]

    def get_feedback_for_event(self, event_id: str) -> List[FeedbackRecord]:
        with self._get_session() as session:
            stmt = select(FeedbackRecordModel).where(FeedbackRecordModel.event_id == event_id).order_by(FeedbackRecordModel.created_at.asc())
            results = session.execute(stmt).scalars().all()
            return [self._model_to_feedback(f) for f in results]

    def list_all_feedback(self, limit: int = 100) -> List[FeedbackRecord]:
        with self._get_session() as session:
            stmt = select(FeedbackRecordModel).order_by(FeedbackRecordModel.created_at.desc()).limit(limit)
            results = session.execute(stmt).scalars().all()
            return [self._model_to_feedback(f) for f in results]

    def count_events(self) -> int:
        with self._get_session() as session:
            stmt = select(func.count(RoutingEventModel.event_id))
            return session.execute(stmt).scalar() or 0
