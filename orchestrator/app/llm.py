from app.config import settings


def get_llm(model: str | None = None, temperature: float = 0.0):
    """Generic LLM factory. `model` override lets the supervisor use a bigger/
    smarter model than the (optional) lightweight router, while both share the
    same provider/API key config."""
    provider = settings.llm_provider.lower()
    if provider == "groq":
        from langchain_groq import ChatGroq
        if not settings.groq_api_key:
            raise ValueError("GROQ_API_KEY not set for orchestrator LLM.")
        return ChatGroq(groq_api_key=settings.groq_api_key, model=model or settings.groq_model, temperature=temperature)
    elif provider == "openai":
        from langchain_openai import ChatOpenAI
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY not set for orchestrator LLM.")
        return ChatOpenAI(api_key=settings.openai_api_key, model=model or settings.openai_model, temperature=temperature)
    raise ValueError(f"Unsupported LLM_PROVIDER for orchestrator: {provider}")


# kept for backwards compatibility with the earlier single-router version
def get_router_llm():
    return get_llm()
