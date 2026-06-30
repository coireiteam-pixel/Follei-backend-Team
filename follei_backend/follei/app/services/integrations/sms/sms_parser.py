"""Twilio webhook parsing; no business logic belongs here."""

from collections.abc import Mapping
from typing import Any

from pydantic import ValidationError

from app.schemas.integrations.sms import TwilioSmsPayload


class SmsPayloadError(ValueError):
    """Raised when a Twilio form payload is incomplete or invalid."""


class SmsParser:
    @staticmethod
    def parse(payload: Mapping[str, Any]) -> TwilioSmsPayload:
        normalized = {str(key): str(value).strip() for key, value in payload.items()}
        try:
            return TwilioSmsPayload.model_validate(normalized)
        except ValidationError as exc:
            raise SmsPayloadError("Invalid Twilio SMS webhook payload") from exc
