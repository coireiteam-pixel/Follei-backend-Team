import asyncio

from fastapi import APIRouter

from .auto_reply import run_once
from .config import (
    GMAIL_AUTO_REPLY_ENABLED,
    GMAIL_AUTO_REPLY_QUERY,
    GMAIL_CREDENTIALS_FILE,
    GMAIL_POLL_SECONDS,
    GMAIL_TOKEN_FILE,
)


router = APIRouter(
    prefix="/v1/email/gmail-auto-reply",
    tags=["Gmail Auto Reply"],
)


@router.get("/status")
def gmail_auto_reply_status() -> dict:
    """Return configuration readiness without exposing OAuth secrets."""
    return {
        "enabled": GMAIL_AUTO_REPLY_ENABLED,
        "poll_seconds": GMAIL_POLL_SECONDS,
        "query": GMAIL_AUTO_REPLY_QUERY,
        "credentials_configured": bool(GMAIL_CREDENTIALS_FILE),
        "token_configured": bool(GMAIL_TOKEN_FILE),
    }


@router.post("/poll")
async def poll_gmail_once() -> dict:
    """Run one Gmail polling cycle without blocking the API event loop."""
    replies_sent = await asyncio.to_thread(run_once)
    return {"status": "success", "replies_sent": replies_sent}


async def gmail_auto_reply_worker() -> None:
    """Continuously poll Gmail while remaining cancellable by FastAPI."""
    while True:
        await asyncio.to_thread(run_once)
        await asyncio.sleep(GMAIL_POLL_SECONDS)


__all__ = ["gmail_auto_reply_worker", "router"]
