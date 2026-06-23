import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, JSON, Numeric, String, Text, Uuid
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship

from app.database.base import Base
from app.core.ids import short_id


class FAQ(Base):
    __tablename__ = "faqs"

    id = Column(String(4), primary_key=True, default=short_id)
    tenant_id = Column(String(4), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    embedding_vector_id = Column(String(4), nullable=True)
    tags = Column(ARRAY(String).with_variant(JSON, "sqlite"), default=list, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class Policy(Base):
    __tablename__ = "policies"

    id = Column(String(4), primary_key=True, default=short_id)
    tenant_id = Column(String(4), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String, nullable=False)
    body = Column(Text, nullable=True)
    policy_type = Column(String, nullable=True)
    status = Column(String, default="active", nullable=False)
    metadata_ = Column("metadata", JSON, default=dict, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class Procedure(Base):
    __tablename__ = "procedures"

    id = Column(String(4), primary_key=True, default=short_id)
    tenant_id = Column(String(4), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String, nullable=False)
    steps = Column(JSON, default=list, nullable=False)
    status = Column(String, default="active", nullable=False)
    metadata_ = Column("metadata", JSON, default=dict, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class Product(Base):
    __tablename__ = "products"

    id = Column(String(4), primary_key=True, default=short_id)
    tenant_id = Column(String(4), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String, nullable=False)
    sku = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, default=dict, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class Service(Base):
    __tablename__ = "services"

    id = Column(String(4), primary_key=True, default=short_id)
    tenant_id = Column(String(4), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, default=dict, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class PricingModel(Base):
    __tablename__ = "pricing_models"

    id = Column(String(4), primary_key=True, default=short_id)
    tenant_id = Column(String(4), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String, nullable=False)
    model_type = Column(String, nullable=False)
    tiers = Column(JSON, default=list, nullable=False)
    metadata_ = Column("metadata", JSON, default=dict, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class PricingRule(Base):
    __tablename__ = "pricing_rules"

    id = Column(String(4), primary_key=True, default=short_id)
    tenant_id = Column(String(4), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    pricing_model_id = Column(String(4), ForeignKey("pricing_models.id", ondelete="CASCADE"), nullable=True)
    name = Column(String, nullable=False)
    conditions = Column(JSON, default=dict, nullable=False)
    actions = Column(JSON, default=dict, nullable=False)
    priority = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class Competitor(Base):
    __tablename__ = "competitors"

    id = Column(String(4), primary_key=True, default=short_id)
    tenant_id = Column(String(4), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String, nullable=False)
    website = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, default=dict, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class CompetitorFeature(Base):
    __tablename__ = "competitor_features"

    id = Column(String(4), primary_key=True, default=short_id)
    tenant_id = Column(String(4), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    competitor_id = Column(String(4), ForeignKey("competitors.id", ondelete="CASCADE"), nullable=False)
    feature_name = Column(String, nullable=False)
    comparison = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSON, default=dict, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Event(Base):
    __tablename__ = "events"

    id = Column(String(4), primary_key=True, default=short_id)
    tenant_id = Column(String(4), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(String, nullable=False)
    payload = Column(JSON, default=dict, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class AnalyticsDaily(Base):
    __tablename__ = "analytics_daily"

    id = Column(String(4), primary_key=True, default=short_id)
    tenant_id = Column(String(4), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    metric_date = Column(Date, nullable=False)
    metric_name = Column(String, nullable=False)
    metric_value = Column(Numeric, default=0, nullable=False)
    dimensions = Column(JSON, default=dict, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class AnalyticsMonthly(Base):
    __tablename__ = "analytics_monthly"

    id = Column(String(4), primary_key=True, default=short_id)
    tenant_id = Column(String(4), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    metric_month = Column(Date, nullable=False)
    metric_name = Column(String, nullable=False)
    metric_value = Column(Numeric, default=0, nullable=False)
    dimensions = Column(JSON, default=dict, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class ModelUsage(Base):
    __tablename__ = "model_usage"

    id = Column(String(4), primary_key=True, default=short_id)
    tenant_id = Column(String(4), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    model = Column(String, nullable=False)
    provider = Column(String, nullable=True)
    prompt_tokens = Column(Integer, default=0, nullable=False)
    completion_tokens = Column(Integer, default=0, nullable=False)
    total_tokens = Column(Integer, default=0, nullable=False)
    cost = Column(Numeric, default=0, nullable=False)
    latency_ms = Column(Integer, nullable=True)
    metadata_ = Column("metadata", JSON, default=dict, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class RetrievalLog(Base):
    __tablename__ = "retrieval_logs"

    id = Column(String(4), primary_key=True, default=short_id)
    tenant_id = Column(String(4), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    query = Column(Text, nullable=False)
    results = Column(JSON, default=list, nullable=False)
    scores = Column(JSON, default=list, nullable=False)
    latency_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class EvaluationResult(Base):
    __tablename__ = "evaluation_results"

    id = Column(String(4), primary_key=True, default=short_id)
    tenant_id = Column(String(4), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    subject_type = Column(String, nullable=False)
    subject_id = Column(String(4), nullable=True)
    evaluator = Column(String, nullable=True)
    score = Column(Numeric, nullable=True)
    result = Column(JSON, default=dict, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Plan(Base):
    __tablename__ = "plans"

    id = Column(String(4), primary_key=True, default=short_id)
    name = Column(String, nullable=False, unique=True)
    description = Column(Text, nullable=True)
    price = Column(Numeric, default=0, nullable=False)
    currency = Column(String, default="USD", nullable=False)
    billing_interval = Column(String, default="month", nullable=False)
    feature_limits = Column(JSON, default=dict, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(String(4), primary_key=True, default=short_id)
    tenant_id = Column(String(4), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    plan_name = Column(String, nullable=False)
    status = Column(String, default="active", nullable=False)
    current_period_start = Column(DateTime, nullable=True)
    current_period_end = Column(DateTime, nullable=True)
    plan_id = Column(String(4), ForeignKey("plans.id", ondelete="SET NULL"), nullable=True)
    customer_id = Column(String(4), ForeignKey("customers.id", ondelete="SET NULL"), nullable=True)
    metadata_ = Column("metadata", JSON, default=dict, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    customer = relationship("Customer", back_populates="subscriptions")


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(String(4), primary_key=True, default=short_id)
    tenant_id = Column(String(4), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    subscription_id = Column(String(4), ForeignKey("subscriptions.id", ondelete="SET NULL"), nullable=True)
    customer_id = Column(String(4), ForeignKey("customers.id", ondelete="SET NULL"), nullable=True)
    invoice_number = Column(String, nullable=True)
    amount = Column(Numeric, default=0, nullable=False)
    currency = Column(String, default="USD", nullable=False)
    status = Column(String, default="draft", nullable=False)
    due_date = Column(Date, nullable=True)
    paid_at = Column(DateTime, nullable=True)
    metadata_ = Column("metadata", JSON, default=dict, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class Payment(Base):
    __tablename__ = "payments"

    id = Column(String(4), primary_key=True, default=short_id)
    tenant_id = Column(String(4), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    invoice_id = Column(String(4), ForeignKey("invoices.id", ondelete="SET NULL"), nullable=True)
    customer_id = Column(String(4), ForeignKey("customers.id", ondelete="SET NULL"), nullable=True)
    amount = Column(Numeric, default=0, nullable=False)
    currency = Column(String, default="USD", nullable=False)
    status = Column(String, default="pending", nullable=False)
    provider = Column(String, nullable=True)
    provider_payment_id = Column(Text, nullable=True)
    paid_at = Column(DateTime, nullable=True)
    metadata_ = Column("metadata", JSON, default=dict, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class Credit(Base):
    __tablename__ = "credits"

    id = Column(String(4), primary_key=True, default=short_id)
    tenant_id = Column(String(4), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    balance = Column(Numeric, default=0, nullable=False)
    currency = Column(String, default="USD", nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class CreditTransaction(Base):
    __tablename__ = "credit_transactions"

    id = Column(String(4), primary_key=True, default=short_id)
    tenant_id = Column(String(4), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    credit_id = Column(String(4), ForeignKey("credits.id", ondelete="SET NULL"), nullable=True)
    transaction_type = Column(String, nullable=False)
    amount = Column(Numeric, nullable=False)
    balance_after = Column(Numeric, nullable=True)
    metadata_ = Column("metadata", JSON, default=dict, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
