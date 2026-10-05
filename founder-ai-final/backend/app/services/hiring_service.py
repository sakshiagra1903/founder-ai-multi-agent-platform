import os
import uuid
import logging
from typing import List

from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session

from app.core.config import settings
from app.repositories.resume_repository import ResumeRepository
from app.repositories.candidate_repository import CandidateRepository
from app.services.pdf_service import pdf_service
from app.services.parsing_service import parsing_service
from app.services.ai_service import ai_service
from app.services.agentic_ai_service import agentic_ai_service
from app.services.scoring_service import scoring_service
from app.schemas.hiring import (
    ResumeUploadResponse, AnalyzeRequest, AnalyzeResponse,
    CandidateResult, ResumeResponse, ScoreBreakdown,
    FinalRankingRow, FilterOptions,
)
logger = logging.getLogger(__name__)

ALLOWED_TYPES = {"application/pdf"}
MAX_SIZE_BYTES = settings.MAX_FILE_SIZE_MB * 1024 * 1024


class HiringService:
    def __init__(self, db: Session):
        self.resume_repo = ResumeRepository(db)
        self.candidate_repo = CandidateRepository(db)

    async def upload_resumes(self, files: List[UploadFile], user_id: int) -> ResumeUploadResponse:
        """Upload multiple resume PDFs."""
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        resume_ids, filenames = [], []

        for file in files:
            if file.content_type not in ALLOWED_TYPES:
                raise HTTPException(400, detail=f"{file.filename} must be a PDF")
            
            content = await file.read()
            if len(content) > MAX_SIZE_BYTES:
                raise HTTPException(400, detail=f"{file.filename} exceeds {settings.MAX_FILE_SIZE_MB}MB")

            unique_name = f"{uuid.uuid4().hex}_{file.filename}"
            file_path = os.path.join(settings.UPLOAD_DIR, unique_name)
            
            with open(file_path, "wb") as f:
                f.write(content)

            resume = self.resume_repo.create(
                filename=unique_name,
                original_filename=file.filename,
                file_path=file_path,
                file_size=len(content),
                user_id=user_id,
            )
            resume_ids.append(resume.id)
            filenames.append(file.filename)

        return ResumeUploadResponse(
            resume_ids=resume_ids,
            filenames=filenames,
            message=f"✅ Successfully uploaded {len(resume_ids)} resume(s)",
        )

    async def analyze(self, request: AnalyzeRequest, user_id: int) -> AnalyzeResponse:
        """Analyze ALL uploaded resumes independently."""
        resumes = self.resume_repo.get_by_ids(request.resume_ids, user_id)
        if not resumes:
            raise HTTPException(404, detail="No resumes found")

        filters = request.filters or FilterOptions()
        min_exp = filters.min_experience
        req_skills = filters.required_skills or []

        results = []

        # ── EVALUATE EVERY RESUME ────────────────────────────────────────
        for resume in resumes:
            logger.info(f"Evaluating resume {resume.id}: {resume.original_filename}")
            
            text = pdf_service.extract_text(resume.file_path)
            if not text:
                logger.warning(f"Empty text from resume {resume.id}")
                continue

            # Extract metadata from resume
            parsed = parsing_service.parse(text)

            # AI evaluation — settings.AI_MODE picks between the LangGraph
            # multi-agent RAG pipeline ("agentic", default) and the original
            # single-prompt evaluator ("simple", faster/cheaper).
            if settings.AI_MODE == "simple":
                ai_data = await ai_service.evaluate_candidate(
                    resume_text=text,
                    job_description=request.job_description,
                    required_skills=req_skills,
                )
            else:
                try:
                    ai_data = await agentic_ai_service.evaluate_candidate(
                        resume_text=text,
                        job_description=request.job_description,
                        required_skills=req_skills,
                    )
                except Exception as e:
                    logger.error(f"Agentic pipeline failed, falling back to simple mode: {e}")
                    ai_data = await ai_service.evaluate_candidate(
                        resume_text=text,
                        job_description=request.job_description,
                        required_skills=req_skills,
                    )

            # Merge parsed + AI data
            breakdown = ai_data.get("score_breakdown", {})
            merged = {
                "id": 0,  # Will be set by DB
                "resume_id": resume.id,
                "rank": 0,  # Will be set during ranking
                "name": ai_data.get("name") or parsed.get("name") or "Unknown",
                "experience_years": ai_data.get("experience_years") or parsed.get("experience_years", 0),
                "education": ai_data.get("education") or parsed.get("education", []),
                "overall_score": ai_data["overall_score"],
                "score_breakdown": breakdown,
                "skills": list(set(parsed.get("skills", []) + ai_data.get("skills", []))),
                "missing_skills": ai_data.get("missing_skills", []),
                "summary": ai_data.get("summary", ""),
                "strengths": ai_data.get("strengths", []),
                "weaknesses": ai_data.get("weaknesses", []),
                "match_reason": ai_data.get("match_reason", ""),
                "hiring_recommendation": "Pending",  # Will be set during ranking
                "recommendation_reason": ai_data.get("recommendation_reason", ""),
                "startup_fit_signals": ai_data.get("startup_fit_signals", []),
                "red_flags": ai_data.get("red_flags", []),
                "interview_questions": ai_data.get("interview_questions", []),
            }

            # Save to DB
            candidate = self.candidate_repo.upsert(resume.id, merged)
            merged["id"] = candidate.id
            results.append(merged)

        # ── RANK ALL CANDIDATES ──────────────────────────────────────────
        ranked = scoring_service.filter_and_rank(results, min_exp, req_skills)

        # ── BUILD FINAL RANKING TABLE ────────────────────────────────────
        final_ranking = scoring_service.build_final_ranking(ranked)
        best = scoring_service.pick_best(ranked)

        # ── BUILD RESPONSE ───────────────────────────────────────────────
        candidates_out = []
        for r in ranked:
            bd = r.get("score_breakdown", {})
            candidates_out.append(CandidateResult(
                id=r["id"],
                resume_id=r["resume_id"],
                rank=r["rank"],
                name=r.get("name"),
                overall_score=r["overall_score"],
                score_breakdown=ScoreBreakdown(
                    skills_score=      bd.get("skills_score", 0),
                    experience_score=  bd.get("experience_score", 0),
                    education_score=   bd.get("education_score", 0),
                    projects_score=    bd.get("projects_score", 0),
                    culture_fit_score= bd.get("culture_fit_score", 0),
                    overall_score=     bd.get("overall_score", r["overall_score"]),
                ) if bd else None,
                skills=r.get("skills", []),
                missing_skills=r.get("missing_skills", []),
                summary=r.get("summary"),
                strengths=r.get("strengths", []),
                weaknesses=r.get("weaknesses", []),
                match_reason=r.get("match_reason"),
                experience_years=r.get("experience_years", 0),
                education=r.get("education", []),
                hiring_recommendation=r["hiring_recommendation"],
                recommendation_reason=r.get("recommendation_reason"),
                startup_fit_signals=r.get("startup_fit_signals", []),
                red_flags=r.get("red_flags", []),
                interview_questions=r.get("interview_questions", []),
            ))

        return AnalyzeResponse(
            candidates=candidates_out,
            total=len(results),
            filtered_count=len(candidates_out),
            message=f"✅ Analyzed {len(results)} resume(s) — {len(candidates_out)} ranked",
            final_ranking=[FinalRankingRow(**fr) for fr in final_ranking],
            best_candidate_name=best.get("name"),
            best_candidate_reason=best.get("reason"),
        )

    def list_resumes(self, user_id: int) -> List[ResumeResponse]:
        """List all resumes for a user."""
        return [ResumeResponse.model_validate(r) for r in self.resume_repo.list_by_user(user_id)]

    def delete_resume(self, resume_id: int, user_id: int) -> None:
        """Delete a resume and its associated candidate."""
        resume = self.resume_repo.get_by_id(resume_id, user_id)
        if not resume:
            raise HTTPException(404, detail="Resume not found")
        if os.path.exists(resume.file_path):
            os.remove(resume.file_path)
        self.resume_repo.delete(resume)
