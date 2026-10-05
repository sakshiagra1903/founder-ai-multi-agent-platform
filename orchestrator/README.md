# Founder AI — Collaborative Multi-Agent Orchestrator

This is the **deeper, collaborative** version: not a router that picks one
agent and stops, but a **Supervisor Agent** that treats all 3 existing agents
as tools it can call — one or more, in any order, chaining results — plus
shared memory across conversation turns.

None of the 3 original apps (`founder-ai-feedback-agent`, `founder-ai-final`,
`support_agent`) are modified. Everything below only calls their existing
HTTP APIs.

## Architecture

```
                     ┌─────────────────────────────┐
POST /api/orchestrate│   Supervisor (ReAct agent)  │
   { message,        │   loop: agent <-> tools      │
     thread_id }  ──▶│   until it has enough info   │
                     └───────────┬─────────────────┘
                                 │ can call, in any order / combination:
              ┌──────────────────┼───────────────────┬─────────────────┐
              ▼                  ▼                   ▼                 ▼
      feedback_agent(query) support_agent(query) hiring_list_resumes() hiring_analyze(ids, jd)
              │                  │                   │                 │
              ▼                  ▼                   ▼                 ▼
   feedback-backend      support-backend        hiring-backend    hiring-backend
   /api/v1/chat          /api/chat              /hiring/resumes   /hiring/analyze
   (unchanged)           (unchanged)            (unchanged)       (unchanged)
```

### What "collaborative" actually means here

- The supervisor is a **LangGraph prebuilt ReAct agent**
  (`langgraph.prebuilt.create_react_agent`) — its graph is a loop:
  `agent -> tools -> agent -> tools -> ... -> END`. It keeps calling tools
  until it decides it has enough information, then produces one final answer.
- It can call **more than one agent per question**. Example: *"Best resume
  for our support-engineer role, and have customers complained about slow
  support responses recently?"* → it calls `hiring_list_resumes`, then
  `hiring_analyze`, then `feedback_agent`, then combines all three results
  into one recommendation — instead of only answering the hiring half.
- It can use one tool's output to shape the next tool call (true chaining,
  not just parallel fan-out).
- **Shared memory across turns**: pass the same `thread_id` on every request
  in a conversation and the supervisor remembers earlier turns *and* earlier
  tool results (via LangGraph's checkpointer). Omit `thread_id` to get a
  fresh one back each time.

## Auth (still unchanged, per-agent)

Each original app keeps its own separate login/JWT/User table. The caller
must log into whichever agent(s) it needs (same as before) and pass the
resulting JWTs as headers:

```
X-Feedback-Token, X-Hiring-Token, X-Support-Token
```

The supervisor only uses the token(s) needed for the tool(s) it decides to
call.

## Example request

```bash
curl -X POST http://localhost:8000/api/orchestrate \
  -H "Content-Type: application/json" \
  -H "X-Feedback-Token: <jwt>" \
  -H "X-Hiring-Token: <jwt>" \
  -d '{
        "message": "List my uploaded resumes, then tell me the best fit for a customer-support-engineer role, and check if customer feedback mentions slow support as a complaint.",
        "thread_id": "founder-123-session-1"
      }'
```

Response:
```json
{
  "answer": "...(synthesized answer combining hiring_analyze + feedback_agent results)...",
  "tools_used": ["hiring_list_resumes", "hiring_analyze", "feedback_agent"],
  "thread_id": "founder-123-session-1"
}
```

Send another request with the **same** `thread_id` and the supervisor still
remembers this context (e.g. "now compare candidate #2 to that").

## Running everything

Same as before — from the parent folder with all 4 project dirs + this
`docker-compose.yml`:

```bash
docker compose up --build
```

## Files

- `app/tools.py` — wraps the 3 backends as LangChain tools
  (`feedback_agent`, `support_agent`, `hiring_list_resumes`, `hiring_analyze`)
- `app/supervisor.py` — the collaborative ReAct supervisor + memory
  (`MemorySaver` checkpointer; swap for `SqliteSaver`/Postgres in production)
- `app/clients.py` — raw HTTP calls to the 3 existing backends
- `app/llm.py` / `app/config.py` — LLM + settings (Groq/OpenAI)
- `app/main.py` — FastAPI: `/api/orchestrate` (supervisor) + hiring
  upload/analyze proxy routes (multipart upload still needs a direct route,
  since tools only take text/JSON)

## Notes & limits

- **Memory is in-process** (`MemorySaver`). If you run multiple orchestrator
  replicas or restart the container, in-flight conversation memory is lost.
  For production, use `langgraph.checkpoint.sqlite.SqliteSaver` or a
  Postgres-backed checkpointer instead — same API, just swap the one line
  in `app/supervisor.py`.
- **Resume upload** is still a plain file-upload proxy (`/api/hiring/upload-resumes`),
  not a tool — the supervisor can't literally receive file bytes through a
  reasoning loop. Upload first, then ask the supervisor to analyze/compare.
- The supervisor makes real decisions with an LLM, so it can occasionally
  call a tool unnecessarily or skip one it should have called — that's
  inherent to ReAct-style agents, not a bug in the wiring. Tune the system
  prompt in `app/supervisor.py` if you see consistent mis-routing.
