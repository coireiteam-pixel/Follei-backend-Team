import os
from twilio.rest import Client
from fastapi import HTTPException
from dotenv import load_dotenv

load_dotenv()


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

    if not to_phone:
        raise HTTPException(
            status_code=400,
            detail="Recipient phone number missing"
        )

    try:
        client = Client(account_sid, auth_token)

        sms = client.messages.create(
            body=message,
            from_=from_phone,
            to=to_phone
        )

        return {
            "success": True,
            "sid": sms.sid,
            "status": sms.status,
            "from": from_phone,
            "to": to_phone
        }

    except Exception as e:
        print("TWILIO ERROR:", str(e))

        raise HTTPException(
            status_code=500,
            detail=f"Twilio Error: {str(e)}"
        )
