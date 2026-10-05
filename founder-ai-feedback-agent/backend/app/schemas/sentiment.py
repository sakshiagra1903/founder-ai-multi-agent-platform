from uuid import UUID
from datetime import datetime
from pydantic import BaseModel
from app.models.sentiment import SentimentLabel

class SentimentResultResponse(BaseModel):
    id: UUID
    feedback_id: UUID
    sentiment: SentimentLabel
    confidence_score: float
    positive_score: float
    neutral_score: float
    negative_score: float
    model_used: str
    analyzed_at: datetime
    model_config = {"from_attributes": True}

class SentimentSummary(BaseModel):
    total_analyzed: int
    positive_count: int
    neutral_count: int
    negative_count: int
    positive_pct: float
    neutral_pct: float
    negative_pct: float
    avg_confidence: float
