"""MCP tool surface for the persistent SMS integration."""

from sqlalchemy.orm import Session

from app.schemas.integrations.sms import SmsMessageResponse, SmsSendRequest
from app.services.integrations.sms.sms_service import SmsService


async def send_sms(db: Session, *, tenant_id: str, to_phone: str, body: str) -> dict:
    message = await SmsService(db).send_message(
        SmsSendRequest(tenant_id=tenant_id, to_phone=to_phone, body=body)
    )
    return SmsMessageResponse.model_validate(message).model_dump(mode="json")


def get_sms_messages(
    db: Session,
    *,
    tenant_id: str,
    phone_number: str,
    limit: int = 100,
    offset: int = 0,
) -> dict:
    items, total = SmsService(db).get_messages(
        tenant_id,
        phone_number,
        limit=limit,
        offset=offset,
    )
    return {
        "tenant_id": tenant_id,
        "phone_number": phone_number,
        "items": [
            SmsMessageResponse.model_validate(item).model_dump(mode="json")
            for item in items
        ],
        "total": total,
    }


def search_sms_messages(
    db: Session,
    *,
    tenant_id: str,
    query: str,
    limit: int = 50,
) -> list[dict]:
    items = SmsService(db).search_messages(tenant_id, query, limit=limit)
    return [
        SmsMessageResponse.model_validate(item).model_dump(mode="json")
        for item in items
    ]


def list_sms_conversations(
    db: Session,
    *,
    tenant_id: str,
    limit: int = 100,
) -> list[dict]:
    conversations = SmsService(db).list_conversations(tenant_id, limit=limit)
    return [
        {
            "id": item.id,
            "tenant_id": item.tenant_id,
            "contact_id": item.contact_id,
            "phone_number": item.contact.phone_number,
            "status": item.status,
            "created_at": item.created_at.isoformat(),
            "updated_at": item.updated_at.isoformat(),
        }
        for item in conversations
    ]
