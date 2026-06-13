from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from uuid import UUID


class TenantBase(BaseModel):
    name: str
    domain: Optional[str] = None


class TenantCreate(TenantBase):
    pass


class TenantRead(TenantBase):
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True
