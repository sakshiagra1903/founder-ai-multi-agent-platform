"""
Agentic Chat — replaces the old single-shot "dump analytics into a prompt"
chat with a real LangGraph ReAct-style agent.

Flow:
    START -> agent (LLM decides: answer directly, or call a tool) -> {
        has tool_calls -> tools -> agent   (loop, up to agent_max_steps)
        no tool_calls   -> END
    }

The agent has access to RAG search (real feedback quotes) *and* structured
analytics tools (aggregate numbers), so it can ground its answers in both —
e.g. "negative sentiment is up 12% this month, and here's a customer quote
that shows why: ...".

Conversation memory persists per-thread via LangGraph's checkpointer, keyed
by (company_id, user_id), so follow-up questions ("what about last week?")
work without the founder re-explaining context.
"""
from __future__ import annotations

import uuid

from langchain_core.messages import AIMessage, SystemMessage, HumanMessage, ToolMessage
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.services.agents.state import ChatAgentState
from app.services.agents.tools import build_tools
from app.services.llm_service import llm_service

SYSTEM_PROMPT = """You are the Feedback Intelligence AI for {company_name}.

You help the founder understand their customers by combining:
- Aggregate analytics tools (sentiment %, top complaints, top features, topics, trends)
- Semantic search over raw customer feedback (search_feedback) for real quotes/examples

Guidelines:
- Ground every claim in tool output. Never invent numbers or quotes.
- Prefer calling search_feedback when the founder asks "why" something is happening —
  aggregate numbers show *what*, real feedback quotes show *why*.
- Be concise and business-focused. End with 1-2 concrete, actionable recommendations
  when the question calls for a decision.
- If tools return no relevant data, say so plainly rather than guessing.
"""

# One in-memory checkpointer per process. Good enough for this app's scale;
# swap for a Postgres/Redis checkpointer in production for multi-worker deployments.
_checkpointer = MemorySaver()


def _build_graph(company_id: uuid.UUID, db: AsyncSession):
    tools = build_tools(company_id, db)
    llm = llm_service.get_chat_model(fast=False)
    llm_with_tools = llm.bind_tools(tools)

    async def agent_node(state: ChatAgentState) -> dict:
        messages = state["messages"]
        if state.get("steps_taken", 0) == 0:
            system = SystemMessage(content=SYSTEM_PROMPT.format(company_name=state["company_name"]))
            messages = [system] + list(messages)
        response = await llm_with_tools.ainvoke(messages)
        return {"messages": [response], "steps_taken": state.get("steps_taken", 0) + 1}

    def should_continue(state: ChatAgentState) -> str:
        last = state["messages"][-1]
        if state.get("steps_taken", 0) >= settings.agent_max_steps:
            return "end"
        if isinstance(last, AIMessage) and getattr(last, "tool_calls", None):
            return "tools"
        return "end"

    graph = StateGraph(ChatAgentState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", ToolNode(tools))
    graph.add_edge(START, "agent")
    graph.add_conditional_edges("agent", should_continue, {"tools": "tools", "end": END})
    graph.add_edge("tools", "agent")

    return graph.compile(checkpointer=_checkpointer)


class ChatAgentService:

    async def chat(
        self,
        message: str,
        company_id: uuid.UUID,
        user_id: uuid.UUID,
        company_name: str,
        db: AsyncSession,
    ) -> dict:
        """Run one turn of the agentic chat. Returns {answer, tool_calls_made}."""
        graph = _build_graph(company_id, db)
        thread_id = f"{company_id}:{user_id}"
        config = {
            "configurable": {"thread_id": thread_id},
            "recursion_limit": settings.agent_recursion_limit,
        }

        try:
            result = await graph.ainvoke(
                {
                    "messages": [HumanMessage(content=message)],
                    "company_name": company_name,
                    "steps_taken": 0,
                },
                config=config,
            )
        except Exception as e:
            logger.error(f"Chat agent execution failed: {e}")
            raise

        final_messages = result["messages"]
        answer = ""
        tool_calls_made = []
        for m in final_messages:
            if isinstance(m, AIMessage) and m.content:
                answer = m.content
            if isinstance(m, ToolMessage):
                tool_calls_made.append(m.name)

        return {"answer": answer or "I wasn't able to generate a response.", "tools_used": tool_calls_made}


chat_agent_service = ChatAgentService()
