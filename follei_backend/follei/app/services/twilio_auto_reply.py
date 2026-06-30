"""Tenant-aware Twilio SMS auto-reply orchestration."""

import logging
from datetime import datetime, timezone
from time import perf_counter
from typing import Any

from fastapi import HTTPException, status
from fastapi.concurrency import run_in_threadpool
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.ids import short_id
from app.models.conversations.conversation import Conversation, Message
from app.models.domain import Event
from app.models.tenancy import Tenant
from app.services.mistral import get_mistral_reply
from app.services.twilio import send_sms_reply


logger = logging.getLogger(__name__)
DEFAULT_FALLBACK_RESPONSE = "Sorry, we are unable to process your message right now. Please try again later."
HISTORY_LIMIT = 20


def _parse_timestamp(value: str | None) -> datetime:
    if not value:
        return datetime.now(timezone.utc)
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        logger.warning("Invalid Twilio timestamp; using server time", extra={"timestamp": value})
        return datetime.now(timezone.utc)


def _get_or_create_conversation(db: Session, tenant_id: str, customer_phone: str, now: datetime) -> Conversation:
    title = f"SMS:{customer_phone}"
    conversation = db.scalar(
        select(Conversation)
        .where(
            Conversation.tenant_id == tenant_id,
            Conversation.channel == "sms",
            Conversation.title == title,
            Conversation.status == "open",
        )
        .order_by(Conversation.created_at.desc())
        .limit(1)
    )
    if conversation is None:
        conversation = Conversation(
            id=str(short_id()),
            tenant_id=tenant_id,
            title=title,
            channel="sms",
            status="open",
            started_at=now,
            created_at=now,
            updated_at=now,
        )
        db.add(conversation)
        db.flush()
    return conversation


def _conversation_history(db: Session, conversation_id: str) -> list[dict[str, str]]:
    stored = list(
        db.scalars(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(HISTORY_LIMIT)
        )
    )
    return [
        {"role": "assistant" if item.role in {"assistant", "agent"} else "user", "content": item.content}
        for item in reversed(stored)
        if item.role in {"user", "customer", "assistant", "agent"}
    ]


def _system_message(tenant: Tenant) -> str:
    return f"You are the SMS assistant for {tenant.name}. Generate a concise, helpful response."


async def process_twilio_auto_reply(
    *,
    db: Session,
    integration_id: str,
    tenant: Tenant,
    event_id: str,
    customer_phone: str,
    to_phone: str,
    body: str,
    message_sid: str | None,
    timestamp: str | None,
    raw_payload: dict[str, Any],
) -> dict[str, Any]:
    """Persist an inbound SMS, generate tenant-context AI text, and send it."""

    started = perf_counter()
    received_at = _parse_timestamp(timestamp)
    logger.info(
        "Incoming SMS tenant=%s customer=%s integration=%s message_sid=%s",
        tenant.id,
        customer_phone,
        integration_id,
        message_sid,
    )

    conversation = _get_or_create_conversation(db, tenant.id, customer_phone, received_at)
    history = _conversation_history(db, conversation.id)
    db.add(
        Event(
            id=event_id,
            tenant_id=tenant.id,
            event_type="twilio.sms.received",
            payload={"integration_id": integration_id, **raw_payload},
            created_at=received_at,
        )
    )
    db.add(
        Message(
            id=str(short_id()),
            tenant_id=tenant.id,
            conversation_id=conversation.id,
            role="user",
            content=body,
            sender_type="customer",
            message=body,
            message_type="sms",
            metadata_={
                "sender": "customer",
                "customer_phone": customer_phone,
                "twilio_phone_number": to_phone,
                "message_sid": message_sid,
            },
            created_at=received_at,
        )
    )
    try:
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("Failed to persist incoming Twilio SMS tenant=%s", tenant.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to store the incoming SMS",
        )

    mistral_messages = [
        {"role": "system", "content": _system_message(tenant)},
        *history,
        {"role": "user", "content": body},
    ]
    logger.info("Mistral prompt tenant=%s messages=%s", tenant.id, mistral_messages)
    used_fallback = False
    try:
        ai_reply = await get_mistral_reply(mistral_messages)
        logger.info("Mistral response tenant=%s response=%s", tenant.id, ai_reply)
    except Exception:
        used_fallback = True
        ai_reply = DEFAULT_FALLBACK_RESPONSE
        logger.exception("Mistral request failed; using fallback tenant=%s", tenant.id)

    reply_message = Message(
        id=str(short_id()),
        tenant_id=tenant.id,
        conversation_id=conversation.id,
        role="assistant",
        content=ai_reply,
        sender_type="ai",
        message=ai_reply,
        message_type="sms",
        metadata_={"sender": "ai", "fallback": used_fallback},
        created_at=datetime.now(timezone.utc),
    )
    db.add(reply_message)
    try:
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("Failed to persist AI SMS reply tenant=%s", tenant.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to store the AI reply",
        )

    sms_result: dict[str, Any] = {}
    try:
        sms_result = await run_in_threadpool(send_sms_reply, customer_phone, ai_reply)
        sms_status = "sent"
    except Exception:
        logger.exception("Twilio send failed tenant=%s customer=%s", tenant.id, customer_phone)
        sms_status = "failed"

    elapsed_ms = round((perf_counter() - started) * 1000, 2)
    logger.info(
        "Twilio response tenant=%s customer=%s sid=%s status=%s execution_ms=%s",
        tenant.id,
        customer_phone,
        sms_result.get("sid"),
        sms_status,
        elapsed_ms,
    )
    return {
        "tenant_id": tenant.id,
        "conversation_id": conversation.id,
        "customer_phone": customer_phone,
        "tenant_phone": to_phone,
        "customer_message": body,
        "ai_reply": ai_reply,
        "sms_status": sms_status,
        "provider_message_id": sms_result.get("sid"),
        "fallback_used": used_fallback,
    }
