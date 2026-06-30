from urllib.parse import quote

from fastapi.testclient import TestClient

from app.core.ids import short_id
from app.database.session import SessionLocal
from app.main import app
from app.models.tenancy import Tenant
from app.services.integrations.sms import auto_reply_service, twilio_client


client = TestClient(app)


def test_persistent_sms_send_webhook_history_and_deduplication(monkeypatch):
    tenant_id = str(short_id())
    tenant_phone = "+15672467340"
    customer_phone = "+919876543210"
    with SessionLocal() as db:
        db.add(
            Tenant(
                id=tenant_id,
                name=f"Persistent SMS {tenant_id}",
                domain=f"persistent-sms-{tenant_id}.example.com",
                status="active",
            )
        )
        db.commit()

    integration_response = client.post(
        "/api/integrations",
        json={
            "tenant_id": tenant_id,
            "name": "Twilio Persistent SMS",
            "provider": "twilio",
            "phone_number": tenant_phone,
            "status": "active",
        },
    )
    assert integration_response.status_code == 201

    monkeypatch.setenv("TWILIO_ACCOUNT_SID", "AC_TEST")
    monkeypatch.setenv("TWILIO_AUTH_TOKEN", "test-token")
    monkeypatch.setenv("TWILIO_FROM_PHONE", tenant_phone)
    sent_count = 0

    def fake_send(self, to_phone: str, body: str) -> dict[str, str]:
        nonlocal sent_count
        sent_count += 1
        return {
            "sid": f"SM_OUT_{sent_count}",
            "status": "sent",
            "from": tenant_phone,
            "to": to_phone,
        }

    async def fake_mistral(messages: list[dict[str, str]]) -> str:
        return "Follei can help with customer automation."

    monkeypatch.setattr(twilio_client.TwilioClient, "send_sms", fake_send)
    monkeypatch.setattr(auto_reply_service, "get_mistral_reply", fake_mistral)

    form = {
        "From": customer_phone,
        "To": tenant_phone,
        "Body": "What does Follei provide?",
        "MessageSid": "SM_IN_PERSISTENCE_1",
    }
    webhook = client.post("/api/webhooks/sms/twilio", data=form)
    assert webhook.status_code == 200
    assert webhook.json()["duplicate"] is False
    assert webhook.json()["reply_status"] == "sent"

    duplicate = client.post("/api/webhooks/sms/twilio", data=form)
    assert duplicate.status_code == 200
    assert duplicate.json()["duplicate"] is True
    assert sent_count == 1

    outgoing = client.post(
        "/api/integrations/sms/send",
        json={
            "tenant_id": tenant_id,
            "to_phone": customer_phone,
            "body": "A manual follow-up.",
        },
    )
    assert outgoing.status_code == 200
    assert outgoing.json()["message"]["direction"] == "outbound"

    history = client.get(
        f"/api/integrations/sms/messages/{quote(customer_phone, safe='')}",
        params={"tenant_id": tenant_id},
    )
    assert history.status_code == 200
    assert history.json()["total"] == 3
    assert [item["direction"] for item in history.json()["items"]] == [
        "inbound",
        "outbound",
        "outbound",
    ]
