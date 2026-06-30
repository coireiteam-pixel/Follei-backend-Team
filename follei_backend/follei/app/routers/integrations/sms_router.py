"""Thin HTTP routes for sending and reading SMS messages."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.integrations.sms import SmsMessageHistoryResponse, SmsSendRequest, SmsSendResponse
from app.services.integrations.sms.sms_service import SmsService


router = APIRouter(prefix="/integrations/sms", tags=["SMS Integrations"])


@router.post("/send", response_model=SmsSendResponse, summary="Send an SMS through Twilio")
async def send_sms(payload: SmsSendRequest, db: Session = Depends(get_db)) -> SmsSendResponse:
    message = await SmsService(db).send_message(payload)
    return SmsSendResponse(message=message)


@router.get(
    "/messages/{phone}",
    response_model=SmsMessageHistoryResponse,
    summary="Get tenant SMS history for a phone number",
)
def get_sms_messages(
    phone: str,
    tenant_id: str = Query(examples=["T001"]),
    limit: int = Query(default=100, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> SmsMessageHistoryResponse:
    items, total = SmsService(db).get_messages(
        tenant_id,
        phone,
        limit=limit,
        offset=offset,
    )
    return SmsMessageHistoryResponse(
        tenant_id=tenant_id,
        phone_number=phone,
        items=items,
        total=total,
    )
