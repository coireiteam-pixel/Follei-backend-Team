from datetime import datetime, timezone
from app.core.ids import short_id

from fastapi import APIRouter, HTTPException, Query, Response, status

from app.schemas.campaign import (
    CampaignCreate,
    CampaignInboundEmailListResponse,
    CampaignInboundEmailResponse,
    CampaignInboundWebhookResponse,
    CampaignListResponse,
    CampaignMetricCreate,
    CampaignMetricResponse,
    CampaignResponse,
    CampaignSendRecipient,
    CampaignSendRequest,
    CampaignSendResponse,
    CampaignUpdate,
)
from app.services.mcp.email import brevo_send, gmail_send, mailjet_send, outlook_send

router = APIRouter(prefix="/campaigns", tags=["Campaigns"])
metrics_router = APIRouter(prefix="/campaign-metrics", tags=["Campaigns"])
inbound_router = APIRouter(prefix="/email/inbound", tags=["Campaigns"])

CAMPAIGNS: dict[str, CampaignResponse] = {}
CAMPAIGN_LEADS: dict[str, dict[str, str]] = {}  # campaign_id -> lead_id mapping
METRICS: dict[str, CampaignMetricResponse] = {}
CAMPAIGN_METRICS: dict[str, list[str]] = {}  # campaign_id -> metric_ids

INBOUND_EMAILS: dict[str, CampaignInboundEmailResponse] = {}

CAMPAIGN_LEADS: dict[str, dict[str, str]] = {}
METRICS: dict[str, CampaignMetricResponse] = {}
CAMPAIGN_METRICS: dict[str, list[str]] = {}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _get_campaign_or_404(campaign_id: str) -> CampaignResponse:
    campaign = CAMPAIGNS.get(campaign_id)
    if campaign is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")
    return campaign


def _first_text(payload: dict, keys: list[str]) -> str | None:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value
        if isinstance(value, dict):
            nested = value.get("email") or value.get("address") or value.get("Email")
            if isinstance(nested, str) and nested:
                return nested
        if isinstance(value, list) and value:
            first = value[0]
            if isinstance(first, str) and first:
                return first
            if isinstance(first, dict):
                nested = first.get("email") or first.get("address") or first.get("Email")
                if isinstance(nested, str) and nested:
                    return nested
    return None


def _infer_inbound_context(
    from_email: str | None,
    tenant_id: str | None,
    campaign_id: str | None,
    lead_id: str | None,
) -> tuple[str | None, str | None, str | None]:
    from app.routers.leads import LEADS

    if lead_id and lead_id in LEADS:
        lead = LEADS[lead_id]
        tenant_id = tenant_id or lead.tenant_id

    if from_email and not lead_id:
        normalized = from_email.lower()
        for candidate_id, lead in LEADS.items():
            if lead.email and lead.email.lower() == normalized:
                lead_id = candidate_id
                tenant_id = tenant_id or lead.tenant_id
                break

    if lead_id and not campaign_id:
        for candidate_campaign_id, lead_statuses in CAMPAIGN_LEADS.items():
            if lead_id in lead_statuses:
                campaign = CAMPAIGNS.get(candidate_campaign_id)
                if campaign and (tenant_id is None or campaign.tenant_id == tenant_id):
                    campaign_id = candidate_campaign_id
                    tenant_id = tenant_id or campaign.tenant_id
                    break

    if campaign_id and campaign_id in CAMPAIGNS:
        tenant_id = tenant_id or CAMPAIGNS[campaign_id].tenant_id

    return tenant_id, campaign_id, lead_id


def _record_campaign_metric(
    campaign_id: str,
    tenant_id: str,
    metric_type: str,
    value: float,
    metadata: dict | None = None,
) -> CampaignMetricResponse:
    metric_id = str(short_id())
    metric = CampaignMetricResponse(
        id=metric_id,
        campaign_id=campaign_id,
        metric_type=metric_type,
        value=value,
        metadata_=metadata or {},
        tenant_id=tenant_id,
        recorded_at=_now(),
    )
    METRICS[metric_id] = metric
    CAMPAIGN_METRICS.setdefault(campaign_id, []).append(metric_id)
    return metric


@router.post("", response_model=CampaignResponse, status_code=status.HTTP_201_CREATED)
def create_campaign(payload: CampaignCreate) -> CampaignResponse:
    now = _now()
    campaign_id = str(short_id())
    campaign = CampaignResponse(
        id=campaign_id,
        name=payload.name,
        description=payload.description,
        campaign_type=payload.campaign_type,
        status=payload.status,
        start_date=payload.start_date,
        end_date=payload.end_date,
        budget=payload.budget,
        spent=0.0,
        target_audience=payload.target_audience,
        channels=payload.channels,
        metadata_=payload.metadata_,
        tenant_id=payload.tenant_id,
        created_by=payload.created_by,
        created_at=now,
        updated_at=now,
    )
    CAMPAIGNS[campaign_id] = campaign
    CAMPAIGN_LEADS[campaign_id] = {}
    CAMPAIGN_METRICS[campaign_id] = []
    return campaign


@router.get("", response_model=CampaignListResponse)
def list_campaigns(
    tenant_id: str | None = None,
    status_filter: str | None = Query(default=None, alias="status"),
    campaign_type: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> CampaignListResponse:
    items = list(CAMPAIGNS.values())
    if tenant_id is not None:
        items = [item for item in items if item.tenant_id == tenant_id]
    if status_filter is not None:
        items = [item for item in items if item.status == status_filter]
    if campaign_type is not None:
        items = [item for item in items if item.campaign_type == campaign_type]

    total = len(items)
    start = (page - 1) * page_size
    return CampaignListResponse(items=items[start : start + page_size], total=total, page=page, page_size=page_size)


@router.get("/{campaign_id}", response_model=CampaignResponse)
def get_campaign(campaign_id: str) -> CampaignResponse:
    return _get_campaign_or_404(campaign_id)


@router.patch("/{campaign_id}", response_model=CampaignResponse)
def update_campaign(campaign_id: str, payload: CampaignUpdate) -> CampaignResponse:
    campaign = _get_campaign_or_404(campaign_id)
    data = payload.model_dump(exclude_unset=True)
    updated = campaign.model_copy(update={**data, "updated_at": _now()})
    CAMPAIGNS[campaign_id] = updated
    return updated


@router.delete("/{campaign_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_campaign(campaign_id: str) -> Response:
    _get_campaign_or_404(campaign_id)
    CAMPAIGNS.pop(campaign_id, None)
    CAMPAIGN_LEADS.pop(campaign_id, None)
    # Remove associated metrics
    metric_ids = CAMPAIGN_METRICS.pop(campaign_id, [])
    for metric_id in metric_ids:
        METRICS.pop(metric_id, None)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{campaign_id}/leads/{lead_id}", status_code=status.HTTP_201_CREATED)
def add_lead_to_campaign(campaign_id: str, lead_id: str) -> dict:
    _get_campaign_or_404(campaign_id)
    if campaign_id not in CAMPAIGN_LEADS:
        CAMPAIGN_LEADS[campaign_id] = {}
    CAMPAIGN_LEADS[campaign_id][lead_id] = "added"
    return {"message": "Lead added to campaign", "campaign_id": campaign_id, "lead_id": lead_id}


@router.get("/{campaign_id}/leads", response_model=dict)
def list_campaign_leads(campaign_id: str) -> dict:
    _get_campaign_or_404(campaign_id)
    lead_ids = CAMPAIGN_LEADS.get(campaign_id, {})
    return {"campaign_id": campaign_id, "leads": list(lead_ids.keys()), "total": len(lead_ids)}


@router.delete("/{campaign_id}/leads/{lead_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_lead_from_campaign(campaign_id: str, lead_id: str) -> Response:
    _get_campaign_or_404(campaign_id)
    if campaign_id in CAMPAIGN_LEADS:
        CAMPAIGN_LEADS[campaign_id].pop(lead_id, None)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{campaign_id}/send", response_model=CampaignSendResponse)
def send_campaign(campaign_id: str, payload: CampaignSendRequest) -> CampaignSendResponse:
    campaign = _get_campaign_or_404(campaign_id)
    provider = payload.provider.lower()
    if provider not in {"brevo", "gmail", "mailjet", "outlook"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provider must be brevo, gmail, mailjet, or outlook",
        )

    # The current app stores leads in memory, so use that source until campaign persistence is wired in.
    from app.routers.leads import LEADS

    recipients: list[CampaignSendRecipient] = []
    lead_ids = CAMPAIGN_LEADS.get(campaign_id, {})
    sent_count = 0

    for lead_id in lead_ids:
        lead = LEADS.get(lead_id)
        if lead is None:
            recipients.append(CampaignSendRecipient(lead_id=lead_id, status="skipped", detail="Lead not found"))
            continue
        if lead.tenant_id != campaign.tenant_id:
            recipients.append(
                CampaignSendRecipient(
                    lead_id=lead_id,
                    email=lead.email,
                    status="skipped",
                    detail="Lead belongs to a different tenant",
                )
            )
            continue
        if not lead.email:
            recipients.append(CampaignSendRecipient(lead_id=lead_id, status="skipped", detail="Lead has no email"))
            continue

        if payload.dry_run:
            recipients.append(CampaignSendRecipient(lead_id=lead_id, email=lead.email, status="dry_run"))
            continue

        if provider == "brevo":
            result = brevo_send(to=lead.email, subject=payload.subject, body=payload.body)
        elif provider == "gmail":
            result = gmail_send(to=lead.email, subject=payload.subject, body=payload.body)
        elif provider == "mailjet":
            result = mailjet_send(to=lead.email, subject=payload.subject, body=payload.body)
        else:
            result = outlook_send(to=lead.email, subject=payload.subject, body=payload.body)
        CAMPAIGN_LEADS[campaign_id][lead_id] = "contacted"
        sent_count += 1
        recipients.append(
            CampaignSendRecipient(
                lead_id=lead_id,
                email=lead.email,
                status="sent",
                message_id=result.get("message_id"),
            )
        )

    sent_at = _now()
    metric_id = str(short_id())
    metric = CampaignMetricResponse(
        id=metric_id,
        campaign_id=campaign_id,
        metric_type="sent",
        value=sent_count,
        metadata_={"provider": provider, "dry_run": payload.dry_run},
        tenant_id=campaign.tenant_id,
        recorded_at=sent_at,
    )
    METRICS[metric_id] = metric
    CAMPAIGN_METRICS.setdefault(campaign_id, []).append(metric_id)

    return CampaignSendResponse(
        campaign_id=campaign_id,
        tenant_id=campaign.tenant_id,
        provider=provider,
        dry_run=payload.dry_run,
        sent=sent_count,
        skipped=len(recipients) - sent_count,
        recipients=recipients,
        sent_at=sent_at,
    )


@inbound_router.post("/brevo", response_model=CampaignInboundWebhookResponse)
def receive_brevo_inbound_email(
    payload: dict,
    tenant_id: str | None = None,
    campaign_id: str | None = None,
    lead_id: str | None = None,
) -> CampaignInboundWebhookResponse:
    from_email = _first_text(payload, ["from", "From", "sender", "Sender", "email", "from_email"])
    to_email = _first_text(payload, ["to", "To", "recipient", "recipients", "to_email"])
    subject = _first_text(payload, ["subject", "Subject"])
    body = _first_text(payload, ["text", "Text", "body", "Body", "html", "Html", "htmlContent", "textContent"])
    event_type = _first_text(payload, ["event", "eventType", "type"]) or "inbound"

    metadata = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
    tenant_id = tenant_id or metadata.get("tenant_id")
    campaign_id = campaign_id or metadata.get("campaign_id")
    lead_id = lead_id or metadata.get("lead_id")

    tenant_id, campaign_id, lead_id = _infer_inbound_context(from_email, tenant_id, campaign_id, lead_id)
    if tenant_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to resolve tenant_id from webhook payload or query parameters",
        )

    inbound_id = str(short_id())
    inbound_email = CampaignInboundEmailResponse(
        id=inbound_id,
        tenant_id=tenant_id,
        campaign_id=campaign_id,
        lead_id=lead_id,
        from_email=from_email,
        to_email=to_email,
        subject=subject,
        body=body,
        provider="brevo",
        event_type=event_type,
        raw_payload=payload,
        received_at=_now(),
    )
    INBOUND_EMAILS[inbound_id] = inbound_email

    if campaign_id and campaign_id in CAMPAIGNS:
        _record_campaign_metric(
            campaign_id=campaign_id,
            tenant_id=tenant_id,
            metric_type="replied",
            value=1,
            metadata={"provider": "brevo", "inbound_email_id": inbound_id, "event_type": event_type},
        )
        if lead_id and campaign_id in CAMPAIGN_LEADS and lead_id in CAMPAIGN_LEADS[campaign_id]:
            CAMPAIGN_LEADS[campaign_id][lead_id] = "responded"

    return CampaignInboundWebhookResponse(received=True, inbound_email=inbound_email)


@inbound_router.get("", response_model=CampaignInboundEmailListResponse)
def list_inbound_emails(
    tenant_id: str | None = None,
    campaign_id: str | None = None,
    lead_id: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> CampaignInboundEmailListResponse:
    items = list(INBOUND_EMAILS.values())
    if tenant_id is not None:
        items = [item for item in items if item.tenant_id == tenant_id]
    if campaign_id is not None:
        items = [item for item in items if item.campaign_id == campaign_id]
    if lead_id is not None:
        items = [item for item in items if item.lead_id == lead_id]

    total = len(items)
    start = (page - 1) * page_size
    return CampaignInboundEmailListResponse(items=items[start : start + page_size], total=total, page=page, page_size=page_size)


@metrics_router.post("", response_model=CampaignMetricResponse, status_code=status.HTTP_201_CREATED)
def create_metric(payload: CampaignMetricCreate) -> CampaignMetricResponse:
    # Verify campaign exists
    _get_campaign_or_404(payload.campaign_id)
    
    now = _now()
    metric_id = str(short_id())
    metric = CampaignMetricResponse(
        id=metric_id,
        campaign_id=payload.campaign_id,
        metric_type=payload.metric_type,
        value=payload.value,
        metadata_=payload.metadata_,
        tenant_id=payload.tenant_id,
        recorded_at=now,
    )
    METRICS[metric_id] = metric
    CAMPAIGN_METRICS.setdefault(payload.campaign_id, []).append(metric_id)
    return metric


@metrics_router.get("", response_model=dict)
def list_metrics(
    campaign_id: str | None = None,
    metric_type: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> dict:
    items = list(METRICS.values())
    if campaign_id is not None:
        items = [item for item in items if item.campaign_id == campaign_id]
    if metric_type is not None:
        items = [item for item in items if item.metric_type == metric_type]

    total = len(items)
    start = (page - 1) * page_size
    return {
        "items": items[start : start + page_size],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@metrics_router.get("/{metric_id}", response_model=CampaignMetricResponse)
def get_metric(metric_id: str) -> CampaignMetricResponse:
    metric = METRICS.get(metric_id)
    if metric is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Metric not found")
    return metric


@metrics_router.delete("/{metric_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_metric(metric_id: str) -> Response:
    metric = METRICS.get(metric_id)
    if metric is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Metric not found")
    campaign_id = metric.campaign_id
    METRICS.pop(metric_id, None)
    if campaign_id in CAMPAIGN_METRICS:
        CAMPAIGN_METRICS[campaign_id] = [m for m in CAMPAIGN_METRICS[campaign_id] if m != metric_id]
    return Response(status_code=status.HTTP_204_NO_CONTENT)
