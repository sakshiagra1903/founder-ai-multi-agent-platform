"""Feedback ingestion and retrieval routes."""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.db.database import get_db
from app.models.user import User
from app.models.feedback import Feedback, FeedbackStatus
from app.schemas.feedback import FeedbackUploadResponse, FeedbackResponse, FeedbackListResponse
from app.core.dependencies import get_current_active_user
from app.services.ingestion_service import ingestion_service
from app.services.analysis_pipeline import analysis_pipeline
from app.core.config import settings
import math

router = APIRouter(prefix="/feedback", tags=["Feedback"])

ALLOWED_EXTENSIONS = {"csv", "xlsx", "xls", "json"}


@router.post("/upload", response_model=FeedbackUploadResponse, status_code=202)
async def upload_feedback(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    auto_analyze: bool = Query(True, description="Automatically run NLP analysis after upload"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload CSV / XLSX / JSON feedback file."""
    if not current_user.company_id:
        raise HTTPException(status_code=400, detail="User must belong to a company")

    ext = (file.filename or "").rsplit(".", 1)[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: .{ext}")

    content = await file.read()
    if len(content) > settings.max_upload_size_bytes:
        raise HTTPException(status_code=413, detail=f"File exceeds {settings.max_upload_size_mb}MB limit")

    result = await ingestion_service.process_upload(
        file_content=content,
        filename=file.filename,
        company_id=current_user.company_id,
        user_id=current_user.id,
        db=db,
    )

    if auto_analyze and result.feedback_ids:
        background_tasks.add_task(
            _run_analysis,
            result.feedback_ids,
            current_user.company_id,
        )

    return result


async def _run_analysis(feedback_ids, company_id):
    """Background task for NLP analysis."""
    from app.db.database import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        await analysis_pipeline.run(feedback_ids, company_id, db)
        await db.commit()


@router.get("", response_model=FeedbackListResponse)
async def list_feedback(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: FeedbackStatus | None = Query(None),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    if not current_user.company_id:
        raise HTTPException(status_code=400, detail="No company associated")

    base_q = select(Feedback).where(Feedback.company_id == current_user.company_id)
    if status:
        base_q = base_q.where(Feedback.status == status)

    count_result = await db.execute(select(func.count()).select_from(base_q.subquery()))
    total = count_result.scalar() or 0

    items_result = await db.execute(
        base_q.order_by(Feedback.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = items_result.scalars().all()

    return FeedbackListResponse(
        items=[FeedbackResponse.model_validate(f) for f in items],
        total=total,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size),
    )


@router.get("/{feedback_id}", response_model=FeedbackResponse)
async def get_feedback(
    feedback_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    import uuid as _uuid
    result = await db.execute(
        select(Feedback).where(
            Feedback.id == _uuid.UUID(feedback_id),
            Feedback.company_id == current_user.company_id,
        )
    )
    fb = result.scalar_one_or_none()
    if not fb:
        raise HTTPException(status_code=404, detail="Feedback not found")
    return FeedbackResponse.model_validate(fb)
