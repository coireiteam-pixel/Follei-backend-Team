from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.tenancy import Tenant
from app.schemas.message import MistralSmsRequest, MistralSmsResponse
from app.services.twilio import send_sms

router = APIRouter(prefix="/sms", tags=["SMS"])

@router.post("/mistral-send", response_model=MistralSmsResponse)
async def send_mistral_reply_sms(
    payload: MistralSmsRequest,
    db: Session = Depends(get_db),
) -> MistralSmsResponse:
    tenant = db.get(Tenant, payload.tenant_id)
    if tenant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")

    tenant_phone = (tenant.phone or "").strip()
    if not tenant_phone:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tenant phone missing")

    sms_result = send_sms(tenant_phone, payload.message)

    return MistralSmsResponse(
        tenant_id=tenant.id,
        tenant_phone=sms_result["to"],
        user_message=payload.message,
        mistral_reply=payload.message,
        sms_status=sms_result["status"],
        sms_sid=sms_result["sid"],
    )
