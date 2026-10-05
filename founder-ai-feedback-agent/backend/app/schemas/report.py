from uuid import UUID
from datetime import datetime
from pydantic import BaseModel
from app.models.report import ReportType, ReportFormat

class ReportRequest(BaseModel):
    report_type: ReportType = ReportType.full
    format: ReportFormat = ReportFormat.pdf
    period_start: datetime | None = None
    period_end: datetime | None = None

class ReportResponse(BaseModel):
    id: UUID
    report_type: ReportType
    format: ReportFormat
    file_path: str | None
    payload: dict | None
    generated_at: datetime
    model_config = {"from_attributes": True}
