import json
from datetime import datetime, timezone
from app.core.ids import short_id

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.tenancy import Tenant
from app.repositories.integration_repository import IntegrationRepository
from app.schemas.integration import (
    CreateIntegrationRequest,
    CreateIntegrationResponse,
    InboundWebhookRequest,
    InboundWebhookResponse,
    IntegrationConnectionListResponse,
    IntegrationConnectionRequest,
    IntegrationConnectionResponse,
    IntegrationConnectionSummary,
    IntegrationListResponse,
    IntegrationResponse,
    IntegrationSummary,
    SyncJobListResponse,
    SyncJobResponse,
    SyncRequest,
    TwilioSmsWebhookRequest,
    UpdateIntegrationConnectionRequest,
    WebhookEventListResponse,
    WebhookEventResponse,
    WebhookListResponse,
    WebhookRequest,
    WebhookResponse,
)
from app.services.integration_service import IntegrationService
from app.services.twilio_auto_reply import process_twilio_auto_reply

integrations_router = APIRouter(prefix="/integrations", tags=["Integrations"])
connections_router = APIRouter(prefix="/integration-connections", tags=["Integrations"])
webhook_events_router = APIRouter(prefix="/webhook-events", tags=["Webhooks & Events"])
webhooks_receive_router = APIRouter(prefix="/webhooks", tags=["Webhooks & Events"])


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


SALESFORCE_ID = "alpha123beta456gamma789"
HUBSPOT_ID = "delta789echo123foxtrot456"
GMAIL_ID = "golf123hotel456india789"
WHATSAPP_ID = "juliet789kilo123lima456"
TWILIO_ID = "twilio_sms"

INTEGRATIONS: dict[str, IntegrationResponse] = {
    SALESFORCE_ID: IntegrationResponse(
        id=SALESFORCE_ID,
        name="Salesforce",
        category="crm",
        auth_type="oauth2",
        status="available",
        auth_url="https://login.salesforce.com/services/oauth2/authorize",
        token_url="https://login.salesforce.com/services/oauth2/token",
        scopes=["api", "refresh_token"],
        webhook_support=True,
        actions=["create_contact", "update_deal", "search_leads"],
    ),
    HUBSPOT_ID: IntegrationResponse(
        id=HUBSPOT_ID,
        name="HubSpot",
        category="crm",
        auth_type="api_key",
        status="available",
        webhook_support=True,
        actions=["create_contact", "update_deal", "search_contacts"],
    ),
    GMAIL_ID: IntegrationResponse(
        id=GMAIL_ID,
        name="Gmail",
        category="email",
        auth_type="oauth2",
        status="available",
        auth_url="https://accounts.google.com/o/oauth2/v2/auth",
        token_url="https://oauth2.googleapis.com/token",
        scopes=["gmail.send", "gmail.readonly"],
        webhook_support=False,
        actions=["send_email", "read_email"],
    ),
    WHATSAPP_ID: IntegrationResponse(
        id=WHATSAPP_ID,
        name="WhatsApp",
        category="messaging",
        auth_type="api_key",
        status="available",
        webhook_support=True,
        actions=["send_message", "send_template"],
    ),
    TWILIO_ID: IntegrationResponse(
        id=TWILIO_ID,
        name="Twilio SMS",
        category="messaging",
        auth_type="api_key",
        status="available",
        webhook_support=True,
        actions=["receive_sms", "send_sms", "auto_reply"],
    ),
}
CONNECTIONS: dict[str, IntegrationConnectionResponse] = {}
CONNECTION_CREDENTIALS: dict[str, dict] = {}
SYNC_JOBS: dict[str, SyncJobResponse] = {}
CONNECTION_SYNC_JOBS: dict[str, list[str]] = {}
WEBHOOKS: dict[str, WebhookResponse] = {}
CONNECTION_WEBHOOKS: dict[str, list[str]] = {}
WEBHOOK_EVENTS: dict[str, WebhookEventResponse] = {}


def _get_integration_or_404(integration_id: str) -> IntegrationResponse:
    integration = INTEGRATIONS.get(integration_id)
    if integration is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Integration not found")
    return integration


def _get_connection_or_404(connection_id: str) -> IntegrationConnectionResponse:
    connection = CONNECTIONS.get(connection_id)
    if connection is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Integration connection not found")
    return connection


@integrations_router.post(
    "",
    response_model=CreateIntegrationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a tenant integration",
    description="Creates a tenant-owned Twilio integration used by the SMS auto-response webhook.",
    responses={
        403: {"description": "Tenant is inactive"},
        404: {"description": "Tenant not found"},
        409: {
            "description": "Integration name or phone number already exists",
            "content": {
                "application/json": {
                    "example": {"detail": "Twilio phone number is already assigned to an integration"}
                }
            },
        },
        422: {"description": "Invalid provider, status, phone number, or request payload"},
    },
)
def create_integration(
    payload: CreateIntegrationRequest,
    db: Session = Depends(get_db),
) -> CreateIntegrationResponse:
    integration = IntegrationService(db).create_integration(payload)
    return CreateIntegrationResponse(
        integration_id=integration.id,
        tenant_id=integration.tenant_id,
    )


@integrations_router.get("", response_model=IntegrationListResponse)
def list_integrations(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> IntegrationListResponse:
    items = [
        IntegrationSummary(
            id=item.id,
            name=item.name,
            category=item.category,
            auth_type=item.auth_type,
            status=item.status,
        )
        for item in INTEGRATIONS.values()
    ]
    total = len(items)
    start = (page - 1) * page_size
    return IntegrationListResponse(items=items[start : start + page_size], total=total, page=page, page_size=page_size)


@integrations_router.get("/{integration_id}", response_model=IntegrationResponse)
def get_integration(integration_id: str) -> IntegrationResponse:
    return _get_integration_or_404(integration_id)


@connections_router.post("", response_model=IntegrationConnectionSummary, status_code=status.HTTP_201_CREATED)
def create_connection(payload: IntegrationConnectionRequest) -> IntegrationConnectionSummary:
    integration = _get_integration_or_404(payload.integration_id)
    connection_id = str(short_id())
    now = _now()
    connection = IntegrationConnectionResponse(
        id=connection_id,
        integration_id=integration.id,
        integration_name=integration.name,
        tenant_id=payload.tenant_id,
        status="connected",
        connected_at=now,
        last_sync=None,
        integration={"id": integration.id, "name": integration.name},
        auth_type=payload.auth_type or integration.auth_type,
        settings=payload.settings,
        sync_jobs=[],
    )
    CONNECTIONS[connection_id] = connection
    CONNECTION_CREDENTIALS[connection_id] = {**payload.config, **payload.credentials}
    return IntegrationConnectionSummary(**connection.model_dump(exclude={"integration", "auth_type", "settings", "sync_jobs"}))


@connections_router.get("", response_model=IntegrationConnectionListResponse)
def list_connections(
    tenant_id: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> IntegrationConnectionListResponse:
    items = [
        IntegrationConnectionSummary(**item.model_dump(exclude={"integration", "auth_type", "settings", "sync_jobs"}))
        for item in CONNECTIONS.values()
        if tenant_id is None or item.tenant_id == tenant_id
    ]
    total = len(items)
    start = (page - 1) * page_size
    return IntegrationConnectionListResponse(items=items[start : start + page_size], total=total, page=page, page_size=page_size)


@connections_router.get("/{connection_id}", response_model=IntegrationConnectionResponse)
def get_connection(connection_id: str) -> IntegrationConnectionResponse:
    connection = _get_connection_or_404(connection_id)
    job_ids = CONNECTION_SYNC_JOBS.get(connection_id, [])
    jobs = [SYNC_JOBS[job_id].model_dump() for job_id in job_ids if job_id in SYNC_JOBS]
    return connection.model_copy(update={"sync_jobs": jobs})


@connections_router.patch("/{connection_id}", response_model=IntegrationConnectionResponse)
def update_connection(connection_id: str, payload: UpdateIntegrationConnectionRequest) -> IntegrationConnectionResponse:
    connection = _get_connection_or_404(connection_id)
    data = payload.model_dump(exclude_unset=True)
    if "settings" in data and data["settings"] is not None:
        data["settings"] = {**connection.settings, **data["settings"]}
    updated = connection.model_copy(update=data)
    CONNECTIONS[connection_id] = updated
    return updated


@connections_router.delete("/{connection_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_connection(connection_id: str) -> Response:
    _get_connection_or_404(connection_id)
    CONNECTIONS.pop(connection_id, None)
    CONNECTION_CREDENTIALS.pop(connection_id, None)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@connections_router.post("/{connection_id}/sync", response_model=SyncJobResponse, status_code=status.HTTP_202_ACCEPTED)
def trigger_sync(connection_id: str, payload: SyncRequest) -> SyncJobResponse:
    connection = _get_connection_or_404(connection_id)
    job_id = str(short_id())
    job = SyncJobResponse(
        id=job_id,
        job_id=job_id,
        connection_id=connection_id,
        status="queued",
        sync_type=payload.sync_type,
        entities=payload.entities,
        records_synced=0,
        started_at=_now(),
        completed_at=None,
    )
    SYNC_JOBS[job_id] = job
    CONNECTION_SYNC_JOBS.setdefault(connection_id, []).append(job_id)
    CONNECTIONS[connection_id] = connection.model_copy(update={"last_sync": job.started_at})
    return job


@connections_router.get("/{connection_id}/sync-jobs", response_model=SyncJobListResponse)
def list_sync_jobs(
    connection_id: str,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> SyncJobListResponse:
    _get_connection_or_404(connection_id)
    items = [SYNC_JOBS[job_id] for job_id in CONNECTION_SYNC_JOBS.get(connection_id, []) if job_id in SYNC_JOBS]
    total = len(items)
    start = (page - 1) * page_size
    return SyncJobListResponse(items=items[start : start + page_size], total=total, page=page, page_size=page_size)


@connections_router.post("/{connection_id}/webhooks", response_model=WebhookResponse, status_code=status.HTTP_201_CREATED)
def create_webhook(connection_id: str, payload: WebhookRequest) -> WebhookResponse:
    _get_connection_or_404(connection_id)
    webhook_id = str(short_id())
    webhook = WebhookResponse(
        id=webhook_id,
        connection_id=connection_id,
        event_type=payload.event_type,
        url=payload.url,
        active=payload.active,
        created_at=_now(),
    )
    WEBHOOKS[webhook_id] = webhook
    CONNECTION_WEBHOOKS.setdefault(connection_id, []).append(webhook_id)
    return webhook


@connections_router.get("/{connection_id}/webhooks", response_model=WebhookListResponse)
def list_webhooks(
    connection_id: str,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> WebhookListResponse:
    _get_connection_or_404(connection_id)
    items = [WEBHOOKS[webhook_id] for webhook_id in CONNECTION_WEBHOOKS.get(connection_id, []) if webhook_id in WEBHOOKS]
    total = len(items)
    start = (page - 1) * page_size
    return WebhookListResponse(items=items[start : start + page_size], total=total, page=page, page_size=page_size)


@connections_router.delete("/{connection_id}/webhooks/{webhook_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_webhook(connection_id: str, webhook_id: str) -> Response:
    _get_connection_or_404(connection_id)
    webhook = WEBHOOKS.get(webhook_id)
    if webhook is None or webhook.connection_id != connection_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Webhook not found")
    WEBHOOKS.pop(webhook_id, None)
    CONNECTION_WEBHOOKS[connection_id] = [item_id for item_id in CONNECTION_WEBHOOKS.get(connection_id, []) if item_id != webhook_id]
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@webhooks_receive_router.post(
    "/receive/{integration_id}",
    response_model=InboundWebhookResponse,
    response_model_exclude_none=True,
    openapi_extra={
        "requestBody": {
            "required": True,
            "content": {
                "application/json": {
                    "schema": {
                        "oneOf": [
                            {"$ref": "#/components/schemas/InboundWebhookRequest"},
                            {"$ref": "#/components/schemas/TwilioSmsWebhookRequest"},
                        ]
                    },
                    "examples": {
                        "twilio_sms": {
                            "summary": "Swagger SMS test",
                            "value": {
                                "From": "+919876543210",
                                "To": "+15672467340",
                                "Body": "Hi, what services do you provide?",
                                "MessageSid": "SM_TEST_001",
                            },
                        },
                        "existing_webhook": {
                            "summary": "Existing generic webhook",
                            "value": {"event_type": "lead.created", "payload": {"email": "lead@example.com"}},
                        },
                    },
                },
                "application/x-www-form-urlencoded": {
                    "schema": {
                        "type": "object",
                        "required": ["From", "To", "Body"],
                        "properties": {
                            "From": {"type": "string", "example": "+919876543210"},
                            "To": {"type": "string", "example": "+15672467340"},
                            "Body": {"type": "string", "example": "What are your pricing plans?"},
                            "MessageSid": {"type": "string", "example": "SMXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"},
                        },
                    },
                },
            },
        }
    },
)
async def receive_webhook(
    integration_id: str,
    request: Request,
    db: Session = Depends(get_db),
) -> InboundWebhookResponse:
    stored_integration = IntegrationRepository(db).get_by_id(integration_id)
    if integration_id not in INTEGRATIONS and stored_integration is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Integration not found")
    if stored_integration is not None and stored_integration.status != "active":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Integration is inactive")

    content_type = request.headers.get("content-type", "").lower()
    sms_payload: TwilioSmsWebhookRequest | None = None

    try:
        if "application/x-www-form-urlencoded" in content_type or "multipart/form-data" in content_type:
            form = await request.form()
            raw_payload = {key: str(value) for key, value in form.items()}
            sms_payload = TwilioSmsWebhookRequest.model_validate(raw_payload)
            event_type = "twilio_sms"
            event_payload = raw_payload
            event_timestamp = sms_payload.timestamp
        else:
            raw_payload = await request.json()
            if isinstance(raw_payload, dict) and "event_type" in raw_payload and "payload" in raw_payload:
                body = InboundWebhookRequest.model_validate(raw_payload)
                event_type = body.event_type
                event_payload = body.payload
                event_timestamp = body.timestamp
            else:
                sms_payload = TwilioSmsWebhookRequest.model_validate(raw_payload)
                event_type = "twilio_sms"
                event_payload = raw_payload
                event_timestamp = sms_payload.timestamp
    except (json.JSONDecodeError, ValidationError) as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid webhook payload") from exc

    if sms_payload is not None and not all(
        value.strip() for value in (sms_payload.from_phone, sms_payload.to_phone, sms_payload.body)
    ):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid webhook payload")

    event_id = str(short_id())
    event = WebhookEventResponse(
        id=event_id,
        integration_id=integration_id,
        event_type=event_type,
        payload=event_payload,
        status="processed",
        created_at=event_timestamp or _now(),
    )
    WEBHOOK_EVENTS[event_id] = event

    if sms_payload is None:
        return InboundWebhookResponse(received=True, event_id=event_id)

    if stored_integration is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant integration not found")
    tenant = db.get(Tenant, stored_integration.tenant_id)
    if tenant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
    if tenant.status.lower() != "active":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant is inactive")

    result = await process_twilio_auto_reply(
        db=db,
        integration_id=integration_id,
        tenant=tenant,
        event_id=event_id,
        customer_phone=sms_payload.from_phone.strip(),
        to_phone=sms_payload.to_phone.strip(),
        body=sms_payload.body.strip(),
        message_sid=sms_payload.message_sid,
        timestamp=sms_payload.timestamp,
        raw_payload=event_payload,
    )

    return InboundWebhookResponse(
        received=True,
        event_id=event_id,
        customer_phone=result["customer_phone"],
        tenant_phone=result["tenant_phone"],
        customer_message=result["customer_message"],
        ai_reply=result["ai_reply"],
        sms_status=result["sms_status"],
        provider_message_id=result["provider_message_id"],
    )


@webhook_events_router.get("", response_model=WebhookEventListResponse)
def list_webhook_events(
    event_type: str | None = None,
    status_filter: str | None = Query(default=None, alias="status"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> WebhookEventListResponse:
    items = list(WEBHOOK_EVENTS.values())
    if event_type is not None:
        items = [item for item in items if item.event_type == event_type]
    if status_filter is not None:
        items = [item for item in items if item.status == status_filter]
    total = len(items)
    start = (page - 1) * page_size
    return WebhookEventListResponse(items=items[start : start + page_size], total=total, page=page, page_size=page_size)
