"""Report generation routes — PDF and JSON. Now runs the full LangGraph
insight agent (executive summary + root cause + recommendations, all
grounded via RAG) instead of a single executive-summary-only LLM call."""
import os
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.models.user import User
from app.models.report import Report, ReportFormat
from app.schemas.report import ReportRequest, ReportResponse
from app.core.dependencies import get_current_active_user
from app.services.analytics_service import analytics_service
from app.services.agents.insight_agent import insight_agent_service
from app.services.report_service import report_service

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.post("", response_model=ReportResponse, status_code=201)
async def generate_report(
    payload: ReportRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    if not current_user.company_id:
        raise HTTPException(status_code=400, detail="No company associated")

    analytics = await analytics_service.get_dashboard(current_user.company_id, db)
    company_name = current_user.company.name if current_user.company else "Company"

    # Run the full agentic pipeline: executive summary -> root cause -> recommendations,
    # each grounded in real feedback quotes retrieved via RAG.
    agent_result = await insight_agent_service.run(
        company_id=current_user.company_id,
        insight_types=["executive_summary", "root_cause", "recommendation"],
        db=db,
    )

    insights = []
    if agent_result.get("executive_summary"):
        insights.append({"title": "Executive Summary", "content": agent_result["executive_summary"]})
    if agent_result.get("root_cause"):
        insights.append({"title": "Root Cause Analysis", "content": agent_result["root_cause"]})
    if agent_result.get("recommendations"):
        insights.append({"title": "Recommendations", "content": agent_result["recommendations"]})

    report_data = report_service._build_report_data(
        report_type=payload.report_type.value,
        analytics=analytics,
        insights=insights,
        company_name=company_name,
        period_start=payload.period_start,
        period_end=payload.period_end,
    )

    file_path = None
    db_payload = None

    if payload.format == ReportFormat.pdf:
        import uuid
        filename = f"report_{uuid.uuid4().hex[:8]}.pdf"
        file_path = report_service.generate_pdf(report_data, filename)
    else:
        db_payload = report_data

    report = Report(
        company_id=current_user.company_id,
        generated_by=current_user.id,
        report_type=payload.report_type,
        format=payload.format,
        file_path=file_path,
        payload=db_payload,
        period_start=payload.period_start,
        period_end=payload.period_end,
    )
    db.add(report)
    await db.flush()
    return ReportResponse.model_validate(report)


@router.get("/{report_id}/download")
async def download_report(
    report_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    import uuid
    from sqlalchemy import select
    result = await db.execute(
        select(Report).where(
            Report.id == uuid.UUID(report_id),
            Report.company_id == current_user.company_id,
        )
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    if report.format != ReportFormat.pdf or not report.file_path:
        raise HTTPException(status_code=400, detail="No file available for this report")
    if not os.path.exists(report.file_path):
        raise HTTPException(status_code=404, detail="Report file not found on disk")
    return FileResponse(report.file_path, media_type="application/pdf", filename=os.path.basename(report.file_path))
