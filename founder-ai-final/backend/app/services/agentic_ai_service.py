"""
Agentic hiring-evaluation pipeline built with LangGraph.

Instead of one giant prompt asking an LLM to guess every field at once, the
candidate is evaluated by a small team of specialist agents that each get
their own RAG-retrieved context (relevant resume chunks + relevant rubric
passages), and a final reflection agent sanity-checks the result before it's
returned:

    chunk_and_retrieve
            |
      skills_experience_agent
            |
      education_culture_agent
            |
        risk_agent (red flags)
            |
      synthesis_agent (summary, strengths, projects score, match reason)
            |
      interview_agent (tailored questions)
            |
      reflection_agent  -- (needs_revision?) --> synthesis_agent  [max 1 loop]
            |
        aggregate (pure code: weighted overall score)

The public entry point `agentic_ai_service.evaluate_candidate(...)` returns
the exact same dict shape as the simple `ai_service.evaluate_candidate(...)`,
so callers (hiring_service.py) can switch between the two via settings.AI_MODE
without touching anything else.
"""
import json
import logging
import re
from typing import Any, Dict, List, Optional, TypedDict

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langgraph.graph import StateGraph, END

from app.services.llm_provider import get_llm
from app.services import rag_service

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────
# Graph state
# ─────────────────────────────────────────────────────────────────────────
class EvalState(TypedDict, total=False):
    resume_text: str
    job_description: str
    required_skills: List[str]

    resume_index: Any  # Chroma index or None (short resume)

    skills_experience: Dict[str, Any]
    education_culture: Dict[str, Any]
    risk: Dict[str, Any]
    synthesis: Dict[str, Any]
    interview_questions: List[str]

    revision_count: int
    needs_revision: bool
    qa_notes: str

    final_result: Dict[str, Any]


def _clean_json(raw: str) -> Dict[str, Any]:
    """Best-effort extraction of a JSON object from an LLM response."""
    try:
        clean = re.sub(r"```json|```", "", raw).strip()
        start = clean.find("{")
        end = clean.rfind("}") + 1
        if start >= 0 and end > start:
            clean = clean[start:end]
        return json.loads(clean)
    except Exception as e:
        logger.error("Agentic pipeline JSON parse error: %s | raw=%s", e, raw[:300])
        return {}


async def _ainvoke_json(prompt: ChatPromptTemplate, variables: Dict[str, Any]) -> Dict[str, Any]:
    chain = prompt | get_llm() | StrOutputParser()
    raw = await chain.ainvoke(variables)
    return _clean_json(raw)


# ─────────────────────────────────────────────────────────────────────────
# Node 1: chunk resume + retrieve RAG context (pure retrieval, no LLM call)
# ─────────────────────────────────────────────────────────────────────────
async def node_chunk_and_retrieve(state: EvalState) -> Dict[str, Any]:
    resume_text = state["resume_text"]
    index = rag_service.build_resume_index(resume_text)
    return {"resume_index": index, "revision_count": 0, "needs_revision": False}


SKILLS_EXP_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You are a technical recruiter specialized in skills & experience assessment. "
     "Ground your evaluation in the RUBRIC provided. Return ONLY valid JSON, no markdown."),
    ("human", """JOB DESCRIPTION:
{job_description}

REQUIRED SKILLS: {required_skills_list}

RELEVANT RESUME EXCERPTS:
{resume_context}

RUBRIC (apply these standards):
{rubric}

Return JSON:
{{
  "name": "<candidate full name or Unknown>",
  "experience_years": <number>,
  "skills_score": <0-100>,
  "experience_score": <0-100>,
  "skills": ["<skill1>", "<skill2>"],
  "missing_skills": ["<required skill NOT evidenced in resume>"],
  "transferable_skills_note": "<short note on adjacent skills, or empty string>"
}}"""),
])

EDU_CULTURE_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You are an HR analyst specialized in education credentials and startup culture fit. "
     "Ground your evaluation in the RUBRIC provided. Return ONLY valid JSON, no markdown."),
    ("human", """JOB DESCRIPTION:
{job_description}

RELEVANT RESUME EXCERPTS:
{resume_context}

RUBRIC (apply these standards):
{rubric}

Return JSON:
{{
  "education": ["<degree and institution>"],
  "education_score": <0-100>,
  "culture_fit_score": <0-100>,
  "startup_fit_signals": ["<ownership demonstrated>", "<generalist skills>", "<entrepreneurial background>"]
}}"""),
])

RISK_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You are a careful, fair background-pattern analyst. You flag genuine risks and "
     "explicitly avoid flagging things the rubric says are NOT red flags. "
     "Ground your evaluation in the RUBRIC provided. Return ONLY valid JSON, no markdown."),
    ("human", """FULL RESUME TEXT (truncated):
{resume_text}

RUBRIC (apply these standards):
{rubric}

Return JSON:
{{
  "red_flags": ["<specific red flag with brief evidence>"],
  "weaknesses": ["<gap1>", "<gap2>"]
}}"""),
])

SYNTHESIS_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You are a senior hiring manager synthesizing specialist assessments into a final "
     "narrative. Be concise, specific, and evidence-based. Return ONLY valid JSON, no markdown."),
    ("human", """JOB DESCRIPTION:
{job_description}

RELEVANT RESUME EXCERPTS:
{resume_context}

RUBRIC (projects evaluation):
{projects_rubric}

SPECIALIST FINDINGS SO FAR:
Skills/Experience: {skills_experience}
Education/Culture: {education_culture}
Risk assessment: {risk}
{revision_note}

Return JSON:
{{
  "projects_score": <0-100>,
  "summary": "<2-3 sentence overall summary>",
  "strengths": ["<strength1>", "<strength2>", "<strength3>"],
  "match_reason": "<why they fit or don't fit this specific role>",
  "recommendation_reason": "<1 sentence justifying the hiring recommendation>"
}}"""),
])

INTERVIEW_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You write sharp, tailored interview questions per the provided RUBRIC. "
     "Return ONLY valid JSON, no markdown."),
    ("human", """CANDIDATE SUMMARY: {summary}
STRENGTHS: {strengths}
WEAKNESSES/RED FLAGS: {weaknesses_and_flags}
JOB DESCRIPTION: {job_description}

RUBRIC:
{rubric}

Return JSON:
{{
  "interview_questions": [
    "<question probing depth of a claimed skill/project>",
    "<question about a gap, transition, or weakness>",
    "<question testing startup-relevant judgment>"
  ]
}}"""),
])

REFLECTION_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You are a QA reviewer checking an AI hiring evaluation for internal consistency "
     "before it's shown to a human recruiter. Be strict but fair. Return ONLY valid JSON, no markdown."),
    ("human", """Review this draft evaluation for internal consistency (e.g. do the scores match the "
"listed strengths/weaknesses/red flags? Is anything contradictory or clearly hallucinated?).

DRAFT: {draft}

Return JSON:
{{
  "needs_revision": <true/false>,
  "qa_notes": "<brief note on what's wrong, or 'consistent' if fine>"
}}"""),
])


# ─────────────────────────────────────────────────────────────────────────
# Node 2: skills & experience specialist (RAG-grounded)
# ─────────────────────────────────────────────────────────────────────────
async def node_skills_experience(state: EvalState) -> Dict[str, Any]:
    required_skills = state.get("required_skills") or []
    query = f"skills and experience relevant to: {', '.join(required_skills) or state['job_description'][:200]}"
    resume_context = rag_service.retrieve_resume_context(state["resume_text"], query, state.get("resume_index"))
    rubric = rag_service.retrieve_rubric(query, category="skills") + "\n" + \
        rag_service.retrieve_rubric(query, category="experience")

    result = await _ainvoke_json(SKILLS_EXP_PROMPT, {
        "job_description": state["job_description"],
        "required_skills_list": ", ".join(required_skills) or "Not specified",
        "resume_context": resume_context,
        "rubric": rubric,
    })
    return {"skills_experience": result}


# ─────────────────────────────────────────────────────────────────────────
# Node 3: education & culture-fit specialist (RAG-grounded)
# ─────────────────────────────────────────────────────────────────────────
async def node_education_culture(state: EvalState) -> Dict[str, Any]:
    query = "education background and startup culture fit signals"
    resume_context = rag_service.retrieve_resume_context(state["resume_text"], query, state.get("resume_index"))
    rubric = rag_service.retrieve_rubric(query, category="education") + "\n" + \
        rag_service.retrieve_rubric(query, category="culture")

    result = await _ainvoke_json(EDU_CULTURE_PROMPT, {
        "job_description": state["job_description"],
        "resume_context": resume_context,
        "rubric": rubric,
    })
    return {"education_culture": result}


# ─────────────────────────────────────────────────────────────────────────
# Node 4: risk / red-flag specialist (uses fuller resume text, not chunk-retrieved,
# since red flags like gaps require seeing the whole timeline)
# ─────────────────────────────────────────────────────────────────────────
async def node_risk(state: EvalState) -> Dict[str, Any]:
    rubric = rag_service.retrieve_rubric("employment gaps job hopping red flags", category="red_flags")
    resume_text = state["resume_text"]
    truncated = resume_text[:6000]

    result = await _ainvoke_json(RISK_PROMPT, {
        "resume_text": truncated,
        "rubric": rubric,
    })
    return {"risk": result}


# ─────────────────────────────────────────────────────────────────────────
# Node 5: synthesis agent — combines everything into a narrative + projects score
# ─────────────────────────────────────────────────────────────────────────
async def node_synthesis(state: EvalState) -> Dict[str, Any]:
    query = "notable projects and measurable impact"
    resume_context = rag_service.retrieve_resume_context(state["resume_text"], query, state.get("resume_index"))
    projects_rubric = rag_service.retrieve_rubric(query, category="projects")

    revision_note = ""
    if state.get("needs_revision"):
        revision_note = f"NOTE — a QA reviewer flagged issues with the previous draft: {state.get('qa_notes')}. Please correct them."

    result = await _ainvoke_json(SYNTHESIS_PROMPT, {
        "job_description": state["job_description"],
        "resume_context": resume_context,
        "projects_rubric": projects_rubric,
        "skills_experience": json.dumps(state.get("skills_experience", {})),
        "education_culture": json.dumps(state.get("education_culture", {})),
        "risk": json.dumps(state.get("risk", {})),
        "revision_note": revision_note,
    })
    return {"synthesis": result}


# ─────────────────────────────────────────────────────────────────────────
# Node 6: interview question agent
# ─────────────────────────────────────────────────────────────────────────
async def node_interview(state: EvalState) -> Dict[str, Any]:
    rubric = rag_service.retrieve_rubric("tailored interview questions", category="interview")
    synthesis = state.get("synthesis", {})
    risk = state.get("risk", {})

    result = await _ainvoke_json(INTERVIEW_PROMPT, {
        "summary": synthesis.get("summary", ""),
        "strengths": json.dumps(synthesis.get("strengths", [])),
        "weaknesses_and_flags": json.dumps(risk.get("weaknesses", []) + risk.get("red_flags", [])),
        "job_description": state["job_description"],
        "rubric": rubric,
    })
    return {"interview_questions": result.get("interview_questions", [])}


# ─────────────────────────────────────────────────────────────────────────
# Node 7: reflection / QA agent — bounded to a single revision loop
# ─────────────────────────────────────────────────────────────────────────
async def node_reflection(state: EvalState) -> Dict[str, Any]:
    revision_count = state.get("revision_count", 0)
    if revision_count >= 1:
        # Already revised once — accept the result to avoid infinite loops / extra latency+cost.
        return {"needs_revision": False}

    draft = {
        "skills_experience": state.get("skills_experience", {}),
        "education_culture": state.get("education_culture", {}),
        "risk": state.get("risk", {}),
        "synthesis": state.get("synthesis", {}),
    }
    result = await _ainvoke_json(REFLECTION_PROMPT, {"draft": json.dumps(draft)})
    needs_revision = bool(result.get("needs_revision", False))
    return {
        "needs_revision": needs_revision,
        "qa_notes": result.get("qa_notes", ""),
        "revision_count": revision_count + (1 if needs_revision else 0),
    }


def route_after_reflection(state: EvalState) -> str:
    return "revise" if state.get("needs_revision") else "aggregate"


# ─────────────────────────────────────────────────────────────────────────
# Node 8: aggregate — pure code, combines specialist outputs into the
# same weighted-score schema the rest of the app already expects.
# ─────────────────────────────────────────────────────────────────────────
async def node_aggregate(state: EvalState) -> Dict[str, Any]:
    se = state.get("skills_experience", {}) or {}
    ec = state.get("education_culture", {}) or {}
    risk = state.get("risk", {}) or {}
    synth = state.get("synthesis", {}) or {}

    def f(v, default=0.0):
        try:
            return float(v)
        except (TypeError, ValueError):
            return default

    skills_s = min(100.0, max(0.0, f(se.get("skills_score"), 50)))
    exp_s = min(100.0, max(0.0, f(se.get("experience_score"), 50)))
    edu_s = min(100.0, max(0.0, f(ec.get("education_score"), 50)))
    proj_s = min(100.0, max(0.0, f(synth.get("projects_score"), 50)))
    cult_s = min(100.0, max(0.0, f(ec.get("culture_fit_score"), 50)))

    overall = skills_s * 0.40 + exp_s * 0.30 + edu_s * 0.15 + proj_s * 0.10 + cult_s * 0.05

    final = {
        "name": se.get("name") or "Unknown",
        "experience_years": f(se.get("experience_years"), 0),
        "education": ec.get("education", []),
        "score_breakdown": {
            "skills_score": round(skills_s, 1),
            "experience_score": round(exp_s, 1),
            "education_score": round(edu_s, 1),
            "projects_score": round(proj_s, 1),
            "culture_fit_score": round(cult_s, 1),
            "overall_score": round(min(100, max(0, overall)), 1),
        },
        "overall_score": round(min(100, max(0, overall)), 1),
        "skills": se.get("skills", []),
        "missing_skills": se.get("missing_skills", []),
        "summary": synth.get("summary", ""),
        "strengths": synth.get("strengths", []),
        "weaknesses": risk.get("weaknesses", []),
        "match_reason": synth.get("match_reason", ""),
        "startup_fit_signals": ec.get("startup_fit_signals", []),
        "red_flags": risk.get("red_flags", []),
        "interview_questions": state.get("interview_questions", []),
        "recommendation_reason": synth.get("recommendation_reason", ""),
    }
    return {"final_result": final}


def _fallback_response() -> Dict[str, Any]:
    return {
        "name": "Unknown",
        "experience_years": 0,
        "education": [],
        "score_breakdown": {
            "skills_score": 0, "experience_score": 0, "education_score": 0,
            "projects_score": 0, "culture_fit_score": 0, "overall_score": 0,
        },
        "overall_score": 0.0,
        "skills": [], "missing_skills": [],
        "summary": "Could not evaluate this candidate.",
        "strengths": [], "weaknesses": ["Evaluation failed"],
        "match_reason": "N/A",
        "startup_fit_signals": [], "red_flags": ["Evaluation error"],
        "interview_questions": [],
        "recommendation_reason": "Evaluation failed",
    }


def _build_graph():
    # Node names are intentionally suffixed with "_agent"/"_step" so they never
    # collide with the EvalState TypedDict field names (LangGraph forbids that).
    graph = StateGraph(EvalState)
    graph.add_node("retrieve_step", node_chunk_and_retrieve)
    graph.add_node("skills_experience_agent", node_skills_experience)
    graph.add_node("education_culture_agent", node_education_culture)
    graph.add_node("risk_agent", node_risk)
    graph.add_node("synthesis_agent", node_synthesis)
    graph.add_node("interview_agent", node_interview)
    graph.add_node("reflection_agent", node_reflection)
    graph.add_node("aggregate_step", node_aggregate)

    graph.set_entry_point("retrieve_step")
    graph.add_edge("retrieve_step", "skills_experience_agent")
    graph.add_edge("skills_experience_agent", "education_culture_agent")
    graph.add_edge("education_culture_agent", "risk_agent")
    graph.add_edge("risk_agent", "synthesis_agent")
    graph.add_edge("synthesis_agent", "interview_agent")
    graph.add_edge("interview_agent", "reflection_agent")
    graph.add_conditional_edges(
        "reflection_agent",
        route_after_reflection,
        {"revise": "synthesis_agent", "aggregate": "aggregate_step"},
    )
    graph.add_edge("aggregate_step", END)
    return graph.compile()


_compiled_graph = None


def _get_graph():
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = _build_graph()
    return _compiled_graph


class AgenticAIService:
    """Public entry point — same interface/return-shape as AIService.evaluate_candidate."""

    async def evaluate_candidate(
        self,
        resume_text: str,
        job_description: str,
        required_skills: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        try:
            graph = _get_graph()
            result_state = await graph.ainvoke({
                "resume_text": resume_text,
                "job_description": job_description,
                "required_skills": required_skills or [],
            })
            final = result_state.get("final_result")
            return final if final else _fallback_response()
        except Exception as e:
            logger.error("Agentic evaluation pipeline error: %s", e, exc_info=True)
            return _fallback_response()


agentic_ai_service = AgenticAIService()
