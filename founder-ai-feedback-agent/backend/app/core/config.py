"""
Application configuration — reads from environment variables.
Switch LLM providers via LLM_PROVIDER env var: groq | ollama | huggingface
"""
from functools import lru_cache
from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "Founder AI - Feedback Agent"
    app_env: Literal["development", "staging", "production"] = "development"
    debug: bool = True
    secret_key: str = "change-me-in-production"
    allowed_origins: list[str] = ["http://localhost:3000"]

    database_url: str = "postgresql+asyncpg://postgres:password@localhost:5432/founder_ai_feedback"
    database_sync_url: str = "postgresql://postgres:password@localhost:5432/founder_ai_feedback"
    db_pool_size: int = 10
    db_max_overflow: int = 20

    redis_url: str = "redis://localhost:6379/0"

    jwt_secret_key: str = "change-me-jwt-secret"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7

    llm_provider: Literal["groq", "ollama", "huggingface"] = "groq"

    groq_api_key: str = ""
    groq_model: str = "openai/gpt-oss-120b"
    groq_fast_model: str = "openai/gpt-oss-20b"

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1"

    huggingface_api_key: str = ""
    hf_model: str = "meta-llama/Meta-Llama-3.1-8B-Instruct"

    sentiment_model: str = "cardiffnlp/twitter-roberta-base-sentiment-latest"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    topic_model_type: Literal["bertopic", "lda"] = "bertopic"

    # --- RAG / Vector Store (ChromaDB) ---
    chroma_persist_dir: str = "./chroma_data"
    chroma_collection_prefix: str = "feedback"
    rag_top_k: int = 8
    rag_min_relevance: float = 0.25  # 1 - cosine_distance threshold, lower distance = more relevant

    # --- Agentic AI (LangGraph) ---
    agent_max_steps: int = 6
    agent_recursion_limit: int = 20
    chat_memory_turns: int = 10

    max_upload_size_mb: int = 50
    upload_dir: str = "./uploads"

    @property
    def max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
