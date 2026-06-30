"""Backward-compatible MCP facade for the canonical Twilio SMS service."""

from twilio.rest import Client

from app.services.twilio import send_sms as _send_sms


def send_sms(to_phone: str, message: str, **kwargs):
    """Delegate to `app.services.twilio` for existing MCP consumers."""

    kwargs.setdefault("client_factory", Client)
    return _send_sms(to_phone, message, **kwargs)
