"""Graph state definitions for the LangGraph agents."""
from __future__ import annotations

from typing import Annotated, Any, TypedDict

from langgraph.graph.message import add_messages


class ChatAgentState(TypedDict):
    """State for the conversational RAG+tools chat agent."""
    messages: Annotated[list, add_messages]
    company_name: str
    steps_taken: int


class InsightAgentState(TypedDict, total=False):
    """State for the multi-step insight/report generation agent."""
    company_id: str
    company_name: str
    insight_types: list[str]          # which sections to produce this run
    analytics: dict[str, Any]         # aggregate numbers (from analytics_service)
    rag_examples: list[dict]          # retrieved qualitative feedback snippets
    executive_summary: str
    root_cause: str
    recommendations: str
    final_report: str
    errors: list[str]
