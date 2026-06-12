from pydantic import BaseModel
from typing import Optional
from uuid import UUID


class MessageBase(BaseModel):
    tenant_id: UUID
    conversation_id: UUID
    sender_type: str
    message: str
    message_type: Optional[str] = "text"


class MessageCreate(MessageBase):
    sender_id: Optional[UUID] = None


class MessageRead(MessageBase):
    id: UUID
    created_at: Optional[str] = None

    class Config:
        from_attributes = True
