import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, Numeric, String, Text, Uuid
from sqlalchemy.orm import relationship

from app.database.base import Base
from app.core.ids import short_id

class Lead(Base):
    __tablename__ = "leads"

    id = Column(String(4), primary_key=True, default=short_id, index=True)
    tenant_id = Column(String(4), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    full_name = Column(String, nullable=True)
    company = Column(String, nullable=True)
    job_title = Column(String, nullable=True)
    industry = Column(String, nullable=True)
    website = Column(String, nullable=True)
    source = Column(String, nullable=True)
    status = Column(String, default="new", nullable=False)
    score = Column(Numeric, nullable=True)
    assigned_to = Column(String(4), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    metadata_ = Column("metadata", JSON, default=dict, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    tenant = relationship("Tenant", back_populates="leads")
    conversations = relationship("Conversation", back_populates="lead")
    activities = relationship("LeadActivity", back_populates="lead", cascade="all, delete-orphan")
    qualifications = relationship("LeadQualification", back_populates="lead", cascade="all, delete-orphan")
    scores = relationship("LeadScore", back_populates="lead", cascade="all, delete-orphan")


class LeadActivity(Base):
    __tablename__ = "lead_activities"

    id = Column(String(4), primary_key=True, default=short_id, index=True)
    tenant_id = Column(String(4), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    lead_id = Column(String(4), ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, index=True)
    activity_type = Column(String, nullable=False)
    payload = Column(JSON, default=dict, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    tenant = relationship("Tenant")
    lead = relationship("Lead", back_populates="activities")


class LeadQualification(Base):
    __tablename__ = "lead_qualifications"

    id = Column(String(4), primary_key=True, default=short_id, index=True)
    tenant_id = Column(String(4), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    lead_id = Column(String(4), ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, index=True)
    framework_id = Column(String(4), nullable=True)
    answers = Column(JSON, default=list, nullable=False)
    score = Column(Numeric, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    tenant = relationship("Tenant")
    lead = relationship("Lead", back_populates="qualifications")


class LeadScore(Base):
    __tablename__ = "lead_scores"

    id = Column(String(4), primary_key=True, default=short_id, index=True)
    tenant_id = Column(String(4), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    lead_id = Column(String(4), ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, index=True)
    model = Column(String, nullable=False)
    score = Column(Numeric, nullable=False)
    factors = Column(JSON, default=dict, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    tenant = relationship("Tenant")
    lead = relationship("Lead", back_populates="scores")