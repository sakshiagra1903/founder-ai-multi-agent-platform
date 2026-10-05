from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Founder AI - Multi-Agent Orchestrator"

    # ── Existing agent backends (unchanged apps, just reachable at these URLs) ──
    # Feedback agent mounts its routes under /api/v1 (see its app/main.py)
    feedback_agent_url: str = "http://localhost:8001"
    feedback_agent_chat_path: str = "/api/v1/chat"
    feedback_agent_health_path: str = "/health"
    feedback_agent_register_path: str = "/api/v1/auth/register"
    feedback_agent_login_path: str = "/api/v1/auth/login"
    feedback_agent_upload_path: str = "/api/v1/feedback/upload"

    # Hiring agent mounts routes with no version prefix (see its main.py)
    hiring_agent_url: str = "http://localhost:8002"
    hiring_agent_upload_path: str = "/hiring/upload-resumes"
    hiring_agent_analyze_path: str = "/hiring/analyze"
    hiring_agent_list_resumes_path: str = "/hiring/resumes"
    hiring_agent_health_path: str = "/health"
    hiring_agent_signup_path: str = "/auth/signup"
    hiring_agent_login_path: str = "/auth/login"

    # Support agent mounts routes under API_V1_STR = "/api" (see its config.py)
    support_agent_url: str = "http://localhost:8003"
    support_agent_chat_path: str = "/api/chat"
    # Support agent (as shipped) exposes no dedicated /health route — "/" is
    # its lightweight root/welcome route and is used purely as a reachability
    # probe. We do not add a route to that app to keep it untouched.
    support_agent_health_path: str = "/"
    support_agent_signup_path: str = "/api/auth/signup"
    support_agent_login_path: str = "/api/auth/login"
    support_agent_upload_path: str = "/api/documents/upload"

    # Timeout used for the lightweight health-probe calls in /api/agents/health.
    # Kept short and separate from request_timeout_seconds (used for real
    # agent work) so a slow/offline agent can't stall the dashboard status.
    health_check_timeout_seconds: float = 4.0

    # ── Router LLM (used only to classify the query, not to answer it) ──
    llm_provider: str = "groq"          # groq | openai
    groq_api_key: str = ""
    groq_model: str = "openai/gpt-oss-20b"      # cheap model (used by legacy single-router mode)
    supervisor_model: str = "openai/gpt-oss-120b"  # smarter model, needed for multi-tool reasoning
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    request_timeout_seconds: float = 60.0

    # The orchestrator now also serves its own UI (static/index.html) at "/",
    # so the console itself talks to http://localhost:8000/api/... same-origin
    # and needs no CORS entry. localhost:3000 is kept for any other dev client.
    allowed_origins: list[str] = ["http://localhost:3000", "http://localhost:8000"]


settings = Settings()
