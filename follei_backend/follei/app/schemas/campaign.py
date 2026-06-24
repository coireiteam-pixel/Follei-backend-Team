from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime


class CampaignBase(BaseModel):
    name: str
    description: Optional[str] = None
    campaign_type: str
    status: str = "draft"
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    budget: Optional[float] = None
    target_audience: Optional[Dict[str, Any]] = None
    channels: Optional[List[str]] = None
    metadata_: Optional[Dict[str, Any]] = None


class CampaignCreate(CampaignBase):
    tenant_id: str
    created_by: Optional[str] = None


class CampaignUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    campaign_type: Optional[str] = None
    status: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    budget: Optional[float] = None
    spent: Optional[float] = None
    target_audience: Optional[Dict[str, Any]] = None
    channels: Optional[List[str]] = None
    metadata_: Optional[Dict[str, Any]] = None


class CampaignResponse(CampaignBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    spent: float
    created_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class CampaignListResponse(BaseModel):
    items: List[CampaignResponse]
    total: int
    page: int
    page_size: int


class CampaignSendRequest(BaseModel):
    subject: str
    body: str
    provider: str = "gmail"
    dry_run: bool = False


class CampaignSendRecipient(BaseModel):
    lead_id: str
    email: Optional[str] = None
    status: str
    message_id: Optional[str] = None
    detail: Optional[str] = None


class CampaignSendResponse(BaseModel):
    campaign_id: str
    tenant_id: str
    provider: str
    dry_run: bool
    sent: int
    skipped: int
    recipients: List[CampaignSendRecipient]
    sent_at: datetime


class CampaignLeadBase(BaseModel):
    campaign_id: str
    lead_id: str
    status: str = "added"


class CampaignLeadCreate(CampaignLeadBase):
    tenant_id: str


class CampaignLeadResponse(CampaignLeadBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    added_at: datetime
    contacted_at: Optional[datetime] = None
    responded_at: Optional[datetime] = None
    converted_at: Optional[datetime] = None
    metadata_: Optional[Dict[str, Any]] = None


class CampaignMetricBase(BaseModel):
    campaign_id: str
    metric_type: str
    value: float = 0
    metadata_: Optional[Dict[str, Any]] = None


class CampaignMetricCreate(CampaignMetricBase):
    tenant_id: str


class CampaignMetricResponse(CampaignMetricBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    recorded_at: datetime
