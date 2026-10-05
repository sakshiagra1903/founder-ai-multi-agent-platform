import logging
from typing import Any, AsyncGenerator, Dict, List

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, MessagesState
from langgraph.prebuilt import ToolNode, tools_condition
from sqlalchemy.orm import Session

from app.core.config import settings
from app.services.agent_tools import AgentToolContext, build_tools
from app.services.redis_service import redis_service

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are 'Founder AI Assistant', an intelligent support agent with access to tools.\n\n"
    "Available tools:\n"
    "- search_knowledge_base: searches the user's uploaded documents.\n"
    "- web_search: searches the public web.\n"
    "- create_support_ticket: escalates the issue to a human support agent.\n\n"
    "Workflow rules:\n"
    "1. For any factual question, ALWAYS call search_knowledge_base first.\n"
    "2. If the knowledge base does not contain a sufficient answer, call web_search for "
    "general/public information.\n"
    "3. If neither tool resolves the question, OR the user explicitly asks to talk to a "
    "human / escalate / file a complaint, call create_support_ticket with a clear subject "
    "and description.\n"
    "4. Never call create_support_ticket for questions you can already answer.\n"
    "5. Do not fabricate facts, names, or URLs. If truly unknown, say so honestly.\n"
    "6. When you answer, mention which source(s) informed your answer in plain language "
    "(e.g. 'according to your uploaded handbook...' or 'based on a web search...').\n"
    "7. Be concise, clear, and professional."
)


class AgentService:
    def __init__(self):
        self._llm = None

    def _get_base_llm(self):
        """Initializes the base chat LLM (without tools bound) dynamically."""
        if self._llm:
            return self._llm

        provider = settings.LLM_PROVIDER.lower()
        if provider == "openai":
            if not settings.OPENAI_API_KEY:
                raise ValueError("OpenAI API Key is required but not configured. Set OPENAI_API_KEY.")
            self._llm = ChatOpenAI(
                openai_api_key=settings.OPENAI_API_KEY,
                model=settings.OPENAI_MODEL,
                temperature=0.0,
                streaming=True,
            )
        elif provider == "groq":
            if not settings.GROQ_API_KEY:
                raise ValueError("Groq API Key is required but not configured. Set GROQ_API_KEY.")
            self._llm = ChatGroq(
                groq_api_key=settings.GROQ_API_KEY,
                model=settings.GROQ_MODEL,
                temperature=0.0,
                streaming=True,
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}. Supported are 'openai' or 'groq'.")

        return self._llm

    def _build_graph(self, ctx: AgentToolContext):
        """Builds a LangGraph ReAct-style agent graph: agent -> tools -> agent -> ... -> END."""
        tools = build_tools(ctx)
        llm_with_tools = self._get_base_llm().bind_tools(tools)

        def call_model(state: MessagesState) -> Dict[str, List[Any]]:
            response = llm_with_tools.invoke(state["messages"])
            return {"messages": [response]}

        graph = StateGraph(MessagesState)
        graph.add_node("agent", call_model)
        graph.add_node("tools", ToolNode(tools))
        graph.set_entry_point("agent")
        graph.add_conditional_edges("agent", tools_condition)
        graph.add_edge("tools", "agent")
        return graph.compile()

    def _build_initial_messages(self, user_id: str, question: str) -> List[Any]:
        history = redis_service.get_session_history(user_id, limit=6)  # last 3 rounds
        messages: List[Any] = [SystemMessage(content=SYSTEM_PROMPT)]
        for msg in reversed(history):
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(AIMessage(content=msg["content"]))
        messages.append(HumanMessage(content=question))
        return messages

    def answer_question(self, user_id: str, question: str, db: Session) -> Dict[str, Any]:
        """Non-streaming entry point: runs the full agent graph and returns the final answer."""
        ctx = AgentToolContext(user_id=user_id, question=question, db=db)
        redis_service.add_recent_search(user_id=user_id, query=question)
        messages = self._build_initial_messages(user_id, question)

        try:
            graph = self._build_graph(ctx)
            result = graph.invoke(
                {"messages": messages},
                config={"recursion_limit": settings.AGENT_RECURSION_LIMIT},
            )
            final_message = result["messages"][-1]
            answer = (final_message.content or "").strip()
            if not answer:
                answer = "I could not generate a response for this question."
        except Exception as e:
            logger.error(f"Agent pipeline error: {str(e)}")
            if "not configured" in str(e) or "API Key" in str(e):
                answer = "Error: LLM API key not configured. Please check backend environment variables."
            else:
                answer = f"Error generating answer: {str(e)}"

        redis_service.add_session_message(user_id, "user", question)
        redis_service.add_session_message(user_id, "assistant", answer)

        return {"answer": answer, "sources": ctx.sources, "ticket": ctx.ticket_created}

    async def stream_answer(self, user_id: str, question: str, db: Session) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Streaming entry point: yields structured events as the agent thinks/uses tools/answers.
        Event shapes:
          {"type": "tool_start", "tool": str, "input": Any}
          {"type": "tool_end",   "tool": str}
          {"type": "token",      "content": str}
          {"type": "sources",    "sources": [...]}
          {"type": "ticket",     "ticket": {...}}
          {"type": "error",      "message": str}
          {"type": "done",       "answer": str}
        """
        ctx = AgentToolContext(user_id=user_id, question=question, db=db)
        redis_service.add_recent_search(user_id=user_id, query=question)
        messages = self._build_initial_messages(user_id, question)

        full_answer = ""
        try:
            graph = self._build_graph(ctx)
            async for event in graph.astream_events(
                {"messages": messages},
                version="v2",
                config={"recursion_limit": settings.AGENT_RECURSION_LIMIT},
            ):
                kind = event.get("event")
                if kind == "on_chat_model_stream":
                    chunk = event["data"].get("chunk")
                    token = getattr(chunk, "content", None) if chunk else None
                    if token:
                        full_answer += token
                        yield {"type": "token", "content": token}
                elif kind == "on_tool_start":
                    yield {
                        "type": "tool_start",
                        "tool": event.get("name"),
                        "input": event.get("data", {}).get("input"),
                    }
                elif kind == "on_tool_end":
                    yield {"type": "tool_end", "tool": event.get("name")}
        except Exception as e:
            logger.error(f"Agent streaming error: {str(e)}")
            if not full_answer:
                if "not configured" in str(e) or "API Key" in str(e):
                    full_answer = "Error: LLM API key not configured. Please check backend environment variables."
                else:
                    full_answer = f"Error generating answer: {str(e)}"
            yield {"type": "error", "message": str(e)}

        full_answer = full_answer.strip() or "I could not generate a response for this question."

        redis_service.add_session_message(user_id, "user", question)
        redis_service.add_session_message(user_id, "assistant", full_answer)

        yield {"type": "sources", "sources": ctx.sources}
        if ctx.ticket_created:
            yield {"type": "ticket", "ticket": ctx.ticket_created}
        yield {"type": "done", "answer": full_answer}


agent_service = AgentService()
