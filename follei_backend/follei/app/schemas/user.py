from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class UserBase(BaseModel):
    email: str = Field(examples=["admin@example.com"])
    first_name: str = Field(examples=["John"])
    last_name: str = Field(examples=["Doe"])
    role: str = Field(examples=["admin"])
    status: str = Field(default="active", examples=["active"])
    is_active: bool = True


class UserCreate(UserBase):
    tenant_id: str = Field(examples=["T001"])
    password: str = Field(examples=["SecurePass123"])


class UserUpdate(BaseModel):
    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    role: str | None = None
    status: str | None = None
    is_active: bool | None = None


class UserResponse(UserBase):
    id: str
    tenant_id: str
    created_at: datetime
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


UserRead = UserResponse


class UserListResponse(BaseModel):
    items: list[UserResponse]
    total: int
    page: int
    page_size: int
