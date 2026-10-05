from typing import List
from sqlalchemy.orm import Session
from app.models.chat import ChatHistory

class ChatRepository:
    def create(self, db: Session, user_id: str, question: str, answer: str, sources: List[dict]) -> ChatHistory:
        db_chat = ChatHistory(
            user_id=user_id,
            question=question,
            answer=answer,
            sources=sources
        )
        db.add(db_chat)
        db.commit()
        db.refresh(db_chat)
        return db_chat

    def list_by_user(self, db: Session, user_id: str, limit: int = 50) -> List[ChatHistory]:
        return db.query(ChatHistory).filter(ChatHistory.user_id == user_id).order_by(ChatHistory.timestamp.desc()).limit(limit).all()

chat_repo = ChatRepository()
