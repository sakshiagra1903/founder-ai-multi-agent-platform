"""LLM-generated business insights."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, ForeignKey, Text, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.db.database import Base
import enum


def utcnow(): return datetime.now(timezone.utc)


class InsightType(str, enum.Enum):
    executive_summary = "executive_summary"
    root_cause = "root_cause"
    recommendation = "recommendation"
    trend = "trend"
    weekly = "weekly"
    monthly = "monthly"


class Insight(Base):
    __tablename__ = "insights"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False, index=True)
    insight_type: Mapped[InsightType] = mapped_column(SAEnum(InsightType), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    data_context: Mapped[dict | None] = mapped_column(JSONB)  # stats passed to LLM
    llm_model: Mapped[str | None] = mapped_column(String(100))
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    period_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
