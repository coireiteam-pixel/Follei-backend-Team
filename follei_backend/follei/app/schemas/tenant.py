from pydantic import BaseModel
from typing import Optional
from uuid import UUID


class TenantBase(BaseModel):
    name: str
    slug: str
    industry: Optional[str] = None
    plan: Optional[str] = None


class TenantCreate(TenantBase):
    pass


class TenantRead(TenantBase):
    id: UUID
    status: str
    trial_ends_at: Optional[str] = None

    class Config:
        from_attributes = True
