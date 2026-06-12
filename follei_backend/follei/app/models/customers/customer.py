import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID

from app.database.base import Base

class Customer(Base):
    """
    Represents a converted account and post-sale analytics (Churn, Health Score).
    """
    __tablename__ = "customers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    
    name = Column(String, nullable=False)
    health_score = Column(Integer, default=100)
    churn_risk = Column(String, default="low") # 'low', 'medium', 'high'
    
    created_at = Column(DateTime, default=datetime.utcnow)
