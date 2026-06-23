import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, Numeric, String, Text, Uuid
from sqlalchemy.orm import relationship

from app.database.base import Base
from app.core.ids import short_id

class Customer(Base):
    __tablename__ = "customers"

    id = Column(String(4), primary_key=True, default=short_id, index=True)
    tenant_id = Column(String(4), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    company = Column(String, nullable=True)
    industry = Column(String, nullable=True)
    website = Column(String, nullable=True)
    address = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, default=dict, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    tenant = relationship("Tenant", back_populates="customers")
    conversations = relationship("Conversation", back_populates="customer")
    contacts = relationship("CustomerContact", back_populates="customer", cascade="all, delete-orphan")
    health_scores = relationship("CustomerHealthScore", back_populates="customer", cascade="all, delete-orphan")
    events = relationship("CustomerEvent", back_populates="customer", cascade="all, delete-orphan")
    subscriptions = relationship("Subscription", back_populates="customer")
    agent_memories = relationship("AgentMemory", back_populates="customer")


class CustomerContact(Base):
    __tablename__ = "customer_contacts"

    id = Column(String(4), primary_key=True, default=short_id, index=True)
    tenant_id = Column(String(4), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id = Column(String(4), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    role = Column(String, nullable=True)
    is_primary = Column(String, default="false", nullable=False)
    metadata_ = Column("metadata", JSON, default=dict, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    tenant = relationship("Tenant")
    customer = relationship("Customer", back_populates="contacts")


class CustomerHealthScore(Base):
    __tablename__ = "customer_health_scores"

    id = Column(String(4), primary_key=True, default=short_id, index=True)
    tenant_id = Column(String(4), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id = Column(String(4), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True)
    score = Column(Numeric, nullable=True)
    factors = Column(JSON, default=dict, nullable=False)
    calculated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    tenant = relationship("Tenant")
    customer = relationship("Customer", back_populates="health_scores")


class CustomerEvent(Base):
    __tablename__ = "customer_events"

    id = Column(String(4), primary_key=True, default=short_id, index=True)
    tenant_id = Column(String(4), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id = Column(String(4), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(String, nullable=False)
    payload = Column(JSON, default=dict, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    tenant = relationship("Tenant")
    customer = relationship("Customer", back_populates="events")
