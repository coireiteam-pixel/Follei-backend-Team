from typing import Any, Literal

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class CreateIntegrationRequest(BaseModel):
    """Public metadata only; provider credentials are loaded from .env."""

    model_config = ConfigDict(extra="forbid")

    tenant_id: str = Field(min_length=1, examples=["P427"])
    name: str = Field(min_length=1, examples=["Twilio SMS"])
    provider: Literal["twilio"] = Field(examples=["twilio"])
    phone_number: str | None = Field(
        default=None,
        pattern=r"^\+[1-9]\d{7,14}$",
        examples=["+15672467340"],
    )
    description: str | None = Field(default=None, examples=["Twilio SMS Integration"])
    status: Literal["active", "inactive"] = Field(default="active", examples=["active"])

class CreateIntegrationResponse(BaseModel):
    success: bool = True
    message: str = "Integration created successfully"
    integration_id: str
    tenant_id: str


class IntegrationConnectionRequest(BaseModel):
    integration_id: str = Field(examples=["I001"])
    tenant_id: str = Field(examples=["P427"])
    auth_type: str | None = None
    config: dict[str, Any] = Field(default_factory=dict, examples=[{"api_key": "xxx"}])
    credentials: dict[str, Any] = Field(default_factory=dict, exclude=True)
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


class TwilioSmsWebhookRequest(BaseModel):
    """Canonical SMS payload accepted from Twilio forms and Swagger JSON."""

    model_config = ConfigDict(populate_by_name=True)

    from_phone: str = Field(
        validation_alias=AliasChoices("from", "From"),
        serialization_alias="from",
        examples=["+919876543210"],
    )
    to_phone: str = Field(
        validation_alias=AliasChoices("to", "To"),
        serialization_alias="to",
        examples=["+15672467340"],
    )
    body: str = Field(
        validation_alias=AliasChoices("body", "Body"),
        examples=["What are your pricing plans?"],
    )
    message_sid: str | None = Field(
        default=None,
        validation_alias=AliasChoices("message_sid", "MessageSid"),
        examples=["SMXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"],
    )
    timestamp: str | None = Field(
        default=None,
        validation_alias=AliasChoices("timestamp", "Timestamp"),
    )


class InboundWebhookResponse(BaseModel):
    received: bool
    event_id: str
    customer_phone: str | None = None
    tenant_phone: str | None = None
    customer_message: str | None = None
    ai_reply: str | None = None
    sms_status: str | None = None
    provider_message_id: str | None = None


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
