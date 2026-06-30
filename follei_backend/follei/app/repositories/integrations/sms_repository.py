"""All database access for tenant-scoped SMS data."""

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models.integrations.sms import SmsContact, SmsConversation, SmsMessage
from app.models.tenancy import Tenant


class SmsRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_tenant(self, tenant_id: str) -> Tenant | None:
        return self.db.get(Tenant, tenant_id)

    def get_contact(self, tenant_id: str, phone_number: str) -> SmsContact | None:
        return self.db.scalar(select(SmsContact).where(SmsContact.tenant_id == tenant_id, SmsContact.phone_number == phone_number))

    def get_or_create_contact(self, tenant_id: str, phone_number: str) -> SmsContact:
        contact = self.get_contact(tenant_id, phone_number)
        if contact is None:
            contact = SmsContact(tenant_id=tenant_id, phone_number=phone_number)
            self.db.add(contact)
            self.db.flush()
        return contact

    def get_open_conversation(self, tenant_id: str, contact_id: str) -> SmsConversation | None:
        return self.db.scalar(
            select(SmsConversation)
            .where(
                SmsConversation.tenant_id == tenant_id,
                SmsConversation.contact_id == contact_id,
                SmsConversation.status == "open",
            )
            .order_by(SmsConversation.updated_at.desc())
            .limit(1)
        )

    def get_or_create_conversation(self, tenant_id: str, contact_id: str) -> SmsConversation:
        conversation = self.get_open_conversation(tenant_id, contact_id)
        if conversation is None:
            conversation = SmsConversation(tenant_id=tenant_id, contact_id=contact_id)
            self.db.add(conversation)
            self.db.flush()
        else:
            conversation.updated_at = datetime.now(timezone.utc)
        return conversation

    def get_message_by_sid(self, message_sid: str) -> SmsMessage | None:
        return self.db.scalar(
            select(SmsMessage)
            .options(joinedload(SmsMessage.conversation))
            .where(SmsMessage.twilio_message_sid == message_sid)
        )

    def create_message(self, *, tenant_id: str, conversation_id: str, direction: str, from_phone: str, to_phone: str, body: str, status: str, message_sid: str) -> SmsMessage:
        message = SmsMessage(
            tenant_id=tenant_id,
            conversation_id=conversation_id,
            direction=direction,
            from_phone=from_phone,
            to_phone=to_phone,
            body=body,
            status=status,
            twilio_message_sid=message_sid,
        )
        self.db.add(message)
        self.db.flush()
        return message

    def list_messages(self, tenant_id: str, phone_number: str, *, limit: int = 100, offset: int = 0) -> tuple[list[SmsMessage], int]:
        criteria = (SmsMessage.tenant_id == tenant_id, SmsContact.phone_number == phone_number)
        base = (
            select(SmsMessage)
            .join(SmsConversation, SmsMessage.conversation_id == SmsConversation.id)
            .join(SmsContact, SmsConversation.contact_id == SmsContact.id)
            .where(*criteria)
        )
        items = list(self.db.scalars(base.order_by(SmsMessage.created_at.asc()).offset(offset).limit(limit)))
        total = self.db.scalar(
            select(func.count(SmsMessage.id))
            .join(SmsConversation, SmsMessage.conversation_id == SmsConversation.id)
            .join(SmsContact, SmsConversation.contact_id == SmsContact.id)
            .where(*criteria)
        )
        return items, int(total or 0)

    def recent_messages(self, tenant_id: str, conversation_id: str, limit: int = 20) -> list[SmsMessage]:
        items = list(
            self.db.scalars(
                select(SmsMessage)
                .where(SmsMessage.tenant_id == tenant_id, SmsMessage.conversation_id == conversation_id)
                .order_by(SmsMessage.created_at.desc())
                .limit(limit)
            )
        )
        return list(reversed(items))

    def search_messages(self, tenant_id: str, query: str, limit: int = 50) -> list[SmsMessage]:
        return list(
            self.db.scalars(
                select(SmsMessage)
                .where(SmsMessage.tenant_id == tenant_id, SmsMessage.body.ilike(f"%{query}%"))
                .order_by(SmsMessage.created_at.desc())
                .limit(limit)
            )
        )

    def list_conversations(self, tenant_id: str, limit: int = 100) -> list[SmsConversation]:
        return list(
            self.db.scalars(
                select(SmsConversation)
                .options(joinedload(SmsConversation.contact))
                .where(SmsConversation.tenant_id == tenant_id)
                .order_by(SmsConversation.updated_at.desc())
                .limit(limit)
            )
        )

    def commit(self) -> None:
        self.db.commit()

    def rollback(self) -> None:
        self.db.rollback()

    def refresh(self, instance: object) -> None:
        self.db.refresh(instance)
