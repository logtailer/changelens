import uuid

from pydantic import BaseModel, EmailStr

from changelens.models.user import Role


class TokenRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    model_config = {"from_attributes": True}

    user_id: uuid.UUID
    email: str
    role: Role
    is_active: bool
