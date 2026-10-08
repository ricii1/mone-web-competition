from uuid import UUID

from pydantic import BaseModel, EmailStr

from app.models.user import UserRole


class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: UserRole


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: UUID
    name: str
    email: EmailStr
    role: UserRole

    model_config = {"from_attributes": True}
