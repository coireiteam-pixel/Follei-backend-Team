"""Kafka event handlers."""

from .sms_handler import handle_sms_event

__all__ = ["handle_sms_event"]
