"""Mistral integration for customer SMS replies."""

import json
import os

import httpx
from dotenv import load_dotenv
from fastapi import HTTPException, status


MISTRAL_CHAT_URL = "https://api.mistral.ai/v1/chat/completions"
load_dotenv()


def _error_detail(code: str, message: str) -> dict[str, str | bool]:
    return {"success": False, "code": code, "message": message}


async def generate_mistral_reply(
    message: str | None = None,
    *,
    messages: list[dict[str, str]] | None = None,
    api_key: str | None = None,
    model: str | None = None,
) -> str:
    """Send tenant-scoped conversation messages to Mistral.

    ``message`` remains supported for existing callers. Tenant-aware callers can
    provide their own API key and complete conversation context.
    """

    resolved_api_key = (api_key or os.getenv("MISTRAL_API_KEY") or "").strip()
    if not resolved_api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=_error_detail("MISTRAL_NOT_CONFIGURED", "MISTRAL_API_KEY is not configured."),
        )

    request_messages = messages or ([{"role": "user", "content": message}] if message else [])
    if not request_messages:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=_error_detail("MISTRAL_MESSAGE_REQUIRED", "At least one message is required."),
        )

    resolved_model = (model or os.getenv("MISTRAL_MODEL") or "").strip() or "mistral-small-latest"
    payload = {
        "model": resolved_model,
        "messages": request_messages,
    }
    headers = {"Authorization": f"Bearer {resolved_api_key}", "Content-Type": "application/json"}

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(MISTRAL_CHAT_URL, headers=headers, json=payload)
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=_error_detail("MISTRAL_REQUEST_FAILED", "Unable to reach the Mistral API."),
        ) from exc

    if response.status_code >= 400:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=_error_detail("MISTRAL_API_FAILED", f"Mistral API returned status {response.status_code}."),
        )

    try:
        reply = response.json()["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, TypeError, AttributeError, json.JSONDecodeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=_error_detail("MISTRAL_INVALID_RESPONSE", "Mistral API returned an invalid response."),
        ) from exc

    if not reply:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=_error_detail("MISTRAL_EMPTY_RESPONSE", "Mistral API returned an empty reply."),
        )
    return reply
