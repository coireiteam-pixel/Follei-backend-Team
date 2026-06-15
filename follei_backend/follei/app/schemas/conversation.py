from pydantic import BaseModel, ConfigDict
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
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
