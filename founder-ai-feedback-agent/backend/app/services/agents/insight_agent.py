"""
Insight Generation Agent — LangGraph multi-step pipeline.

Old behaviour (insight_service.py): one LLM call per insight type, fed only
aggregate JSON numbers, no real customer quotes, no shared context between
executive-summary / root-cause / recommendations calls.

New behaviour: a proper agentic pipeline —

    START -> fetch_analytics -> rag_retrieve -> executive_summary
          -> root_cause -> recommendations -> synthesize -> END

Each generation node:
  1) only runs the LLM if its section was actually requested (`insight_types`)
  2) is grounded in BOTH the aggregate analytics AND real feedback quotes
     pulled via RAG in `rag_retrieve`
  3) can see the output of earlier nodes (e.g. root_cause reads the
     executive_summary already produced), so the sections build on each
     other instead of being generated in isolation.

This one graph powers both /insights/generate (single section) and
/reports (full report, all sections) — callers just set `insight_types`.
"""
from __future__ import annotations

import json
import uuid
from typing import Any

from langgraph.graph import StateGraph, START, END
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.agents.state import InsightAgentState
from app.services.analytics_service import analytics_service
from app.services.llm_service import llm_service
from app.services.rag.vector_store_service import vector_store_service

EXECUTIVE_SUMMARY_PROMPT = """You are a senior product analyst AI for startup founders.
Analyze this customer feedback data and write a concise executive summary.

AGGREGATE DATA:
{data}

REAL CUSTOMER QUOTES (retrieved via RAG, for grounding):
{quotes}

Write a professional executive summary (3-4 paragraphs) covering:
1. Overall sentiment health and trend
2. Top customer pain points (reference a real quote where useful)
3. Most demanded features
4. Critical business risks

Be direct, actionable, and data-driven. Use bullet points where helpful.
"""

ROOT_CAUSE_PROMPT = """You are a root cause analysis expert.

AGGREGATE DATA:
{data}

REAL CUSTOMER QUOTES (retrieved via RAG, for grounding):
{quotes}

EXECUTIVE SUMMARY ALREADY WRITTEN (for context, don't repeat it):
{summary}

Perform a root cause analysis:
1. Identify the PRIMARY root cause of customer dissatisfaction, citing a real quote as evidence
2. Identify CONTRIBUTING factors
3. Suggest the most impactful fix

Format:
## Primary Root Cause
[Your analysis, with a supporting quote]

## Contributing Factors
- [Factor 1]
- [Factor 2]

## Recommended Fix
[Specific actionable recommendation]
"""

RECOMMENDATION_PROMPT = """You are an AI product strategist for a startup.

AGGREGATE DATA:
{data}

ROOT CAUSE ANALYSIS ALREADY WRITTEN (build on this, don't repeat it):
{root_cause}

Generate 5 specific, prioritized product recommendations.
Format each as:
**Priority [1-5]: [Action Title]**
- Problem: [What customers are experiencing]
- Solution: [Specific fix or feature]
- Impact: [Expected outcome]
- Effort: [Low/Medium/High]
"""


def _format_quotes(examples: list[dict]) -> str:
    if not examples:
        return "(no representative quotes retrieved)"
    lines = []
    for ex in examples[:8]:
        meta = ex.get("metadata", {})
        lines.append(f"- [{meta.get('sentiment', 'unknown')}] \"{ex['text'][:220]}\"")
    return "\n".join(lines)


def build_graph(company_id: uuid.UUID, db: AsyncSession):

    async def fetch_analytics_node(state: InsightAgentState) -> dict:
        sentiment = await analytics_service.get_sentiment_summary(company_id, db)
        complaints = await analytics_service.get_top_complaints(company_id, db)
        features = await analytics_service.get_top_features(company_id, db)
        topics = await analytics_service.get_top_topics(company_id, db)
        trend = await analytics_service.get_sentiment_trend(company_id, db)
        analytics_ctx = {
            "sentiment": sentiment,
            "top_complaints": complaints[:5],
            "top_feature_requests": features[:5],
            "top_topics": topics[:5],
            "trend": trend[-14:] if trend else [],
        }
        return {"analytics": analytics_ctx}

    async def rag_retrieve_node(state: InsightAgentState) -> dict:
        # Pull representative negative-sentiment + complaint quotes to ground generation.
        queries = ["biggest customer complaints and frustrations", "most requested new features"]
        examples: list[dict] = []
        for q in queries:
            try:
                examples.extend(vector_store_service.similarity_search(company_id, q, k=5))
            except Exception as e:
                logger.warning(f"RAG retrieve failed for insight agent: {e}")
        return {"rag_examples": examples}

    async def executive_summary_node(state: InsightAgentState) -> dict:
        if "executive_summary" not in state.get("insight_types", []):
            return {}
        prompt = EXECUTIVE_SUMMARY_PROMPT.format(
            data=json.dumps(state["analytics"], indent=2, default=str),
            quotes=_format_quotes(state.get("rag_examples", [])),
        )
        content = await llm_service.ainvoke(prompt)
        return {"executive_summary": content}

    async def root_cause_node(state: InsightAgentState) -> dict:
        if "root_cause" not in state.get("insight_types", []):
            return {}
        prompt = ROOT_CAUSE_PROMPT.format(
            data=json.dumps(state["analytics"], indent=2, default=str),
            quotes=_format_quotes(state.get("rag_examples", [])),
            summary=state.get("executive_summary") or "(not generated this run)",
        )
        content = await llm_service.ainvoke(prompt)
        return {"root_cause": content}

    async def recommendations_node(state: InsightAgentState) -> dict:
        if "recommendation" not in state.get("insight_types", []):
            return {}
        prompt = RECOMMENDATION_PROMPT.format(
            data=json.dumps(state["analytics"], indent=2, default=str),
            root_cause=state.get("root_cause") or "(not generated this run)",
        )
        content = await llm_service.ainvoke(prompt)
        return {"recommendations": content}

    async def synthesize_node(state: InsightAgentState) -> dict:
        sections = []
        if state.get("executive_summary"):
            sections.append("## Executive Summary\n\n" + state["executive_summary"])
        if state.get("root_cause"):
            sections.append("## Root Cause Analysis\n\n" + state["root_cause"])
        if state.get("recommendations"):
            sections.append("## Recommendations\n\n" + state["recommendations"])
        return {"final_report": "\n\n---\n\n".join(sections)}

    graph = StateGraph(InsightAgentState)
    graph.add_node("fetch_analytics", fetch_analytics_node)
    graph.add_node("rag_retrieve", rag_retrieve_node)
    graph.add_node("executive_summary", executive_summary_node)
    graph.add_node("root_cause", root_cause_node)
    graph.add_node("recommendations", recommendations_node)
    graph.add_node("synthesize", synthesize_node)

    graph.add_edge(START, "fetch_analytics")
    graph.add_edge("fetch_analytics", "rag_retrieve")
    graph.add_edge("rag_retrieve", "executive_summary")
    graph.add_edge("executive_summary", "root_cause")
    graph.add_edge("root_cause", "recommendations")
    graph.add_edge("recommendations", "synthesize")
    graph.add_edge("synthesize", END)

    return graph.compile()


class InsightAgentService:

    async def run(
        self,
        company_id: uuid.UUID,
        insight_types: list[str],
        db: AsyncSession,
    ) -> InsightAgentState:
        """
        Run the agentic pipeline. `insight_types` subset of
        {"executive_summary", "root_cause", "recommendation"}.
        """
        graph = build_graph(company_id, db)
        result = await graph.ainvoke({
            "company_id": str(company_id),
            "insight_types": insight_types,
        })
        return result


insight_agent_service = InsightAgentService()
