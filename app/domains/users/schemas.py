from datetime import datetime
from uuid import UUID

from pydantic import ConfigDict, EmailStr, Field

from app.core.schemas import BaseDTO
from app.db.models import GlobalRole


class UserResponse(BaseDTO):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    email: EmailStr
    global_role: GlobalRole
    is_active: bool
    created_at: datetime
    updated_at: datetime


class UpdateUserDTO(BaseDTO):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    email: EmailStr | None = Field(default=None, max_length=255)
    password: str | None = Field(default=None, min_length=8, max_length=128)
    global_role: GlobalRole | None = None
    is_active: bool | None = None


class UserListResponse(BaseDTO):
    items: list[UserResponse]
    total: int
    limit: int
    offset: int
