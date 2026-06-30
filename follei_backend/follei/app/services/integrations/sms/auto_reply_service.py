"""Mistral-powered SMS reply business rules."""

from app.models.integrations.sms import SmsMessage
from app.services.mistral import get_mistral_reply


DEFAULT_FALLBACK_REPLY = "Sorry, we are unable to process your message right now. Please try again later."


class SmsAutoReplyService:
    async def generate_reply(self, tenant_name: str, history: list[SmsMessage]) -> str:
        messages: list[dict[str, str]] = [
            {
                "role": "system",
                "content": f"You are the SMS assistant for {tenant_name}. Reply concisely and helpfully.",
            }
        ]
        messages.extend(
            {
                "role": "assistant" if message.direction == "outbound" else "user",
                "content": message.body,
            }
            for message in history
        )
        try:
            reply = (await get_mistral_reply(messages)).strip()
            return reply or DEFAULT_FALLBACK_REPLY
        except Exception:
            return DEFAULT_FALLBACK_REPLY
