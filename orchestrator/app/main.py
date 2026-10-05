"""
Founder AI - Multi-Agent Orchestrator

Wraps the 3 existing, UNCHANGED agent apps (feedback, hiring, support) behind
a single entry point. This service does not contain any agent logic itself —
it only classifies the query (router LLM) and forwards it to whichever
agent's own existing API already handles it.

Each of the 3 original apps keeps running exactly as before, on its own port,
with its own DB, its own auth, its own LangGraph agent code untouched.
"""
from __future__ import annotations

import asyncio
import os
import uuid
from typing import Optional

from fastapi import FastAPI, UploadFile, File, Form, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, EmailStr

from app.config import settings
from app.supervisor import run_supervisor
from app.clients import (
    call_hiring_upload,
    call_hiring_analyze,
    call_hiring_list_resumes,
    call_hiring_signup,
    call_hiring_login,
    call_feedback_register,
    call_feedback_login,
    call_feedback_upload,
    call_support_signup,
    call_support_login,
    call_support_upload,
    probe_agent_health,
    AgentCallError,
)

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")

app = FastAPI(
    title=settings.app_name,
    description=(
        "Collaborative multi-agent supervisor for the feedback / hiring / "
        "support agents — can call multiple agents per query and chain their "
        "results together."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class OrchestrateRequest(BaseModel):
    message: str
    thread_id: Optional[str] = None  # same thread_id across turns = shared memory


class OrchestrateResponse(BaseModel):
    answer: str
    tools_used: list[str] = []
    thread_id: str


@app.post("/api/orchestrate", response_model=OrchestrateResponse)
async def orchestrate(
    payload: OrchestrateRequest,
    x_feedback_token: Optional[str] = Header(default=None),
    x_hiring_token: Optional[str] = Header(default=None),
    x_support_token: Optional[str] = Header(default=None),
    x_thread_id: Optional[str] = Header(default=None),
):
    """
    Single entry point for the founder's chat UI, backed by a collaborative
    supervisor agent (see app/supervisor.py) that can call one or more of the
    3 existing agents' APIs — in any order, chaining results — instead of
    picking just one.

    The caller must have already logged into whichever underlying agent(s)
    it needs (each agent's own /auth/login is unchanged) and pass those JWTs
    through as headers here:
      X-Feedback-Token, X-Hiring-Token, X-Support-Token

    Pass the same `thread_id` (body field or X-Thread-Id header) on every
    request in a conversation to keep shared memory across turns; omit it to
    get a fresh one back each time.
    """
    if not payload.message.strip():
        raise HTTPException(status_code=400, detail="message cannot be empty")

    thread_id = payload.thread_id or x_thread_id or str(uuid.uuid4())
    tokens = {
        "feedback": x_feedback_token,
        "hiring": x_hiring_token,
        "support": x_support_token,
    }

    result = await run_supervisor(payload.message, tokens, thread_id)

    return OrchestrateResponse(
        answer=result["answer"],
        tools_used=result["tools_used"],
        thread_id=thread_id,
    )


# ── Hiring agent proxy routes (no free-text chat endpoint upstream, so the
#    orchestrator exposes its two real endpoints — upload + analyze — as-is) ──

@app.post("/api/hiring/upload-resumes")
async def upload_resumes_proxy(
    files: list[UploadFile] = File(...),
    x_hiring_token: Optional[str] = Header(default=None),
):
    file_tuples = [(f.filename, await f.read(), f.content_type) for f in files]
    try:
        return await call_hiring_upload(file_tuples, x_hiring_token)
    except AgentCallError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@app.post("/api/hiring/analyze")
async def analyze_proxy(
    payload: dict,
    x_hiring_token: Optional[str] = Header(default=None),
):
    try:
        return await call_hiring_analyze(payload, x_hiring_token)
    except AgentCallError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


# Read-only proxy for the Hiring workspace's resume list (the supervisor's
# hiring_list_resumes tool already calls this same hiring-backend route
# internally — this just exposes it directly to the UI too).
@app.get("/api/hiring/resumes")
async def list_resumes_proxy(
    x_hiring_token: Optional[str] = Header(default=None),
):
    try:
        return await call_hiring_list_resumes(x_hiring_token)
    except AgentCallError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "app": settings.app_name,
        "downstream": {
            "feedback_agent": settings.feedback_agent_url,
            "hiring_agent": settings.hiring_agent_url,
            "support_agent": settings.support_agent_url,
        },
    }


# ── Aggregated agent status for the dashboard (new, additive; read-only) ──
# Pings each of the 3 agents' own health/root route in parallel. Never calls
# into agent business logic, never mutates anything, and never blocks the
# real /api/orchestrate path — this endpoint exists purely so the UI can show
# real online/offline status instead of a hard-coded value.
@app.get("/api/agents/health")
async def agents_health():
    results = await asyncio.gather(
        probe_agent_health("feedback", settings.feedback_agent_url, settings.feedback_agent_health_path),
        probe_agent_health("hiring", settings.hiring_agent_url, settings.hiring_agent_health_path),
        probe_agent_health("support", settings.support_agent_url, settings.support_agent_health_path),
    )
    agents = {r["agent"]: r for r in results}
    online_count = sum(1 for r in results if r["status"] == "online")
    return {
        "orchestrator": "healthy",
        "agents": agents,
        "online_count": online_count,
        "total_count": len(results),
    }


# ── Unified auth convenience layer (new, additive) ──────────────────────────
# Each of the 3 agents keeps its own separate user table and login endpoint
# exactly as before (see README) — this does NOT change that. It only saves
# the founder from signing into 3 separate apps by calling each agent's own
# existing /auth endpoint with the same credentials and combining whichever
# tokens come back. If the founder only has an account on some of the agents,
# this reports which ones connected and which didn't — it never fabricates a
# token for an agent that rejected the credentials.
class UnifiedRegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    company_name: Optional[str] = None


class UnifiedLoginRequest(BaseModel):
    email: EmailStr
    password: str


def _connection_result(agent: str, token: Optional[str], error: Optional[str] = None) -> dict:
    return {"agent": agent, "connected": token is not None, "token": token, "error": error}


@app.post("/api/auth/register")
async def unified_register(payload: UnifiedRegisterRequest):
    """Best-effort registration across all 3 agents, then logs in to collect
    tokens. Each agent call is independent — one agent already having this
    email (e.g. re-running register) does not block the others; that agent
    simply falls through to the login attempt below."""

    async def register_one(coro, agent: str):
        try:
            await coro
        except AgentCallError:
            pass  # likely "already registered" — fall through to login
        except Exception:
            pass

    await asyncio.gather(
        register_one(
            call_feedback_register(
                {
                    "email": payload.email,
                    "password": payload.password,
                    "full_name": payload.name,
                    "company_name": payload.company_name,
                }
            ),
            "feedback",
        ),
        register_one(call_hiring_signup({"name": payload.name, "email": payload.email, "password": payload.password}), "hiring"),
        register_one(call_support_signup({"name": payload.name, "email": payload.email, "password": payload.password}), "support"),
    )

    return await unified_login(UnifiedLoginRequest(email=payload.email, password=payload.password))


@app.post("/api/auth/login")
async def unified_login(payload: UnifiedLoginRequest):
    async def try_login(coro, agent: str, token_field: str = "access_token"):
        try:
            result = await coro
            return _connection_result(agent, result.get(token_field))
        except AgentCallError as e:
            return _connection_result(agent, None, error=f"HTTP {e.status_code}")
        except Exception as e:
            return _connection_result(agent, None, error=str(e))

    feedback_res, hiring_res, support_res = await asyncio.gather(
        try_login(call_feedback_login(payload.email, payload.password), "feedback"),
        try_login(call_hiring_login(payload.email, payload.password), "hiring", token_field="access_token"),
        try_login(call_support_login(payload.email, payload.password), "support"),
    )

    connections = [feedback_res, hiring_res, support_res]
    connected_count = sum(1 for c in connections if c["connected"])
    if connected_count == 0:
        raise HTTPException(status_code=401, detail="Invalid credentials on all agents.")

    return {
        "email": payload.email,
        "connected_count": connected_count,
        "total_count": len(connections),
        "tokens": {
            "feedback": feedback_res["token"],
            "hiring": hiring_res["token"],
            "support": support_res["token"],
        },
        "connections": connections,
    }


# ── Feedback / Support upload proxies (new; mirrors the existing hiring ──
# ── upload proxy pattern already in this file, same-origin for the UI) ──
@app.post("/api/feedback/upload")
async def feedback_upload_proxy(
    file: UploadFile = File(...),
    auto_analyze: bool = Form(True),
    x_feedback_token: Optional[str] = Header(default=None),
):
    content = await file.read()
    try:
        return await call_feedback_upload(
            (file.filename, content, file.content_type), x_feedback_token, auto_analyze
        )
    except AgentCallError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@app.post("/api/support/upload")
async def support_upload_proxy(
    file: UploadFile = File(...),
    x_support_token: Optional[str] = Header(default=None),
):
    content = await file.read()
    try:
        return await call_support_upload((file.filename, content, file.content_type), x_support_token)
    except AgentCallError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


# ── UI ───────────────────────────────────────────────────────────────────
# The Founder AI Command Center is a single static page (vanilla HTML/CSS/JS)
# served directly by this FastAPI app, so every API call it makes is
# same-origin (no CORS needed for the console itself).
if os.path.isdir(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
async def console():
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.isfile(index_path):
        return FileResponse(index_path)
    return {"message": f"{settings.app_name} — see /docs", "docs": "/docs"}
