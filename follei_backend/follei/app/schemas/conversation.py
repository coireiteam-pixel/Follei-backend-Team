from pydantic import BaseModel
from typing import Optional
from uuid import UUID


class ConversationBase(BaseModel):
    tenant_id: UUID
    channel: str
    status: Optional[str] = "open"


class ConversationCreate(ConversationBase):
    customer_id: Optional[UUID] = None


class ConversationRead(ConversationBase):
    id: UUID
    started_at: Optional[str] = None
    ended_at: Optional[str] = None

    class Config:
        from_attributes = True
