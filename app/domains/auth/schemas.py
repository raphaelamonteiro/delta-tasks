from datetime import datetime
from uuid import UUID

from pydantic import ConfigDict, EmailStr, Field

from app.core.schemas import BaseDTO
from app.db.models import GlobalRole


class RegisterUserDTO(BaseDTO):
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=128)


class CreateUserDTO(BaseDTO):
    name: str
    email: EmailStr
    password_hash: str


class RegisterUserResponse(BaseDTO):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    email: EmailStr
    global_role: GlobalRole
    is_active: bool
    created_at: datetime


class LoginDTO(BaseDTO):
    pass
