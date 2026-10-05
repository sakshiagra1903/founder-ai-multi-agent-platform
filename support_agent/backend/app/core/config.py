import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Founder AI Assistant - Support Agent"
    API_V1_STR: str = "/api"
    
    # JWT Auth
    SECRET_KEY: str = "super-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Database
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: str = "5432"
    POSTGRES_DB: str = "support_agent"
    
    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    
    # AI / LLM Config
    LLM_PROVIDER: str = "groq"  # "openai" or "groq" — default groq for consistency with the orchestrator, Feedback, and Hiring agents; switch back to "openai" here anytime by env var if preferred.
    OPENAI_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o-mini"
    GROQ_MODEL: str = "openai/gpt-oss-120b"
    
    # Vector DB / Uploads
    UPLOAD_DIR: str = "backend/app/uploads"
    FAISS_INDEX_DIR: str = "backend/app/uploads/faiss_index"
    
    # Chunking Configuration
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    
    # Document size validation (10MB limit by default)
    MAX_FILE_SIZE_BYTES: int = 10 * 1024 * 1024 

    # Agentic RAG Configuration
    AGENT_RECURSION_LIMIT: int = 10          # max agent<->tool loop steps (LangGraph)
    AGENT_WEB_SEARCH_ENABLED: bool = True    # toggle the web_search tool
    AGENT_TICKET_TOOL_ENABLED: bool = True   # toggle the create_support_ticket tool
    AGENT_KB_TOP_K: int = 5                  # chunks retrieved per knowledge-base search

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="ignore")

settings = Settings()

# Ensure directories exist
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.FAISS_INDEX_DIR, exist_ok=True)
