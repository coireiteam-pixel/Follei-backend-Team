from fastapi.testclient import TestClient

from app.core.ids import short_id
from app.database.session import SessionLocal
from app.main import app
from app.models.tenancy import Tenant
from app.services import twilio_auto_reply

client = TestClient(app)


def _integration(*, tenant_status: str = "active") -> str:
    tenant_id = str(short_id())
    with SessionLocal() as db:
        db.add(Tenant(id=tenant_id, name=f"SMS Tenant {tenant_id}", domain=f"sms-{tenant_id}.example.com", status=tenant_status))
        db.commit()
    response = client.post("/api/integrations", json={"tenant_id": tenant_id, "name": "Twilio SMS", "provider": "twilio", "description": "Twilio SMS Integration", "status": "active"})
    if tenant_status == "active":
        assert response.status_code == 201
        return response.json()["integration_id"]
    # Create directly as active, then deactivate the tenant to exercise webhook authorization.
    with SessionLocal() as db:
        tenant = db.get(Tenant, tenant_id)
        tenant.status = "active"
        db.commit()
    response = client.post("/api/integrations", json={"tenant_id": tenant_id, "name": "Twilio SMS", "provider": "twilio", "status": "active"})
    with SessionLocal() as db:
        tenant = db.get(Tenant, tenant_id)
        tenant.status = tenant_status
        db.commit()
    return response.json()["integration_id"]


def test_twilio_form_payload_uses_required_fallback(monkeypatch):
    integration_id = _integration()
    sent = {}

    async def failed_mistral(messages):
        raise RuntimeError("provider unavailable")

    def fake_twilio(to_phone, message):
        sent.update(to=to_phone, message=message)
        return {"sid": "SM_FALLBACK", "status": "sent"}

    monkeypatch.setattr(twilio_auto_reply, "get_mistral_reply", failed_mistral)
    monkeypatch.setattr(twilio_auto_reply, "send_sms_reply", fake_twilio)
    response = client.post(f"/api/webhooks/receive/{integration_id}", data={"From": "+919999999999", "To": "+15672467340", "Body": "Hello", "MessageSid": "SM_IN_2"})
    fallback = "Sorry, we are unable to process your message right now. Please try again later."
    assert response.status_code == 200
    assert response.json()["ai_reply"] == fallback
    assert response.json()["sms_status"] == "sent"
    assert sent["message"] == fallback
def test_twilio_failure_returns_failed_status(monkeypatch):
    integration_id = _integration()

    async def fake_mistral(messages):
        return "Hello from Follei"

    def failed_twilio(to_phone, message):
        raise RuntimeError("Twilio unavailable")

    monkeypatch.setattr(twilio_auto_reply, "get_mistral_reply", fake_mistral)
    monkeypatch.setattr(twilio_auto_reply, "send_sms_reply", failed_twilio)
    response = client.post(f"/api/webhooks/receive/{integration_id}", json={"From": "+919999999998", "To": "+15672467340", "Body": "Hello"})
    assert response.status_code == 200
    assert response.json()["sms_status"] == "failed"
    assert "provider_message_id" not in response.json()


def test_webhook_lookup_tenant_and_payload_errors():
    active_id = _integration()
    inactive_id = _integration(tenant_status="inactive")
    payload = {"From": "+919999999997", "To": "+15672467340", "Body": "Hello"}
    assert client.post("/api/webhooks/receive/not-found", json=payload).status_code == 404
    assert client.post(f"/api/webhooks/receive/{inactive_id}", json=payload).status_code == 403
    assert client.post(f"/api/webhooks/receive/{active_id}", json={"From": "+919999999997", "To": "+15672467340"}).status_code == 422


def test_swagger_exposes_both_required_endpoints():
    schema = client.get("/openapi.json").json()
    assert "post" in schema["paths"]["/api/integrations"]
    assert "post" in schema["paths"]["/api/webhooks/receive/{integration_id}"]