from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)
TENANT_ID = "11111111-1111-4111-8111-111111111111"


def test_health_check():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "message": "Follei backend is running"}


def test_vignesh_p1_p2_p3_api_contract_is_registered():
    openapi = client.app.openapi()
    methods = {
        f"{method.upper()} {path}"
        for path, operations in openapi["paths"].items()
        for method in operations
        if method.lower() in {"get", "post", "patch", "delete"}
        and path.startswith("/api")
    }

    assert len(methods) == 61
    assert "POST /api/messages/{message_id}/attachments" in methods
    assert "POST /api/conversations/{conversation_id}/buying-signals" in methods
    assert "POST /api/qualification-frameworks" in methods
    assert "POST /api/opportunities/{opportunity_id}/quotes" in methods
    assert "PATCH /api/renewals/{renewal_id}" in methods
    assert "GET /api/auth/me" not in methods
    assert "GET /api/agents" not in methods


def test_conversation_message_p2_p3_flow_does_not_return_422():
    conversation_response = client.post(
        "/api/conversations",
        json={"title": "Pricing question", "type": "sales", "tenant_id": TENANT_ID, "channel": "web"},
    )
    conversation_id = conversation_response.json()["id"]
    message_response = client.post(
        f"/api/conversations/{conversation_id}/messages",
        json={"content": "The Pro plan starts at $99.", "role": "assistant", "metadata": {"rag_used": True}},
    )
    message_id = message_response.json()["id"]

    responses = [
        client.patch(f"/api/messages/{message_id}", json={"content": "Updated answer"}),
        client.post(
            f"/api/messages/{message_id}/attachments",
            json={"filename": "pricing.pdf", "url": "https://example.com/pricing.pdf"},
        ),
        client.post(f"/api/messages/{message_id}/reactions", json={"emoji": "like"}),
        client.post(f"/api/conversations/{conversation_id}/summaries", json={"max_length": 120}),
        client.post(f"/api/conversations/{conversation_id}/intents", json={"intent": "pricing_question"}),
        client.post(f"/api/conversations/{conversation_id}/sentiments", json={"sentiment": "positive"}),
        client.post(f"/api/conversations/{conversation_id}/emotions", json={"emotion": "curious"}),
        client.post(
            f"/api/conversations/{conversation_id}/objections",
            json={"objection_type": "price", "severity": "medium"},
        ),
        client.post(
            f"/api/conversations/{conversation_id}/buying-signals",
            json={"signal_type": "demo_requested", "strength": 0.9},
        ),
        client.get(f"/api/conversations/{conversation_id}/metrics"),
    ]

    assert all(response.status_code < 400 for response in responses)


def test_lead_revenue_p2_p3_flow_does_not_return_422():
    lead_response = client.post(
        "/api/leads",
        json={"email": "lead@example.com", "full_name": "Jane Lead", "tenant_id": TENANT_ID},
    )
    lead_id = lead_response.json()["id"]
    framework_response = client.post(
        "/api/qualification-frameworks",
        json={"name": "BANT", "criteria": [{"name": "budget", "weight": 25}]},
    )
    framework_id = framework_response.json()["id"]
    opportunity_response = client.post(
        "/api/opportunities",
        json={"lead_id": lead_id, "name": "Acme deal", "value": 25000, "tenant_id": TENANT_ID},
    )
    opportunity_id = opportunity_response.json()["id"]
    meeting_response = client.post(
        "/api/meetings",
        json={
            "lead_id": lead_id,
            "opportunity_id": opportunity_id,
            "title": "Demo",
            "start_time": "2026-07-01T10:00:00+00:00",
            "end_time": "2026-07-01T10:30:00+00:00",
        },
    )
    meeting_id = meeting_response.json()["id"]

    responses = [
        client.post(f"/api/leads/{lead_id}/activities", json={"type": "call"}),
        client.post(f"/api/leads/{lead_id}/scores", json={"model": "default", "force_recalculate": True}),
        client.post(
            f"/api/leads/{lead_id}/qualifications",
            json={"framework_id": framework_id, "answers": [{"question": "Budget?", "answer": "Yes"}]},
        ),
        client.patch(f"/api/opportunities/{opportunity_id}", json={"stage": "proposal", "probability": 0.7}),
        client.post(f"/api/opportunities/{opportunity_id}/proposals", json={"title": "Acme proposal"}),
        client.post(
            f"/api/opportunities/{opportunity_id}/quotes",
            json={"items": [{"name": "Pro plan", "quantity": 10, "price": 99}]},
        ),
        client.patch(f"/api/meetings/{meeting_id}", json={"status": "completed", "notes": "Good fit"}),
    ]

    assert all(response.status_code < 400 for response in responses)


def test_customer_success_p2_p3_flow_does_not_return_422():
    customer_response = client.post(
        "/api/customers",
        json={"name": "Customer Corp", "email": "admin@customer.com", "tenant_id": TENANT_ID},
    )
    customer_id = customer_response.json()["id"]
    renewal_response = client.post(
        f"/api/customers/{customer_id}/renewals",
        json={"renewal_date": "2026-12-31", "expected_value": 25000, "probability": 0.8},
    )
    renewal_id = renewal_response.json()["id"]

    responses = [
        client.post(f"/api/customers/{customer_id}/contacts", json={"name": "Priya", "email": "priya@acme.com"}),
        client.post(f"/api/customers/{customer_id}/health-scores", json={"force_recalculate": True}),
        client.post(f"/api/customers/{customer_id}/events", json={"type": "feature_used", "feature": "dashboard"}),
        client.patch(f"/api/renewals/{renewal_id}", json={"status": "closed_won", "actual_value": 26000}),
    ]

    assert all(response.status_code < 400 for response in responses)
