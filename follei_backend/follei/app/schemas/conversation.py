from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from uuid import UUID


class ConversationBase(BaseModel):
    tenant_id: UUID
    agent_id: Optional[UUID] = None
    title: Optional[str] = None


class ConversationCreate(ConversationBase):
    pass


class ConversationRead(ConversationBase):
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True
