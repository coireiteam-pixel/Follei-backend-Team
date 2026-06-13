from datetime import datetime
from pydantic import BaseModel
from uuid import UUID


class MessageBase(BaseModel):
    tenant_id: UUID
    conversation_id: UUID
    role: str
    content: str


class MessageCreate(MessageBase):
    pass


class MessageRead(MessageBase):
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True
