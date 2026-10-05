from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.repositories.user_repository import UserRepository
from app.core.security import verify_password, create_access_token
from app.schemas.auth import UserCreate, Token, UserResponse


class AuthService:
    def __init__(self, db: Session):
        self.repo = UserRepository(db)

    def signup(self, data: UserCreate) -> UserResponse:
        if self.repo.get_by_email(data.email):
            raise HTTPException(status_code=400, detail="Email already registered")
        user = self.repo.create(name=data.name, email=data.email, password=data.password)
        return UserResponse.model_validate(user)

    def login(self, email: str, password: str) -> Token:
        user = self.repo.get_by_email(email)
        if not user or not verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )
        token = create_access_token({"sub": str(user.id)})
        return Token(access_token=token, user=UserResponse.model_validate(user))
