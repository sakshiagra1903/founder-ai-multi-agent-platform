"""Feature requests extracted from feedback."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Float, DateTime, ForeignKey, Text, Integer, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base
import enum


def utcnow(): return datetime.now(timezone.utc)


class FeaturePriority(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class FeatureRequest(Base):
    __tablename__ = "feature_requests"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    feedback_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("feedback.id"), nullable=False, index=True)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False, index=True)
    request: Mapped[str] = mapped_column(String(500), nullable=False)
    normalized_request: Mapped[str | None] = mapped_column(String(500), index=True)  # clustered label
    category: Mapped[str | None] = mapped_column(String(100), index=True)
    priority: Mapped[FeaturePriority] = mapped_column(SAEnum(FeaturePriority), default=FeaturePriority.medium, index=True)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)
    frequency: Mapped[int] = mapped_column(Integer, default=1)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    feedback: Mapped["Feedback"] = relationship("Feedback", back_populates="feature_requests")
