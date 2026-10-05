from uuid import UUID
from datetime import datetime
from pydantic import BaseModel
from app.models.feature_request import FeaturePriority

class FeatureRequestResponse(BaseModel):
    id: UUID
    feedback_id: UUID
    request: str
    normalized_request: str | None
    category: str | None
    priority: FeaturePriority
    confidence_score: float
    frequency: int
    detected_at: datetime
    model_config = {"from_attributes": True}

class FeatureRequestSummary(BaseModel):
    total_requests: int
    unique_features: int
    top_requests: list[dict]
    categories: list[dict]
