import base64
import html
import re
import json
import os
import sys
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Add current directory to path for direct execution
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __package__:
    from .config import (
        GMAIL_CLIENT_ID,
        GMAIL_CLIENT_SECRET,
        GMAIL_CREDENTIALS_FILE,
        GMAIL_TOKEN_FILE,
    )
else:
    # Docker/local runner imports this file as a top-level module.
    from config import (
        GMAIL_CLIENT_ID,
        GMAIL_CLIENT_SECRET,
        GMAIL_CREDENTIALS_FILE,
        GMAIL_TOKEN_FILE,
    )

# If modifying these scopes, delete the file token.json.
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify",
]


def get_gmail_service():
    """Authenticate and return a Gmail API service instance."""
    creds = None
    token_path = GMAIL_TOKEN_FILE
    credentials_path = GMAIL_CREDENTIALS_FILE

    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(credentials_path):
                raise FileNotFoundError(
                    f"Gmail credentials file not found at {credentials_path}. "
                    "Please download OAuth 2.0 credentials from Google Cloud Console."
                )
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(token_path, "w") as token:
            token.write(creds.to_json())

    service = build("gmail", "v1", credentials=creds)
    return service


def get_unread_messages(service, query: str, max_results: int = 10):
    """Fetch unread messages matching the query."""
    try:
        results = (
            service.users()
            .messages()
            .list(userId="me", q=query, maxResults=max_results)
            .execute()
        )
        messages = results.get("messages", [])
        return messages
    except HttpError as error:
        print(f"An error occurred while fetching messages: {error}")
        return []


def get_message_details(service, msg_id: str) -> Optional[dict]:
    """Get full message details including subject, from, and body."""
    try:
        message = (
            service.users().messages().get(userId="me", id=msg_id, format="full").execute()
        )
        return message
    except HttpError as error:
        print(f"An error occurred while fetching message {msg_id}: {error}")
        return None


def extract_message_data(message: dict) -> dict:
    """Extract relevant data from a Gmail message."""
    headers = message.get("payload", {}).get("headers", [])
    subject = ""
    from_email = ""
    to_email = ""
    message_id = message.get("id", "")
    thread_id = message.get("threadId", "")

    for header in headers:
        name = header.get("name", "").lower()
        value = header.get("value", "")
        if name == "subject":
            subject = value
        elif name == "from":
            from_email = value
        elif name == "to":
            to_email = value

    def decode_part(data: str) -> str:
        if not data:
            return ""
        return base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")

    def find_body(part: dict, mime_type: str) -> str:
        if part.get("mimeType") == mime_type:
            decoded = decode_part(part.get("body", {}).get("data", ""))
            if decoded.strip():
                return decoded
        for child in part.get("parts", []):
            decoded = find_body(child, mime_type)
            if decoded.strip():
                return decoded
        return ""

    payload = message.get("payload", {})
    body = find_body(payload, "text/plain")
    if not body.strip():
        html_body = find_body(payload, "text/html")
        body = html.unescape(re.sub(r"<[^>]+>", " ", html_body))
    body = re.sub(r"\s+", " ", body).strip()

    return {
        "id": message_id,
        "thread_id": thread_id,
        "subject": subject,
        "from": from_email,
        "to": to_email,
        "body": body,
    }


def add_message_label(service, message_id: str, label_name: str) -> bool:
    '''Create a Gmail label when needed and apply it to one message.'''
    try:
        labels = service.users().labels().list(userId='me').execute()
        label_id = next(
            (label['id'] for label in labels.get('labels', []) if label['name'] == label_name),
            None,
        )

        if not label_id:
            created_label = service.users().labels().create(
                userId='me',
                body={
                    'name': label_name,
                    'labelListVisibility': 'labelShow',
                    'messageListVisibility': 'show',
                },
            ).execute()
            label_id = created_label['id']

        service.users().messages().modify(
            userId='me',
            id=message_id,
            body={'addLabelIds': [label_id]},
        ).execute()
        return True
    except HttpError as error:
        print(f'Warning: Could not add Gmail label {label_name}: {error}')
        return False


def send_reply(service, to_email: str, subject: str, body: str, thread_id: str, message_id: str):
    """Send a reply to a Gmail message."""
    try:
        # Create the message
        message_text = f"To: {to_email}\n"
        message_text += f"Subject: Re: {subject}\n"
        message_text += f"In-Reply-To: {message_id}\n"
        message_text += f"References: {message_id}\n\n"
        message_text += body

        encoded_message = base64.urlsafe_b64encode(message_text.encode("utf-8")).decode(
            "utf-8"
        )

        create_message = {
            "raw": encoded_message,
            "threadId": thread_id,
        }

        sent_message = (
            service.users()
            .messages()
            .send(userId="me", body=create_message)
            .execute()
        )

        # Add label to mark as replied
        label_name = "Follei-Auto-Replied"
        try:
            # Get or create the label
            labels = service.users().labels().list(userId="me").execute()
            label_id = None
            for label in labels.get("labels", []):
                if label["name"] == label_name:
                    label_id = label["id"]
                    break

            if not label_id:
                label_object = {
                    "name": label_name,
                    "labelListVisibility": "labelShow",
                    "messageListVisibility": "show",
                }
                created_label = (
                    service.users()
                    .labels()
                    .create(userId="me", body=label_object)
                    .execute()
                )
                label_id = created_label["id"]

            # Add label to the original message
            service.users().messages().modify(
                userId="me", id=message_id, body={"addLabelIds": [label_id]}
            ).execute()
        except HttpError as label_error:
            print(f"Warning: Could not add label: {label_error}")

        return sent_message
    except HttpError as error:
        print(f"An error occurred while sending reply: {error}")
        return None
