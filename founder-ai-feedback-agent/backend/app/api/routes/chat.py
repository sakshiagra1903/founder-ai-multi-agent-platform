"""AI Chat interface — founder asks questions about feedback data.

Now backed by a LangGraph agent (see services/agents/chat_agent.py) that can
call RAG search + analytics tools on its own, across multiple turns, instead
of a single static prompt built from pre-fetched analytics.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.models.user import User
from app.core.dependencies import get_current_active_user
from app.services.agents.chat_agent import chat_agent_service

router = APIRouter(prefix="/chat", tags=["AI Chat"])


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    answer: str
    model: str
    tools_used: list[str] = []


@router.post("", response_model=ChatResponse)
async def chat(
    payload: ChatRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    if not current_user.company_id:
        raise HTTPException(status_code=400, detail="No company associated")
    if not payload.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    company_name = current_user.company.name if current_user.company else "Your Company"

    result = await chat_agent_service.chat(
        message=payload.message,
        company_id=current_user.company_id,
        user_id=current_user.id,
        company_name=company_name,
        db=db,
    )

    from app.core.config import settings
    model_used = {"groq": settings.groq_model, "ollama": settings.ollama_model, "huggingface": settings.hf_model}.get(settings.llm_provider, "unknown")

    return ChatResponse(answer=result["answer"], model=model_used, tools_used=result["tools_used"])
