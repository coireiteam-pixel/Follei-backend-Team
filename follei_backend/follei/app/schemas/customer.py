from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class CustomerBase(BaseModel):
    name: str = Field(examples=["Acme Corp"])
    email: str | None = Field(default=None, examples=["admin@acme.com"])
    phone: str | None = Field(default=None, examples=["+1-555-0100"])
    company: str | None = Field(default=None, examples=["Acme Inc"])
    industry: str | None = Field(default=None, examples=["Technology"])
    website: str | None = Field(default=None, examples=["https://acme.com"])
    address: str | None = Field(default=None, examples=["123 Main St"])
    status: str = Field(default="active", examples=["active"])
    plan_id: str | None = Field(default=None, examples=["P001"])
    mrr: float = 0.0
    arr: float = 0.0
    company_size: str | None = None
    billing_address: dict[str, Any] = Field(default_factory=dict)
    custom_fields: dict[str, Any] = Field(default_factory=dict)
    health_score: float = 0.0
    churn_risk: str = "unknown"
    expansion_score: float = 0.0
    contacts: list[Any] = Field(default_factory=list)
    conversations: list[Any] = Field(default_factory=list)
    events: list[Any] = Field(default_factory=list)
    metadata_: dict[str, Any] = Field(default_factory=dict, alias="metadata")


class CustomerContactBase(BaseModel):
    name: str = Field(examples=["Priya Sharma"])
    email: str | None = Field(default=None, examples=["priya@acme.com"])
    phone: str | None = Field(default=None, examples=["+1-555-0101"])
    role: str | None = Field(default=None, examples=["Admin"])
    is_primary: bool = False
    metadata_: dict[str, Any] = Field(default_factory=dict, alias="metadata")


class CustomerEventBase(BaseModel):
    event_type: str | None = Field(default=None, examples=["feature_used"])
    type: str | None = Field(default=None, examples=["feature_used"])
    feature: str | None = None
    timestamp: datetime | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class CustomerCreate(CustomerBase):
    tenant_id: str = Field(examples=["T001"])


class CustomerUpdate(BaseModel):
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    company: str | None = None
    industry: str | None = None
    website: str | None = None
    address: str | None = None
    status: str | None = None
    plan_id: str | None = None
    mrr: float | None = None
    arr: float | None = None
    company_size: str | None = None
    billing_address: dict[str, Any] | None = None
    custom_fields: dict[str, Any] | None = None
    health_score: float | None = None
    churn_risk: str | None = None
    expansion_score: float | None = None
    metadata_: dict[str, Any] | None = Field(default=None, alias="metadata")


class CustomerResponse(CustomerBase):
    id: str
    tenant_id: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CustomerListResponse(BaseModel):
    items: list[CustomerResponse]
    total: int
    page: int
    page_size: int


CreateCustomerRequest = CustomerCreate
UpdateCustomerRequest = CustomerUpdate


class CustomerContactCreate(CustomerContactBase):
    customer_id: str | None = Field(default=None, examples=["C001"])


class CustomerContactResponse(CustomerContactBase):
    id: str
    customer_id: str
    tenant_id: str | None = None
    created_at: datetime
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class CustomerContactListResponse(BaseModel):
    items: list[CustomerContactResponse]
    total: int
    page: int
    page_size: int


CustomerContactRequest = CustomerContactCreate
CreateCustomerContactRequest = CustomerContactCreate


class CustomerHealthScoreResponse(BaseModel):
    id: str
    customer_id: str
    tenant_id: str | None = None
    score: float | None = None
    model: str = "default"
    factors: dict[str, Any] = Field(default_factory=dict)
    trend: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    calculated_at: datetime
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


HealthScoreResponse = CustomerHealthScoreResponse
HealthScoreListResponse = CustomerHealthScoreResponse


class CustomerEventCreate(CustomerEventBase):
    customer_id: str | None = Field(default=None, examples=["C001"])


class CustomerEventResponse(CustomerEventBase):
    id: str
    customer_id: str
    tenant_id: str | None = None
    timestamp: datetime | str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


CustomerEventRequest = CustomerEventCreate
CustomerEventListResponse = CustomerEventResponse
CreateCustomerEventRequest = CustomerEventCreate


class HealthScoreRequest(BaseModel):
    force_recalculate: bool = False
    model: str = "default"
    metadata: dict[str, Any] = Field(default_factory=dict)


class RenewalRequest(BaseModel):
    renewal_date: str = Field(examples=["2026-12-31"])
    expected_value: float = Field(examples=[25000])
    probability: float = Field(examples=[0.8])
    notes: str | None = None


class RenewalResponse(BaseModel):
    id: str
    customer_id: str
    tenant_id: str | None = None
    renewal_date: str
    expected_value: float
    actual_value: float | None = None
    probability: float
    status: str
    notes: str | None = None
    closed_date: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


RenewalListResponse = RenewalResponse


class UpdateRenewalRequest(BaseModel):
    status: str | None = None
    actual_value: float | None = None
    notes: str | None = None
