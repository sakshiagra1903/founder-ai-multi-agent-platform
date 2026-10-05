"""
LLM Provider Service — supports Groq, Ollama, HuggingFace.
Switch via LLM_PROVIDER environment variable.
Used ONLY for: executive summaries, root cause analysis, chat, report insights.
Traditional ML handles sentiment/complaints/features — no LLM per record.
"""
from __future__ import annotations
from typing import Any
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential
from app.core.config import settings


class LLMService:
    """
    Unified LLM interface with provider abstraction.
    Instantiated once and reused across services.
    """

    _chain = None
    _provider: str = ""

    def _build_groq(self):
        from langchain_groq import ChatGroq
        return ChatGroq(
            api_key=settings.groq_api_key,
            model=settings.groq_model,
            temperature=0.3,
            max_tokens=2048,
        )

    def _build_groq_fast(self):
        from langchain_groq import ChatGroq
        return ChatGroq(
            api_key=settings.groq_api_key,
            model=settings.groq_fast_model,
            temperature=0.1,
            max_tokens=1024,
        )

    def _build_ollama(self):
        from langchain_community.llms import Ollama
        return Ollama(
            base_url=settings.ollama_base_url,
            model=settings.ollama_model,
            temperature=0.3,
        )

    def _build_huggingface(self):
        from langchain_community.llms import HuggingFaceEndpoint
        return HuggingFaceEndpoint(
            repo_id=settings.hf_model,
            huggingfacehub_api_token=settings.huggingface_api_key,
            temperature=0.3,
            max_new_tokens=1024,
        )

    def _get_llm(self, fast: bool = False):
        provider = settings.llm_provider
        logger.info(f"LLM provider: {provider}")
        if provider == "groq":
            return self._build_groq_fast() if fast else self._build_groq()
        elif provider == "ollama":
            return self._build_ollama()
        elif provider == "huggingface":
            return self._build_huggingface()
        else:
            raise ValueError(f"Unknown LLM_PROVIDER: {provider}")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def ainvoke(self, prompt: str, fast: bool = False) -> str:
        """Async invoke the configured LLM."""
        llm = self._get_llm(fast=fast)
        try:
            from langchain_core.messages import HumanMessage
            response = await llm.ainvoke([HumanMessage(content=prompt)])
            if hasattr(response, "content"):
                return response.content
            return str(response)
        except Exception as e:
            logger.error(f"LLM invocation failed: {e}")
            raise

    def get_chat_model(self, fast: bool = False):
        """
        Return the raw LangChain chat model (not the string-invoking wrapper
        above). Used by the LangGraph agents, which need to call
        `.bind_tools(...)` on the model themselves.
        """
        return self._get_llm(fast=fast)

    def invoke(self, prompt: str, fast: bool = False) -> str:
        """Sync invoke the configured LLM."""
        llm = self._get_llm(fast=fast)
        try:
            from langchain_core.messages import HumanMessage
            response = llm.invoke([HumanMessage(content=prompt)])
            if hasattr(response, "content"):
                return response.content
            return str(response)
        except Exception as e:
            logger.error(f"LLM invocation failed: {e}")
            raise


llm_service = LLMService()
