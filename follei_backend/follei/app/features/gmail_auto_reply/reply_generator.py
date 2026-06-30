import os
import sys
from typing import Optional

import requests

# Add current directory to path for direct execution
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __package__:
    from .config import MISTRAL_API_KEY, MISTRAL_MODEL
else:
    # Docker/local runner imports this file as a top-level module.
    from config import MISTRAL_API_KEY, MISTRAL_MODEL


def generate_reply(
    original_subject: str,
    original_body: str,
    from_email: str,
    context: Optional[str] = None,
) -> str:
    """
    Generate an AI-powered reply using Mistral API.
    
    Args:
        original_subject: The subject of the incoming email
        original_body: The body/content of the incoming email
        from_email: The sender's email address
        context: Optional context about the business/service
    
    Returns:
        Generated reply text
    """
    if not MISTRAL_API_KEY:
        return "Thank you for your email. We have received your message and will get back to you soon."

    # Build the prompt
    system_prompt = """You are Follei's email assistant.
Answer the sender's actual question directly and accurately using the message content.
Do not send a generic acknowledgement and do not promise a reply in 24-48 hours.
Keep the answer concise, useful, friendly, and professional (usually 3-6 sentences).
Use plain text only. Do not invent Follei-specific facts that were not provided."""

    if context:
        system_prompt += f"\n\nContext about our service: {context}"

    user_prompt = f"""Generate a professional reply to this email:

From: {from_email}
Subject: {original_subject}

Message:
{original_body}

Write the ready-to-send answer. If the subject is empty, infer the topic from the message."""

    try:
        response = requests.post(
            "https://api.mistral.ai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {MISTRAL_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": MISTRAL_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "max_tokens": 350,
                "temperature": 0.3,
            },
            timeout=30,
        )

        if response.status_code == 200:
            result = response.json()
            reply = result["choices"][0]["message"]["content"].strip()
            return reply
        else:
            print(f"Mistral API error: {response.status_code} - {response.text}")
            return "Thank you for your email. We have received your message and will get back to you soon."

    except Exception as e:
        print(f"Error generating reply: {e}")
        return "Thank you for your email. We have received your message and will get back to you soon."


def generate_simple_reply(original_subject: str, from_email: str) -> str:
    """Generate a simple acknowledgment reply when AI generation fails."""
    return f"""Hi,

Thank you for reaching out regarding "{original_subject}". 

We have received your email and our team will review it and get back to you within 24-48 hours.

Best regards,
Follei Team"""
