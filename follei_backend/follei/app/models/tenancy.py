import uuid
from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, JSON, String, Uuid
from sqlalchemy.orm import relationship

from app.database.base import Base
from app.core.ids import short_id

class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(String(4), primary_key=True, default=short_id, index=True)
    name = Column(String, index=True, nullable=False)
    domain = Column(String, unique=True, index=True, nullable=True)
    phone = Column(String, nullable=True)
    status = Column(String, default="active", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    users = relationship("User", back_populates="tenant", cascade="all, delete-orphan")
    agents = relationship("Agent", back_populates="tenant", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="tenant", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="tenant", cascade="all, delete-orphan")
    customers = relationship("Customer", back_populates="tenant", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="tenant", cascade="all, delete-orphan")
    integration_connections = relationship(
        "IntegrationConnection",
        back_populates="tenant",
        cascade="all, delete-orphan",
    )
    leads = relationship("Lead", back_populates="tenant", cascade="all, delete-orphan")


class TenantSettings(Base):
    """ORM mapping for the existing ``tenant_settings`` table."""

    __tablename__ = "tenant_settings"

    id = Column(String(4), primary_key=True, default=short_id)
    tenant_id = Column(String(4), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    settings = Column(JSON, default=dict, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class User(Base):
    __tablename__ = "users"

    id = Column(String(4), primary_key=True, default=short_id, index=True)
    tenant_id = Column(String(4), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    role = Column(String, nullable=False)
    status = Column(String, default="active", nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    tenant = relationship("Tenant", back_populates="users")
    assigned_agent_tasks = relationship(
        "AgentTask",
        back_populates="assignee",
        foreign_keys="AgentTask.assigned_by",
    )
    created_agent_feedback = relationship(
        "AgentFeedback",
        back_populates="creator",
        foreign_keys="AgentFeedback.created_by",
    )
    created_agent_prompt_versions = relationship(
        "AgentPromptVersion",
        back_populates="creator",
        foreign_keys="AgentPromptVersion.created_by",
    )
    created_agent_versions = relationship(
        "AgentVersion",
        back_populates="creator",
        foreign_keys="AgentVersion.created_by",
    )
