from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class TicketOut(BaseModel):
    id: str
    subject: str
    description: str
    source_question: Optional[str] = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
