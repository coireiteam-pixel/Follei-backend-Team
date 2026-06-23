from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class CreateConversationRequest(BaseModel):
    title: str | None = Field(default=None, examples=["Pricing question"])
    type: str | None = Field(default=None, examples=["sales"])
    channel: str | None = Field(default=None, examples=["web"])
    status: str = Field(default="open", examples=["open"])
    lead_id: str | None = Field(default=None, examples=["L001"])
    customer_id: str | None = Field(default=None, examples=["C001"])
    agent_id: str | None = Field(default=None, examples=["A001"])
    metadata_: dict[str, Any] = Field(default_factory=dict, alias="metadata")
    tenant_id: str = Field(examples=["T001"])

    @property
    def metadata(self) -> dict[str, Any]:
        return self.metadata_


class UpdateConversationRequest(BaseModel):
    title: str | None = None
    type: str | None = None
    channel: str | None = None
    status: str | None = None
    lead_id: str | None = None
    customer_id: str | None = None
    agent_id: str | None = None
    metadata_: dict[str, Any] | None = Field(default=None, alias="metadata")


class ConversationResponse(BaseModel):
    id: str
    tenant_id: str
    title: str | None = None
    type: str | None = None
    channel: str | None = None
    status: str
    lead_id: str | None = None
    customer_id: str | None = None
    agent_id: str | None = None
    participants: list[Any] = Field(default_factory=list)
    message_count: int = 0
    started_at: datetime | None = None
    ended_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    metadata_: dict[str, Any] = Field(default_factory=dict, alias="metadata")

    model_config = {"from_attributes": True}


class ConversationListResponse(BaseModel):
    items: list[ConversationResponse]
    total: int
    page: int
    page_size: int


class MessageBase(BaseModel):
    content: str = Field(examples=["The Pro plan starts at $99."])
    role: str = Field(default="user", examples=["assistant"])
    message_type: str = Field(default="text", examples=["text"])
    metadata_: dict[str, Any] = Field(default_factory=dict, alias="metadata")


class MessageCreate(MessageBase):
    conversation_id: str = Field(examples=["C001"])
    sender_type: str | None = Field(default=None, examples=["user"])
    sender_id: str | None = Field(default=None, examples=["U001"])


class MessageUpdate(BaseModel):
    content: str | None = None
    metadata_: dict[str, Any] | None = Field(default=None, alias="metadata")


class MessageResponse(MessageBase):
    id: str
    conversation_id: str
    tenant_id: str
    sender_type: str | None = None
    sender_id: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class MessageListResponse(BaseModel):
    items: list[MessageResponse]
    total: int
    page: int
    page_size: int


class ConversationActionBase(BaseModel):
    action_type: str = Field(examples=["transfer"])
    payload: dict[str, Any] = Field(default_factory=dict)
    status: str = Field(default="completed", examples=["completed"])


class ConversationActionCreate(ConversationActionBase):
    conversation_id: str = Field(examples=["C001"])
    agent_id: str | None = Field(default=None, examples=["A001"])


class ConversationActionResponse(ConversationActionBase):
    id: str
    conversation_id: str
    tenant_id: str
    agent_id: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ConversationAnalyticsResponse(BaseModel):
    id: str
    conversation_id: str
    tenant_id: str
    metrics: dict[str, Any] = Field(default_factory=dict)
    measured_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}


class BuyingSignalRequest(BaseModel):
    signal_type: str = Field(examples=["demo_requested"])
    message_id: str | None = None
    evidence: str | None = Field(default=None, examples=["User asked for demo"])
    confidence: float | None = Field(default=None, examples=[0.9])
    strength: float | None = Field(default=None, examples=[0.9])


class BuyingSignalResponse(BaseModel):
    id: str
    conversation_id: str
    tenant_id: str | None = None
    signal_type: str
    message_id: str | None = None
    evidence: str | None = None
    confidence: float | None = None
    strength: float | None = None
    detected_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ConversationCitationResponse(BaseModel):
    id: str
    message_id: str
    tenant_id: str
    document_id: str | None = None
    chunk_id: str | None = None
    quote: str | None = None
    confidence: float | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class EmotionRequest(BaseModel):
    emotion: str = Field(examples=["happy"])
    message_id: str | None = None
    score: float | None = Field(default=None, examples=[0.8])


class EmotionResponse(BaseModel):
    id: str
    conversation_id: str
    tenant_id: str | None = None
    message_id: str | None = None
    emotion: str
    score: float | None = None
    detected_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ConversationEntityResponse(BaseModel):
    id: str
    conversation_id: str
    tenant_id: str
    entity_id: str | None = None
    entity_text: str | None = None
    entity_type: str | None = None
    confidence: float | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ConversationFeedbackResponse(BaseModel):
    id: str
    conversation_id: str
    tenant_id: str
    message_id: str | None = None
    rating: int | None = None
    feedback: str | None = None
    feedback_type: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class IntentRequest(BaseModel):
    intent: str = Field(examples=["pricing_question"])
    message_id: str | None = None
    confidence: float | None = Field(default=None, examples=[0.95])
    evidence: str | None = Field(default=None, examples=["User asked about pricing"])


class IntentResponse(BaseModel):
    id: str
    conversation_id: str
    tenant_id: str | None = None
    message_id: str | None = None
    intent: str
    confidence: float | None = None
    evidence: str | None = None
    detected_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ConversationMetricResponse(BaseModel):
    id: str | None = None
    conversation_id: str
    tenant_id: str | None = None
    response_time_seconds: float | None = None
    resolution_time_seconds: float | None = None
    message_count: int
    participant_count: int = 0
    user_message_count: int = 0
    assistant_message_count: int = 0
    attachment_count: int = 0
    reaction_count: int = 0
    summary_count: int = 0
    avg_confidence: float | None = None
    rag_used_count: int = 0
    metadata_: dict[str, Any] = Field(default_factory=dict, alias="metadata")
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


ConversationMetricsResponse = ConversationMetricResponse


class ObjectionRequest(BaseModel):
    objection_type: str = Field(examples=["price"])
    message_id: str | None = None
    evidence: str | None = Field(default=None, examples=["User mentioned budget concerns"])
    confidence: float | None = Field(default=None, examples=[0.85])


class ObjectionResponse(BaseModel):
    id: str
    conversation_id: str
    tenant_id: str | None = None
    message_id: str | None = None
    objection_type: str
    evidence: str | None = None
    confidence: float | None = None
    detected_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ConversationParticipantRequest(BaseModel):
    participant_type: str = Field(default="user", examples=["user"])
    participant_id: str | None = Field(default=None, examples=["U001"])
    display_name: str | None = Field(default=None, examples=["John Doe"])
    user_id: str | None = Field(default=None, examples=["U001"])
    type: str = Field(default="user", examples=["user"])
    role: str | None = Field(default=None, examples=["customer"])
    name: str | None = Field(default=None, examples=["John Doe"])
    metadata_: dict[str, Any] = Field(default_factory=dict, alias="metadata")

    @property
    def metadata(self) -> dict[str, Any]:
        return self.metadata_


class ParticipantResponse(BaseModel):
    id: str
    conversation_id: str
    tenant_id: str
    participant_type: str
    participant_id: str | None = None
    display_name: str | None = None
    user_id: str | None = None
    type: str | None = None
    role: str | None = None
    name: str | None = None
    metadata_: dict[str, Any] = Field(default_factory=dict, alias="metadata")
    joined_at: datetime
    left_at: datetime | None = None

    model_config = {"from_attributes": True}


class ParticipantListResponse(BaseModel):
    items: list[ParticipantResponse]
    total: int
    page: int
    page_size: int


class SentimentRequest(BaseModel):
    sentiment: str = Field(examples=["positive"])
    message_id: str | None = None
    score: float | None = Field(default=None, examples=[0.9])


class SentimentResponse(BaseModel):
    id: str
    conversation_id: str
    tenant_id: str | None = None
    message_id: str | None = None
    sentiment: str
    score: float | None = None
    detected_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class SummaryRequest(BaseModel):
    max_length: int | None = Field(default=None, examples=[120])
    focus: str | None = None
    metadata_: dict[str, Any] = Field(default_factory=dict, alias="metadata")

    @property
    def metadata(self) -> dict[str, Any]:
        return self.metadata_


class SummaryResponse(BaseModel):
    id: str
    conversation_id: str
    tenant_id: str | None = None
    summary_type: str = "ai"
    summary: str
    created_by: str | None = None
    key_points: list[str] = Field(default_factory=list)
    action_items: list[str] = Field(default_factory=list)
    sentiment: str | None = None
    metadata_: dict[str, Any] = Field(default_factory=dict, alias="metadata")
    created_at: datetime

    model_config = {"from_attributes": True}


class SummaryListResponse(BaseModel):
    items: list[SummaryResponse]
    total: int
    page: int
    page_size: int


class ConversationTranscriptResponse(BaseModel):
    id: str
    conversation_id: str
    tenant_id: str
    transcript: str
    provider: str | None = None
    metadata_: dict[str, Any] = Field(default_factory=dict, alias="metadata")
    created_at: datetime

    model_config = {"from_attributes": True}


class MessageAttachmentResponse(BaseModel):
    id: str
    message_id: str
    tenant_id: str
    file_name: str | None = None
    file_url: str | None = None
    content_type: str | None = None
    metadata_: dict[str, Any] = Field(default_factory=dict, alias="metadata")
    created_at: datetime

    model_config = {"from_attributes": True}


class MessageDeliveryStatusResponse(BaseModel):
    id: str
    message_id: str
    tenant_id: str
    status: str
    provider: str | None = None
    delivered_at: datetime | None = None
    metadata_: dict[str, Any] = Field(default_factory=dict, alias="metadata")
    created_at: datetime

    model_config = {"from_attributes": True}


class MessageReactionResponse(BaseModel):
    id: str
    message_id: str
    tenant_id: str
    user_id: str | None = None
    reaction: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ResponseMetricResponse(BaseModel):
    id: str
    message_id: str | None = None
    tenant_id: str
    quality_score: float | None = None
    metrics: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

    model_config = {"from_attributes": True}
