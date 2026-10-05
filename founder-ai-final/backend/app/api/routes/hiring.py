from typing import List
from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.user import User
from app.utils.deps import get_current_user
from app.services.hiring_service import HiringService
from app.schemas.hiring import (
    ResumeUploadResponse, AnalyzeRequest, AnalyzeResponse,
    ResumeResponse, DeleteResumeResponse,
)

router = APIRouter(prefix="/hiring", tags=["Hiring"])


@router.post("/upload-resumes", response_model=ResumeUploadResponse, status_code=201)
async def upload_resumes(
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload multiple PDF resumes."""
    return await HiringService(db).upload_resumes(files, current_user.id)


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_candidates(
    request: AnalyzeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Analyze all uploaded resumes and return ranked candidates."""
    return await HiringService(db).analyze(request, current_user.id)


@router.get("/resumes", response_model=List[ResumeResponse])
def list_resumes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all resumes for the current user."""
    return HiringService(db).list_resumes(current_user.id)


@router.delete("/resumes/{resume_id}", response_model=DeleteResumeResponse)
def delete_resume(
    resume_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a resume."""
    HiringService(db).delete_resume(resume_id, current_user.id)
    return DeleteResumeResponse(message="Resume deleted successfully", resume_id=resume_id)
