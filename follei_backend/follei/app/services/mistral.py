import json
import os
from typing import AsyncGenerator, Dict, List

import httpx
from dotenv import load_dotenv
from fastapi import HTTPException, status

load_dotenv()


MISTRAL_CHAT_COMPLETIONS_URL = "https://api.mistral.ai/v1/chat/completions"
PLACEHOLDER_API_KEYS = {
    "",
    "your_mistral_api_key",
    "change_this_mistral_api_key",
}


class MistralConfigurationError(RuntimeError):
    pass


class MistralAPIError(RuntimeError):
    pass


def _get_mistral_api_key() -> str:
    api_key = (os.getenv("MISTRAL_API_KEY") or "").strip()
    if api_key in PLACEHOLDER_API_KEYS:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="MISTRAL_API_KEY missing in .env",
        )
    return api_key


def _get_mistral_model() -> str:
    return (os.getenv("MISTRAL_MODEL") or "mistral-large-latest").strip()


def _mistral_error_detail(response: httpx.Response) -> str:
    try:
        payload = response.json()
    except json.JSONDecodeError:
        payload = response.text

    if response.status_code in {401, 403}:
        return "Mistral API authentication failed. Check MISTRAL_API_KEY in .env"

    return f"Mistral API error {response.status_code}: {str(payload)[:500]}"


async def get_mistral_reply(messages: list[dict]) -> str:
    headers = {
        "Authorization": f"Bearer {_get_mistral_api_key()}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": _get_mistral_model(),
        "messages": messages,
        "temperature": 0.4,
        "max_tokens": 800,
    }

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(MISTRAL_CHAT_COMPLETIONS_URL, headers=headers, json=payload)
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Mistral API request failed: {exc}",
        ) from exc

    if response.status_code >= 400:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=_mistral_error_detail(response),
        )

    try:
        data = response.json()
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Mistral API returned an unexpected response",
        ) from exc


async def stream_mistral_reply(messages: List[Dict]) -> AsyncGenerator[str, None]:
    headers = {
        "Authorization": f"Bearer {_get_mistral_api_key()}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": _get_mistral_model(),
        "messages": messages,
        "stream": True,
        "temperature": 0.4,
        "max_tokens": 800,
    }

    async with httpx.AsyncClient(timeout=None) as client:
        async with client.stream("POST", MISTRAL_CHAT_COMPLETIONS_URL, headers=headers, json=payload) as response:
            if response.status_code >= 400:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=_mistral_error_detail(response),
                )

            async for line in response.aiter_lines():
                if not line:
                    continue

                if line.startswith("data: "):
                    data = line.replace("data: ", "")

                    if data == "[DONE]":
                        break

                    try:
                        chunk = json.loads(data)
                        delta = chunk["choices"][0]["delta"].get("content")
                        if delta:
                            yield delta
                    except Exception:
                        continue


def chat_completion(
    *,
    system_prompt: str,
    user_message: str,
    context: str | None = None,
    model: str | None = None,
    max_tokens: int = 1024,
) -> str:
    api_key = (os.getenv("MISTRAL_API_KEY") or "").strip()
    if api_key in PLACEHOLDER_API_KEYS:
        raise MistralConfigurationError("MISTRAL_API_KEY is not configured.")

    selected_model = model or _get_mistral_model()
    prompt = user_message if not context else f"{context}\n\nUser request:\n{user_message}"
    payload = {
        "model": selected_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": max_tokens,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    try:
        with httpx.Client(timeout=45) as client:
            response = client.post(MISTRAL_CHAT_COMPLETIONS_URL, headers=headers, json=payload)
    except httpx.RequestError as exc:
        raise MistralAPIError(f"Could not reach Mistral API: {exc}") from exc

    if response.status_code >= 400:
        raise MistralAPIError(_mistral_error_detail(response))

    try:
        data = response.json()
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
        raise MistralAPIError(f"Unexpected Mistral API response: {response.text}") from exc
