from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

class ChatRequest(BaseModel):
    question: str

class SourceCitation(BaseModel):
    document: str
    page: int = 0
    type: str = "document"  # "document" | "web"
    url: Optional[str] = None

class TicketInfo(BaseModel):
    id: str
    subject: str
    status: str

class ChatResponse(BaseModel):
    answer: str
    sources: List[SourceCitation]
    ticket: Optional[TicketInfo] = None

class ChatHistoryOut(BaseModel):
    id: str
    question: str
    answer: str
    sources: Optional[List[SourceCitation]] = None
    timestamp: datetime

    class Config:
        from_attributes = True
