from typing import Any

from pydantic import BaseModel, Field


class IntegrationConnectionRequest(BaseModel):
    integration_id: str = Field(examples=["I001"])
    tenant_id: str = Field(examples=["T001"])
    auth_type: str | None = None
    config: dict[str, Any] = Field(default_factory=dict, examples=[{"api_key": "xxx"}])
    settings: dict[str, Any] = Field(default_factory=dict, examples=[{"sync_frequency": "hourly"}])


class IntegrationConnectionResponse(BaseModel):
    id: str
    integration_id: str
    integration_name: str
    tenant_id: str
    status: str
    connected_at: str
    last_sync: str | None = None
    integration: dict[str, Any]
    auth_type: str
    settings: dict[str, Any]
    sync_jobs: list[dict[str, Any]]


class IntegrationConnectionSummary(BaseModel):
    id: str
    integration_id: str
    integration_name: str
    tenant_id: str
    status: str
    connected_at: str
    last_sync: str | None = None


class IntegrationConnectionListResponse(BaseModel):
    items: list[IntegrationConnectionSummary]
    total: int
    page: int
    page_size: int


class UpdateIntegrationConnectionRequest(BaseModel):
    settings: dict[str, Any] | None = None


class IntegrationResponse(BaseModel):
    id: str
    name: str
    category: str
    auth_type: str
    status: str
    auth_url: str | None = None
    token_url: str | None = None
    scopes: list[str] | None = None
    webhook_support: bool
    actions: list[str]


class IntegrationSummary(BaseModel):
    id: str
    name: str
    category: str
    auth_type: str
    status: str


class IntegrationListResponse(BaseModel):
    items: list[IntegrationSummary]
    total: int
    page: int
    page_size: int


class SyncRequest(BaseModel):
    sync_type: str = Field(examples=["full"])
    entities: list[str] = Field(default_factory=list, examples=[["contacts", "deals"]])


class SyncJobResponse(BaseModel):
    id: str
    job_id: str
    connection_id: str
    status: str
    sync_type: str
    entities: list[str]
    records_synced: int
    started_at: str
    completed_at: str | None = None


class SyncJobListResponse(BaseModel):
    items: list[SyncJobResponse]
    total: int
    page: int
    page_size: int


class WebhookRequest(BaseModel):
    event_type: str = Field(examples=["contact.created"])
    url: str = Field(examples=["https://example.com/webhook"])
    active: bool = True


class WebhookResponse(BaseModel):
    id: str
    connection_id: str
    event_type: str
    url: str
    active: bool
    created_at: str


class WebhookListResponse(BaseModel):
    items: list[WebhookResponse]
    total: int
    page: int
    page_size: int


class InboundWebhookRequest(BaseModel):
    event_type: str
    payload: dict[str, Any]
    timestamp: str | None = None


class InboundWebhookResponse(BaseModel):
    received: bool
    event_id: str


class WebhookEventResponse(BaseModel):
    id: str
    integration_id: str
    event_type: str
    payload: dict[str, Any]
    status: str
    created_at: str


class WebhookEventListResponse(BaseModel):
    items: list[WebhookEventResponse]
    total: int
    page: int
    page_size: int