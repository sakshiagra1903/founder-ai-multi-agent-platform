"""
Collaborative Supervisor Agent.

Unlike a simple router (classify → forward to exactly one agent → stop),
this supervisor is itself a ReAct-style LangGraph agent that can:

  1. Call any of the 3 agent-tools (feedback_agent, support_agent,
     hiring_list_resumes, hiring_analyze) zero, one, or many times, in any
     order it decides.
  2. Read a tool's result and decide — based on that result — to call a
     *different* tool next (true cross-agent collaboration), e.g.:
       "Best candidate for the role, and does our support history show any
        red flags customers raised about similar past hires?"
       -> calls hiring_analyze, reads the result, then calls feedback_agent
          with a question shaped by what it learned, then synthesizes both
          into one final answer.
  3. Remember the conversation across turns via a LangGraph checkpointer
     keyed by `thread_id`, so follow-up questions ("now compare that to...")
     have context from earlier tool calls without the caller resending
     history.

None of this touches the 3 original agents — the supervisor only ever talks
to them through their existing HTTP APIs (via app/tools.py -> app/clients.py).
"""
from __future__ import annotations

from typing import Optional

from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

from app.llm import get_llm
from app.config import settings
from app.tools import build_agent_tools

SUPERVISOR_SYSTEM_PROMPT = """You are the Supervisor of a founder's 3-agent AI \
system:

- feedback_agent: customer feedback, sentiment, complaints, feature requests, \
  trends.
- support_agent: general product/support questions, knowledge base + web \
  search, can file support tickets.
- hiring_list_resumes / hiring_analyze: evaluates uploaded candidate resumes \
  against a job description (scoring, ranking, interview questions).

You do not answer from your own knowledge about the company's data — you MUST \
call the relevant tool(s) to get real information before answering anything \
that depends on company data (feedback, tickets, candidates).

You CAN and SHOULD call more than one tool when a question genuinely needs \
input from more than one agent, and you can use the output of one tool call \
to decide what to ask another tool next. For example, if asked to evaluate a \
candidate for a support-facing role, you might call hiring_analyze first, \
then call feedback_agent to check if customers have complained about response \
quality, then combine both into one coherent recommendation.

If a required tool call fails or a resource doesn't exist (e.g. no resumes \
uploaded yet), tell the user plainly what's missing instead of guessing.

Always give ONE final, synthesized answer in the user's own language/tone — \
do not just concatenate raw tool outputs, actually combine the insights.
"""

# Shared in-memory checkpointer: keeps conversation + tool-call history per
# thread_id across turns. For multi-process/production deployments, swap this
# for langgraph.checkpoint.sqlite.SqliteSaver or a Postgres-backed checkpointer.
_checkpointer = MemorySaver()


def build_supervisor(tokens: dict[str, Optional[str]]):
    """Builds a fresh supervisor agent bound to this request's per-agent JWTs.
    The compiled graph is cheap (no network calls at build time); the shared
    `_checkpointer` is what actually carries memory across calls with the
    same thread_id, regardless of which built instance handles the request.
    """
    llm = get_llm(model=settings.supervisor_model, temperature=0.1)
    tools = build_agent_tools(tokens)
    return create_react_agent(
        llm,
        tools,
        prompt=SUPERVISOR_SYSTEM_PROMPT,
        checkpointer=_checkpointer,
    )


async def run_supervisor(message: str, tokens: dict[str, Optional[str]], thread_id: str) -> dict:
    agent = build_supervisor(tokens)
    config = {"configurable": {"thread_id": thread_id}}
    result = await agent.ainvoke({"messages": [{"role": "user", "content": message}]}, config=config)

    messages = result["messages"]
    final_message = messages[-1]

    tool_calls_made = [
        m.name for m in messages if getattr(m, "type", None) == "tool"
    ]

    return {
        "answer": final_message.content,
        "tools_used": tool_calls_made,
        "turn_count": len(messages),
    }
