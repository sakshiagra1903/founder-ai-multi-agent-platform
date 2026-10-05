"""
Thin HTTP proxy clients to the 3 existing agent backends.

None of these change anything inside the original apps — they just call the
APIs that already exist (chat_agent_service, agent_service, HiringService)
exactly as a normal frontend would, using the JWT the user already got from
that specific app's own /auth/login endpoint.

Since each app has its own separate auth/User table, the orchestrator does
not try to unify login — the caller (frontend) must have a token for
whichever agent(s) it wants to use, and pass them through to /orchestrate.
"""
from __future__ import annotations

import time
from typing import Any, Optional

import httpx

from app.config import settings


class AgentCallError(Exception):
    def __init__(self, agent: str, status_code: int, detail: Any):
        self.agent = agent
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"{agent} agent call failed [{status_code}]: {detail}")


def _auth_headers(token: Optional[str]) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"} if token else {}


async def call_feedback_chat(message: str, token: Optional[str]) -> dict[str, Any]:
    url = settings.feedback_agent_url + settings.feedback_agent_chat_path
    async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as client:
        resp = await client.post(url, json={"message": message}, headers=_auth_headers(token))
    if resp.status_code >= 400:
        raise AgentCallError("feedback", resp.status_code, resp.text)
    return resp.json()


async def call_support_chat(question: str, token: Optional[str]) -> dict[str, Any]:
    url = settings.support_agent_url + settings.support_agent_chat_path
    async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as client:
        resp = await client.post(url, json={"question": question}, headers=_auth_headers(token))
    if resp.status_code >= 400:
        raise AgentCallError("support", resp.status_code, resp.text)
    return resp.json()


async def call_hiring_analyze(payload: dict[str, Any], token: Optional[str]) -> dict[str, Any]:
    """Hiring agent has no free-text chat endpoint — it works on uploaded
    resumes (/hiring/upload-resumes) + a structured /hiring/analyze request.
    This proxies the analyze step; resume upload has its own proxy route in
    main.py (upload_resumes_proxy) because it's multipart/form-data, not JSON.
    """
    url = settings.hiring_agent_url + settings.hiring_agent_analyze_path
    async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as client:
        resp = await client.post(url, json=payload, headers=_auth_headers(token))
    if resp.status_code >= 400:
        raise AgentCallError("hiring", resp.status_code, resp.text)
    return resp.json()


async def call_hiring_list_resumes(token: Optional[str]) -> list[dict[str, Any]]:
    url = settings.hiring_agent_url + "/hiring/resumes"
    async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as client:
        resp = await client.get(url, headers=_auth_headers(token))
    if resp.status_code >= 400:
        raise AgentCallError("hiring", resp.status_code, resp.text)
    return resp.json()


async def call_hiring_upload(files: list[tuple[str, bytes, str]], token: Optional[str]) -> dict[str, Any]:
    """files: list of (filename, content_bytes, content_type) tuples."""
    url = settings.hiring_agent_url + settings.hiring_agent_upload_path
    multipart = [("files", (fname, content, ctype)) for fname, content, ctype in files]
    async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as client:
        resp = await client.post(url, files=multipart, headers=_auth_headers(token))
    if resp.status_code >= 400:
        raise AgentCallError("hiring", resp.status_code, resp.text)
    return resp.json()


# ─────────────────────────────────────────────────────────────────────────
# Additions below this line are new, additive UI-support helpers used by the
# upgraded orchestrator console. They only ever call the 3 agents' EXISTING,
# unchanged endpoints (health/root, their own signup, their own login, their
# own upload routes) — no agent code is modified. See main.py for the routes
# that use these.
# ─────────────────────────────────────────────────────────────────────────

async def probe_agent_health(name: str, url: str, path: str) -> dict[str, Any]:
    """Best-effort reachability probe for one agent's own health/root route.
    Never raises — a failure just means the agent reports as offline. Used
    only for dashboard display, never to gate real agent calls.
    """
    started = time.monotonic()
    try:
        async with httpx.AsyncClient(timeout=settings.health_check_timeout_seconds) as client:
            resp = await client.get(url + path)
        latency_ms = round((time.monotonic() - started) * 1000)
        if resp.status_code < 400:
            return {"agent": name, "status": "online", "latency_ms": latency_ms}
        return {
            "agent": name,
            "status": "degraded",
            "latency_ms": latency_ms,
            "detail": f"HTTP {resp.status_code}",
        }
    except httpx.RequestError as e:
        return {"agent": name, "status": "offline", "latency_ms": None, "detail": str(e)}


async def call_feedback_register(payload: dict[str, Any]) -> dict[str, Any]:
    url = settings.feedback_agent_url + settings.feedback_agent_register_path
    async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as client:
        resp = await client.post(url, json=payload)
    if resp.status_code >= 400:
        raise AgentCallError("feedback", resp.status_code, resp.text)
    return resp.json()


async def call_feedback_login(email: str, password: str) -> dict[str, Any]:
    url = settings.feedback_agent_url + settings.feedback_agent_login_path
    async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as client:
        resp = await client.post(url, json={"email": email, "password": password})
    if resp.status_code >= 400:
        raise AgentCallError("feedback", resp.status_code, resp.text)
    return resp.json()


async def call_hiring_signup(payload: dict[str, Any]) -> dict[str, Any]:
    url = settings.hiring_agent_url + settings.hiring_agent_signup_path
    async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as client:
        resp = await client.post(url, json=payload)
    if resp.status_code >= 400:
        raise AgentCallError("hiring", resp.status_code, resp.text)
    return resp.json()


async def call_hiring_login(email: str, password: str) -> dict[str, Any]:
    url = settings.hiring_agent_url + settings.hiring_agent_login_path
    async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as client:
        resp = await client.post(url, json={"email": email, "password": password})
    if resp.status_code >= 400:
        raise AgentCallError("hiring", resp.status_code, resp.text)
    return resp.json()


async def call_support_signup(payload: dict[str, Any]) -> dict[str, Any]:
    url = settings.support_agent_url + settings.support_agent_signup_path
    async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as client:
        resp = await client.post(url, json=payload)
    if resp.status_code >= 400:
        raise AgentCallError("support", resp.status_code, resp.text)
    return resp.json()


async def call_support_login(email: str, password: str) -> dict[str, Any]:
    url = settings.support_agent_url + settings.support_agent_login_path
    async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as client:
        resp = await client.post(url, json={"email": email, "password": password})
    if resp.status_code >= 400:
        raise AgentCallError("support", resp.status_code, resp.text)
    return resp.json()


async def call_feedback_upload(
    file_tuple: tuple[str, bytes, str], token: Optional[str], auto_analyze: bool = True
) -> dict[str, Any]:
    fname, content, ctype = file_tuple
    url = settings.feedback_agent_url + settings.feedback_agent_upload_path
    async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as client:
        resp = await client.post(
            url,
            params={"auto_analyze": str(auto_analyze).lower()},
            files={"file": (fname, content, ctype)},
            headers=_auth_headers(token),
        )
    if resp.status_code >= 400:
        raise AgentCallError("feedback", resp.status_code, resp.text)
    return resp.json()


async def call_support_upload(file_tuple: tuple[str, bytes, str], token: Optional[str]) -> dict[str, Any]:
    fname, content, ctype = file_tuple
    url = settings.support_agent_url + settings.support_agent_upload_path
    async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as client:
        resp = await client.post(
            url,
            files={"file": (fname, content, ctype)},
            headers=_auth_headers(token),
        )
    if resp.status_code >= 400:
        raise AgentCallError("support", resp.status_code, resp.text)
    return resp.json()
