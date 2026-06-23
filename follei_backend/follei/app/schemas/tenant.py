from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class TenantBase(BaseModel):
    name: str = Field(examples=["Acme Corp"])
    domain: str | None = Field(default=None, examples=["acme.example.com"])


class TenantCreate(TenantBase):
    admin_email: str = Field(examples=["admin@acme.com"])
    admin_password: str = Field(examples=["SecurePass123"])
    admin_first_name: str = Field(examples=["John"])
    admin_last_name: str = Field(examples=["Doe"])


class TenantUpdate(BaseModel):
    name: str | None = None
    domain: str | None = None


class TenantResponse(TenantBase):
    id: str
    created_at: datetime

    model_config = {"from_attributes": True}


TenantRead = TenantResponse


class TenantListResponse(BaseModel):
    items: list[TenantResponse]
    total: int
    page: int
    page_size: int