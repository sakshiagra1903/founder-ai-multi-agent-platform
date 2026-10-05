from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.session import Base

class Candidate(Base):
    __tablename__ = "candidates"

    id                   = Column(Integer, primary_key=True, index=True)
    resume_id            = Column(Integer, ForeignKey("resumes.id"), nullable=False)

    # Identity
    name                 = Column(String(255))
    experience_years     = Column(Float, default=0.0)
    education            = Column(JSON, default=list)

    # Scores
    overall_score        = Column(Float, default=0.0)
    skills_score         = Column(Float, default=0.0)
    experience_score     = Column(Float, default=0.0)
    education_score      = Column(Float, default=0.0)
    projects_score       = Column(Float, default=0.0)
    culture_fit_score    = Column(Float, default=0.0)

    # Skills
    skills               = Column(JSON, default=list)
    missing_skills       = Column(JSON, default=list)

    # AI narrative
    summary              = Column(Text)
    strengths            = Column(JSON, default=list)
    weaknesses           = Column(JSON, default=list)
    match_reason         = Column(Text)

    # Hiring decision
    hiring_recommendation = Column(String(50), default="Reject")
    recommendation_reason = Column(Text)

    # Startup-specific
    startup_fit_signals  = Column(JSON, default=list)
    red_flags            = Column(JSON, default=list)

    # Interview questions
    interview_questions  = Column(JSON, default=list)

    # Ranking (persisted)
    rank                 = Column(Integer, default=0)

    analyzed_at          = Column(DateTime(timezone=True), server_default=func.now())
    resume               = relationship("Resume", back_populates="candidate")
