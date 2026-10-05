# Founder AI Assistant - Support Agent Subsystem

A local Retrieval-Augmented Generation (RAG) Support Agent designed for start-up founders. This subsystem is a key module of the Founder AI Assistant startup operating system. It allows founders to upload PDF documents, parse, split, and index pages in a local FAISS vector store, ask questions, and retrieve page-level source citations securely.

---

## Technical Stack
* **Frontend**: Next.js 15 (with App Router), TypeScript, Tailwind CSS, Lucide Icons. Live SSE streaming chat UI.
* **Backend**: FastAPI, Python 3.11.
* **Database**: PostgreSQL (SQLAlchemy ORM).
* **Vector Store**: Local FAISS CPU index.
* **AI/Agentic RAG**: LangChain + **LangGraph** multi-tool agent, LangHuggingFace (`all-MiniLM-L6-v2` embeddings), LangGroq/OpenAI (LLM options), DuckDuckGo web search.
* **Memory & Cache**: Redis (session-level conversation history and queries, with safe dictionary fallback).

---

## Agentic RAG Architecture

The chat pipeline (`backend/app/services/agent_service.py`) is a **LangGraph** ReAct-style agent, not a single-shot RAG call. On every question, an `agent` node (LLM bound to tools) decides what to do next, and a `tools` node executes whichever tool(s) it picks; the two nodes loop until the LLM responds without further tool calls:

```
        ┌────────┐   tool call    ┌────────┐
 START →│ agent  │ ─────────────► │ tools  │
        └────────┘ ◄───────────── └────────┘
             │        tool result
             │ no tool call
             ▼
            END
```

**Tools available to the agent** (`backend/app/services/agent_tools.py`):
1. `search_knowledge_base` — FAISS similarity search over the user's uploaded documents. Always tried first.
2. `web_search` — DuckDuckGo web search (no API key required), used when the knowledge base doesn't have the answer.
3. `create_support_ticket` — writes a row to the new `support_tickets` table, used only when neither source resolves the question or the user explicitly asks to escalate to a human.

Each tool call/response is tracked in a per-request `AgentToolContext`, so citations (document pages *and* web URLs) and any created ticket are collected and returned alongside the final answer — without the LLM needing to format them itself.

**Streaming**: `POST /api/chat/stream` uses `graph.astream_events()` to emit Server-Sent Events as the agent works: `tool_start` / `tool_end` (so the UI can show "Searching your documents…", "Searching the web…", "Creating a support ticket…") and `token` events for the live-typed answer, followed by `sources`, an optional `ticket`, and a final `done` event. `POST /api/chat` remains available as a plain non-streaming JSON endpoint (same agent, blocking call).

Toggle agent behavior via `backend/app/core/config.py` / environment variables:
* `AGENT_WEB_SEARCH_ENABLED` (default `true`)
* `AGENT_TICKET_TOOL_ENABLED` (default `true`)
* `AGENT_RECURSION_LIMIT` (default `10`) — max agent↔tool loop steps
* `AGENT_KB_TOP_K` (default `5`) — chunks retrieved per knowledge-base search

---

## Folder Architecture

```text
support_agent/
│
├── backend/
│   ├── app/
│   │   ├── api/             # Route handlers & deps injection
│   │   ├── core/            # JWT config & App settings 
│   │   ├── database/        # Engine & Session initialization
│   │   ├── models/          # SQLAlchemy Database Models
│   │   ├── repositories/    # User, Document, & Chat database operations
│   │   ├── schemas/         # Pydantic Schemas for JSON I/O validation
│   │   ├── services/        # PDF parse, Text split, FAISS, Redis, & RAG
│   │   └── main.py          # App boot & Database auto-migration hook
│   ├── tests/               # Pytest suite
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/
│   ├── app/                 # Next.js Pages (Chat, Docs, Login, Signup)
│   ├── components/          # Navigation Sidebars & Citations drawers
│   ├── hooks/               # useAuth Session handling context
│   ├── services/            # Client HTTP API Wrapper
│   ├── types/               # TypeScript Definitions
│   ├── Dockerfile
│   └── package.json
│
├── docker-compose.yml       # Orchestrates app, database, and Redis cache
└── README.md
```

---

## Database Schemas & Models

The subsystem manages four key entities using PostgreSQL and SQLAlchemy:

1. **`users`**: Manages signup, login, and hashes passwords using bcrypt.
   * `id` (UUID, Primary Key)
   * `name` (String)
   * `email` (String, Unique Index)
   * `password_hash` (String)
   * `created_at` (Timestamp)

2. **`documents`**: Tracks user-uploaded PDFs and indexing statuses.
   * `id` (UUID, Primary Key)
   * `user_id` (Foreign Key to users, CASCADE)
   * `filename` (String)
   * `file_path` (String)
   * `file_size` (Integer)
   * `status` (String: processing, processed, failed)
   * `created_at` (Timestamp)

3. **`document_chunks`**: Stores exact text segments linked to their source document pages.
   * `id` (UUID, Primary Key)
   * `document_id` (Foreign Key to documents, CASCADE)
   * `chunk_id` (String, Unique indexing key)
   * `page_number` (Integer)
   * `content` (Text)
   * `created_at` (Timestamp)

4. **`chat_history`**: Persists conversation questions, answers, and citation references.
   * `id` (UUID, Primary Key)
   * `user_id` (Foreign Key to users, CASCADE)
   * `question` (Text)
   * `answer` (Text)
   * `sources` (JSON array: `[{"document": "Filename.pdf", "page": 12, "type": "document"}]` or `[{"document": "Page Title", "page": 0, "type": "web", "url": "https://..."}]`)
   * `timestamp` (Timestamp)

5. **`support_tickets`**: Escalation tickets, created automatically by the agent's `create_support_ticket` tool.
   * `id` (UUID, Primary Key)
   * `user_id` (Foreign Key to users, CASCADE)
   * `subject` (String)
   * `description` (Text)
   * `source_question` (Text, nullable) — the chat question that triggered the escalation
   * `status` (String: open, in_progress, resolved)
   * `created_at` (Timestamp)

---

## Setup & Running Guide

### Option 1: Docker Compose (Recommended)

To run the entire ecosystem (Next.js frontend, FastAPI backend, PostgreSQL, and Redis) with one command, make sure Docker is running on your host machine and follow these steps:

1. Create a `.env` file in the root directory:
   ```env
   # Set LLM provider (openai or groq)
   LLM_PROVIDER=openai
   
   # Add your key
   OPENAI_API_KEY=sk-your-openai-api-key
   # OR GROQ_API_KEY=gsk_your-groq-api-key
   ```
2. Build and launch services:
   ```bash
   docker-compose up --build
   ```
3. Access the interfaces:
   * **Next.js Web Frontend**: http://localhost:3000
   * **FastAPI Backend Documentation**: http://localhost:8000/docs
   * **PostgreSQL Database**: Port `5432`
   * **Redis Server**: Port `6379`

---

### Option 2: Running Locally (Manual Setup)

#### Step 1: Backend Setup
1. Move to the backend folder:
   ```bash
   cd backend
   ```
2. Create and activate a Python virtual environment:
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```
3. Install package requirements:
   ```bash
   pip install -r requirements.txt
   ```
4. Create a `.env` file inside `backend/` and populate variables:
   ```env
   # Database connection configuration (auto-migrated on startup)
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=postgres
   POSTGRES_HOST=localhost
   POSTGRES_PORT=5432
   POSTGRES_DB=support_agent

   # LLM settings
   LLM_PROVIDER=openai
   OPENAI_API_KEY=sk-xxxx...
   # OR GROQ_API_KEY=gsk-xxxx...
   ```
5. Run the FastAPI development server:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

#### Step 2: Frontend Setup
1. Move to the frontend folder:
   ```bash
   cd ../frontend
   ```
2. Install npm dependencies:
   ```bash
   npm install
   ```
3. Run the Next.js development server:
   ```bash
   npm run dev
   ```
4. Open http://localhost:3000 in your browser.

---

## Running the Automated Test Suite

We use `pytest` for unit, API route, and pipeline integration tests.

1. Ensure your backend virtual environment is active:
   ```bash
   cd backend
   # Activate virtualenv if not already done
   ```
2. Execute the test suite using pytest:
   ```bash
   pytest -v
   ```
3. The tests run utilizing a fully mock-wrapped SQLite in-memory database (`sqlite:///:memory:`), keeping the local postgres databases unaffected.
