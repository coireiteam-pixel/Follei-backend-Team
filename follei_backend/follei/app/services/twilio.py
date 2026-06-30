"""Compatibility facade for the structured Twilio client.

New code should import TwilioClient directly from
app.services.integrations.sms.twilio_client.
"""

from typing import Any, Callable

from fastapi import HTTPException
from twilio.rest import Client

from app.services.integrations.sms.twilio_client import SmsProviderError, TwilioClient


def send_sms(
    to_phone: str,
    message: str,
    *,
    account_sid: str | None = None,
    auth_token: str | None = None,
    from_phone: str | None = None,
    client_factory: Callable[[str, str], Any] | None = None,
) -> dict[str, Any]:
    kwargs: dict[str, Any] = {
        "account_sid": account_sid,
        "auth_token": auth_token,
        "from_phone": from_phone,
    }
    if client_factory is not None:
        kwargs["client_factory"] = client_factory
    try:
        return TwilioClient(**kwargs).send_sms(to_phone, message)
    except SmsProviderError as exc:
        raise HTTPException(status_code=500, detail=f"Twilio Error: {exc}") from exc


def send_sms_reply(to_phone: str, message: str) -> dict[str, str]:
    try:
        return TwilioClient().send_sms(to_phone, message)
    except SmsProviderError as exc:
        raise RuntimeError(str(exc)) from exc
