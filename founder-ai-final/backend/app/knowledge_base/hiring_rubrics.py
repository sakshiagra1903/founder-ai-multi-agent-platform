"""
Curated hiring/recruiting knowledge base.

These documents are embedded into a persistent vector store (Chroma) once,
on first run, and retrieved by the LangGraph agent nodes to *ground* the
LLM's scoring in explicit, human-authored rubrics instead of relying purely
on the model's parametric knowledge. This is the "RAG" layer of the
evaluation pipeline (retrieval-augmented scoring).

Each entry has:
  - id: stable id (used so we don't re-insert duplicates)
  - category: used for metadata filtering during retrieval
  - text: the actual rubric content that gets embedded
"""

RUBRIC_DOCS = [
    {
        "id": "skills-001",
        "category": "skills",
        "text": (
            "Skills evaluation rubric: Score 90-100 when the candidate demonstrates "
            "hands-on production experience with nearly all required skills, backed by "
            "concrete projects or metrics. Score 70-89 when most required skills are present "
            "but 1-2 are missing or only lightly used. Score 50-69 when roughly half the "
            "required skills are present, or skills are only mentioned without evidence of "
            "real usage. Score below 50 when most required skills are absent or the resume "
            "shows only tangential exposure (e.g. a single course or tutorial)."
        ),
    },
    {
        "id": "skills-002",
        "category": "skills",
        "text": (
            "Adjacent/transferable skills matter: a candidate missing an exact tool but with "
            "strong experience in a close equivalent (e.g. FastAPI vs Flask, PostgreSQL vs "
            "MySQL, React vs Vue) should not be penalized as heavily as a candidate with no "
            "related experience at all. Note transferable skills explicitly in the reasoning."
        ),
    },
    {
        "id": "experience-001",
        "category": "experience",
        "text": (
            "Experience evaluation rubric: Weigh relevance over raw years. 5 years in an "
            "unrelated domain is worth less than 2 years directly relevant to the job "
            "description. Prefer candidates who show scope growth (increasing responsibility, "
            "ownership, or team size) over static years-in-role. For early-stage startup roles, "
            "value hands-on individual-contributor experience and generalist range over deep "
            "specialization in a single narrow area."
        ),
    },
    {
        "id": "experience-002",
        "category": "experience",
        "text": (
            "When experience years are ambiguous or unstated, estimate conservatively from "
            "listed employment dates and internship/project history rather than inventing a "
            "number. Freelance, open-source, and side-project work counts but should be "
            "weighted slightly lower than full-time employment unless the output quality is "
            "clearly production-grade."
        ),
    },
    {
        "id": "education-001",
        "category": "education",
        "text": (
            "Education evaluation rubric: A relevant degree (CS, Engineering, or the job's "
            "domain) from any accredited institution scores well. Bootcamps and strong "
            "self-taught portfolios should score comparably to a degree for technical roles "
            "when skills evidence is strong — education is a signal, not a gate. Do not "
            "penalize candidates for lacking a degree if their skills and experience are solid; "
            "startups especially should weight demonstrated ability over credentials."
        ),
    },
    {
        "id": "culture-001",
        "category": "culture",
        "text": (
            "Startup culture-fit signals to look for: evidence of ownership (built something "
            "0-to-1, launched a product, ran a project end-to-end), comfort with ambiguity, "
            "generalist range (wore multiple hats: eng + design + growth), fast iteration "
            "speed, and entrepreneurial background (founded something, froze/grew a side "
            "project, contributed to open source under their own initiative). Absence of these "
            "signals is not disqualifying but should lower the culture-fit score moderately."
        ),
    },
    {
        "id": "culture-002",
        "category": "culture",
        "text": (
            "Be wary of over-crediting buzzwords ('rockstar', 'ninja', 'passionate about "
            "innovation') with no concrete backing. Culture fit should be inferred from "
            "specific, verifiable actions described in the resume, not adjectives the "
            "candidate uses to describe themselves."
        ),
    },
    {
        "id": "redflags-001",
        "category": "red_flags",
        "text": (
            "Common resume red flags to check for: unexplained employment gaps longer than 6 "
            "months, a pattern of multiple jobs each lasting under 12 months (job hopping) "
            "without clear reason (e.g. layoffs, acquisitions), vague or unverifiable claims "
            "('increased revenue by 500%' with no context), inconsistent timelines/overlapping "
            "dates, and generic responsibility-listing with no outcomes or metrics."
        ),
    },
    {
        "id": "redflags-002",
        "category": "red_flags",
        "text": (
            "Not every gap or short tenure is a genuine red flag — context matters. A gap "
            "during a well-known industry downturn, a short stint at a company known for mass "
            "layoffs, or a stated career break (education, caregiving, health) should be noted "
            "as low-severity or excluded, not treated the same as unexplained churn."
        ),
    },
    {
        "id": "projects-001",
        "category": "projects",
        "text": (
            "Projects/portfolio evaluation rubric: Prioritize projects with measurable impact "
            "(users, revenue, performance improvement, scale) over a long list of toy projects. "
            "A single well-documented, deployed, end-to-end project outweighs five tutorial "
            "clones. Open-source contributions with merged PRs or meaningful stars/usage count "
            "positively."
        ),
    },
    {
        "id": "interview-001",
        "category": "interview",
        "text": (
            "Good tailored interview questions probe: (1) the specific technical depth behind "
            "a claimed skill or project, (2) how the candidate handled a gap, transition, or "
            "weakness visible on the resume, and (3) a scenario that tests startup-relevant "
            "judgment such as prioritization under ambiguity or ownership of an end-to-end "
            "outcome. Avoid generic questions that could apply to any candidate."
        ),
    },
]
