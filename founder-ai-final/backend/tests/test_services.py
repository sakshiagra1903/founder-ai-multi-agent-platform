from app.services.parsing_service import parsing_service
from app.services.scoring_service import scoring_service
from app.services.pdf_service import pdf_service


# ─── Parsing Service ───────────────────────────────────────────────────────────

SAMPLE_RESUME = """
John Smith
john.smith@email.com | +1-555-1234

EXPERIENCE
Software Engineer at Acme Corp — 3 years of experience
Developed Python microservices using FastAPI and PostgreSQL.

SKILLS
Python, FastAPI, PostgreSQL, Docker, Machine Learning, React

EDUCATION
Bachelor of Science in Computer Science, MIT 2020
"""


def test_extract_name():
    result = parsing_service.parse(SAMPLE_RESUME)
    assert "John" in result["name"] or result["name"] != "Unknown"


def test_extract_skills():
    result = parsing_service.parse(SAMPLE_RESUME)
    assert "python" in result["skills"]
    assert "fastapi" in result["skills"]


def test_extract_experience():
    result = parsing_service.parse(SAMPLE_RESUME)
    assert result["experience_years"] == 3.0


def test_extract_education():
    result = parsing_service.parse(SAMPLE_RESUME)
    assert len(result["education"]) >= 1


# ─── Scoring Service ───────────────────────────────────────────────────────────

CANDIDATES = [
    {"id": 1, "resume_id": 1, "name": "Alice", "score": 85.0, "skills": ["python", "ml"], "experience_years": 4, "summary": "", "strengths": [], "weaknesses": [], "match_reason": "", "education": []},
    {"id": 2, "resume_id": 2, "name": "Bob", "score": 70.0, "skills": ["java"], "experience_years": 1, "summary": "", "strengths": [], "weaknesses": [], "match_reason": "", "education": []},
    {"id": 3, "resume_id": 3, "name": "Charlie", "score": 90.0, "skills": ["python", "ml", "react"], "experience_years": 5, "summary": "", "strengths": [], "weaknesses": [], "match_reason": "", "education": []},
]


def test_sort_by_score():
    ranked = scoring_service.filter_and_rank(CANDIDATES.copy())
    assert ranked[0]["name"] == "Charlie"
    assert ranked[1]["name"] == "Alice"


def test_filter_by_min_experience():
    ranked = scoring_service.filter_and_rank(CANDIDATES.copy(), min_experience=2)
    names = [c["name"] for c in ranked]
    assert "Bob" not in names


def test_filter_by_required_skills():
    ranked = scoring_service.filter_and_rank(CANDIDATES.copy(), required_skills=["python"])
    # Bob has no python; his score should be penalized
    bob = next((c for c in ranked if c["name"] == "Bob"), None)
    assert bob is not None
    assert bob["score"] < 70.0
