import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, ARRAY

from app.database.base import Base

class Document(Base):
    """
    Represents an uploaded document or scraped source for the RAG Knowledge Base.
    """
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    
    title = Column(String, nullable=False)
    source_type = Column(String, nullable=False) # e.g., 'pdf', 'url', 'notion'
    status = Column(String, default="pending")   # pending, processing, ready, failed
    tags = Column(ARRAY(String), default=list)
    
    created_at = Column(DateTime, default=datetime.utcnow)
