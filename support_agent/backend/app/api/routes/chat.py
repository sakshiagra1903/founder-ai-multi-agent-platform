import json
import logging
from typing import List

from fastapi import APIRouter, Depends, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.repositories.chat_repo import chat_repo
from app.schemas.chat import ChatRequest, ChatResponse, ChatHistoryOut
from app.services.agent_service import agent_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("", response_model=ChatResponse, status_code=status.HTTP_200_OK)
def ask_question(
    payload: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Asks a question using the agentic RAG pipeline (LangGraph):
    the agent decides whether to search the knowledge base, search the web,
    and/or escalate to a human support ticket, then returns the final answer
    with source citations.
    """
    result = agent_service.answer_question(
        user_id=current_user.id,
        question=payload.question,
        db=db,
    )

    chat_repo.create(
        db,
        user_id=current_user.id,
        question=payload.question,
        answer=result["answer"],
        sources=result["sources"]
    )

    return {
        "answer": result["answer"],
        "sources": result["sources"],
        "ticket": result.get("ticket"),
    }


@router.post("/stream", status_code=status.HTTP_200_OK)
async def ask_question_stream(
    payload: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Same agentic RAG pipeline as POST /chat, but streams tokens and tool-activity
    events over Server-Sent Events (SSE) as the agent thinks/acts, so the frontend
    can render a live typing effect plus "searching documents...", "searching web...",
    "creating ticket..." style status updates.

    Each SSE line is `data: <json>\\n\\n` where the json has a `type` field:
    tool_start | tool_end | token | sources | ticket | error | done
    """

    async def event_generator():
        final_answer = ""
        final_sources: List[dict] = []
        try:
            async for event in agent_service.stream_answer(
                user_id=current_user.id,
                question=payload.question,
                db=db,
            ):
                if event.get("type") == "done":
                    final_answer = event.get("answer", "")
                elif event.get("type") == "sources":
                    final_sources = event.get("sources", [])
                yield f"data: {json.dumps(event)}\n\n"
        except Exception as e:
            logger.error(f"Streaming chat endpoint failed: {str(e)}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
            final_answer = final_answer or f"Error generating answer: {str(e)}"

        # Persist the full turn to Postgres once streaming completes
        try:
            chat_repo.create(
                db,
                user_id=current_user.id,
                question=payload.question,
                answer=final_answer,
                sources=final_sources,
            )
        except Exception as e:
            logger.error(f"Failed to persist streamed chat turn: {str(e)}")

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # disable proxy buffering (nginx) for real-time streaming
        },
    )


@router.get("/history", response_model=List[ChatHistoryOut])
def get_chat_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = 50
):
    """
    Retrieves previous chat conversations for the current user.
    """
    histories = chat_repo.list_by_user(db, user_id=current_user.id, limit=limit)
    return histories
