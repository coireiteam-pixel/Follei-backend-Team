import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, Numeric, String, Text, Uuid
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship

from app.database.base import Base
from app.core.ids import short_id

class KnowledgeSource(Base):
    __tablename__ = "knowledge_sources"

    id = Column(String(4), primary_key=True, default=short_id, index=True)
    tenant_id = Column(String(4), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String, nullable=False)
    source_type = Column(String, nullable=False)
    config = Column(JSON, default=dict, nullable=False)
    status = Column(String, default="active", nullable=False)
    last_sync = Column(DateTime, nullable=True)
    metadata_ = Column("metadata", JSON, default=dict, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    documents = relationship("Document", back_populates="source", cascade="all, delete-orphan")


class Document(Base):
    __tablename__ = "documents"

    id = Column(String(4), primary_key=True, default=short_id, index=True)
    tenant_id = Column(String(4), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    source_id = Column(String(4), ForeignKey("knowledge_sources.id", ondelete="SET NULL"), nullable=True)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=True)
    file_type = Column(String, nullable=False)
    file_size = Column(Integer, nullable=True)
    status = Column(String, default="processing", nullable=False)
    total_pages = Column(Integer, default=0, nullable=False)
    total_chunks = Column(Integer, default=0, nullable=False)
    summary = Column(Text, nullable=True)
    keywords = Column(ARRAY(String).with_variant(JSON, "sqlite"), default=list, nullable=False)
    metadata_ = Column("metadata", JSON, default=dict, nullable=False)
    indexed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    tenant = relationship("Tenant", back_populates="documents")
    source = relationship("KnowledgeSource", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")
    pages = relationship("DocumentPage", back_populates="document", cascade="all, delete-orphan")
    versions = relationship("DocumentVersion", back_populates="document", cascade="all, delete-orphan")
    conversation_citations = relationship("ConversationCitation", back_populates="document")


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(String(4), primary_key=True, default=short_id, index=True)
    tenant_id = Column(String(4), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    document_id = Column(String(4), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    page = Column(Integer, nullable=True)
    section = Column(String, nullable=True)
    heading = Column(String, nullable=True)
    tags = Column(ARRAY(String).with_variant(JSON, "sqlite"), default=list, nullable=False)
    embedding_hash = Column(String, nullable=True)
    vector_id = Column(String, nullable=True)
    metadata_ = Column("metadata", JSON, default=dict, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    tenant = relationship("Tenant")
    document = relationship("Document", back_populates="chunks")
    citations = relationship("ChunkCitation", back_populates="chunk")
    conversation_citations = relationship("ConversationCitation", back_populates="chunk")
    embeddings = relationship("ChunkEmbedding", back_populates="chunk", cascade="all, delete-orphan")


class DocumentPage(Base):
    __tablename__ = "document_pages"

    id = Column(String(4), primary_key=True, default=short_id, index=True)
    tenant_id = Column(String(4), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    document_id = Column(String(4), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    page_number = Column(Integer, nullable=False)
    text = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, default=dict, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    tenant = relationship("Tenant")
    document = relationship("Document", back_populates="pages")


class DocumentVersion(Base):
    __tablename__ = "document_versions"

    id = Column(String(4), primary_key=True, default=short_id, index=True)
    tenant_id = Column(String(4), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    document_id = Column(String(4), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    version = Column(Integer, nullable=False)
    change_summary = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, default=dict, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    tenant = relationship("Tenant")
    document = relationship("Document", back_populates="versions")


class ChunkCitation(Base):
    __tablename__ = "chunk_citations"

    id = Column(String(4), primary_key=True, default=short_id, index=True)
    tenant_id = Column(String(4), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    message_id = Column(String(4), ForeignKey("conversation_messages.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_id = Column(String(4), ForeignKey("document_chunks.id", ondelete="SET NULL"), nullable=True)
    quote = Column(Text, nullable=True)
    confidence = Column(Numeric, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    tenant = relationship("Tenant")
    message = relationship("Message", back_populates="chunk_citations")
    chunk = relationship("DocumentChunk", back_populates="citations")


class ChunkEmbedding(Base):
    __tablename__ = "chunk_embeddings"

    id = Column(String(4), primary_key=True, default=short_id, index=True)
    tenant_id = Column(String(4), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_id = Column(String(4), ForeignKey("document_chunks.id", ondelete="CASCADE"), nullable=False, index=True)
    vector_id = Column(String, nullable=False)
    model = Column(String, nullable=False)
    dimensions = Column(Integer, nullable=True)
    distance_metric = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    tenant = relationship("Tenant")
    chunk = relationship("DocumentChunk", back_populates="embeddings")


class KnowledgeFeedback(Base):
    __tablename__ = "knowledge_feedback"

    id = Column(String(4), primary_key=True, default=short_id, index=True)
    tenant_id = Column(String(4), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_id = Column(String(4), ForeignKey("document_chunks.id", ondelete="CASCADE"), nullable=False, index=True)
    message_id = Column(String(4), ForeignKey("conversation_messages.id", ondelete="SET NULL"), nullable=True)
    rating = Column(String, nullable=False)
    feedback = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    tenant = relationship("Tenant")
    chunk = relationship("DocumentChunk")
    message = relationship("Message")


class KnowledgeTag(Base):
    __tablename__ = "knowledge_tags"

    id = Column(String(4), primary_key=True, default=short_id, index=True)
    tenant_id = Column(String(4), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, default=dict, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    tenant = relationship("Tenant")
