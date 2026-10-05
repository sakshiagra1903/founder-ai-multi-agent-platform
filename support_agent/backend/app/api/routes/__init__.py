from fastapi import APIRouter
from app.api.routes.auth import router as auth_router
from app.api.routes.documents import router as doc_router
from app.api.routes.chat import router as chat_router
from app.api.routes.tickets import router as ticket_router

api_router = APIRouter()

api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(doc_router, prefix="/documents", tags=["documents"])
api_router.include_router(chat_router, prefix="/chat", tags=["chat"])
api_router.include_router(ticket_router, prefix="/tickets", tags=["tickets"])
