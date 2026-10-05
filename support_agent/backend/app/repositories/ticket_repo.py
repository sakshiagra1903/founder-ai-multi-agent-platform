from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.ticket import SupportTicket


class TicketRepository:
    def create(
        self,
        db: Session,
        user_id: str,
        subject: str,
        description: str,
        source_question: Optional[str] = None,
    ) -> SupportTicket:
        ticket = SupportTicket(
            user_id=user_id,
            subject=subject,
            description=description,
            source_question=source_question,
        )
        db.add(ticket)
        db.commit()
        db.refresh(ticket)
        return ticket

    def list_by_user(self, db: Session, user_id: str, limit: int = 50) -> List[SupportTicket]:
        return (
            db.query(SupportTicket)
            .filter(SupportTicket.user_id == user_id)
            .order_by(SupportTicket.created_at.desc())
            .limit(limit)
            .all()
        )


ticket_repo = TicketRepository()
