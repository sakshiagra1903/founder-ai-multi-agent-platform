# 🤖 Founder AI — Hiring Agent v2.0

**The complete AI-powered hiring platform for early-stage startups.**

Upload unlimited resumes, get AI-scored candidates ranked with hiring recommendations, missing skills analysis, red flags detection, and AI-generated interview questions.

---

## ✨ What's New in v2

✅ **Score Breakdown** — 5 dimensions: Skills (40%) + Experience (30%) + Education (15%) + Projects (10%) + Culture Fit (5%)

✅ **Hiring Recommendations** — Strong Hire / Hire / Consider / Reject with AI-generated reasoning

✅ **Missing Skills Analysis** — Shows exactly which JD skills the candidate lacks

✅ **Red Flag Detection** — Employment gaps, job hopping, inflated claims

✅ **Startup Fit Signals** — Ownership, generalist skills, entrepreneurial background

✅ **Interview Questions** — 3 AI-generated questions tailored to each candidate

✅ **Final Ranking Table** — Trophy-style ranking with recommendation summary

✅ **Best Candidate Pick** — AI explains why the top candidate is the best match

---

## 🧠 What's New in v2.1 — Agentic RAG Pipeline

The AI evaluation engine now runs as a **multi-agent LangGraph pipeline grounded with RAG** instead of a single prompt:

```
                 ┌─────────────────────┐
 Resume + JD ──▶ │ Chunk + Retrieve     │  ← splits long resumes, retrieves the
                 └─────────┬───────────┘     most relevant chunks per dimension
                           ▼
                 ┌─────────────────────┐
                 │ Skills & Experience │ ← RAG-grounded on skills/experience rubric
                 └─────────┬───────────┘
                           ▼
                 ┌─────────────────────┐
                 │ Education & Culture │ ← RAG-grounded on education/culture rubric
                 └─────────┬───────────┘
                           ▼
                 ┌─────────────────────┐
                 │ Risk / Red-Flag     │ ← RAG-grounded on red-flag rubric
                 └─────────┬───────────┘
                           ▼
                 ┌─────────────────────┐
                 │ Synthesis           │ ← combines everything into summary/strengths
                 └─────────┬───────────┘
                           ▼
                 ┌─────────────────────┐
                 │ Interview Questions │
                 └─────────┬───────────┘
                           ▼
                 ┌─────────────────────┐
                 │ Reflection / QA     │──┐ loops back to Synthesis once if
                 └─────────┬───────────┘  │ scores look internally inconsistent
                           ▼               │
                 ┌─────────────────────┐   │
                 │ Aggregate (weighted)│◀──┘ (max 1 revision)
                 └─────────┬───────────┘
                           ▼
                     Final candidate result
```

- **RAG grounding**: a curated hiring-rubric knowledge base (`app/knowledge_base/hiring_rubrics.py`) is embedded once into a persistent [Chroma](https://www.trychroma.com/) vector store. Every specialist agent retrieves the rubric passages relevant to *its* dimension instead of relying purely on the LLM's own judgment.
- **Resume RAG**: long/multi-page resumes are chunked and embedded per-analysis; each agent retrieves only the passages relevant to what it's scoring (skills, education, red flags, projects) instead of stuffing the whole resume into every prompt.
- **Local embeddings, no extra API key**: retrieval uses `fastembed` (`BAAI/bge-small-en-v1.5`), which runs 100% locally via ONNX — the model (~130MB) downloads once from Hugging Face on first run and is cached after that. It does **not** use your Groq/OpenAI quota.
- **Self-correcting**: a reflection agent checks the draft evaluation for internal consistency and can trigger one revision pass before returning a result.
- **Same output shape**: the API response and DB schema are unchanged, so the existing frontend needs zero changes.

### Toggle: agentic vs. simple mode
In `backend/.env`:
```
# "agentic" (default) = LangGraph multi-agent RAG pipeline — deeper, ~6-8 LLM calls/resume
# "simple"            = original single-prompt evaluator — 1 LLM call/resume, faster & cheaper
AI_MODE=agentic
```
Use `AI_MODE=simple` if you're processing many resumes on a free-tier rate limit and want the fast/cheap path. If the agentic pipeline ever errors (e.g. rate limit mid-run), it automatically falls back to simple mode for that resume so analysis never fails outright.

---

## 🚀 Quick Start (5 Minutes)

### Step 1 — Get Free Groq API Key
1. Go to **https://console.groq.com**
2. Sign up with email (no credit card needed)
3. Go to **API Keys** → **Create New API Key**
4. Copy the key (starts with `gsk_`)

### Step 2 — Backend Setup
```powershell
cd founder-ai-final\backend

# Update .env with your Groq key
notepad .env
# Replace: gsk_PUT_YOUR_GROQ_API_KEY_HERE

# Install dependencies
pip install -r requirements.txt

# Start backend
python -m uvicorn main:app --reload
```
✅ Backend: http://localhost:8000
✅ API Docs: http://localhost:8000/docs

### Step 3 — Frontend Setup (NEW PowerShell window)
```powershell
cd founder-ai-final\frontend

npm install
npm run dev
```
✅ App: http://localhost:3000

### Step 4 — Use It
1. Open http://localhost:3000
2. **Sign up** with any email
3. Go to **Analyze** tab
4. Upload multiple PDF resumes
5. Paste a job description
6. Click **Analyze Candidates with AI**
7. View results with all scores, rankings, recommendations

---

## 📊 Scoring System

### 5-Dimension Score Breakdown
```
Skills Match:     40% — Candidates technical skills vs JD requirements
Experience:       30% — Years + relevance of work history
Education:        15% — Degree level + field relevance
Projects:         10% — Portfolio impact + quality of work
Culture Fit:       5% — Startup signals (ownership, generalist, founder DNA)
                 ─────
OVERALL:         100%
```

### Hiring Recommendations
| Score | Label | What it means |
|---|---|---|
| 85–100 | ✅ Strong Hire | Exceptional fit. Interview immediately. |
| 70–84 | 🟢 Hire | Good fit. Likely a solid team member. |
| 55–69 | 🟡 Consider | Could work. Interview if time permits. |
| <55 | 🔴 Reject | Not a fit for this role. |

---

## 🎯 Features

### Upload & Analyze
- ✅ Upload unlimited PDF resumes at once
- ✅ Each resume evaluated independently
- ✅ Paste job description (the more detailed, the better)
- ✅ Optional: Min experience + required skills filter
- ✅ All results ranked #1, #2, #3…

### Scoring & Ranking
- ✅ 5-dimensional score breakdown (skills, exp, ed, projects, culture)
- ✅ Hiring recommendation (Strong Hire / Hire / Consider / Reject)
- ✅ Missing skills highlighted in amber
- ✅ Red flags detected (gaps, job hopping)
- ✅ Startup fit signals identified

### Per-Candidate Details
- ✅ AI summary in 2–3 sentences
- ✅ Top 3 strengths
- ✅ Weaknesses / gaps
- ✅ 3 tailored interview questions
- ✅ Why they're a fit (or not)

### Final Results
- ✅ Ranking table with scores + recommendations
- ✅ Best candidate pick with AI explanation
- ✅ Filter by recommendation (Strong Hire only, etc.)
- ✅ Sort by score, experience, name
- ✅ **Export to CSV** for Excel/Sheets

---

## 🗂 Project Structure

```
founder-ai-final/
├── backend/                      ← FastAPI + SQLAlchemy
│   ├── main.py                  ← App entry point
│   ├── requirements.txt          ← Dependencies
│   ├── .env                      ← Config (GROQ_API_KEY goes here)
│   └── app/
│       ├── api/routes/
│       │   ├── auth.py          ← Login/signup/me
│       │   └── hiring.py        ← Upload/analyze/list/delete
│       ├── services/
│       │   ├── ai_service.py    ← Simple single-prompt evaluator (AI_MODE=simple)
│       │   ├── agentic_ai_service.py ← LangGraph multi-agent RAG evaluator (default)
│       │   ├── rag_service.py   ← Chroma + fastembed retrieval layer
│       │   ├── llm_provider.py  ← Shared Groq/OpenAI chat-model factory
│       │   ├── scoring_service.py ← Ranking + recommendations
│       │   ├── hiring_service.py ← Orchestration
│       │   ├── parsing_service.py ← Skill/exp extraction
│       │   └── pdf_service.py   ← PyMuPDF text extraction
│       ├── knowledge_base/
│       │   └── hiring_rubrics.py ← RAG source documents (scoring rubrics)
│       ├── models/              ← SQLAlchemy DB models
│       ├── schemas/             ← Pydantic request/response schemas
│       ├── repositories/        ← DB access layer
│       └── core/                ← Config, JWT, password hashing
│
└── frontend/                     ← Next.js + React + Tailwind
    ├── app/
    │   ├── login/page.tsx       ← Sign in
    │   ├── signup/page.tsx      ← Create account
    │   ├── dashboard/page.tsx   ← Resume library
    │   ├── upload/page.tsx      ← Upload + analyze (multi-step)
    │   └── results/page.tsx     ← Ranking table + candidates
    ├── components/
    │   ├── CandidateCard.tsx    ← Full card (scores, gaps, Q&As)
    │   ├── ScoreBadge.tsx       ← SVG ring score
    │   ├── ScoreBar.tsx         ← Horizontal bar (skills, exp, etc.)
    │   ├── HiringBadge.tsx      ← Recommendation label
    │   ├── AlertBox.tsx         ← Red flags / signals / Q&As
    │   ├── ResumeDropzone.tsx   ← Drag-drop upload
    │   ├── SkillsInput.tsx      ← Tag-style skill input
    │   ├── Navbar.tsx
    │   └── ProtectedLayout.tsx
    └── types/index.ts           ← TypeScript interfaces
```

---

## 🆓 AI Providers

### Groq (Recommended — Free)
- **Model**: Llama 3.1 70B
- **Free limit**: 1,000 requests/day
- **Speed**: ~315 tokens/sec (fastest)
- **Sign up**: https://console.groq.com (no card)

### OpenAI (Paid)
To use GPT instead, change `.env`:
```
AI_PROVIDER=openai
OPENAI_API_KEY=sk_...
```

---

## 🐛 Troubleshooting

| Problem | Solution |
|---|---|
| `python -m uvicorn` not found | Make sure Python 3.10+ installed: `python --version` |
| `npm: not found` | Install Node.js from https://nodejs.org (LTS) |
| SQLite errors | Delete `founderai.db` — will auto-create on next run |
| Groq API error | Check your `.env` GROQ_API_KEY. Get a fresh one at https://console.groq.com |
| Page refresh loses results | Results auto-save to DB — refresh now shows persistent data |
| Frontend can't reach backend | Make sure backend running on 8000, frontend .env has `NEXT_PUBLIC_API_URL=http://localhost:8000` |
| First analyze request is slow / "downloading model" in logs | Normal — the local embedding model (~130MB) downloads once on first run and is cached in `backend/chroma_db` + your fastembed cache folder. Needs internet the first time only. |
| Want faster/cheaper analysis | Set `AI_MODE=simple` in `backend/.env` to skip the multi-agent RAG pipeline and use the original single-prompt evaluator |
| `chromadb`/telemetry warnings in logs | Harmless — these are cosmetic telemetry-library warnings and don't affect analysis results |

---

## 📈 Example Workflow

**Scenario**: You're a startup founder hiring a Senior React Engineer.

1. **Create job description**:
   ```
   We're looking for a Senior React Engineer with:
   - 3+ years React experience
   - TypeScript & Node.js
   - PostgreSQL familiarity
   - AWS knowledge
   - Ability to own features end-to-end
   ```

2. **Upload 15 resumes** (drag & drop all at once)

3. **Set filters**:
   - Min experience: 3 years
   - Required skills: React, TypeScript, Node.js

4. **Click Analyze** — AI evaluates all 15 instantly

5. **Review results**:
   - Rank #1: Alice (92/100) — Strong Hire ✅
   - Rank #2: Bob (78/100) — Hire 🟢
   - Rank #3: Carol (61/100) — Consider 🟡
   - Rank #4–15: Various scores

6. **See best candidate summary**:
   ```
   🏆 Best Candidate: Alice
   Alice scored highest at 92/100 with exceptional skills
   match (95), strong experience (90), and clear startup DNA
   (strong signals). She's missing Docker but can learn quickly.
   ```

7. **Interview Alice** using AI-generated questions:
   - Tell us about your biggest impact with React
   - How would you approach Docker if starting from scratch?
   - Describe your process for shipping features solo

---

## 🔐 Security Notes

- Passwords hashed with bcrypt (never stored in plaintext)
- JWTs expire after 60 minutes
- Each user can only see their own resumes + results
- .env file with API keys is git-ignored (never committed)

---

## 📚 API Docs

Once backend is running, visit:
**http://localhost:8000/docs** ← Swagger UI

Try all endpoints interactively:
- `POST /auth/signup` — Create account
- `POST /auth/login` — Get access token
- `POST /hiring/upload-resumes` — Upload PDFs
- `POST /hiring/analyze` — Analyze + rank
- `GET /hiring/resumes` — List uploads
- `DELETE /hiring/resumes/{id}` — Delete

---

## 📦 What's Different from v1

| Feature | v1 | v2 |
|---|---|---|
| Score breakdown | ❌ None | ✅ 5 dimensions |
| Hiring recommendation | ❌ No | ✅ Strong Hire / Hire / Consider / Reject |
| Missing skills | ❌ No | ✅ Highlighted with penalties |
| Red flags | ❌ No | ✅ Detected (gaps, job hopping) |
| Startup signals | ❌ No | ✅ Ownership, generalist, founder DNA |
| Interview questions | ❌ No | ✅ 3 AI-generated per candidate |
| Final ranking table | ❌ No | ✅ Trophy-style summary |
| Best candidate pick | ❌ No | ✅ AI-explained |
| Persistent ranking | ❌ Lost on refresh | ✅ Saved to DB |
| Results export | ❌ No | ✅ CSV download |

---

## 🎓 How Scoring Works

**Example: Alice applying for Senior React Engineer role**

```json
{
  "name": "Alice",
  "score_breakdown": {
    "skills_score": 95,        // Has React, TypeScript, Node, PostgreSQL, AWS
    "experience_score": 90,    // 5 years total, 4 senior roles
    "education_score": 85,     // BS Computer Science from good school
    "projects_score": 88,      // 3 impactful open-source contributions
    "culture_fit_score": 92    // Founded a side project, generalist, built 0→1
  },
  "overall_score": 90.5,       // Weighted average
  "hiring_recommendation": "Strong Hire",
  "recommendation_reason": "Alice is an exceptional fit with deep React expertise, proven leadership, and clear startup DNA. Hire immediately."
}
```

---

## 💡 Tips

**For best results**:
1. ✍️ Write detailed job descriptions (AI learns from them)
2. 📄 Use PDF resumes (cleaner than Word)
3. 🎯 Set required skills (AI penalizes missing ones)
4. 📊 Review the interview questions (customize before calling candidate)
5. 💾 Export results to keep a record

---

## 📞 Support

If something breaks:
1. Check `.env` — make sure GROQ_API_KEY is correct
2. Restart backend: `python -m uvicorn main:app --reload`
3. Clear browser cache (Ctrl+Shift+Delete)
4. Check the API logs for errors
5. Verify both backend & frontend are running

---

**Built for founders. By founders.**

Made with ❤️ for early-stage startups hiring their first engineers.
