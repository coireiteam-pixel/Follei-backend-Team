"""Tenant-aware SMS orchestration and persistence."""

from fastapi import HTTPException, status
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.integrations.sms import SmsConversation, SmsMessage
from app.repositories.integration_repository import IntegrationRepository
from app.repositories.integrations.sms_repository import SmsRepository
from app.schemas.integrations.sms import SmsSendRequest, SmsWebhookResponse, TwilioSmsPayload
from app.services.integrations.sms.auto_reply_service import SmsAutoReplyService
from app.services.integrations.sms.twilio_client import SmsProviderError, TwilioClient


class SmsService:
    def __init__(
        self,
        db: Session,
        *,
        twilio_client: TwilioClient | None = None,
        auto_reply_service: SmsAutoReplyService | None = None,
    ) -> None:
        self.repository = SmsRepository(db)
        self.integration_repository = IntegrationRepository(db)
        self._twilio_client = twilio_client
        self.auto_reply_service = auto_reply_service or SmsAutoReplyService()

    def _active_tenant(self, tenant_id: str):
        tenant = self.repository.get_tenant(tenant_id)
        if tenant is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
        if tenant.status.lower() != "active":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant is inactive")
        return tenant

    def _client(self) -> TwilioClient:
        if self._twilio_client is None:
            try:
                self._twilio_client = TwilioClient()
            except SmsProviderError as exc:
                raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
        return self._twilio_client

    async def send_message(self, payload: SmsSendRequest) -> SmsMessage:
        self._active_tenant(payload.tenant_id)
        try:
            result = await run_in_threadpool(self._client().send_sms, payload.to_phone, payload.body)
        except SmsProviderError as exc:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

        try:
            contact = self.repository.get_or_create_contact(payload.tenant_id, result["to"])
            conversation = self.repository.get_or_create_conversation(payload.tenant_id, contact.id)
            message = self.repository.create_message(
                tenant_id=payload.tenant_id,
                conversation_id=conversation.id,
                direction="outbound",
                from_phone=result["from"],
                to_phone=result["to"],
                body=payload.body,
                status=result["status"],
                message_sid=result["sid"],
            )
            self.repository.commit()
            self.repository.refresh(message)
            return message
        except IntegrityError as exc:
            self.repository.rollback()
            existing = self.repository.get_message_by_sid(result["sid"])
            if existing is not None:
                return existing
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Twilio message has already been stored",
            ) from exc
        except Exception:
            self.repository.rollback()
            raise

    async def receive_webhook(self, payload: TwilioSmsPayload) -> SmsWebhookResponse:
        integration = self.integration_repository.get_by_phone(payload.to_phone)
        if integration is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No tenant Twilio integration is configured for this destination number",
            )
        if integration.status.lower() != "active":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Integration is inactive")
        tenant = self._active_tenant(integration.tenant_id)

        duplicate = self.repository.get_message_by_sid(payload.message_sid)
        if duplicate is not None:
            return SmsWebhookResponse(
                duplicate=True,
                inbound_message_id=duplicate.id,
                conversation_id=duplicate.conversation_id,
            )

        try:
            contact = self.repository.get_or_create_contact(tenant.id, payload.from_phone)
            conversation = self.repository.get_or_create_conversation(tenant.id, contact.id)
            inbound = self.repository.create_message(
                tenant_id=tenant.id,
                conversation_id=conversation.id,
                direction="inbound",
                from_phone=payload.from_phone,
                to_phone=payload.to_phone,
                body=payload.body,
                status="received",
                message_sid=payload.message_sid,
            )
            self.repository.commit()
            self.repository.refresh(inbound)
        except IntegrityError:
            self.repository.rollback()
            duplicate = self.repository.get_message_by_sid(payload.message_sid)
            if duplicate is None:
                raise
            return SmsWebhookResponse(
                duplicate=True,
                inbound_message_id=duplicate.id,
                conversation_id=duplicate.conversation_id,
            )
        except Exception:
            self.repository.rollback()
            raise

        history = self.repository.recent_messages(tenant.id, conversation.id)
        reply = await self.auto_reply_service.generate_reply(tenant.name, history)
        try:
            result = await run_in_threadpool(self._client().send_sms, payload.from_phone, reply)
        except (SmsProviderError, HTTPException):
            return SmsWebhookResponse(
                inbound_message_id=inbound.id,
                conversation_id=conversation.id,
                reply_status="failed",
            )

        try:
            outgoing = self.repository.create_message(
                tenant_id=tenant.id,
                conversation_id=conversation.id,
                direction="outbound",
                from_phone=result["from"],
                to_phone=result["to"],
                body=reply,
                status=result["status"],
                message_sid=result["sid"],
            )
            self.repository.commit()
            self.repository.refresh(outgoing)
        except Exception:
            self.repository.rollback()
            raise

        return SmsWebhookResponse(
            inbound_message_id=inbound.id,
            conversation_id=conversation.id,
            reply_message_id=outgoing.id,
            reply_status=outgoing.status,
        )

    def get_messages(self, tenant_id: str, phone_number: str, *, limit: int = 100, offset: int = 0) -> tuple[list[SmsMessage], int]:
        self._active_tenant(tenant_id)
        return self.repository.list_messages(tenant_id, phone_number, limit=limit, offset=offset)

    def search_messages(self, tenant_id: str, query: str, *, limit: int = 50) -> list[SmsMessage]:
        self._active_tenant(tenant_id)
        return self.repository.search_messages(tenant_id, query, limit=limit)

    def list_conversations(self, tenant_id: str, *, limit: int = 100) -> list[SmsConversation]:
        self._active_tenant(tenant_id)
        return self.repository.list_conversations(tenant_id, limit=limit)
