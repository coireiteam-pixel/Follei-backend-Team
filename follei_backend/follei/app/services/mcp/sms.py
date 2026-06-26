import os
import re
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from fastapi import HTTPException
from dotenv import load_dotenv

load_dotenv()


def _normalize_phone(phone: str | None, *, field_name: str) -> str:
    value = (phone or "").strip()
    if not value:
        raise HTTPException(
            status_code=400,
            detail=f"{field_name} missing",
        )

    digits = re.sub(r"\D", "", value)
    if value.startswith("+") and 8 <= len(digits) <= 15:
        return f"+{digits}"

    default_country_code = os.getenv("DEFAULT_PHONE_COUNTRY_CODE", "+91").strip()
    country_digits = re.sub(r"\D", "", default_country_code)
    if len(digits) == 10 and country_digits:
        return f"+{country_digits}{digits}"

    raise HTTPException(
        status_code=400,
        detail=f"{field_name} must be in E.164 format, for example +15551234567",
    )


def send_sms(to_phone: str, message: str):
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    from_phone = os.getenv("TWILIO_FROM_PHONE")

    if not account_sid:
        raise HTTPException(
            status_code=500,
            detail="TWILIO_ACCOUNT_SID missing in .env"
        )

    if not auth_token:
        raise HTTPException(
            status_code=500,
            detail="TWILIO_AUTH_TOKEN missing in .env"
        )

    if not from_phone:
        raise HTTPException(
            status_code=500,
            detail="TWILIO_FROM_PHONE missing in .env"
        )

    normalized_from_phone = _normalize_phone(from_phone, field_name="TWILIO_FROM_PHONE")
    normalized_to_phone = _normalize_phone(to_phone, field_name="Recipient phone number")

    try:
        client = Client(account_sid, auth_token)

        sms = client.messages.create(
            body=message,
            from_=normalized_from_phone,
            to=normalized_to_phone
        )

        return {
            "success": True,
            "sid": sms.sid,
            "status": sms.status,
            "from": normalized_from_phone,
            "to": normalized_to_phone
        }

    except TwilioRestException as e:
        print("TWILIO ERROR:", str(e))
        error_text = f"{e.msg or ''} {str(e)}"
        if e.code == 21606 or "is not a Twilio phone number" in error_text:
            detail = (
                "Twilio Error: TWILIO_FROM_PHONE must be an SMS-capable Twilio phone number, "
                "not a normal personal mobile number. Buy or select a Twilio number in the Twilio console "
                "and put that number in .env as TWILIO_FROM_PHONE."
            )
        elif e.status in {401, 403}:
            detail = "Twilio Error: authentication failed. Check TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN in .env"
        else:
            detail = f"Twilio Error: {e.msg or str(e)}"

        raise HTTPException(
            status_code=500,
            detail=detail,
        )

    except Exception as e:
        print("TWILIO ERROR:", str(e))

        raise HTTPException(
            status_code=500,
            detail=f"Twilio Error: {str(e)}"
        )
