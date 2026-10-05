"""
Main NLP Analysis Pipeline.
Orchestrates: sentiment → complaint detection → feature request → topic modeling.
Designed as the central coordinator for all NLP services.
"""
from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import Any
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.models.feedback import Feedback, FeedbackStatus
from app.models.sentiment import SentimentResult, SentimentLabel
from app.models.complaint import Complaint, ComplaintSeverity
from app.models.feature_request import FeatureRequest, FeaturePriority
from app.models.topic import Topic, TopicFeedback
from app.services.nlp.sentiment_service import sentiment_service
from app.services.nlp.complaint_service import complaint_service
from app.services.nlp.feature_request_service import feature_request_service
from app.services.nlp.topic_modeling_service import topic_modeling_service
from app.services.rag.vector_store_service import vector_store_service


class AnalysisPipeline:
    """Runs the full NLP pipeline on a batch of feedback records."""

    BATCH_SIZE = 64

    async def run(
        self,
        feedback_ids: list[uuid.UUID],
        company_id: uuid.UUID,
        db: AsyncSession,
    ) -> dict[str, Any]:
        """Execute full analysis pipeline."""
        logger.info(f"Starting analysis pipeline for {len(feedback_ids)} records")

        # Load feedback records
        stmt = select(Feedback).where(Feedback.id.in_(feedback_ids))
        result = await db.execute(stmt)
        feedbacks = result.scalars().all()

        if not feedbacks:
            return {"analyzed": 0}

        texts = [f.cleaned_text or f.feedback_text for f in feedbacks]
        ids = [f.id for f in feedbacks]

        # Update status to processing
        await db.execute(
            update(Feedback).where(Feedback.id.in_(ids)).values(status=FeedbackStatus.processing)
        )
        await db.flush()

        stats = {"analyzed": 0, "sentiments": 0, "complaints": 0, "features": 0, "topics": 0}

        # 1. SENTIMENT ANALYSIS (batch)
        try:
            logger.info("Running sentiment analysis...")
            sentiment_scores = sentiment_service.analyze_batch(texts, batch_size=self.BATCH_SIZE)
            for feedback, score in zip(feedbacks, sentiment_scores):
                label_map = {"positive": SentimentLabel.positive, "neutral": SentimentLabel.neutral, "negative": SentimentLabel.negative}
                sr = SentimentResult(
                    feedback_id=feedback.id,
                    sentiment=label_map.get(score.label, SentimentLabel.neutral),
                    confidence_score=score.confidence,
                    positive_score=score.positive_score,
                    neutral_score=score.neutral_score,
                    negative_score=score.negative_score,
                    model_used=score.model_used,
                )
                db.add(sr)
            stats["sentiments"] = len(sentiment_scores)
            logger.info(f"Sentiment done: {stats['sentiments']} records")
        except Exception as e:
            logger.error(f"Sentiment analysis failed: {e}")

        # 2. COMPLAINT DETECTION (batch)
        try:
            logger.info("Running complaint detection...")
            complaint_results = complaint_service.detect_batch(texts)
            severity_map = {
                "critical": ComplaintSeverity.critical,
                "high": ComplaintSeverity.high,
                "medium": ComplaintSeverity.medium,
                "low": ComplaintSeverity.low,
            }
            for feedback, cr in zip(feedbacks, complaint_results):
                if cr.is_complaint and cr.category:
                    complaint = Complaint(
                        feedback_id=feedback.id,
                        company_id=company_id,
                        category=cr.category,
                        subcategory=cr.subcategory,
                        description=cr.description,
                        severity=severity_map.get(cr.severity or "medium", ComplaintSeverity.medium),
                        confidence_score=cr.confidence_score,
                    )
                    db.add(complaint)
                    stats["complaints"] += 1
        except Exception as e:
            logger.error(f"Complaint detection failed: {e}")

        # 3. FEATURE REQUEST DETECTION (batch)
        try:
            logger.info("Running feature request detection...")
            feature_results = feature_request_service.detect_batch(texts)
            priority_map = {
                "critical": FeaturePriority.critical,
                "high": FeaturePriority.high,
                "medium": FeaturePriority.medium,
                "low": FeaturePriority.low,
            }
            for feedback, fr in zip(feedbacks, feature_results):
                if fr.is_feature_request:
                    feat = FeatureRequest(
                        feedback_id=feedback.id,
                        company_id=company_id,
                        request=fr.request_text or feedback.cleaned_text[:500] or "",
                        normalized_request=fr.normalized_request,
                        category=fr.category,
                        priority=priority_map.get(fr.priority, FeaturePriority.medium),
                        confidence_score=fr.confidence_score,
                    )
                    db.add(feat)
                    stats["features"] += 1
        except Exception as e:
            logger.error(f"Feature request detection failed: {e}")

        # 4. TOPIC MODELING (fit on whole batch)
        try:
            logger.info("Running topic modeling...")
            clean_texts = [t for t in texts if t and len(t.strip()) >= 10]
            if len(clean_texts) >= 5:
                topic_results = topic_modeling_service.fit(clean_texts)
                for tr in topic_results:
                    topic = Topic(
                        company_id=company_id,
                        topic_id=tr.topic_id,
                        label=tr.label,
                        keywords=tr.keywords,
                        frequency=tr.frequency,
                        model_version=f"{topic_modeling_service._model_type}_v1",
                    )
                    db.add(topic)
                    stats["topics"] += 1
        except Exception as e:
            logger.error(f"Topic modeling failed: {e}")

        # 5. Mark as analyzed
        await db.execute(
            update(Feedback).where(Feedback.id.in_(ids)).values(status=FeedbackStatus.analyzed)
        )
        stats["analyzed"] = len(feedbacks)
        await db.flush()

        # 6. RAG INDEXING — push analyzed feedback into the vector store so the
        #    chat/insight LangGraph agents can retrieve it semantically. Best-effort:
        #    a Chroma failure should never fail the ingestion pipeline itself.
        try:
            logger.info("Indexing feedback into vector store (RAG)...")
            sentiment_by_id = {}
            try:
                for feedback, score in zip(feedbacks, sentiment_scores):
                    sentiment_by_id[feedback.id] = score.label
            except NameError:
                pass
            complaint_ids = set()
            feature_ids = set()
            try:
                for feedback, cr in zip(feedbacks, complaint_results):
                    if cr.is_complaint:
                        complaint_ids.add(feedback.id)
            except NameError:
                pass
            try:
                for feedback, fr in zip(feedbacks, feature_results):
                    if fr.is_feature_request:
                        feature_ids.add(feedback.id)
            except NameError:
                pass

            rag_items = [
                {
                    "id": f.id,
                    "text": f.cleaned_text or f.feedback_text,
                    "sentiment": sentiment_by_id.get(f.id, "unknown"),
                    "rating": f.rating,
                    "is_complaint": f.id in complaint_ids,
                    "is_feature_request": f.id in feature_ids,
                    "created_at": f.feedback_date or f.created_at,
                }
                for f in feedbacks
            ]
            indexed = vector_store_service.upsert_feedback(company_id, rag_items)
            stats["rag_indexed"] = indexed
        except Exception as e:
            logger.error(f"RAG indexing failed (non-fatal): {e}")
            stats["rag_indexed"] = 0

        logger.info(f"Pipeline complete: {stats}")
        return stats


analysis_pipeline = AnalysisPipeline()
