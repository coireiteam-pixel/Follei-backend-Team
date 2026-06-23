from app.core.ids import short_id


def gmail_send(to: str, subject: str, body: str, attachments: list | None = None) -> dict:
    return {"message_id": str(short_id()), "to": to, "subject": subject, "attachments": attachments or [], "sent": True}


def gmail_read(query: str, max_results: int = 10) -> dict:
    return {"messages": [{"id": str(short_id()), "subject": "Follow up", "body": "Sample message"} for _ in range(min(max_results, 3))]}


def outlook_send(to: str, subject: str, body: str) -> dict:
    return {"message_id": str(short_id()), "to": to, "subject": subject, "sent": True}
