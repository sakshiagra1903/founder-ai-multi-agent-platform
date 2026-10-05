from uuid import UUID
from datetime import datetime
from pydantic import BaseModel
from app.models.complaint import ComplaintSeverity

class ComplaintResponse(BaseModel):
    id: UUID
    feedback_id: UUID
    category: str
    subcategory: str | None
    description: str | None
    severity: ComplaintSeverity
    confidence_score: float
    detected_at: datetime
    model_config = {"from_attributes": True}

class ComplaintCategorySummary(BaseModel):
    category: str
    count: int
    percentage: float
    severity_breakdown: dict[str, int]

class ComplaintSummary(BaseModel):
    total_complaints: int
    categories: list[ComplaintCategorySummary]
    most_severe_category: str | None
    trend: str | None
