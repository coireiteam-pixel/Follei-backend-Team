import csv
import io
import json
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel
from app.core.ids import short_id
from app.services.mistral import get_mistral_reply

from fastapi import APIRouter, File, Form, HTTPException, Query, Response, UploadFile, status

from app.schemas.lead import (
    CSVImportError,
    CSVImportResponse,
    CreateLeadRequest,
    LeadActivityListResponse,
    LeadActivityRequest,
    LeadActivityResponse,
    LeadListResponse,
    LeadQualificationListResponse,
    LeadQualificationRequest,
    LeadQualificationResponse,
    LeadResponse,
    LeadScoreListResponse,
    LeadScoreRequest,
    LeadScoreResponse,
    MeetingListResponse,
    MeetingRequest,
    MeetingResponse,
    OpportunityListResponse,
    OpportunityRequest,
    OpportunityResponse,
    ProposalRequest,
    ProposalResponse,
    QualificationFrameworkListResponse,
    QualificationFrameworkRequest,
    QualificationFrameworkResponse,
    QuoteRequest,
    QuoteResponse,
    UpdateLeadRequest,
    UpdateMeetingRequest,
    UpdateOpportunityRequest,
)

router = APIRouter(prefix="/leads", tags=["Leads & Revenue"])
frameworks_router = APIRouter(prefix="/qualification-frameworks", tags=["Leads & Revenue"])
opportunities_router = APIRouter(prefix="/opportunities", tags=["Leads & Revenue"])
meetings_router = APIRouter(prefix="/meetings", tags=["Leads & Revenue"])

LEADS: dict[str, LeadResponse] = {}
ACTIVITIES: dict[str, LeadActivityResponse] = {}
LEAD_ACTIVITIES: dict[str, list[str]] = {}
SCORES: dict[str, LeadScoreResponse] = {}
LEAD_SCORES: dict[str, list[str]] = {}
FRAMEWORKS: dict[str, QualificationFrameworkResponse] = {}
QUALIFICATIONS: dict[str, LeadQualificationResponse] = {}
LEAD_QUALIFICATIONS: dict[str, list[str]] = {}
OPPORTUNITIES: dict[str, OpportunityResponse] = {}
PROPOSALS: dict[str, ProposalResponse] = {}
QUOTES: dict[str, QuoteResponse] = {}
MEETINGS: dict[str, MeetingResponse] = {}

LEAD_MESSAGES: dict[str, list[dict]] = {}


class LeadMessageRequest(BaseModel):
    message: str


class LeadMessageResponse(BaseModel):
    lead_id: str
    user_message: str
    ai_response: str
    history: list[dict]


class LeadMessagesResponse(BaseModel):
    lead_id: str
    messages: list[dict[str, Any]]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


async def _read_csv_upload(file: UploadFile) -> list[dict[str, str]]:
    filename = file.filename or "upload.csv"
    if not filename.lower().endswith(".csv"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only CSV files are supported")

    raw_content = await file.read()
    if not raw_content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="CSV file is empty")

    try:
        content = raw_content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="CSV file must use UTF-8 encoding",
        ) from exc

    reader = csv.DictReader(io.StringIO(content, newline=""))
    if not reader.fieldnames:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="CSV file has no header row")

    rows: list[dict[str, str]] = []
    for row in reader:
        if None in row:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"CSV row {reader.line_num} has more values than the header",
            )
        if any(str(value or "").strip() for value in row.values()):
            rows.append({str(key).strip(): str(value or "").strip() for key, value in row.items()})
    return rows


def _json_cell(row: dict[str, str], field: str, default: Any, expected_type: type) -> Any:
    value = row.get(field, "")
    if not value:
        return default
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{field} contains invalid JSON") from exc
    if not isinstance(parsed, expected_type):
        raise ValueError(f"{field} must be a JSON {expected_type.__name__}")
    return parsed


def _float_cell(row: dict[str, str], field: str, default: float | None = None) -> float | None:
    value = row.get(field, "")
    if not value:
        return default
    try:
        return float(value)
    except ValueError as exc:
        raise ValueError(f"{field} must be a number") from exc


def _unique_id(prefix: str, store: dict[str, Any]) -> str:
    entity_id = short_id(prefix)
    while entity_id in store:
        entity_id = short_id(prefix)
    return entity_id


def _get_lead_or_404(lead_id: str) -> LeadResponse:
    lead = LEADS.get(lead_id)
    if lead is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found")
    return lead


@router.post("", response_model=LeadResponse, status_code=status.HTTP_201_CREATED)
def create_lead(payload: CreateLeadRequest) -> LeadResponse:
    now = _now()
    lead_id = _unique_id("L", LEADS)
    lead = LeadResponse(
        id=lead_id,
        email=payload.email,
        phone=payload.phone,
        full_name=payload.full_name,
        company=payload.company,
        job_title=payload.job_title,
        industry=payload.industry,
        website=payload.website,
        source=payload.source,
        tenant_id=payload.tenant_id or "T001",
        status=payload.status,
        priority=payload.priority,
        tags=payload.tags,
        custom_fields=payload.custom_fields,
        assigned_to=payload.assigned_to,
        score=payload.score,
        metadata=payload.metadata_,
        created_at=now,
        updated_at=now,
    )
    LEADS[lead_id] = lead
    return lead


@router.post("/import-csv", response_model=CSVImportResponse)
async def import_leads_csv(
    file: UploadFile = File(...),
    default_tenant_id: str = Form(default="T001"),
) -> CSVImportResponse:
    rows = await _read_csv_upload(file)
    imported = 0
    updated = 0
    errors: list[CSVImportError] = []

    for row_number, row in enumerate(rows, start=2):
        try:
            now = _now()
            lead_id = row.get("id") or _unique_id("L", LEADS)
            existing = LEADS.get(lead_id)
            lead = LeadResponse(
                id=lead_id,
                email=row.get("email") or None,
                phone=row.get("phone") or None,
                full_name=row.get("full_name") or None,
                company=row.get("company") or None,
                job_title=row.get("job_title") or None,
                industry=row.get("industry") or None,
                website=row.get("website") or None,
                source=row.get("source") or "csv_upload",
                status=row.get("status") or "new",
                priority=row.get("priority") or "medium",
                tags=_json_cell(row, "tags", [], list),
                custom_fields=_json_cell(row, "custom_fields", {}, dict),
                score=_float_cell(row, "score"),
                assigned_to=row.get("assigned_to") or None,
                metadata=_json_cell(row, "metadata", {}, dict),
                tenant_id=row.get("tenant_id") or default_tenant_id,
                created_at=row.get("created_at") or (existing.created_at if existing else now),
                updated_at=row.get("updated_at") or now,
            )
            LEADS[lead_id] = lead
            if existing:
                updated += 1
            else:
                imported += 1
        except (TypeError, ValueError) as exc:
            errors.append(CSVImportError(row=row_number, message=str(exc)))

    return CSVImportResponse(
        filename=file.filename or "upload.csv",
        total_rows=len(rows),
        imported=imported,
        updated=updated,
        failed=len(errors),
        errors=errors,
    )


@router.get("", response_model=LeadListResponse)
def list_leads(
    tenant_id: str | None = None,
    status_filter: str | None = Query(default=None, alias="status"),
    priority: str | None = None,
    assigned_to: str | None = None,
    source: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> LeadListResponse:
    items = list(LEADS.values())

    if tenant_id is not None:
        items = [item for item in items if item.tenant_id == tenant_id]
    if status_filter is not None:
        items = [item for item in items if item.status == status_filter]
    if priority is not None:
        items = [item for item in items if item.priority == priority]
    if assigned_to is not None:
        items = [item for item in items if item.assigned_to == assigned_to]
    if source is not None:
        items = [item for item in items if item.source == source]

    total = len(items)
    start = (page - 1) * page_size
    return LeadListResponse(items=items[start:start + page_size], total=total, page=page, page_size=page_size)


@router.get("/{lead_id}", response_model=LeadResponse)
def get_lead(lead_id: str) -> LeadResponse:
    return _get_lead_or_404(lead_id)


@router.patch("/{lead_id}", response_model=LeadResponse)
def update_lead(lead_id: str, payload: UpdateLeadRequest) -> LeadResponse:
    lead = _get_lead_or_404(lead_id)
    data = payload.model_dump(exclude_unset=True)

    if "email" in data and data["email"] is not None:
        data["email"] = str(data["email"])

    updated = lead.model_copy(update={**data, "updated_at": _now()})
    LEADS[lead_id] = updated
    return updated


@router.delete("/{lead_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_lead(lead_id: str) -> Response:
    _get_lead_or_404(lead_id)
    LEADS.pop(lead_id, None)
    LEAD_MESSAGES.pop(lead_id, None)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{lead_id}/reply", response_model=LeadMessageResponse)
async def reply_to_lead(
    lead_id: str,
    payload: LeadMessageRequest,
) -> LeadMessageResponse:
    lead = _get_lead_or_404(lead_id)
    history = LEAD_MESSAGES.setdefault(lead_id, [])
    user_message = {
        "role": "user",
        "content": payload.message,
        "created_at": _now(),
    }

    mistral_messages = [
        {
            "role": "system",
            "content": (
                "You are a professional sales assistant. "
                "Reply clearly, politely, and based on the lead details. "
                "Keep the response useful for sales follow-up."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Lead details:\n"
                f"Name: {lead.full_name}\n"
                f"Email: {lead.email}\n"
                f"Company: {lead.company}\n"
                f"Phone: {lead.phone}\n"
                f"Source: {lead.source}\n"
                f"Status: {lead.status}\n"
                f"Priority: {lead.priority}\n"
                f"Score: {lead.score}\n"
            ),
        },
    ]

    for msg in history[-20:]:
        mistral_messages.append({
            "role": msg["role"],
            "content": msg["content"],
        })
    mistral_messages.append({"role": "user", "content": payload.message})

    ai_response = await get_mistral_reply(mistral_messages)

    history.append(user_message)
    history.append({
        "role": "assistant",
        "content": ai_response,
        "created_at": _now(),
    })

    return LeadMessageResponse(
        lead_id=lead_id,
        user_message=payload.message,
        ai_response=ai_response,
        history=history,
    )


@router.get("/{lead_id}/messages", response_model=LeadMessagesResponse)
def get_lead_messages(lead_id: str) -> LeadMessagesResponse:
    _get_lead_or_404(lead_id)
    return LeadMessagesResponse(lead_id=lead_id, messages=LEAD_MESSAGES.get(lead_id, []))


def _get_opportunity_or_404(opportunity_id: str) -> OpportunityResponse:
    opportunity = OPPORTUNITIES.get(opportunity_id)
    if opportunity is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Opportunity not found")
    return opportunity


def _get_meeting_or_404(meeting_id: str) -> MeetingResponse:
    meeting = MEETINGS.get(meeting_id)
    if meeting is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meeting not found")
    return meeting


@router.post("/{lead_id}/activities", response_model=LeadActivityResponse, status_code=status.HTTP_201_CREATED)
def create_activity(lead_id: str, payload: LeadActivityRequest) -> LeadActivityResponse:
    _get_lead_or_404(lead_id)

    activity_id = str(short_id())
    activity = LeadActivityResponse(
        id=activity_id,
        lead_id=lead_id,
        created_at=_now(),
        **payload.model_dump(exclude={"lead_id"}),
    )

    ACTIVITIES[activity_id] = activity
    LEAD_ACTIVITIES.setdefault(lead_id, []).append(activity_id)
    return activity


@router.get("/{lead_id}/activities", response_model=LeadActivityListResponse)
def list_activities(
    lead_id: str,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> LeadActivityListResponse:
    _get_lead_or_404(lead_id)

    items = [
        ACTIVITIES[item_id]
        for item_id in LEAD_ACTIVITIES.get(lead_id, [])
        if item_id in ACTIVITIES
    ]

    total = len(items)
    start = (page - 1) * page_size
    return LeadActivityListResponse(items=items[start:start + page_size], total=total, page=page, page_size=page_size)


@router.post("/{lead_id}/scores", response_model=LeadScoreResponse, status_code=status.HTTP_201_CREATED)
def create_score(lead_id: str, payload: LeadScoreRequest) -> LeadScoreResponse:
    lead = _get_lead_or_404(lead_id)

    base_score = 85 if payload.force_recalculate else max(lead.score, 50)
    score_id = str(short_id())

    score = LeadScoreResponse(
        id=score_id,
        lead_id=lead_id,
        score=base_score,
        model=payload.model,
        factors={
            "profile_fit": 25,
            "engagement": 30,
            "intent": 20,
            "company_size": 10,
        },
        metadata=payload.metadata,
        calculated_at=_now(),
    )

    SCORES[score_id] = score
    LEAD_SCORES.setdefault(lead_id, []).append(score_id)
    LEADS[lead_id] = lead.model_copy(update={"score": base_score, "updated_at": _now()})

    return score


@router.get("/{lead_id}/scores", response_model=LeadScoreListResponse)
def list_scores(
    lead_id: str,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> LeadScoreListResponse:
    _get_lead_or_404(lead_id)

    items = [
        SCORES[item_id]
        for item_id in LEAD_SCORES.get(lead_id, [])
        if item_id in SCORES
    ]

    total = len(items)
    start = (page - 1) * page_size
    return LeadScoreListResponse(items=items[start:start + page_size], total=total, page=page, page_size=page_size)


@frameworks_router.post("", response_model=QualificationFrameworkResponse, status_code=status.HTTP_201_CREATED)
def create_framework(payload: QualificationFrameworkRequest) -> QualificationFrameworkResponse:
    framework_id = str(short_id())
    framework = QualificationFrameworkResponse(id=framework_id, created_at=_now(), **payload.model_dump())
    FRAMEWORKS[framework_id] = framework
    return framework


@frameworks_router.get("", response_model=QualificationFrameworkListResponse)
def list_frameworks(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> QualificationFrameworkListResponse:
    items = list(FRAMEWORKS.values())
    total = len(items)
    start = (page - 1) * page_size
    return QualificationFrameworkListResponse(items=items[start:start + page_size], total=total, page=page, page_size=page_size)


@router.post("/{lead_id}/qualifications", response_model=LeadQualificationResponse, status_code=status.HTTP_201_CREATED)
def create_qualification(lead_id: str, payload: LeadQualificationRequest) -> LeadQualificationResponse:
    _get_lead_or_404(lead_id)

    if payload.framework_id not in FRAMEWORKS:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Qualification framework not found")

    qualification_id = str(short_id())

    qualification = LeadQualificationResponse(
        id=qualification_id,
        lead_id=lead_id,
        score=min(100, len(payload.answers) * 25),
        created_at=_now(),
        **payload.model_dump(exclude={"lead_id", "score"}),
    )

    QUALIFICATIONS[qualification_id] = qualification
    LEAD_QUALIFICATIONS.setdefault(lead_id, []).append(qualification_id)
    return qualification


@router.get("/{lead_id}/qualifications", response_model=LeadQualificationListResponse)
def list_qualifications(
    lead_id: str,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> LeadQualificationListResponse:
    _get_lead_or_404(lead_id)

    items = [
        QUALIFICATIONS[item_id]
        for item_id in LEAD_QUALIFICATIONS.get(lead_id, [])
        if item_id in QUALIFICATIONS
    ]

    total = len(items)
    start = (page - 1) * page_size
    return LeadQualificationListResponse(items=items[start:start + page_size], total=total, page=page, page_size=page_size)


@opportunities_router.post("", response_model=OpportunityResponse, status_code=status.HTTP_201_CREATED)
def create_opportunity(payload: OpportunityRequest) -> OpportunityResponse:
    if payload.lead_id is not None:
        _get_lead_or_404(payload.lead_id)

    now = _now()
    opportunity_id = _unique_id("O", OPPORTUNITIES)
    opportunity = OpportunityResponse(
        id=opportunity_id,
        weighted_revenue=round(payload.value * payload.probability, 2),
        created_at=now,
        updated_at=now,
        **payload.model_dump(),
    )
    OPPORTUNITIES[opportunity_id] = opportunity
    return opportunity


@opportunities_router.post("/import-csv", response_model=CSVImportResponse)
async def import_opportunities_csv(
    file: UploadFile = File(...),
    default_tenant_id: str = Form(default="T001"),
) -> CSVImportResponse:
    rows = await _read_csv_upload(file)
    imported = 0
    updated = 0
    errors: list[CSVImportError] = []

    for row_number, row in enumerate(rows, start=2):
        try:
            lead_id = row.get("lead_id", "")
            if not lead_id:
                raise ValueError("lead_id is required")
            _get_lead_or_404(lead_id)

            value = _float_cell(row, "value")
            if value is None:
                raise ValueError("value is required")
            probability = _float_cell(row, "probability", 0.0) or 0.0
            if not 0 <= probability <= 1:
                raise ValueError("probability must be between 0 and 1")

            now = _now()
            opportunity_id = row.get("id") or _unique_id("O", OPPORTUNITIES)
            existing = OPPORTUNITIES.get(opportunity_id)
            opportunity = OpportunityResponse(
                id=opportunity_id,
                lead_id=lead_id,
                name=row.get("name") or f"{lead_id} opportunity",
                value=value,
                stage=row.get("stage") or "qualification",
                probability=probability,
                weighted_revenue=round(value * probability, 2),
                expected_close_date=row.get("expected_close_date") or None,
                tenant_id=row.get("tenant_id") or default_tenant_id,
                metadata=_json_cell(row, "metadata", {}, dict),
                created_at=row.get("created_at") or (existing.created_at if existing else now),
                updated_at=row.get("updated_at") or now,
            )
            OPPORTUNITIES[opportunity_id] = opportunity
            if existing:
                updated += 1
            else:
                imported += 1
        except HTTPException as exc:
            errors.append(CSVImportError(row=row_number, message=str(exc.detail)))
        except (TypeError, ValueError) as exc:
            errors.append(CSVImportError(row=row_number, message=str(exc)))

    return CSVImportResponse(
        filename=file.filename or "upload.csv",
        total_rows=len(rows),
        imported=imported,
        updated=updated,
        failed=len(errors),
        errors=errors,
    )


@opportunities_router.get("", response_model=OpportunityListResponse)
def list_opportunities(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> OpportunityListResponse:
    items = list(OPPORTUNITIES.values())
    total = len(items)
    start = (page - 1) * page_size
    return OpportunityListResponse(items=items[start:start + page_size], total=total, page=page, page_size=page_size)


@opportunities_router.get("/{opportunity_id}", response_model=OpportunityResponse)
def get_opportunity(opportunity_id: str) -> OpportunityResponse:
    return _get_opportunity_or_404(opportunity_id)


@opportunities_router.patch("/{opportunity_id}", response_model=OpportunityResponse)
def update_opportunity(opportunity_id: str, payload: UpdateOpportunityRequest) -> OpportunityResponse:
    opportunity = _get_opportunity_or_404(opportunity_id)
    changes = payload.model_dump(exclude_unset=True)
    value = changes.get("value", opportunity.value)
    probability = changes.get("probability", opportunity.probability)
    updated = opportunity.model_copy(
        update={
            **changes,
            "weighted_revenue": round(value * probability, 2),
            "updated_at": _now(),
        }
    )
    OPPORTUNITIES[opportunity_id] = updated
    return updated


@opportunities_router.post("/{opportunity_id}/proposals", response_model=ProposalResponse, status_code=status.HTTP_201_CREATED)
def create_proposal(opportunity_id: str, payload: ProposalRequest) -> ProposalResponse:
    _get_opportunity_or_404(opportunity_id)

    proposal_id = str(short_id())

    proposal = ProposalResponse(
        id=proposal_id,
        opportunity_id=opportunity_id,
        document_id=str(short_id()),
        status="draft",
        created_at=_now(),
        **payload.model_dump(exclude={"opportunity_id", "document_id", "status"}),
    )

    PROPOSALS[proposal_id] = proposal
    return proposal


@opportunities_router.post("/{opportunity_id}/quotes", response_model=QuoteResponse, status_code=status.HTTP_201_CREATED)
def create_quote(opportunity_id: str, payload: QuoteRequest) -> QuoteResponse:
    _get_opportunity_or_404(opportunity_id)

    quote_id = str(short_id())

    total = sum(
        float(item.get("quantity", 1)) * float(item.get("price", 0))
        for item in payload.items
    )

    quote = QuoteResponse(
        id=quote_id,
        opportunity_id=opportunity_id,
        status="draft",
        total=total,
        created_at=_now(),
        **payload.model_dump(exclude={"opportunity_id", "status", "total"}),
    )

    QUOTES[quote_id] = quote
    return quote


@meetings_router.post("", response_model=MeetingResponse, status_code=status.HTTP_201_CREATED)
def create_meeting(payload: MeetingRequest) -> MeetingResponse:
    if payload.lead_id is not None:
        _get_lead_or_404(payload.lead_id)

    if payload.opportunity_id is not None:
        _get_opportunity_or_404(payload.opportunity_id)

    now = _now()
    meeting_id = str(short_id())

    meeting = MeetingResponse(
        id=meeting_id,
        status="scheduled",
        notes=None,
        created_at=now,
        updated_at=now,
        **payload.model_dump(exclude={"status", "notes"}),
    )

    MEETINGS[meeting_id] = meeting
    return meeting


@meetings_router.get("", response_model=MeetingListResponse)
def list_meetings(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> MeetingListResponse:
    items = list(MEETINGS.values())
    total = len(items)
    start = (page - 1) * page_size
    return MeetingListResponse(items=items[start:start + page_size], total=total, page=page, page_size=page_size)


@meetings_router.patch("/{meeting_id}", response_model=MeetingResponse)
def update_meeting(meeting_id: str, payload: UpdateMeetingRequest) -> MeetingResponse:
    meeting = _get_meeting_or_404(meeting_id)

    updated = meeting.model_copy(
        update={**payload.model_dump(exclude_unset=True), "updated_at": _now()}
    )

    MEETINGS[meeting_id] = updated
    return updated


@meetings_router.delete("/{meeting_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_meeting(meeting_id: str) -> Response:
    _get_meeting_or_404(meeting_id)
    MEETINGS.pop(meeting_id, None)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
