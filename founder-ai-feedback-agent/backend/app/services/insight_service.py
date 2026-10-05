"""
AI Business Insight Generator.
Uses LLM ONLY for high-level summaries, root cause, and recommendations.
All raw data is computed via traditional ML before LLM call.

DEPRECATED: superseded by app/services/agents/insight_agent.py (LangGraph
multi-step agent with RAG grounding). Kept only for reference; no routes
import this module anymore.
"""
from __future__ import annotations
import json
from datetime import datetime, timezone
from typing import Any
from loguru import logger
from app.services.llm_service import llm_service
from app.core.config import settings


EXECUTIVE_SUMMARY_PROMPT = """You are a senior product analyst AI for startup founders.
Analyze this customer feedback data and write a concise executive summary.

DATA:
{data}

Write a professional executive summary (3-4 paragraphs) covering:
1. Overall sentiment health and trend
2. Top customer pain points
3. Most demanded features
4. Critical business risks

Be direct, actionable, and data-driven. Use bullet points where helpful.
"""

ROOT_CAUSE_PROMPT = """You are a root cause analysis expert.
Given this customer feedback data showing rising negative sentiment:

DATA:
{data}

Perform a root cause analysis:
1. Identify the PRIMARY root cause of customer dissatisfaction
2. Identify CONTRIBUTING factors
3. Suggest the most impactful fix

Format:
## Primary Root Cause
[Your analysis]

## Contributing Factors
- [Factor 1]
- [Factor 2]

## Recommended Fix
[Specific actionable recommendation]
"""

RECOMMENDATION_PROMPT = """You are an AI product strategist for a startup.
Based on this customer feedback analysis:

DATA:
{data}

Generate 5 specific, prioritized product recommendations.
Format each as:
**Priority [1-5]: [Action Title]**
- Problem: [What customers are experiencing]
- Solution: [Specific fix or feature]
- Impact: [Expected outcome]
- Effort: [Low/Medium/High]
"""

CHAT_SYSTEM_PROMPT = """You are the Feedback Intelligence AI for {company_name}.
You analyze customer feedback data to help founders make decisions.

Current feedback analytics:
{analytics}

Answer the founder's question directly, cite specific data points, and always end with 1-2 actionable recommendations.
Be concise and business-focused."""


class InsightService:
    """Generates AI-powered business insights using feedback analytics data."""

    def _format_data(self, analytics: dict[str, Any]) -> str:
        return json.dumps(analytics, indent=2, default=str)

    async def generate_executive_summary(self, analytics: dict[str, Any]) -> str:
        prompt = EXECUTIVE_SUMMARY_PROMPT.format(data=self._format_data(analytics))
        return await llm_service.ainvoke(prompt)

    async def generate_root_cause(self, analytics: dict[str, Any]) -> str:
        prompt = ROOT_CAUSE_PROMPT.format(data=self._format_data(analytics))
        return await llm_service.ainvoke(prompt)

    async def generate_recommendations(self, analytics: dict[str, Any]) -> str:
        prompt = RECOMMENDATION_PROMPT.format(data=self._format_data(analytics))
        return await llm_service.ainvoke(prompt)

    async def chat(self, question: str, analytics: dict[str, Any], company_name: str) -> str:
        """Answer a founder's question about their feedback data."""
        system = CHAT_SYSTEM_PROMPT.format(
            company_name=company_name,
            analytics=self._format_data(analytics)
        )
        full_prompt = f"{system}\n\nFounder question: {question}"
        return await llm_service.ainvoke(full_prompt)

    def build_analytics_context(
        self,
        sentiment_summary: dict,
        top_complaints: list[dict],
        top_features: list[dict],
        top_topics: list[dict],
        trend_data: dict | None = None,
        period_label: str = "recent period",
    ) -> dict[str, Any]:
        """Build a structured analytics dict to pass to LLM prompts."""
        return {
            "period": period_label,
            "sentiment": {
                "total_analyzed": sentiment_summary.get("total_analyzed", 0),
                "positive_pct": sentiment_summary.get("positive_pct", 0),
                "neutral_pct": sentiment_summary.get("neutral_pct", 0),
                "negative_pct": sentiment_summary.get("negative_pct", 0),
            },
            "top_complaints": top_complaints[:5],
            "top_feature_requests": top_features[:5],
            "top_topics": top_topics[:5],
            "trend": trend_data or {},
        }


insight_service = InsightService()
