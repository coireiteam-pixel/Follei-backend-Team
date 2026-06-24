from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class LeadBase(BaseModel):
    email: str | None = Field(default=None, examples=["lead@example.com"])
    phone: str | None = Field(default=None, examples=["+1-555-0200"])
    full_name: str | None = Field(default=None, examples=["Jane Lead"])
    company: str | None = Field(default=None, examples=["Acme Corp"])
    job_title: str | None = Field(default=None, examples=["CTO"])
    industry: str | None = Field(default=None, examples=["Technology"])
    website: str | None = Field(default=None, examples=["https://acme.com"])
    source: str | None = Field(default=None, examples=["website"])
    status: str = Field(default="new", examples=["qualified"])
    priority: str = Field(default="medium", examples=["high"])
    tags: list[str] = Field(default_factory=list)
    custom_fields: dict[str, Any] = Field(default_factory=dict)
    score: float | None = Field(default=None, examples=[85.5])
    assigned_to: str | None = Field(default=None, examples=["U001"])
    metadata_: dict[str, Any] = Field(default_factory=dict, alias="metadata")


class LeadCreate(LeadBase):
    tenant_id: str | None = Field(default=None, examples=["T001"])


CreateLeadRequest = LeadCreate


class LeadUpdate(BaseModel):
    email: str | None = None
    phone: str | None = None
    full_name: str | None = None
    company: str | None = None
    job_title: str | None = None
    industry: str | None = None
    website: str | None = None
    source: str | None = None
    status: str | None = None
    priority: str | None = None
    tags: list[str] | None = None
    custom_fields: dict[str, Any] | None = None
    score: float | None = None
    assigned_to: str | None = None
    metadata_: dict[str, Any] | None = Field(default=None, alias="metadata")


UpdateLeadRequest = LeadUpdate


class LeadResponse(LeadBase):
    id: str
    tenant_id: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class LeadListResponse(BaseModel):
    items: list[LeadResponse]
    total: int
    page: int
    page_size: int


class LeadActivityBase(BaseModel):
    activity_type: str | None = Field(default=None, examples=["call"])
    type: str | None = Field(default=None, examples=["call"])
    payload: dict[str, Any] = Field(default_factory=dict)


class LeadActivityCreate(LeadActivityBase):
    lead_id: str | None = Field(default=None, examples=["L001"])


LeadActivityRequest = LeadActivityCreate


class LeadActivityResponse(LeadActivityBase):
    id: str
    lead_id: str
    tenant_id: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class LeadActivityListResponse(BaseModel):
    items: list[LeadActivityResponse]
    total: int
    page: int
    page_size: int


class LeadQualificationBase(BaseModel):
    framework_id: str | None = Field(default=None, examples=["F001"])
    answers: list[dict[str, Any]] = Field(default_factory=list)
    score: float | None = Field(default=None, examples=[75.0])


class LeadQualificationCreate(LeadQualificationBase):
    lead_id: str | None = Field(default=None, examples=["L001"])


LeadQualificationRequest = LeadQualificationCreate


class LeadQualificationResponse(LeadQualificationBase):
    id: str
    lead_id: str
    tenant_id: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class LeadQualificationListResponse(BaseModel):
    items: list[LeadQualificationResponse]
    total: int
    page: int
    page_size: int


class LeadScoreResponse(BaseModel):
    id: str
    lead_id: str
    tenant_id: str | None = None
    model: str
    score: float
    factors: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    calculated_at: datetime | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class LeadScoreListResponse(BaseModel):
    items: list[LeadScoreResponse]
    total: int
    page: int
    page_size: int


class LeadScoreRequest(BaseModel):
    model: str = Field(examples=["default"])
    force_recalculate: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class QualificationFrameworkBase(BaseModel):
    name: str = Field(examples=["BANT"])
    description: str | None = None
    criteria: list[dict[str, Any]] = Field(default_factory=list)
    tenant_id: str | None = Field(default=None, examples=["T001"])


class QualificationFrameworkCreate(QualificationFrameworkBase):
    pass


class QualificationFrameworkResponse(QualificationFrameworkBase):
    id: str
    created_at: datetime
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


QualificationFrameworkRequest = QualificationFrameworkCreate


class QualificationFrameworkListResponse(BaseModel):
    items: list[QualificationFrameworkResponse]
    total: int
    page: int
    page_size: int


class OpportunityBase(BaseModel):
    lead_id: str = Field(examples=["L001"])
    name: str = Field(examples=["Acme deal"])
    value: float = Field(examples=[25000])
    stage: str = Field(default="qualification", examples=["proposal"])
    probability: float = Field(default=0.0, examples=[0.7])
    expected_close_date: str | None = None
    tenant_id: str = Field(examples=["T001"])
    metadata_: dict[str, Any] = Field(default_factory=dict, alias="metadata")


class OpportunityCreate(OpportunityBase):
    pass


class OpportunityUpdate(BaseModel):
    name: str | None = None
    value: float | None = None
    stage: str | None = None
    probability: float | None = None
    expected_close_date: str | None = None
    metadata_: dict[str, Any] | None = Field(default=None, alias="metadata")


UpdateOpportunityRequest = OpportunityUpdate


class OpportunityResponse(OpportunityBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


OpportunityRequest = OpportunityCreate


class OpportunityListResponse(BaseModel):
    items: list[OpportunityResponse]
    total: int
    page: int
    page_size: int


class MeetingBase(BaseModel):
    lead_id: str = Field(examples=["L001"])
    opportunity_id: str | None = None
    title: str = Field(examples=["Demo"])
    meeting_type: str = Field(default="demo", examples=["demo"])
    start_time: str = Field(examples=["2026-07-01T10:00:00+00:00"])
    end_time: str = Field(examples=["2026-07-01T10:30:00+00:00"])
    location: str | None = None
    notes: str | None = None
    status: str = Field(default="scheduled", examples=["completed"])
    tenant_id: str | None = Field(default=None, examples=["T001"])


class MeetingCreate(MeetingBase):
    pass


class MeetingUpdate(BaseModel):
    title: str | None = None
    meeting_type: str | None = None
    start_time: str | None = None
    end_time: str | None = None
    location: str | None = None
    notes: str | None = None
    status: str | None = None


UpdateMeetingRequest = MeetingUpdate


class MeetingResponse(MeetingBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


MeetingRequest = MeetingCreate


class MeetingListResponse(BaseModel):
    items: list[MeetingResponse]
    total: int
    page: int
    page_size: int


class ProposalBase(BaseModel):
    opportunity_id: str | None = Field(default=None, examples=["O001"])
    title: str = Field(examples=["Acme proposal"])
    content: str | None = None
    document_id: str | None = None
    amount: float = Field(default=0.0, examples=[25000])
    currency: str = Field(default="USD", examples=["USD"])
    status: str = Field(default="draft", examples=["sent"])
    tenant_id: str | None = Field(default=None, examples=["T001"])


class ProposalCreate(ProposalBase):
    pass


class ProposalUpdate(BaseModel):
    title: str | None = None
    content: str | None = None
    amount: float | None = None
    currency: str | None = None
    status: str | None = None


class ProposalResponse(ProposalBase):
    id: str
    created_at: datetime
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


ProposalListResponse = ProposalResponse
ProposalRequest = ProposalCreate


class QuoteItem(BaseModel):
    name: str = Field(examples=["Pro plan"])
    quantity: int = Field(examples=[10])
    price: float = Field(examples=[99])
    metadata_: dict[str, Any] = Field(default_factory=dict, alias="metadata")


class QuoteBase(BaseModel):
    opportunity_id: str | None = Field(default=None, examples=["O001"])
    title: str = Field(default="Quote", examples=["Acme quote"])
    items: list[dict[str, Any]] = Field(default_factory=list)
    subtotal: float = Field(default=0.0, examples=[990])
    tax: float = Field(default=0.0, examples=[99])
    total: float = Field(default=0.0, examples=[1089])
    currency: str = Field(default="USD", examples=["USD"])
    status: str = Field(default="draft", examples=["sent"])
    valid_until: str | None = None
    tenant_id: str | None = Field(default=None, examples=["T001"])


class QuoteCreate(QuoteBase):
    pass


class QuoteUpdate(BaseModel):
    title: str | None = None
    items: list[dict[str, Any]] | None = None
    subtotal: float | None = None
    tax: float | None = None
    total: float | None = None
    currency: str | None = None
    status: str | None = None
    valid_until: str | None = None


class QuoteResponse(QuoteBase):
    id: str
    created_at: datetime
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


QuoteListResponse = QuoteResponse
QuoteRequest = QuoteCreate
