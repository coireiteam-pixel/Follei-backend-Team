from app.core.ids import short_id
import os
import smtplib
from email.message import EmailMessage


def _smtp_send(to: str, subject: str, body: str) -> dict | None:
    host = os.getenv("SMTP_HOST")
    if not host:
        return None

    port = int(os.getenv("SMTP_PORT", "587"))
    username = os.getenv("SMTP_USER")
    password = os.getenv("SMTP_PASSWORD")
    from_email = os.getenv("SMTP_FROM", username or "noreply@follei.local")

    message = EmailMessage()
    message["From"] = from_email
    message["To"] = to
    message["Subject"] = subject
    message.set_content(body)

    with smtplib.SMTP(host, port) as smtp:
        if os.getenv("SMTP_TLS", "true").lower() == "true":
            smtp.starttls()
        if username and password:
            smtp.login(username, password)
        smtp.send_message(message)

    return {"message_id": str(short_id()), "to": to, "subject": subject, "sent": True, "provider": "smtp"}


def gmail_send(to: str, subject: str, body: str, attachments: list | None = None) -> dict:
    result = _smtp_send(to=to, subject=subject, body=body)
    if result is not None:
        return {**result, "attachments": attachments or []}
    return {"message_id": str(short_id()), "to": to, "subject": subject, "attachments": attachments or [], "sent": True, "mock": True}


def gmail_read(query: str, max_results: int = 10) -> dict:
    return {"messages": [{"id": str(short_id()), "subject": "Follow up", "body": "Sample message"} for _ in range(min(max_results, 3))]}


def outlook_send(to: str, subject: str, body: str) -> dict:
    result = _smtp_send(to=to, subject=subject, body=body)
    if result is not None:
        return result
    return {"message_id": str(short_id()), "to": to, "subject": subject, "sent": True, "mock": True}
