"""Insight generation routes — now backed by the LangGraph insight agent."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.database import get_db
from app.models.user import User
from app.models.insight import Insight, InsightType
from app.schemas.insight import InsightRequest, InsightResponse
from app.core.dependencies import get_current_active_user
from app.services.agents.insight_agent import insight_agent_service

router = APIRouter(prefix="/insights", tags=["Insights"])

_TYPE_MAP = {
    InsightType.executive_summary: ("executive_summary", "Executive Summary"),
    InsightType.root_cause: ("root_cause", "Root Cause Analysis"),
    InsightType.recommendation: ("recommendation", "Product Recommendations"),
}


@router.post("/generate", response_model=InsightResponse, status_code=201)
async def generate_insight(
    payload: InsightRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    if not current_user.company_id:
        raise HTTPException(status_code=400, detail="No company associated")

    key, title = _TYPE_MAP.get(payload.insight_type, ("executive_summary", "Business Insight"))

    result = await insight_agent_service.run(
        company_id=current_user.company_id,
        insight_types=[key],
        db=db,
    )

    content = result.get(key) or result.get("final_report") or "No content generated."

    from app.core.config import settings
    llm_model = {"groq": settings.groq_model, "ollama": settings.ollama_model, "huggingface": settings.hf_model}.get(settings.llm_provider, "unknown")

    insight = Insight(
        company_id=current_user.company_id,
        insight_type=payload.insight_type,
        title=title,
        content=content,
        data_context=result.get("analytics", {}),
        llm_model=llm_model,
        period_start=payload.period_start,
        period_end=payload.period_end,
    )
    db.add(insight)
    await db.flush()
    return InsightResponse.model_validate(insight)


@router.get("", response_model=list[InsightResponse])
async def list_insights(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    if not current_user.company_id:
        raise HTTPException(status_code=400, detail="No company associated")
    result = await db.execute(
        select(Insight)
        .where(Insight.company_id == current_user.company_id)
        .order_by(Insight.generated_at.desc())
        .limit(20)
    )
    return [InsightResponse.model_validate(i) for i in result.scalars().all()]
