from typing import Any, Dict, Optional
from sqlalchemy.orm import Session
from app.models.candidate import Candidate


class CandidateRepository:
    def __init__(self, db: Session):
        self.db = db

    def upsert(self, resume_id: int, data: Dict[str, Any]) -> Candidate:
        """Create or update candidate."""
        candidate = self.db.query(Candidate).filter(Candidate.resume_id == resume_id).first()
        bd = data.get("score_breakdown", {})
        
        if not candidate:
            candidate = Candidate(resume_id=resume_id)
            self.db.add(candidate)

        # Basic info
        candidate.name             = data.get("name")
        candidate.experience_years = data.get("experience_years", 0)
        candidate.education        = data.get("education", [])

        # Scores
        candidate.overall_score    = data.get("overall_score", 0)
        candidate.skills_score     = bd.get("skills_score", 0)
        candidate.experience_score = bd.get("experience_score", 0)
        candidate.education_score  = bd.get("education_score", 0)
        candidate.projects_score   = bd.get("projects_score", 0)
        candidate.culture_fit_score= bd.get("culture_fit_score", 0)

        # Skills
        candidate.skills           = data.get("skills", [])
        candidate.missing_skills   = data.get("missing_skills", [])

        # Narrative
        candidate.summary          = data.get("summary", "")
        candidate.strengths        = data.get("strengths", [])
        candidate.weaknesses       = data.get("weaknesses", [])
        candidate.match_reason     = data.get("match_reason", "")

        # Hiring decision
        candidate.hiring_recommendation = data.get("hiring_recommendation", "Reject")
        candidate.recommendation_reason = data.get("recommendation_reason", "")

        # Startup signals
        candidate.startup_fit_signals = data.get("startup_fit_signals", [])
        candidate.red_flags          = data.get("red_flags", [])

        # Interview
        candidate.interview_questions = data.get("interview_questions", [])

        # Ranking
        candidate.rank = data.get("rank", 0)

        self.db.commit()
        self.db.refresh(candidate)
        return candidate

    def get_by_resume(self, resume_id: int) -> Optional[Candidate]:
        return self.db.query(Candidate).filter(Candidate.resume_id == resume_id).first()
