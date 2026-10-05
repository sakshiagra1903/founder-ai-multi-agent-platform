"""
Wraps the 3 existing (unchanged) agent backends as LangChain tools.

This is what makes the system genuinely *collaborative*: the supervisor
agent below (app/supervisor.py) can call these tools one or more times, in
any order, read what came back, and decide to call another tool with that
information before giving a final combined answer — instead of picking
exactly one agent and stopping.

Tools are built per-request (via `build_agent_tools`) because each call
needs the specific user's JWTs for each downstream agent — nothing about the
original agents' code changes, we're just calling their existing endpoints.
"""
from __future__ import annotations

from typing import Optional

from langchain_core.tools import tool

from app.clients import (
    call_feedback_chat,
    call_support_chat,
    call_hiring_analyze,
    call_hiring_list_resumes,
    AgentCallError,
)


def build_agent_tools(tokens: dict[str, Optional[str]]) -> list:
    feedback_token = tokens.get("feedback")
    hiring_token = tokens.get("hiring")
    support_token = tokens.get("support")

    @tool
    async def feedback_agent(query: str) -> str:
        """Ask the Feedback Agent about customer feedback: sentiment, complaints,
        feature requests, recurring topics/themes, or analytics/trends drawn from
        the company's collected customer feedback. Input: a natural-language
        question, e.g. "what are the top 3 complaints this month?"."""
        try:
            result = await call_feedback_chat(query, feedback_token)
            return result.get("answer", "(feedback agent returned no answer)")
        except AgentCallError as e:
            return f"[feedback_agent error] {e}"

    @tool
    async def support_agent(query: str) -> str:
        """Ask the Support Agent a general product/company support question. It can
        search the knowledge base, search the web, and/or create a human support
        ticket. Input: a natural-language question or support request."""
        try:
            result = await call_support_chat(query, support_token)
            answer = result.get("answer", "(support agent returned no answer)")
            ticket = result.get("ticket")
            if ticket:
                answer += f"\n(Support ticket created: {ticket.get('id')} - {ticket.get('subject')})"
            return answer
        except AgentCallError as e:
            return f"[support_agent error] {e}"

    @tool
    async def hiring_list_resumes() -> str:
        """List resumes already uploaded to the Hiring Agent for the current user,
        with their resume_id and filename. Use this before hiring_analyze to find
        which resume_ids to analyze."""
        try:
            resumes = await call_hiring_list_resumes(hiring_token)
            if not resumes:
                return "No resumes uploaded yet. Ask the user to upload resumes first."
            return "\n".join(f"id={r['id']} filename={r['original_filename']}" for r in resumes)
        except AgentCallError as e:
            return f"[hiring_agent error] {e}"

    @tool
    async def hiring_analyze(resume_ids: list[int], job_description: str) -> str:
        """Analyze specific uploaded resumes against a job description using the
        Hiring Agent's evaluation pipeline (skills/experience/education/culture-fit
        scoring + ranking + interview questions). Get resume_ids first from
        hiring_list_resumes. Input: resume_ids (list of ints) and job_description
        (free text)."""
        try:
            result = await call_hiring_analyze(
                {"resume_ids": resume_ids, "job_description": job_description}, hiring_token
            )
            best = result.get("best_candidate_name")
            reason = result.get("best_candidate_reason", "")
            ranking = result.get("final_ranking", [])
            ranking_str = "\n".join(
                f"#{row['rank']} {row['name']} — score {row['overall_score']} ({row['hiring_recommendation']})"
                for row in ranking
            )
            return (
                f"Best candidate: {best}. Reason: {reason}\n\nFull ranking:\n{ranking_str}"
            )
        except AgentCallError as e:
            return f"[hiring_agent error] {e}"

    return [feedback_agent, support_agent, hiring_list_resumes, hiring_analyze]
