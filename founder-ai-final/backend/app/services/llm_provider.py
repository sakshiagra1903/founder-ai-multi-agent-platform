from app.core.config import settings


def get_llm(temperature: float = 0.1, max_tokens: int = 2000):
    """Return a chat model for the configured AI_PROVIDER (groq or openai)."""
    if settings.AI_PROVIDER == "groq":
        from langchain_groq import ChatGroq
        return ChatGroq(
            api_key=settings.GROQ_API_KEY,
            model=settings.GROQ_MODEL,
            temperature=temperature,
            max_tokens=max_tokens,
        )
    else:
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            api_key=settings.OPENAI_API_KEY,
            model=settings.OPENAI_MODEL,
            temperature=temperature,
            max_tokens=max_tokens,
        )
