from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.repositories.ticket_repo import ticket_repo
from app.schemas.ticket import TicketOut

router = APIRouter()


@router.get("", response_model=List[TicketOut])
def list_tickets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Lists support tickets that were created for the current user, either manually
    or automatically by the agent's create_support_ticket tool during a chat.
    """
    return ticket_repo.list_by_user(db, user_id=current_user.id)
