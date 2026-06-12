import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, ARRAY

from app.database.base import Base

class Agent(Base):
    """
    Represents an autonomous AI worker within a tenant.
    """
    __tablename__ = "agents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    
    name = Column(String, nullable=False)
    role = Column(String, nullable=False) # e.g., 'SDR', 'Support'
    system_prompt = Column(String, nullable=False)
    tools = Column(ARRAY(String), default=list) # Assigned MCP tool names
    
    created_at = Column(DateTime, default=datetime.utcnow)
