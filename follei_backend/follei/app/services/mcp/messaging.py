from app.core.ids import short_id


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
