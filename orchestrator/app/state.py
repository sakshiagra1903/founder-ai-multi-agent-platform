"""
Shared LangGraph state for the orchestrator.

This does NOT re-implement any of the 3 agents' logic. Each agent
(feedback / hiring / support) keeps its own LangGraph graph, its own RAG
pipeline, its own DB and auth exactly as it already is. This state is only
used by the *routing* graph that decides which existing backend to call.
"""
from __future__ import annotations

from typing import Any, Literal, Optional, TypedDict

AgentName = Literal["feedback", "hiring", "support", "unknown"]


class OrchestratorState(TypedDict, total=False):
    # input
    user_query: str
    tokens: dict[str, Optional[str]]   # {"feedback": jwt_or_None, "hiring": ..., "support": ...}

    # routing
    selected_agent: AgentName
    router_reasoning: str

    # output
    agent_status_code: int
    agent_response: dict[str, Any]
    final_answer: str
    error: Optional[str]
