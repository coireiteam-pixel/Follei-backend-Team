from app.core.ids import short_id
from fastapi.concurrency import run_in_threadpool

from app.services.mcp.mistral import generate_mistral_reply
from app.services.twilio import send_sms


async def process_customer_message(
    *,
    tenant_id: str,
    customer_phone: str,
    customer_name: str | None,
    message: str,
    channel: str,
    conversation_id: str | None,
) -> dict:
    """Generate an AI reply and deliver it to the customer through Twilio."""

    # TODO: Add tenant lookup when tenant integration is implemented.
    # TODO: Add MCP tenant knowledge search when retrieval is implemented.
    ai_reply = await generate_mistral_reply(message)
    sms_result = await run_in_threadpool(send_sms, customer_phone, ai_reply)

    # TODO: Save the conversation and both messages when DB persistence is implemented.
    return {
        "tenant_id": tenant_id,
        "conversation_id": conversation_id,
        "customer_phone": sms_result["to"],
        "customer_name": customer_name,
        "customer_message": message,
        "ai_reply": ai_reply,
        "channel": channel,
        "sms_status": sms_result["status"],
        "sms_provider": "twilio",
        "provider_message_id": sms_result["sid"],
    }


def whatsapp_send_message(to: str, body: str, template: str | None = None) -> dict:
    return {"message_id": f"wamid.{short_id()}", "to": to, "body": body, "template": template, "status": "sent"}


def whatsapp_send_template(to: str, template_name: str, language: str, parameters: dict | None = None) -> dict:
    return {"message_id": f"wamid.{short_id()}", "to": to, "template_name": template_name, "language": language, "parameters": parameters or {}, "status": "sent"}


def slack_send_message(channel: str, text: str, blocks: list | None = None) -> dict:
    return {"message_ts": str(short_id()), "channel": channel, "text": text, "blocks": blocks or [], "sent": True}


def slack_post_channel(channel: str, message: str) -> dict:
    return {"message_ts": str(short_id()), "channel": channel, "message": message, "sent": True}


def teams_send_message(team_id: str, channel_id: str, text: str) -> dict:
    return {"message_id": str(short_id()), "team_id": team_id, "channel_id": channel_id, "text": text, "sent": True}
