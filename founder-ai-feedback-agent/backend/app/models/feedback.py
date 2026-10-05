"""Core Feedback model — stores raw ingested feedback."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Float, DateTime, ForeignKey, Text, Integer, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base
import enum


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class FeedbackStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    analyzed = "analyzed"
    failed = "failed"


class FeedbackSource(str, enum.Enum):
    csv = "csv"
    xlsx = "xlsx"
    json = "json"
    api = "api"


class Feedback(Base):
    __tablename__ = "feedback"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    external_id: Mapped[str | None] = mapped_column(String(255), index=True)  # original feedback_id from upload
    customer_id: Mapped[str | None] = mapped_column(String(255), index=True)
    feedback_text: Mapped[str] = mapped_column(Text, nullable=False)
    cleaned_text: Mapped[str | None] = mapped_column(Text)
    rating: Mapped[float | None] = mapped_column(Float)
    feedback_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    source: Mapped[FeedbackSource] = mapped_column(SAEnum(FeedbackSource), default=FeedbackSource.api)
    status: Mapped[FeedbackStatus] = mapped_column(SAEnum(FeedbackStatus), default=FeedbackStatus.pending, index=True)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB)

    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False, index=True)
    uploaded_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    company: Mapped["Company"] = relationship("Company", back_populates="feedbacks")
    sentiment_result: Mapped["SentimentResult | None"] = relationship("SentimentResult", back_populates="feedback", uselist=False)
    complaints: Mapped[list["Complaint"]] = relationship("Complaint", back_populates="feedback")
    feature_requests: Mapped[list["FeatureRequest"]] = relationship("FeatureRequest", back_populates="feedback")
    topic_associations: Mapped[list["TopicFeedback"]] = relationship("TopicFeedback", back_populates="feedback")
