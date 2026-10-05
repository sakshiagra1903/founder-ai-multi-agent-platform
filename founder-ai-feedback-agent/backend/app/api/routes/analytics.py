"""Analytics and dashboard routes."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.models.user import User
from app.core.dependencies import get_current_active_user
from app.services.analytics_service import analytics_service
from app.schemas.analytics import DashboardAnalytics
from fastapi import HTTPException

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/dashboard", response_model=DashboardAnalytics)
async def get_dashboard(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    if not current_user.company_id:
        raise HTTPException(status_code=400, detail="No company associated")
    return await analytics_service.get_dashboard(current_user.company_id, db)


@router.get("/sentiment")
async def get_sentiment(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    if not current_user.company_id:
        raise HTTPException(status_code=400, detail="No company associated")
    return await analytics_service.get_sentiment_summary(current_user.company_id, db)


@router.get("/complaints")
async def get_complaints(
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    if not current_user.company_id:
        raise HTTPException(status_code=400, detail="No company associated")
    return await analytics_service.get_top_complaints(current_user.company_id, db, limit=limit)


@router.get("/features")
async def get_features(
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    if not current_user.company_id:
        raise HTTPException(status_code=400, detail="No company associated")
    return await analytics_service.get_top_features(current_user.company_id, db, limit=limit)


@router.get("/topics")
async def get_topics(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    if not current_user.company_id:
        raise HTTPException(status_code=400, detail="No company associated")
    return await analytics_service.get_top_topics(current_user.company_id, db)


@router.get("/trend")
async def get_trend(
    days: int = Query(30, ge=7, le=365),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    if not current_user.company_id:
        raise HTTPException(status_code=400, detail="No company associated")
    return await analytics_service.get_sentiment_trend(current_user.company_id, db, days=days)
