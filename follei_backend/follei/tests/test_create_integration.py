from fastapi.testclient import TestClient

from app.core.ids import short_id
from app.database.session import SessionLocal
from app.main import app
from app.models.tenancy import Tenant
from app.repositories.integration_repository import IntegrationRepository
from app.services import twilio_auto_reply

client = TestClient(app)


def _tenant(*, status: str = "active") -> str:
    tenant_id = str(short_id())
    with SessionLocal() as db:
        db.add(Tenant(id=tenant_id, name=f"Integration Tenant {tenant_id}", domain=f"integration-{tenant_id}.example.com", status=status))
        db.commit()
    return tenant_id


def _payload(tenant_id: str, *, name: str = "Twilio SMS") -> dict:
    return {"tenant_id": tenant_id, "name": name, "provider": "twilio", "description": "Twilio SMS Integration", "status": "active"}


def test_create_integration_accepts_simple_metadata_and_persists():
    tenant_id = _tenant()
    response = client.post("/api/integrations", json=_payload(tenant_id))
    assert response.status_code == 201
    assert response.json() == {"success": True, "message": "Integration created successfully", "integration_id": response.json()["integration_id"], "tenant_id": tenant_id}
    with SessionLocal() as db:
        integration = IntegrationRepository(db).get_by_id(response.json()["integration_id"])
        assert integration.tenant_id == tenant_id
        assert integration.provider == "twilio"
        assert integration.config == {}
        assert integration.ai_config == {}
def test_create_integration_validates_tenant_provider_and_duplicates():
    tenant_id = _tenant()
    inactive_id = _tenant(status="inactive")
    assert client.post("/api/integrations", json=_payload(tenant_id)).status_code == 201
    assert client.post("/api/integrations", json=_payload(tenant_id, name="twilio sms")).status_code == 409
    assert client.post("/api/integrations", json=_payload(inactive_id)).status_code == 403
    assert client.post("/api/integrations", json=_payload("NONE")).status_code == 404
    assert client.post("/api/integrations", json={**_payload(_tenant()), "provider": "mistral"}).status_code == 422
    assert client.post("/api/integrations", json={**_payload(_tenant()), "auth_token": "secret"}).status_code == 422


def test_created_integration_id_drives_json_twilio_webhook(monkeypatch):
    tenant_id = _tenant()
    integration_id = client.post("/api/integrations", json=_payload(tenant_id)).json()["integration_id"]
    captured = {}

    async def fake_mistral(messages):
        captured["messages"] = messages
        return "We provide onboarding and customer support services."

    def fake_twilio(to_phone, message):
        captured["sms"] = {"to": to_phone, "message": message}
        return {"sid": "SM_REPLY_001", "status": "sent", "to": to_phone}

    monkeypatch.setattr(twilio_auto_reply, "get_mistral_reply", fake_mistral)
    monkeypatch.setattr(twilio_auto_reply, "send_sms_reply", fake_twilio)
    response = client.post(f"/api/webhooks/receive/{integration_id}", json={"From": "+919876543210", "To": "+15672467340", "Body": "Hi, what services do you provide?", "MessageSid": "SM_TEST_001"})
    assert response.status_code == 200
    assert response.json() == {
        "received": True,
        "event_id": response.json()["event_id"],
        "customer_phone": "+919876543210",
        "tenant_phone": "+15672467340",
        "customer_message": "Hi, what services do you provide?",
        "ai_reply": "We provide onboarding and customer support services.",
        "sms_status": "sent",
        "provider_message_id": "SM_REPLY_001",
    }
    assert captured["messages"][-1]["content"] == "Hi, what services do you provide?"
    assert captured["sms"]["to"] == "+919876543210"