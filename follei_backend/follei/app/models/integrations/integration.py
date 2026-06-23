import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, Numeric, String, Text, Uuid
from sqlalchemy.orm import relationship

from app.database.base import Base
from app.core.ids import short_id

class Integration(Base):
    __tablename__ = "integrations"

    id = Column(String(4), primary_key=True, default=short_id, index=True)
    tenant_id = Column(String(4), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String, nullable=False)
    category = Column(String, nullable=False)
    auth_type = Column(String, nullable=False)
    status = Column(String, default="available", nullable=False)
    auth_url = Column(String, nullable=True)
    token_url = Column(String, nullable=True)
    scopes = Column(JSON, default=list, nullable=False)
    webhook_support = Column(String, default="false", nullable=False)
    actions = Column(JSON, default=list, nullable=False)
    metadata_ = Column("metadata", JSON, default=dict, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    connections = relationship("IntegrationConnection", back_populates="integration", cascade="all, delete-orphan")


class IntegrationConnection(Base):
    __tablename__ = "integration_connections"

    id = Column(String(4), primary_key=True, default=short_id, index=True)
    tenant_id = Column(String(4), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    integration_id = Column(String(4), ForeignKey("integrations.id", ondelete="CASCADE"), nullable=False, index=True)
    auth_type = Column(String, nullable=True)
    credentials = Column(JSON, default=dict, nullable=False)
    settings = Column(JSON, default=dict, nullable=False)
    status = Column(String, default="disconnected", nullable=False)
    connected_at = Column(DateTime, nullable=True)
    last_sync = Column(DateTime, nullable=True)
    metadata_ = Column("metadata", JSON, default=dict, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    tenant = relationship("Tenant", back_populates="integration_connections")
    integration = relationship("Integration", back_populates="connections")
    sync_jobs = relationship("SyncJob", back_populates="connection", cascade="all, delete-orphan")
    webhooks = relationship("Webhook", back_populates="connection", cascade="all, delete-orphan")


class SyncJob(Base):
    __tablename__ = "sync_jobs"

    id = Column(String(4), primary_key=True, default=short_id, index=True)
    tenant_id = Column(String(4), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    connection_id = Column(String(4), ForeignKey("integration_connections.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id = Column(String(4), nullable=False)
    sync_type = Column(String, nullable=False)
    entities = Column(JSON, default=list, nullable=False)
    status = Column(String, default="queued", nullable=False)
    records_synced = Column(Integer, default=0, nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    metadata_ = Column("metadata", JSON, default=dict, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    tenant = relationship("Tenant")
    connection = relationship("IntegrationConnection", back_populates="sync_jobs")


class Webhook(Base):
    __tablename__ = "webhooks"

    id = Column(String(4), primary_key=True, default=short_id, index=True)
    tenant_id = Column(String(4), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    connection_id = Column(String(4), ForeignKey("integration_connections.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(String, nullable=False)
    url = Column(String, nullable=False)
    active = Column(String, default="true", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    tenant = relationship("Tenant")
    connection = relationship("IntegrationConnection", back_populates="webhooks")