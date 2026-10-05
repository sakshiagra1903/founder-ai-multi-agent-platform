from uuid import UUID
from datetime import datetime
from pydantic import BaseModel
from app.models.insight import InsightType

class InsightRequest(BaseModel):
    insight_type: InsightType = InsightType.executive_summary
    period_start: datetime | None = None
    period_end: datetime | None = None

class InsightResponse(BaseModel):
    id: UUID
    insight_type: InsightType
    title: str
    content: str
    llm_model: str | None
    generated_at: datetime
    period_start: datetime | None
    period_end: datetime | None
    model_config = {"from_attributes": True}
