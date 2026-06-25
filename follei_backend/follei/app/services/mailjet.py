import base64
import json
import os
from urllib import error, request


MAILJET_SEND_URL = "https://api.mailjet.com/v3.1/send"


class MailjetConfigurationError(RuntimeError):
    pass


class MailjetAPIError(RuntimeError):
    pass


def send_email(*, to_email: str, subject: str, body: str, from_email: str | None = None) -> dict:
    api_key = os.getenv("MAILJET_API_KEY")
    api_secret = os.getenv("MAILJET_API_SECRET")
    sender_email = from_email or os.getenv("MAILJET_FROM_EMAIL")
    sender_name = os.getenv("MAILJET_FROM_NAME", "Follei")

    missing = [
        name
        for name, value in {
            "MAILJET_API_KEY": api_key,
            "MAILJET_API_SECRET": api_secret,
            "MAILJET_FROM_EMAIL": sender_email,
        }.items()
        if not value
    ]
    if missing:
        raise MailjetConfigurationError(f"{', '.join(missing)} is not configured.")

    payload = {
        "Messages": [
            {
                "From": {"Email": sender_email, "Name": sender_name},
                "To": [{"Email": to_email}],
                "Subject": subject,
                "TextPart": body,
            }
        ]
    }
    credentials = base64.b64encode(f"{api_key}:{api_secret}".encode("utf-8")).decode("ascii")
    mailjet_request = request.Request(
        MAILJET_SEND_URL,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )

    try:
        with request.urlopen(mailjet_request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace")
        raise MailjetAPIError(f"Mailjet API returned {exc.code}: {details}") from exc
    except error.URLError as exc:
        raise MailjetAPIError(f"Could not reach Mailjet API: {exc.reason}") from exc
