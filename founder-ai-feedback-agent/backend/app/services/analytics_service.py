"""
Analytics Service — aggregates NLP results into dashboard/report-ready data.

NOTE: this file was referenced everywhere (chat, insights, reports, analytics
routes) but missing from the scaffold. Implemented here with plain SQLAlchemy
aggregation queries so both the REST endpoints and the new LangGraph agent
tools have real data to work with instead of stubs.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.complaint import Complaint
from app.models.feature_request import FeatureRequest
from app.models.feedback import Feedback
from app.models.insight import Insight
from app.models.sentiment import SentimentLabel, SentimentResult
from app.models.topic import Topic


class AnalyticsService:

    async def get_sentiment_summary(self, company_id: uuid.UUID, db: AsyncSession) -> dict[str, Any]:
        stmt = (
            select(SentimentResult.sentiment, func.count())
            .join(Feedback, Feedback.id == SentimentResult.feedback_id)
            .where(Feedback.company_id == company_id)
            .group_by(SentimentResult.sentiment)
        )
        rows = (await db.execute(stmt)).all()
        counts = {"positive": 0, "neutral": 0, "negative": 0}
        for label, cnt in rows:
            counts[label.value if hasattr(label, "value") else label] = cnt
        total = sum(counts.values())
        pct = lambda n: round((n / total) * 100, 1) if total else 0.0
        return {
            "total_analyzed": total,
            "positive_pct": pct(counts["positive"]),
            "neutral_pct": pct(counts["neutral"]),
            "negative_pct": pct(counts["negative"]),
            "counts": counts,
        }

    async def get_top_complaints(self, company_id: uuid.UUID, db: AsyncSession, limit: int = 10) -> list[dict]:
        stmt = (
            select(Complaint.category, Complaint.severity, func.count().label("count"))
            .where(Complaint.company_id == company_id)
            .group_by(Complaint.category, Complaint.severity)
            .order_by(func.count().desc())
            .limit(limit)
        )
        rows = (await db.execute(stmt)).all()
        return [{"category": cat, "severity": sev.value if hasattr(sev, "value") else sev, "count": cnt} for cat, sev, cnt in rows]

    async def get_top_features(self, company_id: uuid.UUID, db: AsyncSession, limit: int = 10) -> list[dict]:
        stmt = (
            select(FeatureRequest.normalized_request, FeatureRequest.category, func.count().label("count"))
            .where(FeatureRequest.company_id == company_id)
            .group_by(FeatureRequest.normalized_request, FeatureRequest.category)
            .order_by(func.count().desc())
            .limit(limit)
        )
        rows = (await db.execute(stmt)).all()
        return [{"request": req or "Unlabeled", "category": cat, "count": cnt} for req, cat, cnt in rows]

    async def get_top_topics(self, company_id: uuid.UUID, db: AsyncSession, limit: int = 10) -> list[dict]:
        stmt = (
            select(Topic)
            .where(Topic.company_id == company_id)
            .order_by(Topic.frequency.desc())
            .limit(limit)
        )
        rows = (await db.execute(stmt)).scalars().all()
        return [{"label": t.label, "keywords": t.keywords, "frequency": t.frequency} for t in rows]

    async def get_sentiment_trend(self, company_id: uuid.UUID, db: AsyncSession, days: int = 30) -> list[dict]:
        since = datetime.now(timezone.utc) - timedelta(days=days)
        stmt = (
            select(
                func.date(Feedback.feedback_date).label("day"),
                SentimentResult.sentiment,
                func.count().label("count"),
            )
            .join(SentimentResult, SentimentResult.feedback_id == Feedback.id)
            .where(Feedback.company_id == company_id, Feedback.feedback_date >= since)
            .group_by("day", SentimentResult.sentiment)
            .order_by("day")
        )
        rows = (await db.execute(stmt)).all()
        by_day: dict[str, dict[str, int]] = {}
        for day, sentiment, cnt in rows:
            key = str(day)
            by_day.setdefault(key, {"positive": 0, "neutral": 0, "negative": 0})
            label = sentiment.value if hasattr(sentiment, "value") else sentiment
            by_day[key][label] = cnt

        trend = []
        for day, counts in sorted(by_day.items()):
            total = sum(counts.values())
            trend.append({
                "date": day,
                "positive_pct": round(counts["positive"] / total * 100, 1) if total else 0,
                "neutral_pct": round(counts["neutral"] / total * 100, 1) if total else 0,
                "negative_pct": round(counts["negative"] / total * 100, 1) if total else 0,
                "total": total,
            })
        return trend

    async def get_dashboard(self, company_id: uuid.UUID, db: AsyncSession) -> dict[str, Any]:
        sentiment = await self.get_sentiment_summary(company_id, db)
        complaints = await self.get_top_complaints(company_id, db)
        features = await self.get_top_features(company_id, db)
        topics = await self.get_top_topics(company_id, db)
        trend = await self.get_sentiment_trend(company_id, db)

        total_feedback = (await db.execute(
            select(func.count()).select_from(Feedback).where(Feedback.company_id == company_id)
        )).scalar() or 0
        total_complaints = (await db.execute(
            select(func.count()).select_from(Complaint).where(Complaint.company_id == company_id)
        )).scalar() or 0
        total_features = (await db.execute(
            select(func.count()).select_from(FeatureRequest).where(FeatureRequest.company_id == company_id)
        )).scalar() or 0

        recent_insights_rows = (await db.execute(
            select(Insight).where(Insight.company_id == company_id).order_by(Insight.generated_at.desc()).limit(5)
        )).scalars().all()

        return {
            "total_feedback": total_feedback,
            "positive_pct": sentiment["positive_pct"],
            "neutral_pct": sentiment["neutral_pct"],
            "negative_pct": sentiment["negative_pct"],
            "total_complaints": total_complaints,
            "total_feature_requests": total_features,
            "top_complaints": complaints,
            "top_feature_requests": features,
            "top_topics": topics,
            "most_critical_issue": complaints[0]["category"] if complaints else None,
            "sentiment_trend": trend,
            "recent_insights": [{"title": i.title, "type": str(i.insight_type)} for i in recent_insights_rows],
        }


analytics_service = AnalyticsService()
