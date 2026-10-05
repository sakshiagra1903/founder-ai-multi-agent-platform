"""
Shared FastAPI dependencies.
NOTE: this file was referenced by every route module (auth, analytics, chat,
insights, reports, feedback) but was missing from the scaffold, which meant
the app couldn't actually boot. Adding a standard OAuth2-bearer + JWT
dependency here so the AI upgrades below are runnable end-to-end.
"""
from __future__ import annotations
import uuid
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import decode_token, CREDENTIALS_EXCEPTION
from app.db.database import get_db
from app.models.user import User
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    payload = decode_token(token)
    if payload.get("type") != "access":
        raise CREDENTIALS_EXCEPTION
    user_id = payload.get("sub")
    if not user_id:
        raise CREDENTIALS_EXCEPTION
    try:
        result = await db.execute(select(User).options(selectinload(User.company)).where(User.id == uuid.UUID(user_id)))
    except ValueError:
        raise CREDENTIALS_EXCEPTION
    user = result.scalar_one_or_none()
    if user is None:
        raise CREDENTIALS_EXCEPTION
    return user
async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")
    return current_user
