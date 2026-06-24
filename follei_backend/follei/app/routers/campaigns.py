from datetime import datetime, timezone
from app.core.ids import short_id

from fastapi import APIRouter, HTTPException, Query, Response, status

from app.schemas.campaign import (
    CampaignCreate,
    CampaignListResponse,
    CampaignMetricCreate,
    CampaignMetricResponse,
    CampaignResponse,
    CampaignUpdate,
)

router = APIRouter(prefix="/campaigns", tags=["Campaigns"])
metrics_router = APIRouter(prefix="/campaign-metrics", tags=["Campaigns"])

CAMPAIGNS: dict[str, CampaignResponse] = {}
CAMPAIGN_LEADS: dict[str, dict[str, str]] = {}  # campaign_id -> lead_id mapping
METRICS: dict[str, CampaignMetricResponse] = {}
CAMPAIGN_METRICS: dict[str, list[str]] = {}  # campaign_id -> metric_ids


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _get_campaign_or_404(campaign_id: str) -> CampaignResponse:
    campaign = CAMPAIGNS.get(campaign_id)
    if campaign is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")
    return campaign


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