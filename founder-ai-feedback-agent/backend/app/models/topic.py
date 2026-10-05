"""Topic modeling results."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Float, DateTime, ForeignKey, Text, Integer
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base


def utcnow(): return datetime.now(timezone.utc)


class Topic(Base):
    __tablename__ = "topics"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False, index=True)
    topic_id: Mapped[int] = mapped_column(Integer, nullable=False)  # BERTopic internal id
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    keywords: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    frequency: Mapped[int] = mapped_column(Integer, default=0)
    model_version: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    feedback_associations: Mapped[list["TopicFeedback"]] = relationship("TopicFeedback", back_populates="topic")


class TopicFeedback(Base):
    __tablename__ = "topic_feedback"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    topic_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("topics.id"), nullable=False, index=True)
    feedback_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("feedback.id"), nullable=False, index=True)
    probability: Mapped[float] = mapped_column(Float, default=0.0)

    topic: Mapped["Topic"] = relationship("Topic", back_populates="feedback_associations")
    feedback: Mapped["Feedback"] = relationship("Feedback", back_populates="topic_associations")
