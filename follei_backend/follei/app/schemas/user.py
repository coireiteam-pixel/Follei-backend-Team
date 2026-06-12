from pydantic import BaseModel
from typing import Optional
from uuid import UUID


class UserBase(BaseModel):
    tenant_id: UUID
    email: str
    full_name: Optional[str] = None
    role: Optional[str] = None


class UserCreate(UserBase):
    pass


class UserRead(UserBase):
    id: UUID
    status: str
    last_login_at: Optional[str] = None

    class Config:
        from_attributes = True
