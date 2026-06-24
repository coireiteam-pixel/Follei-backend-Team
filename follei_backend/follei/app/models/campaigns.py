import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, String, Text, Boolean, Numeric, JSON
from sqlalchemy.orm import relationship

from app.database.base import Base
from app.core.ids import short_id


class Campaign(Base):
    __tablename__ = "campaigns"

    id = Column(String(4), primary_key=True, default=short_id, index=True)
    tenant_id = Column(String(4), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    campaign_type = Column(String, nullable=False)  # email, sms, social, multi-channel
    status = Column(String, nullable=False, default="draft")  # draft, active, paused, completed
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    budget = Column(Numeric, nullable=True)
    spent = Column(Numeric, nullable=False, default=0)
    target_audience = Column(JSON, nullable=True)  # segments, filters, criteria
    channels = Column(JSON, nullable=True)  # list of channels used
    metadata_ = Column("metadata", JSON, default=dict, nullable=False)
    created_by = Column(String(4), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    tenant = relationship("Tenant")
    creator = relationship("User")
    leads = relationship("CampaignLead", back_populates="campaign", cascade="all, delete-orphan")
    metrics = relationship("CampaignMetric", back_populates="campaign", cascade="all, delete-orphan")


class CampaignLead(Base):
    __tablename__ = "campaign_leads"

    id = Column(String(4), primary_key=True, default=short_id, index=True)
    tenant_id = Column(String(4), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    campaign_id = Column(String(4), ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False, index=True)
    lead_id = Column(String(4), ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String, nullable=False, default="added")  # added, contacted, responded, converted
    added_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    contacted_at = Column(DateTime, nullable=True)
    responded_at = Column(DateTime, nullable=True)
    converted_at = Column(DateTime, nullable=True)
    metadata_ = Column("metadata", JSON, default=dict, nullable=False)

    # Relationships
    tenant = relationship("Tenant")
    campaign = relationship("Campaign", back_populates="leads")
    lead = relationship("Lead")


class CampaignMetric(Base):
    __tablename__ = "campaign_metrics"

    id = Column(String(4), primary_key=True, default=short_id, index=True)
    tenant_id = Column(String(4), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    campaign_id = Column(String(4), ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False, index=True)
    metric_type = Column(String, nullable=False)  # sent, delivered, opened, clicked, replied, converted
    value = Column(Numeric, nullable=False, default=0)
    recorded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    metadata_ = Column("metadata", JSON, default=dict, nullable=False)

    # Relationships
    tenant = relationship("Tenant")
    campaign = relationship("Campaign", back_populates="metrics")