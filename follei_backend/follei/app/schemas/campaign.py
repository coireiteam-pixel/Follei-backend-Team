<<<<<<< HEAD
from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
=======
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict
>>>>>>> a0e9f77 (saravanan commit)


class CampaignBase(BaseModel):
    name: str
<<<<<<< HEAD
    description: Optional[str] = None
    campaign_type: str
    status: str = "draft"
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    budget: Optional[float] = None
    target_audience: Optional[Dict[str, Any]] = None
    channels: Optional[List[str]] = None
    metadata_: Optional[Dict[str, Any]] = None
=======
    description: str | None = None
    campaign_type: str
    status: str = "draft"
    start_date: datetime | None = None
    end_date: datetime | None = None
    budget: float | None = None
    target_audience: dict[str, Any] | None = None
    channels: list[str] | None = None
    metadata_: dict[str, Any] | None = None
>>>>>>> a0e9f77 (saravanan commit)


class CampaignCreate(CampaignBase):
    tenant_id: str
<<<<<<< HEAD
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
=======
    created_by: str | None = None


class CampaignUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    campaign_type: str | None = None
    status: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    budget: float | None = None
    spent: float | None = None
    target_audience: dict[str, Any] | None = None
    channels: list[str] | None = None
    metadata_: dict[str, Any] | None = None
>>>>>>> a0e9f77 (saravanan commit)


class CampaignResponse(CampaignBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    spent: float
<<<<<<< HEAD
    created_by: Optional[str] = None
=======
    created_by: str | None = None
>>>>>>> a0e9f77 (saravanan commit)
    created_at: datetime
    updated_at: datetime


class CampaignListResponse(BaseModel):
<<<<<<< HEAD
    items: List[CampaignResponse]
=======
    items: list[CampaignResponse]
>>>>>>> a0e9f77 (saravanan commit)
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
<<<<<<< HEAD
    email: Optional[str] = None
    status: str
    message_id: Optional[str] = None
    detail: Optional[str] = None
=======
    email: str | None = None
    status: str
    message_id: str | None = None
    detail: str | None = None
>>>>>>> a0e9f77 (saravanan commit)


class CampaignSendResponse(BaseModel):
    campaign_id: str
    tenant_id: str
    provider: str
    dry_run: bool
    sent: int
    skipped: int
<<<<<<< HEAD
    recipients: List[CampaignSendRecipient]
    sent_at: datetime


class CampaignInboundEmailResponse(BaseModel):
    id: str
    tenant_id: str
    campaign_id: Optional[str] = None
    lead_id: Optional[str] = None
    from_email: Optional[str] = None
    to_email: Optional[str] = None
    subject: Optional[str] = None
    body: Optional[str] = None
    provider: str = "brevo"
    event_type: str = "inbound"
    raw_payload: Dict[str, Any] = {}
    received_at: datetime


class CampaignInboundEmailListResponse(BaseModel):
    items: List[CampaignInboundEmailResponse]
    total: int
    page: int
    page_size: int


class CampaignInboundWebhookResponse(BaseModel):
    received: bool
    inbound_email: CampaignInboundEmailResponse


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


=======
    recipients: list[CampaignSendRecipient]
    sent_at: datetime


>>>>>>> a0e9f77 (saravanan commit)
class CampaignMetricBase(BaseModel):
    campaign_id: str
    metric_type: str
    value: float = 0
<<<<<<< HEAD
    metadata_: Optional[Dict[str, Any]] = None
=======
    metadata_: dict[str, Any] | None = None
>>>>>>> a0e9f77 (saravanan commit)


class CampaignMetricCreate(CampaignMetricBase):
    tenant_id: str


class CampaignMetricResponse(CampaignMetricBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    recorded_at: datetime
