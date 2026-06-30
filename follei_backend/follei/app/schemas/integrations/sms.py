"""Validation contracts for SMS integration endpoints and MCP tools."""

from datetime import datetime
from typing import Literal

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


E164_PATTERN = r"^\+[1-9]\d{7,14}$"


class SmsSendRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: str = Field(min_length=1, examples=["T001"])
    to_phone: str = Field(pattern=E164_PATTERN, examples=["+919876543210"])
    body: str = Field(min_length=1, max_length=1600, examples=["Your Follei appointment is confirmed."])


class SmsMessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    conversation_id: str
    direction: Literal["inbound", "outbound"]
    from_phone: str
    to_phone: str
    body: str
    status: str
    twilio_message_sid: str
    created_at: datetime
    updated_at: datetime


class SmsSendResponse(BaseModel):
    success: bool = True
    message: SmsMessageResponse


class SmsMessageHistoryResponse(BaseModel):
    tenant_id: str
    phone_number: str
    items: list[SmsMessageResponse]
    total: int


class SmsConversationResponse(BaseModel):
    id: str
    tenant_id: str
    contact_id: str
    phone_number: str
    status: str
    created_at: datetime
    updated_at: datetime


class TwilioSmsPayload(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    from_phone: str = Field(validation_alias=AliasChoices("From", "from", "from_phone"), pattern=E164_PATTERN)
    to_phone: str = Field(validation_alias=AliasChoices("To", "to", "to_phone"), pattern=E164_PATTERN)
    body: str = Field(validation_alias=AliasChoices("Body", "body"), min_length=1, max_length=1600)
    message_sid: str = Field(validation_alias=AliasChoices("MessageSid", "message_sid"), min_length=1, max_length=64)


class SmsWebhookResponse(BaseModel):
    received: bool = True
    duplicate: bool = False
    inbound_message_id: str
    conversation_id: str
    reply_message_id: str | None = None
    reply_status: str | None = None


class SmsSearchRequest(BaseModel):
    tenant_id: str = Field(min_length=1)
    query: str = Field(min_length=1, max_length=255)
    limit: int = Field(default=50, ge=1, le=200)
