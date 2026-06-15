from datetime import datetime
from pydantic import BaseModel, ConfigDict
from uuid import UUID


class MessageBase(BaseModel):
    tenant_id: UUID
    conversation_id: UUID
    role: str
    content: str


class MessageCreate(MessageBase):
    pass


class MessageRead(MessageBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
