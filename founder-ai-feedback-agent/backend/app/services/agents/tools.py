"""
Agent Tools — the "hands" of the LangGraph agents.

Each tool is bound to a specific (company_id, db session) request context via
a closure, then handed to the agent as a normal LangChain tool. The LLM only
ever sees the tool name, description, and a small typed input schema — never
the db session or company_id directly (multi-tenant safety: a company's
agent can only ever see that company's data, by construction, not by prompt
instruction).
"""
from __future__ import annotations

import uuid
from typing import Any

from langchain_core.tools import StructuredTool
from loguru import logger
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.analytics_service import analytics_service
from app.services.rag.vector_store_service import vector_store_service


# ---------------------------------------------------------------------------
# Tool input schemas
# ---------------------------------------------------------------------------

class SearchFeedbackInput(BaseModel):
    query: str = Field(..., description="Natural language description of the feedback you want to find, e.g. 'complaints about slow checkout' or 'requests for dark mode'.")
    sentiment: str | None = Field(default=None, description="Optional filter: 'positive', 'neutral', or 'negative'.")
    only_complaints: bool = Field(default=False, description="If true, only return feedback flagged as a complaint.")
    only_feature_requests: bool = Field(default=False, description="If true, only return feedback flagged as a feature request.")


class NoInput(BaseModel):
    pass


class LimitInput(BaseModel):
    limit: int = Field(default=10, description="Max number of items to return.")


# ---------------------------------------------------------------------------
# Tool factory — bound to one request's company_id + db session
# ---------------------------------------------------------------------------

def build_tools(company_id: uuid.UUID, db: AsyncSession) -> list[StructuredTool]:

    async def _search_feedback(query: str, sentiment: str | None = None,
                                only_complaints: bool = False, only_feature_requests: bool = False) -> str:
        filters: dict[str, Any] = {}
        if sentiment:
            filters["sentiment"] = sentiment
        if only_complaints:
            filters["is_complaint"] = True
        if only_feature_requests:
            filters["is_feature_request"] = True

        chroma_filter = None
        if len(filters) == 1:
            chroma_filter = filters
        elif len(filters) > 1:
            chroma_filter = {"$and": [{k: v} for k, v in filters.items()]}

        results = vector_store_service.similarity_search(company_id, query, filters=chroma_filter)
        if not results:
            return "No matching feedback found in the vector store for this query."
        lines = []
        for i, r in enumerate(results, 1):
            meta = r["metadata"]
            tag = meta.get("sentiment", "unknown")
            lines.append(f"{i}. [{tag}, relevance={r['score']}] {r['text'][:400]}")
        return "\n".join(lines)

    async def _get_dashboard(_: str = "") -> str:
        data = await analytics_service.get_dashboard(company_id, db)
        return str(data)

    async def _get_sentiment_summary(_: str = "") -> str:
        data = await analytics_service.get_sentiment_summary(company_id, db)
        return str(data)

    async def _get_top_complaints(limit: int = 10) -> str:
        data = await analytics_service.get_top_complaints(company_id, db, limit=limit)
        return str(data)

    async def _get_top_features(limit: int = 10) -> str:
        data = await analytics_service.get_top_features(company_id, db, limit=limit)
        return str(data)

    async def _get_top_topics(_: str = "") -> str:
        data = await analytics_service.get_top_topics(company_id, db)
        return str(data)

    async def _get_sentiment_trend(_: str = "") -> str:
        data = await analytics_service.get_sentiment_trend(company_id, db)
        return str(data)

    tools = [
        StructuredTool.from_function(
            name="search_feedback",
            description=(
                "RAG semantic search over raw customer feedback text. Use this whenever you need "
                "actual customer quotes/examples to support an answer, not just aggregate numbers."
            ),
            coroutine=_search_feedback,
            args_schema=SearchFeedbackInput,
        ),
        StructuredTool.from_function(
            name="get_dashboard_analytics",
            description="Get the full aggregate dashboard: sentiment %, top complaints, top features, top topics, trend.",
            coroutine=_get_dashboard,
            args_schema=NoInput,
        ),
        StructuredTool.from_function(
            name="get_sentiment_summary",
            description="Get overall sentiment breakdown (positive/neutral/negative %) across all analyzed feedback.",
            coroutine=_get_sentiment_summary,
            args_schema=NoInput,
        ),
        StructuredTool.from_function(
            name="get_top_complaints",
            description="Get the most frequent complaint categories, ranked by count.",
            coroutine=_get_top_complaints,
            args_schema=LimitInput,
        ),
        StructuredTool.from_function(
            name="get_top_feature_requests",
            description="Get the most frequently requested features, ranked by count.",
            coroutine=_get_top_features,
            args_schema=LimitInput,
        ),
        StructuredTool.from_function(
            name="get_top_topics",
            description="Get the top discussion topics discovered via topic modeling (BERTopic), with keywords.",
            coroutine=_get_top_topics,
            args_schema=NoInput,
        ),
        StructuredTool.from_function(
            name="get_sentiment_trend",
            description="Get the day-by-day sentiment trend for the last 30 days.",
            coroutine=_get_sentiment_trend,
            args_schema=NoInput,
        ),
    ]
    return tools
