"""
SQLAlchemy ORM Schema for Feedback Pipeline.
Defines RoutingEventModel and FeedbackRecordModel database tables.
"""

from datetime import datetime, timezone
import json
from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    DateTime,
    Text,
    ForeignKey,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class RoutingEventModel(Base):
    """SQLAlchemy model for routing_events table storing telemetry execution traces."""

    __tablename__ = "routing_events"

    event_id = Column(String(36), primary_key=True)
    request_id = Column(String(64), index=True, nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True, nullable=False)
    task_category = Column(String(64), nullable=False, default="General Prompting")
    complexity_tier = Column(String(16), nullable=True)
    complexity_score = Column(Integer, nullable=True)
    complexity_confidence = Column(Float, nullable=True)
    model_id = Column(String(64), index=True, nullable=True)
    provider = Column(String(64), index=True, nullable=True)
    decision_state = Column(String(32), nullable=True)
    execution_status = Column(String(32), index=True, nullable=False, default="SUCCESS")
    execution_mode = Column(String(16), default="mock")
    latency_ms = Column(Float, default=0.0)
    retry_count = Column(Integer, default=0)
    fallback_used = Column(Boolean, default=False)
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    cost_tier = Column(String(16), nullable=True)
    latency_tier = Column(String(16), nullable=True)
    selected_rank = Column(Integer, nullable=True)
    feasible_candidate_count = Column(Integer, nullable=True)
    allowed_candidate_count = Column(Integer, nullable=True)
    ranked_candidate_count = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    prompt_summary = Column(String(255), nullable=True)
    metadata_json = Column(Text, nullable=True)

    feedback_records = relationship(
        "FeedbackRecordModel",
        back_populates="event",
        cascade="all, delete-orphan",
        lazy="select"
    )


class FeedbackRecordModel(Base):
    """SQLAlchemy model for feedback_records table storing user/evaluator quality scores."""

    __tablename__ = "feedback_records"

    feedback_id = Column(String(36), primary_key=True)
    event_id = Column(String(36), ForeignKey("routing_events.event_id"), index=True, nullable=False)
    rating = Column(Integer, index=True, nullable=False)
    quality_category = Column(String(64), nullable=True)
    comment = Column(Text, nullable=True)
    evaluator_id = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    event = relationship("RoutingEventModel", back_populates="feedback_records")
