from pydantic import BaseModel, EmailStr, Field
from fastapi import APIRouter

from app.services.mcp.email import mailjet_send
from app.services.mistral import get_mistral_reply

router = APIRouter(prefix="/v1/email", tags=["AI Email Assistant"])


class MailjetAutoReplyRequest(BaseModel):
    tenant_id: str = Field(default="T001", description="Tenant that owns this email flow")
    from_email: EmailStr = Field(..., description="Customer or lead email address")
    to_email: EmailStr = Field(..., description="Recipient email address for the reply")
    subject: str = Field(..., min_length=1, description="Incoming email subject")
    body: str = Field(..., min_length=1, description="Incoming email body")
    tone: str = Field(default="professional", description="Reply tone")
    context: str | None = Field(default=None, description="Extra business context for the assistant")
    dry_run: bool = Field(default=False, description="Generate the reply without sending email")


class MailjetAutoReplyResponse(BaseModel):
    tenant_id: str
    from_email: EmailStr
    to_email: EmailStr
    subject: str
    ai_reply: str
    dry_run: bool
    email_result: dict


@router.post("/mailjet-auto-reply", response_model=MailjetAutoReplyResponse)
async def mailjet_auto_reply(payload: MailjetAutoReplyRequest) -> MailjetAutoReplyResponse:
    prompt = (
        "Write a concise, helpful email reply for a sales/customer-success team.\n"
        f"Tone: {payload.tone}\n"
        f"Incoming from: {payload.from_email}\n"
        f"Subject: {payload.subject}\n"
        f"Message:\n{payload.body}"
    )
    if payload.context:
        prompt += f"\n\nBusiness context:\n{payload.context}"

    ai_reply = await get_mistral_reply(
        [
            {
                "role": "system",
                "content": "You are Follei's AI Email Assistant. Reply as the business, not as an AI model.",
            },
            {"role": "user", "content": prompt},
        ]
    )

    if payload.dry_run:
        email_result = {"sent": False, "dry_run": True}
    else:
        email_result = mailjet_send(
            to=str(payload.to_email),
            subject=f"Re: {payload.subject}",
            body=ai_reply,
        )

    return MailjetAutoReplyResponse(
        tenant_id=payload.tenant_id,
        from_email=payload.from_email,
        to_email=payload.to_email,
        subject=payload.subject,
        ai_reply=ai_reply,
        dry_run=payload.dry_run,
        email_result=email_result,
    )
