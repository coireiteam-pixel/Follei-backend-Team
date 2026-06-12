import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID

from app.database.base import Base

class Conversation(Base):
    """
    Represents a chat thread between an end-user/lead and an AI Agent.
    """
    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id", ondelete="SET NULL"), nullable=True)
    
    title = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Message(Base):
    __tablename__ = "conversation_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    role = Column(String, nullable=False) # 'user', 'agent', 'system', 'tool'
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
