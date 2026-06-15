import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Uuid
from sqlalchemy.orm import relationship

from app.database.base import Base

class Lead(Base):
    """
    Represents a prospective customer and their BANT/MEDDIC revenue scores.
    """
    __tablename__ = "leads"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    tenant_id = Column(Uuid(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    
    email = Column(String, nullable=False, index=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    company = Column(String, nullable=True)
    status = Column(String, default="new") # 'new', 'qualified', 'disqualified', 'converted'
    revenue_score = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)

    tenant = relationship("Tenant", back_populates="leads")
    conversations = relationship("Conversation", back_populates="lead")
    customers = relationship("Customer", back_populates="lead")
