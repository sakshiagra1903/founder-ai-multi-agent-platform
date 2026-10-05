"""Daily trend snapshots for analytics."""
import uuid
from datetime import datetime, date, timezone
from sqlalchemy import String, Float, DateTime, ForeignKey, Date, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from app.db.database import Base


def utcnow(): return datetime.now(timezone.utc)


class TrendSnapshot(Base):
    __tablename__ = "trend_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False, index=True)
    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    total_feedback: Mapped[int] = mapped_column(Integer, default=0)
    positive_count: Mapped[int] = mapped_column(Integer, default=0)
    neutral_count: Mapped[int] = mapped_column(Integer, default=0)
    negative_count: Mapped[int] = mapped_column(Integer, default=0)
    positive_pct: Mapped[float] = mapped_column(Float, default=0.0)
    neutral_pct: Mapped[float] = mapped_column(Float, default=0.0)
    negative_pct: Mapped[float] = mapped_column(Float, default=0.0)
    complaint_count: Mapped[int] = mapped_column(Integer, default=0)
    feature_request_count: Mapped[int] = mapped_column(Integer, default=0)
    top_complaint_category: Mapped[str | None] = mapped_column(String(100))
    top_feature_request: Mapped[str | None] = mapped_column(String(255))
    avg_rating: Mapped[float | None] = mapped_column(Float)
    extra_data: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
