"""Thin Twilio webhook transport route."""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.integrations.sms import SmsWebhookResponse
from app.services.integrations.sms.sms_parser import SmsParser, SmsPayloadError
from app.services.integrations.sms.sms_service import SmsService


router = APIRouter(prefix="/webhooks/sms", tags=["SMS Integrations"])


@router.post(
    "/twilio",
    response_model=SmsWebhookResponse,
    summary="Receive an incoming Twilio SMS",
    openapi_extra={
        "requestBody": {
            "required": True,
            "content": {
                "application/x-www-form-urlencoded": {
                    "schema": {
                        "type": "object",
                        "required": ["From", "To", "Body", "MessageSid"],
                        "properties": {
                            "From": {"type": "string", "example": "+919876543210"},
                            "To": {"type": "string", "example": "+15672467340"},
                            "Body": {"type": "string", "example": "What services do you provide?"},
                            "MessageSid": {
                                "type": "string",
                                "example": "SMXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
                            },
                        },
                    }
                }
            },
        }
    },
)
async def receive_twilio_sms(
    request: Request,
    db: Session = Depends(get_db),
) -> SmsWebhookResponse:
    form = await request.form()
    try:
        payload = SmsParser.parse(form)
    except SmsPayloadError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    return await SmsService(db).receive_webhook(payload)
