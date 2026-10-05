from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class ResumeUploadResponse(BaseModel):
    resume_ids: List[int]
    filenames: List[str]
    message: str


class ResumeResponse(BaseModel):
    id: int
    filename: str
    original_filename: str
    file_size: int
    uploaded_at: datetime

    class Config:
        from_attributes = True


class FilterOptions(BaseModel):
    min_experience: Optional[float] = None
    required_skills: Optional[List[str]] = None


class AnalyzeRequest(BaseModel):
    resume_ids: List[int]
    job_description: str
    filters: Optional[FilterOptions] = None


class ScoreBreakdown(BaseModel):
    skills_score:      float
    experience_score:  float
    education_score:   float
    projects_score:    float
    culture_fit_score: float
    overall_score:     float


class CandidateResult(BaseModel):
    id:                    int
    resume_id:             int
    rank:                  int
    name:                  Optional[str]
    overall_score:         float
    score_breakdown:       Optional[ScoreBreakdown]
    skills:                List[str]
    missing_skills:        List[str]
    summary:               Optional[str]
    strengths:             List[str]
    weaknesses:            List[str]
    match_reason:          Optional[str]
    experience_years:      float
    education:             List[str]
    hiring_recommendation: str
    recommendation_reason: Optional[str]
    startup_fit_signals:   List[str]
    red_flags:             List[str]
    interview_questions:   List[str]

    class Config:
        from_attributes = True


class FinalRankingRow(BaseModel):
    rank:                  int
    name:                  str
    overall_score:         float
    hiring_recommendation: str


class AnalyzeResponse(BaseModel):
    candidates:            List[CandidateResult]
    total:                 int
    filtered_count:        int
    message:               str
    final_ranking:         List[FinalRankingRow]
    best_candidate_name:   Optional[str]
    best_candidate_reason: Optional[str]


class DeleteResumeResponse(BaseModel):
    message:   str
    resume_id: int
