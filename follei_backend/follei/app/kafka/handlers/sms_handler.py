"""Kafka handler that delegates SMS work to the application service."""

from typing import Any

from sqlalchemy.orm import Session

from app.database.session import SessionLocal
from app.schemas.integrations.sms import SmsSendRequest
from app.services.integrations.sms.sms_service import SmsService


async def handle_sms_event(event: dict[str, Any], db: Session | None = None) -> dict:
    if event.get("action") != "send_sms":
        raise ValueError("Unsupported SMS event action")

    owns_session = db is None
    session = db or SessionLocal()
    try:
        message = await SmsService(session).send_message(
            SmsSendRequest.model_validate(event.get("payload", {}))
        )
        return {
            "message_id": message.id,
            "twilio_message_sid": message.twilio_message_sid,
            "status": message.status,
        }
    finally:
        if owns_session:
            session.close()
