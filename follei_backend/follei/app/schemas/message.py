from typing import Any

from pydantic import BaseModel, Field


class MistralSmsRequest(BaseModel):
    tenant_id: str = Field(examples=["T001"])
    message: str = Field(examples=["Hi"])


class MistralSmsResponse(BaseModel):
    tenant_id: str
    tenant_phone: str
    user_message: str
    mistral_reply: str
    sms_status: str
    sms_sid: str


class SendCustomerMessageRequest(BaseModel):
    tenant_id: str = Field(examples=["t001"])
    customer_phone: str = Field(examples=["+91000000000"])
    message: str = Field(examples=["Your Query"])
    channel: str = Field(default="sms", examples=["sms"])
    customer_name: str | None = None
    conversation_id: str | None = None


class SentMessageData(BaseModel):
    tenant_id: str
    conversation_id: str | None = None
    customer_phone: str
    customer_name: str | None = None
    customer_message: str
    ai_reply: str
    channel: str
    sms_status: str
    sms_provider: str
    provider_message_id: str


class SendCustomerMessageResponse(BaseModel):
    success: bool = True
    code: str = "MESSAGE_SENT"
    message: str = "AI reply sent to customer successfully."
    data: SentMessageData


class CreateMessageRequest(BaseModel):
    content: str = Field(examples=["Here is the answer based on your knowledge base."])
    role: str = Field(default="user", examples=["assistant"])
    user_id: str | None = Field(default=None, examples=["U001"])
    agent_id: str | None = Field(default=None, examples=["A001"])
    citations: list[dict[str, Any]] = Field(
        default_factory=list,
        examples=[[{"source": "pricing-guide", "url": "https://example.com/pricing", "snippet": "Plan starts at $99"}]],
    )
    confidence: float | None = Field(default=None, examples=[0.91])
    tool_calls: list[dict[str, Any]] = Field(
        default_factory=list,
        examples=[[{"name": "search_knowledge_base", "status": "success"}]],
    )
    metadata: dict[str, Any] = Field(default_factory=dict, examples=[{"rag_used": True}])


class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    content: str
    role: str
    user_id: str | None = None
    agent_id: str | None = None
    citations: list[dict[str, Any]] = Field(default_factory=list)
    confidence: float | None = None
    tool_calls: list[dict[str, Any]] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    status: str
    created_at: str


class MessageListResponse(BaseModel):
    items: list[MessageResponse]
    total: int
    page: int
    page_size: int


class UpdateMessageRequest(BaseModel):
    content: str | None = Field(default=None, examples=["Updated answer text"])
    status: str | None = Field(default=None, examples=["edited"])
    metadata: dict[str, Any] | None = Field(default=None, examples=[{"edited_by": "agent"}])


class AttachmentRequest(BaseModel):
    filename: str = Field(examples=["pricing.pdf"])
    url: str = Field(examples=["https://example.com/files/pricing.pdf"])
    mime_type: str | None = Field(default=None, examples=["application/pdf"])
    size_bytes: int | None = Field(default=None, examples=[204800])
    caption: str | None = Field(default=None, examples=["Pricing document"])
    metadata: dict[str, Any] = Field(default_factory=dict, examples=[{"source": "upload"}])


class AttachmentResponse(BaseModel):
    id: str
    message_id: str
    filename: str
    url: str
    mime_type: str | None = None
    size_bytes: int | None = None
    caption: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: str


class AttachmentListResponse(BaseModel):
    items: list[AttachmentResponse]
    total: int
    page: int
    page_size: int


class ReactionRequest(BaseModel):
    emoji: str = Field(examples=["like"])
    user_id: str | None = Field(default=None, examples=["U001"])
    metadata: dict[str, Any] = Field(default_factory=dict, examples=[{"source": "swagger"}])


class ReactionResponse(BaseModel):
    id: str
    message_id: str
    emoji: str
    user_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: str
