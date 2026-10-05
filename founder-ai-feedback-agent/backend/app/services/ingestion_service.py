"""
Feedback Data Ingestion Service.
Handles CSV, XLSX, JSON upload, preprocessing, and bulk DB storage.
"""
from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import Any
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.feedback import Feedback, FeedbackSource, FeedbackStatus
from app.services.preprocessing_service import preprocessing_service
from app.schemas.feedback import FeedbackUploadResponse


class IngestionService:

    async def process_upload(
        self,
        file_content: bytes,
        filename: str,
        company_id: uuid.UUID,
        user_id: uuid.UUID,
        db: AsyncSession,
    ) -> FeedbackUploadResponse:
        """Parse, clean, deduplicate, and store uploaded feedback."""
        ext = filename.rsplit(".", 1)[-1].lower()
        source_map = {"csv": FeedbackSource.csv, "xlsx": FeedbackSource.xlsx, "xls": FeedbackSource.xlsx, "json": FeedbackSource.json}
        source = source_map.get(ext, FeedbackSource.csv)

        # Parse file
        df = preprocessing_service.parse_upload_file(file_content, filename)
        total_rows = len(df)

        # Clean data
        result = preprocessing_service.process_dataframe(df)
        df_clean = result["dataframe"]
        stats = result["stats"]

        if df_clean.empty:
            return FeedbackUploadResponse(
                total_rows=total_rows,
                imported=0,
                duplicates_skipped=stats["duplicates_removed"],
                errors=stats["empty_removed"],
                feedback_ids=[],
                message="No valid feedback records found after cleaning.",
            )

        # Check for existing records to avoid re-import
        imported_ids: list[uuid.UUID] = []
        imported_objects: list[Feedback] = []
        error_count = 0

        for _, row in df_clean.iterrows():
            try:
                feedback = Feedback(
                    external_id=str(row.get("feedback_id", "")) or None,
                    customer_id=str(row.get("customer_id", "")) or None,
                    feedback_text=str(row["feedback_text"]),
                    cleaned_text=str(row.get("cleaned_text", "")) or None,
                    rating=float(row["rating"]) if row.get("rating") is not None and str(row.get("rating")) != "nan" else None,
                    feedback_date=row.get("feedback_date") if row.get("feedback_date") is not None else None,
                    source=source,
                    status=FeedbackStatus.pending,
                    company_id=company_id,
                    uploaded_by=user_id,
                )
                db.add(feedback)
                imported_objects.append(feedback)
            except Exception as e:
                logger.warning(f"Row ingestion error: {e}")
                error_count += 1

        await db.flush()
        imported_ids = [f.id for f in imported_objects]

        logger.info(f"Ingested {len(imported_ids)} feedback records for company {company_id}")

        return FeedbackUploadResponse(
            total_rows=total_rows,
            imported=len(imported_ids),
            duplicates_skipped=stats["duplicates_removed"],
            errors=error_count + stats["empty_removed"],
            feedback_ids=imported_ids,
            message=f"Successfully imported {len(imported_ids)} feedback records.",
        )

    async def trigger_analysis(
        self,
        feedback_ids: list[uuid.UUID],
        company_id: uuid.UUID,
        db: AsyncSession,
    ) -> None:
        """
        Trigger background NLP analysis pipeline for ingested feedback.
        In production this dispatches to Celery. Here we run directly.
        """
        from app.services.analysis_pipeline import analysis_pipeline
        await analysis_pipeline.run(feedback_ids, company_id, db)


ingestion_service = IngestionService()
