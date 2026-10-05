# 🧠 Founder AI — Feedback Intelligence Agent

A production-grade AI system for startup founders to analyze customer feedback, detect complaints, identify feature requests, and generate actionable business insights.

---

## 🚀 Quick Start (Docker — Recommended)

### Prerequisites
- Docker & Docker Compose installed
- Groq API key (free at https://console.groq.com)

### 1. Clone / unzip the project
```bash
cd founder-ai-feedback-agent
```

### 2. Set environment variables
```bash
cp backend/.env.example backend/.env
```

Edit `backend/.env` and set:
```
GROQ_API_KEY=your_groq_api_key_here
JWT_SECRET_KEY=any-random-secret-string
SECRET_KEY=another-random-secret-string
```

### 3. Start all services
```bash
docker-compose up --build
```

Services started:
| Service    | URL                          |
|------------|------------------------------|
| Frontend   | http://localhost:3000        |
| Backend API| http://localhost:8000        |
| API Docs   | http://localhost:8000/docs   |
| PostgreSQL | localhost:5432               |
| Redis      | localhost:6379               |

### 4. Use the app
1. Open http://localhost:3000
2. Register your account
3. Upload a feedback CSV file
4. View analytics on the dashboard
5. Chat with the AI about your feedback

---

## 🛠️ Local Development (Without Docker)

### Backend

```bash
cd backend

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy and configure env
cp .env.example .env
# Edit .env with your GROQ_API_KEY, DATABASE_URL, etc.

# Start PostgreSQL (via Docker or local install)
docker run -d --name pg -e POSTGRES_PASSWORD=password -e POSTGRES_DB=founder_ai_feedback -p 5432:5432 postgres:16-alpine

# Run database migrations (tables auto-created on startup)
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Configure environment
echo "NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1" > .env.local

# Start dev server
npm run dev
```

Open http://localhost:3000

---

## 🔄 Switching LLM Providers

Edit `backend/.env`:

```bash
# Use Groq (default — free tier, fastest)
LLM_PROVIDER=groq
GROQ_API_KEY=your_key
GROQ_MODEL=openai/gpt-oss-120b

# Use local Ollama (completely free, no API key)
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1

# Use HuggingFace
LLM_PROVIDER=huggingface
HUGGINGFACE_API_KEY=your_hf_token
HF_MODEL=meta-llama/Meta-Llama-3.1-8B-Instruct
```

---

## 📁 Feedback File Format

Upload CSV, XLSX, or JSON with these columns:

| Column          | Required | Description              |
|-----------------|----------|--------------------------|
| `feedback_text` | ✅ Yes   | The customer review text |
| `rating`        | No       | Score (1–5 or 1–10)      |
| `customer_id`   | No       | Customer identifier      |
| `feedback_id`   | No       | Unique feedback ID       |
| `date`          | No       | Feedback date            |

**Aliases accepted:** `text`, `comment`, `review` → `feedback_text` | `score`, `stars` → `rating`

### Sample CSV
```csv
feedback_id,customer_id,feedback_text,rating,date
1,c001,"The app keeps crashing during payment",1,2024-01-15
2,c002,"Love the new dashboard! Very intuitive",5,2024-01-16
3,c003,"Please add dark mode, it would be great",4,2024-01-17
4,c004,"Customer support took 5 days to respond",2,2024-01-18
5,c005,"Would love a mobile app for iOS",3,2024-01-19
```

---

## 🧪 Running Tests

```bash
cd backend

# Make sure test DB exists
createdb founder_ai_feedback_test  # or via psql

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/unit/test_preprocessing.py -v
pytest tests/api/test_auth.py -v
```

---

## 🏗️ Architecture Overview

```
Frontend (Next.js 15)
    ↓  JWT + REST
FastAPI Gateway (Python 3.11)
    ↓
┌─────────────────────────────────────┐
│         NLP Analysis Pipeline       │
│  Sentiment    → HuggingFace Model   │
│  Complaints   → Sentence Transformers│
│  Features     → Rule-based NLP      │
│  Topics       → BERTopic / LDA      │
└─────────────────────────────────────┘
    ↓
AI Insight Engine (Groq Llama 3.3 70B)
    ↓
PostgreSQL + Redis
```

**Cost Optimization:**
- Sentiment: local HuggingFace model (zero API cost)
- Complaints: Sentence Transformers (zero API cost)
- Feature detection: Rule-based NLP (zero API cost)
- Topic modeling: BERTopic/LDA (zero API cost)
- LLM used ONLY for: summaries, insights, chat (Groq free tier)

---

## 📡 API Endpoints

| Method | Endpoint                    | Description                  |
|--------|-----------------------------|------------------------------|
| POST   | /api/v1/auth/register       | Register new account         |
| POST   | /api/v1/auth/login          | Login, get JWT tokens        |
| GET    | /api/v1/auth/me             | Get current user             |
| POST   | /api/v1/feedback/upload     | Upload feedback file         |
| GET    | /api/v1/feedback            | List feedback records        |
| GET    | /api/v1/analytics/dashboard | Full dashboard analytics     |
| GET    | /api/v1/analytics/sentiment | Sentiment summary            |
| GET    | /api/v1/analytics/complaints| Top complaints               |
| GET    | /api/v1/analytics/features  | Top feature requests         |
| GET    | /api/v1/analytics/trend     | Sentiment trend over time    |
| POST   | /api/v1/insights/generate   | Generate AI insight          |
| GET    | /api/v1/insights            | List all insights            |
| POST   | /api/v1/chat                | Chat with AI about feedback  |
| POST   | /api/v1/reports             | Generate PDF/JSON report     |
| GET    | /api/v1/reports/{id}/download | Download PDF report        |

Full interactive docs: http://localhost:8000/docs

---

## 🤖 Agentic AI (LangGraph + RAG)

The AI layer is now a real agentic system, not single-shot prompts:

- **RAG (ChromaDB)** — every piece of analyzed feedback is embedded (local
  `sentence-transformers`, free) and stored in a per-company Chroma
  collection (`app/services/rag/vector_store_service.py`). This happens
  automatically at the end of the analysis pipeline
  (`app/services/analysis_pipeline.py`), so chat/insights always have
  fresh, real customer quotes to ground their answers in — not just
  aggregate numbers.

- **Chat Agent** (`app/services/agents/chat_agent.py`) — a LangGraph
  tool-calling ReAct loop. The LLM decides on its own whether to call
  `search_feedback` (RAG), `get_dashboard_analytics`,
  `get_top_complaints`, `get_sentiment_trend`, etc., possibly across
  several turns, before answering. Conversation memory persists per
  founder via a LangGraph checkpointer, so follow-ups work naturally.

- **Insight/Report Agent** (`app/services/agents/insight_agent.py`) — a
  multi-node `StateGraph` pipeline:
  `fetch_analytics → rag_retrieve → executive_summary → root_cause → recommendations → synthesize`.
  Each generation step sees both the aggregate numbers *and* real
  retrieved customer quotes, and later steps see earlier steps' output
  (root cause reads the executive summary already written, etc.), so the
  sections build on each other instead of being generated in isolation.
  Powers both `POST /api/v1/insights/generate` (one section) and
  `POST /api/v1/reports` (full report, all sections).

- **Tools** (`app/services/agents/tools.py`) — all tools are bound per
  request to `(company_id, db_session)` via closures, so the LLM only ever
  sees tool names/descriptions/args — never a session or company id — and
  can't cross into another company's data no matter what it's prompted to do.

```python
# Example: calling the chat agent directly (e.g. from a script or another service)
from app.services.agents.chat_agent import chat_agent_service

result = await chat_agent_service.chat(
    message="Why is sentiment dropping this month?",
    company_id=company.id,
    user_id=user.id,
    company_name=company.name,
    db=db_session,
)
print(result["answer"], result["tools_used"])
```

---

## 🔧 Environment Variables Reference

| Variable              | Default                    | Description                   |
|-----------------------|----------------------------|-------------------------------|
| `LLM_PROVIDER`        | `groq`                     | groq / ollama / huggingface   |
| `GROQ_API_KEY`        | —                          | Get free at console.groq.com  |
| `GROQ_MODEL`          | `openai/gpt-oss-120b`  | Primary LLM model             |
| `GROQ_FAST_MODEL`     | `openai/gpt-oss-20b`     | Fast model for simple tasks   |
| `SENTIMENT_MODEL`     | `cardiffnlp/twitter-roberta-base-sentiment-latest` | HuggingFace sentiment model |
| `EMBEDDING_MODEL`     | `sentence-transformers/all-MiniLM-L6-v2` | Embedding model |
| `TOPIC_MODEL_TYPE`    | `bertopic`                 | bertopic or lda               |
| `CHROMA_PERSIST_DIR`  | `./chroma_data`            | Where ChromaDB stores vectors |
| `RAG_TOP_K`           | `8`                        | Feedback snippets retrieved per RAG query |
| `AGENT_MAX_STEPS`     | `6`                        | Max tool-call loops for the chat agent |
| `CHAT_MEMORY_TURNS`   | `10`                       | Conversation turns kept in agent memory |
| `DATABASE_URL`        | postgres localhost         | Async PostgreSQL URL          |
| `REDIS_URL`           | redis localhost            | Redis connection URL          |
| `JWT_SECRET_KEY`      | —                          | Change in production!         |
| `MAX_UPLOAD_SIZE_MB`  | `50`                       | Max file upload size          |

---

## 📦 Tech Stack

| Layer       | Technology                                    |
|-------------|-----------------------------------------------|
| Frontend    | Next.js 15, TypeScript, Tailwind, Recharts    |
| Backend     | FastAPI, Python 3.11, SQLAlchemy 2.0          |
| Database    | PostgreSQL 16                                 |
| Cache       | Redis 7                                       |
| Auth        | JWT (python-jose + passlib)                   |
| Sentiment   | HuggingFace Transformers (local inference)    |
| Embeddings  | Sentence Transformers (all-MiniLM-L6-v2)      |
| Topics      | BERTopic + sklearn LDA                        |
| LLM         | Groq (Llama 3.3 70B) / Ollama / HuggingFace  |
| Agentic AI  | LangGraph (tool-calling agent + multi-step insight pipeline) |
| RAG         | ChromaDB (per-company vector collections)     |
| PDF         | ReportLab                                     |
| Tasks       | Celery + Redis                                |
| Container   | Docker + Docker Compose                       |
| Testing     | Pytest + pytest-asyncio                       |

---

## 🆘 Troubleshooting

**"No company associated" error**
→ Make sure you include `company_name` when registering.

**Sentiment model slow first run**
→ HuggingFace models download on first use (~250MB). Subsequent runs are instant.

**Groq rate limit**
→ Switch to `GROQ_FAST_MODEL=openai/gpt-oss-20b` for lighter usage, or use Ollama locally.

**Database connection refused**
→ Ensure PostgreSQL is running: `docker-compose ps`

**BERTopic install fails**
→ Try: `pip install bertopic --no-deps` then install umap-learn, hdbscan separately.

**Chat agent gives generic answers / "no matching feedback found"**
→ RAG only has data for feedback that's finished the analysis pipeline. Upload
  feedback, wait for `status: analyzed`, then chat — new uploads are indexed
  into ChromaDB automatically as the last pipeline step.

**`ollama` / `huggingface` LLM_PROVIDER + chat agent tool calling**
→ The agentic chat agent calls `.bind_tools()` on the model, which needs
  OpenAI-style function calling support. Groq's Llama 3.x models support this;
  Ollama/HF endpoints may not depending on the model — Groq is recommended
  for the chat agent specifically.
