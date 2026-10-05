from uuid import UUID
from datetime import datetime
from pydantic import BaseModel
from app.models.feedback import FeedbackStatus, FeedbackSource

class FeedbackCreate(BaseModel):
    external_id: str | None = None
    customer_id: str | None = None
    feedback_text: str
    rating: float | None = None
    feedback_date: datetime | None = None

class FeedbackResponse(BaseModel):
    id: UUID
    external_id: str | None
    customer_id: str | None
    feedback_text: str
    rating: float | None
    feedback_date: datetime | None
    source: FeedbackSource
    status: FeedbackStatus
    created_at: datetime
    model_config = {"from_attributes": True}

class FeedbackUploadResponse(BaseModel):
    total_rows: int
    imported: int
    duplicates_skipped: int
    errors: int
    feedback_ids: list[UUID]
    message: str

class FeedbackListResponse(BaseModel):
    items: list[FeedbackResponse]
    total: int
    page: int
    page_size: int
    pages: int
