from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, EmailStr, field_validator
import re

class CompanyCreate(BaseModel):
    name: str
    industry: str | None = None

class CompanyResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    industry: str | None
    created_at: datetime
    model_config = {"from_attributes": True}

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    company_name: str | None = None

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain an uppercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain a digit")
        return v

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: UUID
    email: str
    full_name: str
    role: str
    is_active: bool
    company: CompanyResponse | None
    created_at: datetime
    model_config = {"from_attributes": True}

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse
