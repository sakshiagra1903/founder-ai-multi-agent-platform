from datetime import datetime
from pydantic import BaseModel

class DocumentOut(BaseModel):
    id: str
    user_id: str
    filename: str
    file_path: str
    file_size: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

class DocumentUploadResponse(BaseModel):
    document_id: str
    filename: str
    status: str
