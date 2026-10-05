from uuid import UUID
from datetime import datetime
from pydantic import BaseModel

class TopicResponse(BaseModel):
    id: UUID
    topic_id: int
    label: str
    keywords: list[str]
    frequency: int
    created_at: datetime
    model_config = {"from_attributes": True}
