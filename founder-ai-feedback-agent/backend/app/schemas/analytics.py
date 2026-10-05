from pydantic import BaseModel

class TrendPoint(BaseModel):
    date: str
    positive_pct: float
    neutral_pct: float
    negative_pct: float
    total: int

class TrendData(BaseModel):
    sentiment_trend: list[TrendPoint]
    complaint_trend: list[dict]
    feature_trend: list[dict]
    most_increasing_complaint: str | None
    most_requested_feature: str | None

class DashboardAnalytics(BaseModel):
    total_feedback: int
    positive_pct: float
    neutral_pct: float
    negative_pct: float
    total_complaints: int
    total_feature_requests: int
    top_complaints: list[dict]
    top_feature_requests: list[dict]
    top_topics: list[dict]
    most_critical_issue: str | None
    sentiment_trend: list[TrendPoint]
    recent_insights: list[dict]
