import json
import logging
import re
from typing import Dict, Any, List

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.core.config import settings

logger = logging.getLogger(__name__)


EVAL_PROMPT = ChatPromptTemplate.from_messages([
    ("system", (
        "You are a senior HR analyst and technical recruiter with 15+ years of experience. "
        "Evaluate resumes against job descriptions with precision. "
        "Return ONLY valid JSON — no markdown, no explanation, no preamble."
    )),
    ("human", """Evaluate this candidate resume against the job description below.

JOB DESCRIPTION:
{job_description}

REQUIRED SKILLS FROM JD:
{required_skills_list}

RESUME TEXT:
{resume_text}

Return a valid JSON object with this EXACT structure:
{{
  "name": "<full name or Unknown>",
  "experience_years": <total years as number>,
  "education": ["<degree and institution>"],
  
  "score_breakdown": {{
    "skills_score": <0-100, how well candidate skills match JD>,
    "experience_score": <0-100, years and relevance>,
    "education_score": <0-100, degree level and relevance>,
    "projects_score": <0-100, portfolio impact>,
    "culture_fit_score": <0-100, startup attitude signals>
  }},
  
  "overall_score": <0-100, weighted: skills 40% + exp 30% + edu 15% + projects 10% + culture 5%>,
  
  "skills": ["<skill1>", "<skill2>"],
  "missing_skills": ["<skills in JD but NOT in resume>"],
  
  "summary": "<2-3 sentence summary>",
  "strengths": ["<strength1>", "<strength2>", "<strength3>"],
  "weaknesses": ["<gap1>", "<gap2>"],
  "match_reason": "<why they fit or don't for this role>",
  
  "startup_fit_signals": ["<ownership demonstrated>", "<generalist skills>", "<entrepreneurial background>"],
  "red_flags": ["<employment gap >6 months>", "<job hopping pattern>"],
  
  "interview_questions": [
    "<question1 tailored to their profile>",
    "<question2 about their gaps>",
    "<question3 about their strengths>"
  ],
  
  "recommendation_reason": "<1 sentence justifying the hiring recommendation>"
}}""")
])


from app.services.llm_provider import get_llm as _get_llm


class AIService:
    def __init__(self):
        self._chain = None

    def _get_chain(self):
        if not self._chain:
            self._chain = EVAL_PROMPT | _get_llm() | StrOutputParser()
        return self._chain

    async def evaluate_candidate(
        self,
        resume_text: str,
        job_description: str,
        required_skills: List[str] = None,
    ) -> Dict[str, Any]:
        try:
            chain = self._get_chain()
            truncated = resume_text[:5000] if len(resume_text) > 5000 else resume_text
            skills_list = ", ".join(required_skills) if required_skills else "Not specified"
            raw = await chain.ainvoke({
                "job_description": job_description,
                "resume_text": truncated,
                "required_skills_list": skills_list,
            })
            return self._parse_response(raw)
        except Exception as e:
            logger.error(f"AI evaluation error: {e}")
            return self._fallback_response()

    def _parse_response(self, raw: str) -> Dict[str, Any]:
        try:
            clean = re.sub(r"```json|```", "", raw).strip()
            start = clean.find("{")
            end = clean.rfind("}") + 1
            if start >= 0 and end > start:
                clean = clean[start:end]
            data = json.loads(clean)

            bd = data.get("score_breakdown", {})
            skills_s  = float(bd.get("skills_score", 50))
            exp_s     = float(bd.get("experience_score", 50))
            edu_s     = float(bd.get("education_score", 50))
            proj_s    = float(bd.get("projects_score", 50))
            cult_s    = float(bd.get("culture_fit_score", 50))

            overall = (
                skills_s * 0.40 +
                exp_s * 0.30 +
                edu_s * 0.15 +
                proj_s * 0.10 +
                cult_s * 0.05
            )

            return {
                "name": data.get("name", "Unknown"),
                "experience_years": float(data.get("experience_years", 0)),
                "education": data.get("education", []),
                "score_breakdown": {
                    "skills_score":      round(min(100, max(0, skills_s)), 1),
                    "experience_score":  round(min(100, max(0, exp_s)), 1),
                    "education_score":   round(min(100, max(0, edu_s)), 1),
                    "projects_score":    round(min(100, max(0, proj_s)), 1),
                    "culture_fit_score": round(min(100, max(0, cult_s)), 1),
                    "overall_score":     round(min(100, max(0, overall)), 1),
                },
                "overall_score": round(min(100, max(0, overall)), 1),
                "skills":            data.get("skills", []),
                "missing_skills":    data.get("missing_skills", []),
                "summary":           data.get("summary", ""),
                "strengths":         data.get("strengths", []),
                "weaknesses":        data.get("weaknesses", []),
                "match_reason":      data.get("match_reason", ""),
                "startup_fit_signals": data.get("startup_fit_signals", []),
                "red_flags":         data.get("red_flags", []),
                "interview_questions": data.get("interview_questions", []),
                "recommendation_reason": data.get("recommendation_reason", ""),
            }
        except Exception as e:
            logger.error(f"Parse error: {e}\nRaw: {raw[:300]}")
            return self._fallback_response()

    def _fallback_response(self) -> Dict[str, Any]:
        return {
            "name": "Unknown",
            "experience_years": 0,
            "education": [],
            "score_breakdown": {
                "skills_score": 0,
                "experience_score": 0,
                "education_score": 0,
                "projects_score": 0,
                "culture_fit_score": 0,
                "overall_score": 0,
            },
            "overall_score": 0.0,
            "skills": [],
            "missing_skills": [],
            "summary": "Could not evaluate this candidate.",
            "strengths": [],
            "weaknesses": ["Evaluation failed"],
            "match_reason": "N/A",
            "startup_fit_signals": [],
            "red_flags": ["Evaluation error"],
            "interview_questions": [],
            "recommendation_reason": "Evaluation failed",
        }


ai_service = AIService()
