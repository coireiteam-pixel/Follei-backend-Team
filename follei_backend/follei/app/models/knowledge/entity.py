import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, Numeric, String, Text, Uuid
from sqlalchemy.orm import relationship

from app.database.base import Base
from app.core.ids import short_id

class Entity(Base):
    __tablename__ = "entities"

    id = Column(String(4), primary_key=True, default=short_id, index=True)
    tenant_id = Column(String(4), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String, nullable=False)
    entity_type = Column(String, nullable=False)
    metadata_ = Column("metadata", JSON, default=dict, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    tenant = relationship("Tenant")
    aliases = relationship("EntityAlias", back_populates="entity", cascade="all, delete-orphan")
    attributes = relationship("EntityAttribute", back_populates="entity", cascade="all, delete-orphan")
    relations_from = relationship("EntityRelation", foreign_keys="EntityRelation.from_entity_id", back_populates="from_entity", cascade="all, delete-orphan")
    relations_to = relationship("EntityRelation", foreign_keys="EntityRelation.to_entity_id", back_populates="to_entity", cascade="all, delete-orphan")


class EntityAlias(Base):
    __tablename__ = "entity_aliases"

    id = Column(String(4), primary_key=True, default=short_id, index=True)
    tenant_id = Column(String(4), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    entity_id = Column(String(4), ForeignKey("entities.id", ondelete="CASCADE"), nullable=False, index=True)
    alias = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    tenant = relationship("Tenant")
    entity = relationship("Entity", back_populates="aliases")


class EntityAttribute(Base):
    __tablename__ = "entity_attributes"

    id = Column(String(4), primary_key=True, default=short_id, index=True)
    tenant_id = Column(String(4), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    entity_id = Column(String(4), ForeignKey("entities.id", ondelete="CASCADE"), nullable=False, index=True)
    key = Column(String, nullable=False)
    value = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    tenant = relationship("Tenant")
    entity = relationship("Entity", back_populates="attributes")


class EntityRelation(Base):
    __tablename__ = "entity_relations"

    id = Column(String(4), primary_key=True, default=short_id, index=True)
    tenant_id = Column(String(4), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    from_entity_id = Column(String(4), ForeignKey("entities.id", ondelete="CASCADE"), nullable=False, index=True)
    to_entity_id = Column(String(4), ForeignKey("entities.id", ondelete="CASCADE"), nullable=False, index=True)
    relation_type = Column(String, nullable=False)
    weight = Column(Numeric, nullable=True)
    metadata_ = Column("metadata", JSON, default=dict, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    tenant = relationship("Tenant")
    from_entity = relationship("Entity", foreign_keys=[from_entity_id], back_populates="relations_from")
    to_entity = relationship("Entity", foreign_keys=[to_entity_id], back_populates="relations_to")