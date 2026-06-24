from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.tenancy import Tenant
from app.services.mcp.sms import send_sms
from app.services.mistral import get_mistral_reply

router = APIRouter(prefix="/sms", tags=["SMS"])


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

    mistral_reply = await get_mistral_reply(
        [
            {
                "role": "system",
                "content": "You are a helpful assistant. Reply clearly and briefly for an SMS message.",
            },
            {
                "role": "user",
                "content": payload.message,
            },
        ]
    )
    sms_result = send_sms(tenant_phone, mistral_reply)

    return MistralSmsResponse(
        tenant_id=tenant.id,
        tenant_phone=tenant_phone,
        user_message=payload.message,
        mistral_reply=mistral_reply,
        sms_status=sms_result["status"],
        sms_sid=sms_result["sid"],
    )
