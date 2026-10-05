from pydantic_settings import BaseSettings
from typing import Optional
from functools import lru_cache

class Settings(BaseSettings):
    APP_NAME: str = "Founder AI – Hiring Agent"
    APP_ENV: str = "development"
    SECRET_KEY: str = "change-me-in-production-please"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # SQLite by default (zero setup). Switch to PostgreSQL if needed.
    DATABASE_URL: str = "sqlite:///./founderai.db"

    AI_PROVIDER: str = "groq"
    GROQ_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    GROQ_MODEL: str = "openai/gpt-oss-120b"
    OPENAI_MODEL: str = "gpt-4o-mini"

    # "agentic" = LangGraph multi-agent RAG pipeline (deeper, more LLM calls, slower).
    # "simple"  = original single-prompt evaluation (fast, 1 LLM call per resume).
    AI_MODE: str = "agentic"

    # Local (no API key) embedding model used for RAG, served via fastembed/ONNX.
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    CHROMA_PERSIST_DIR: str = "chroma_db"

    MAX_FILE_SIZE_MB: int = 10
    UPLOAD_DIR: str = "uploads"

    class Config:
        env_file = ".env"
        extra = "ignore"

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
