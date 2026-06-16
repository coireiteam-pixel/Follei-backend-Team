import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, Uuid
from sqlalchemy.orm import relationship

from app.database.base import Base

class Customer(Base):
    """
    Represents a converted account and post-sale analytics (Churn, Health Score).
    """
    __tablename__ = "customers"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    tenant_id = Column(Uuid(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    lead_id = Column(Uuid(as_uuid=True), ForeignKey("leads.id", ondelete="SET NULL"), nullable=True)
    
    name = Column(String, nullable=False)
    health_score = Column(Integer, default=100)
    churn_risk = Column(String, default="low") # 'low', 'medium', 'high'
    metadata_ = Column("metadata", JSON, default=dict, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    tenant = relationship("Tenant", back_populates="customers")
    lead = relationship("Lead", back_populates="customers")
    agent_memories = relationship("AgentMemory", back_populates="customer")
    conversations = relationship("Conversation", back_populates="customer")
