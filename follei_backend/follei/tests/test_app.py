import json
import re

import pytest
from fastapi.testclient import TestClient

from app.core.ids import short_id
from app.main import app
from app.routers import documents, leads, sms


client = TestClient(app)
TENANT_ID = "T001"


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

    assert len(methods) == 230
    assert "POST /api/messages/{message_id}/attachments" in methods
    assert "POST /api/conversations/{conversation_id}/buying-signals" in methods
    assert "POST /api/qualification-frameworks" in methods
    assert "POST /api/opportunities/{opportunity_id}/quotes" in methods
    assert "POST /api/leads/import-csv" in methods
    assert "POST /api/opportunities/import-csv" in methods
    assert "PATCH /api/renewals/{renewal_id}" in methods
    assert "GET /api/integrations" in methods
    assert "POST /api/integration-connections/{connection_id}/sync" in methods
    assert "POST /api/webhooks/receive/{integration_id}" in methods
    assert "POST /api/tools/{tool_id}/execute" in methods
    assert "GET /api/connector-logs" in methods
    assert "POST /api/auth/register" in methods
    assert "POST /api/auth/login" in methods
    assert "GET /api/auth/me" in methods
    assert "POST /api/sms/mistral-send" in methods
    assert "POST /api/v1/auth/register" in methods
    assert "POST /api/leads/{lead_id}/reply" in methods
    assert "GET /api/leads/{lead_id}/messages" in methods
    assert "GET /api/documents" in methods
    assert "POST /api/documents/upload" in methods
    assert "POST /api/knowledge/search" in methods
    assert "GET /api/products" in methods
    assert "GET /api/plans" in methods
    assert "GET /api/events" in methods
    assert "GET /api/campaigns" in methods
    assert "POST /api/campaigns/{campaign_id}/send" in methods
    assert "POST /api/v1/email/gmail-auto-reply/poll" in methods
    assert "GET /api/agents" not in methods


def test_all_reference_router_groups_are_visible_in_swagger():
    openapi_paths = client.app.openapi()["paths"]

    assert "/api/v1/health" in openapi_paths
    assert "/agents" in openapi_paths
    assert "/database/tables" in openapi_paths
    assert "/tenants/" in openapi_paths
    assert "/users/{user_id}" in openapi_paths
    assert "/api/chunks/{chunk_id}/embeddings" in openapi_paths
    assert "/api/campaigns" in openapi_paths
    assert "/api/v1/email/gmail-auto-reply/status" in openapi_paths


def test_openapi_schema_does_not_expose_swagger_placeholder_props():
    openapi = client.app.openapi()
    openapi_json = json.dumps(openapi)

    assert "additionalProp" not in openapi_json
    assert '"additionalProperties": true' not in openapi_json


def test_swagger_groups_follow_reference_order():
    assert [tag["name"] for tag in client.app.openapi()["tags"]] == [
        "Identity & Auth",
        "Domain 1 - Auth",
        "Domain 2 - Tenants & Users",
        "Domain 3 - Agents & AI Workforce",
        "Domain 4 - System, Health & Jobs",
        "AI Agents",
        "tenants",
        "users",
        "Database CRUD",
        "Conversations & Messages",
        "Leads & Revenue",
        "Campaigns",
        "AI Email Assistant",
        "Customers & Customer Success",
        "Integrations",
        "Webhooks & Events",
        "Tools, MCP & Registry",
        "Documents",
        "Chunks",
        "Entities",
        "Knowledge & RAG",
        "Products & Pricing",
        "Billing",
        "Analytics & Observability",
        "System",
    ]


@pytest.mark.parametrize(
    ("filename", "content", "content_type", "upload_type"),
    [
        ("pricing.pdf", b"sample pdf bytes", "application/pdf", "document"),
        ("leads.csv", b"name,email\nJane,jane@example.com\n", "text/csv", "csv"),
        (
            "pipeline.xlsx",
            b"fake xlsx bytes for upload smoke test",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "excel",
        ),
        (
            "proposal.docx",
            b"fake docx bytes for upload smoke test",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "document",
        ),
    ],
)
def test_document_upload_accepts_supported_file_types(tmp_path, filename, content, content_type, upload_type):
    suffix = short_id()
    register_response = client.post(
        "/api/auth/register",
        json={
            "name": f"Upload Tenant {suffix}",
            "domain": f"upload-{suffix}.example.com",
            "admin_email": f"upload-{suffix}@example.com",
            "admin_password": "password123",
            "admin_first_name": "Upload",
            "admin_last_name": "User",
        },
    )
    token = register_response.json()["access_token"]
    documents.UPLOAD_ROOT = tmp_path

    response = client.post(
        "/api/documents/upload",
        headers={"Authorization": f"Bearer {token}"},
        data={"metadata": '{"tags":["pricing"]}'},
        files={"file": (filename, content, content_type)},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["filename"] == filename
    assert body["file_type"] == content_type
    assert body["status"] == "uploaded"

    detail_response = client.get(f"/api/documents/{body['id']}", headers={"Authorization": f"Bearer {token}"})
    assert detail_response.status_code == 200
    assert detail_response.json()["metadata"]["upload_type"] == upload_type


def test_document_upload_rejects_unsupported_file_type(tmp_path):
    suffix = short_id()
    register_response = client.post(
        "/api/auth/register",
        json={
            "name": f"Upload Reject Tenant {suffix}",
            "domain": f"upload-reject-{suffix}.example.com",
            "admin_email": f"upload-reject-{suffix}@example.com",
            "admin_password": "password123",
            "admin_first_name": "Upload",
            "admin_last_name": "User",
        },
    )
    token = register_response.json()["access_token"]
    documents.UPLOAD_ROOT = tmp_path

    response = client.post(
        "/api/documents/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("script.exe", b"not allowed", "application/octet-stream")},
    )

    assert response.status_code == 415


def test_auth_register_creates_short_alphanumeric_ids():
    suffix = short_id()
    response = client.post(
        "/api/auth/register",
        json={
            "name": f"Short ID Tenant {suffix}",
            "domain": f"short-{suffix}.example.com",
            "admin_email": f"short-{suffix}@example.com",
            "admin_password": "password123",
            "admin_first_name": "Short",
            "admin_last_name": "User",
        },
    )
    assert response.status_code == 201

    token = response.json()["access_token"]
    profile_response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    profile = profile_response.json()

    assert profile_response.status_code == 200
    assert re.fullmatch(r"[A-Z][0-9]{3}", profile["id"])
    assert re.fullmatch(r"[A-Z][0-9]{3}", profile["tenant_id"])


def test_api_auth_register_login_and_me_return_user_and_tenant():
    suffix = short_id()
    register_response = client.post(
        "/api/auth/register",
        json={
            "tenant_name": f"API Auth Tenant {suffix}",
            "domain": f"api-auth-{suffix}",
            "admin_email": f"api-auth-{suffix}@example.com",
            "admin_password": "Admin@123",
            "admin_first_name": "API",
            "admin_last_name": "Admin",
        },
    )

    assert register_response.status_code == 201
    register_body = register_response.json()
    assert register_body["access_token"]
    assert register_body["token_type"] == "bearer"
    assert register_body["user"]["email"] == f"api-auth-{suffix}@example.com"
    assert register_body["user"]["role"] == "admin"
    assert register_body["tenant"]["domain"] == f"api-auth-{suffix}"

    login_response = client.post(
        "/api/auth/login",
        json={"email": f"api-auth-{suffix}@example.com", "password": "Admin@123"},
    )

    assert login_response.status_code == 200
    login_body = login_response.json()
    assert login_body["access_token"]
    assert login_body["user"]["tenant_id"] == register_body["tenant"]["id"]
    assert login_body["tenant"]["name"] == f"API Auth Tenant {suffix}"

    me_response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {login_body['access_token']}"},
    )

    assert me_response.status_code == 200
    me_body = me_response.json()
    assert me_body["email"] == f"api-auth-{suffix}@example.com"
    assert me_body["tenant"]["id"] == register_body["tenant"]["id"]


def test_tenant_create_creates_admin_user_and_user_create_works():
    suffix = short_id()
    tenant_response = client.post(
        "/tenants/",
        json={
            "name": f"Tenant CRUD {suffix}",
            "domain": f"tenant-crud-{suffix}.example.com",
            "admin_email": f"tenant-admin-{suffix}@example.com",
            "admin_password": "password123",
            "admin_first_name": "Tenant",
            "admin_last_name": "Admin",
        },
    )

    assert tenant_response.status_code == 200
    tenant_id = tenant_response.json()["id"]

    login_response = client.post(
        "/api/auth/login",
        json={"email": f"tenant-admin-{suffix}@example.com", "password": "password123"},
    )
    assert login_response.status_code == 200
    assert login_response.json()["access_token"]

    user_response = client.post(
        "/users/",
        json={
            "tenant_id": tenant_id,
            "email": f"tenant-user-{suffix}@example.com",
            "password": "password123",
            "first_name": "Tenant",
            "last_name": "User",
            "role": "member",
            "is_active": True,
        },
    )

    assert user_response.status_code == 200
    body = user_response.json()
    assert body["tenant_id"] == tenant_id
    assert body["email"] == f"tenant-user-{suffix}@example.com"


def test_lead_reply_uses_mistral_and_persists_history(monkeypatch):
    captured_messages = []

    async def fake_mistral_reply(messages: list[dict]) -> str:
        captured_messages.extend(messages)
        return "Thanks for your interest. I can help you choose the right plan."

    monkeypatch.setattr(leads, "get_mistral_reply", fake_mistral_reply)

    lead_response = client.post(
        "/api/leads",
        json={
            "email": "reply-lead@example.com",
            "full_name": "Reply Lead",
            "company": "Acme",
            "phone": "+15551234567",
            "source": "website",
            "tenant_id": TENANT_ID,
            "priority": "high",
        },
    )
    lead_id = lead_response.json()["id"]

    reply_response = client.post(
        f"/api/leads/{lead_id}/reply",
        json={"message": "Hi, I am interested in your product"},
    )

    assert reply_response.status_code == 200
    body = reply_response.json()
    assert body["lead_id"] == lead_id
    assert body["user_message"] == "Hi, I am interested in your product"
    assert body["ai_response"] == "Thanks for your interest. I can help you choose the right plan."
    assert [item["role"] for item in body["history"]] == ["user", "assistant"]
    assert "Reply Lead" in captured_messages[1]["content"]
    assert captured_messages[-1]["content"] == "Hi, I am interested in your product"

    messages_response = client.get(f"/api/leads/{lead_id}/messages")
    assert messages_response.status_code == 200
    assert len(messages_response.json()["messages"]) == 2


def test_create_lead_without_tenant_id_does_not_return_422():
    response = client.post(
        "/api/leads",
        json={
            "email": "no-tenant-lead@example.com",
            "full_name": "No Tenant Lead",
            "phone": "+15550000000",
            "source": "website",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["tenant_id"] == "T001"
    assert body["email"] == "no-tenant-lead@example.com"


def test_sms_mistral_send_uses_tenant_phone(monkeypatch):
    suffix = short_id()
    tenant_response = client.post(
        "/tenants/",
        json={
            "name": f"SMS Tenant {suffix}",
            "domain": f"sms-tenant-{suffix}.example.com",
            "phone": "+15551230000",
            "admin_email": f"sms-tenant-{suffix}@example.com",
            "admin_password": "password123",
            "admin_first_name": "Sms",
            "admin_last_name": "Admin",
        },
    )
    tenant_id = tenant_response.json()["id"]
    sent = {}

    async def fake_mistral_reply(messages: list[dict]) -> str:
        assert messages[-1]["content"] == "Hi"
        return "Hello from Mistral"

    def fake_send_sms(to_phone: str, message: str) -> dict:
        sent["to_phone"] = to_phone
        sent["message"] = message
        return {"sid": "SM123", "status": "queued"}

    monkeypatch.setattr(sms, "get_mistral_reply", fake_mistral_reply)
    monkeypatch.setattr(sms, "send_sms", fake_send_sms)

    response = client.post(
        "/api/sms/mistral-send",
        json={"tenant_id": tenant_id, "message": "Hi"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["tenant_id"] == tenant_id
    assert body["tenant_phone"] == "+15551230000"
    assert body["user_message"] == "Hi"
    assert body["mistral_reply"] == "Hello from Mistral"
    assert body["sms_status"] == "queued"
    assert body["sms_sid"] == "SM123"
    assert sent == {"to_phone": "+15551230000", "message": "Hello from Mistral"}


def test_sms_mistral_send_requires_existing_tenant_and_phone(monkeypatch):
    missing_response = client.post(
        "/api/sms/mistral-send",
        json={"tenant_id": "NOPE", "message": "Hi"},
    )
    assert missing_response.status_code == 404

    suffix = short_id()
    tenant_response = client.post(
        "/tenants/",
        json={
            "name": f"No Phone Tenant {suffix}",
            "domain": f"no-phone-{suffix}.example.com",
            "admin_email": f"no-phone-{suffix}@example.com",
            "admin_password": "password123",
            "admin_first_name": "No",
            "admin_last_name": "Phone",
        },
    )
    tenant_id = tenant_response.json()["id"]

    async def fail_mistral_reply(messages: list[dict]) -> str:
        raise AssertionError("Mistral should not be called when phone is missing")

    monkeypatch.setattr(sms, "get_mistral_reply", fail_mistral_reply)
    phone_response = client.post(
        "/api/sms/mistral-send",
        json={"tenant_id": tenant_id, "message": "Hi"},
    )
    assert phone_response.status_code == 400


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


def test_integrations_webhooks_and_tools_flow_does_not_return_422():
    integrations_response = client.get("/api/integrations")
    assert integrations_response.status_code == 200
    integration_id = integrations_response.json()["items"][0]["id"]

    connection_response = client.post(
        "/api/integration-connections",
        json={
            "integration_id": integration_id,
            "tenant_id": TENANT_ID,
            "auth_type": "oauth2",
            "credentials": {"access_token": "oauth_token"},
            "settings": {"sync_frequency": "hourly"},
        },
    )
    assert connection_response.status_code == 201
    connection_id = connection_response.json()["id"]

    tool_response = client.post(
        "/api/tools",
        json={
            "name": "crm_search_contacts",
            "display_name": "Search Contacts",
            "category": "crm",
            "tenant_id": TENANT_ID,
            "input_schema": {"type": "object"},
            "output_schema": {"type": "object"},
            "auth_required": True,
            "rate_limit": {"requests_per_minute": 60},
        },
    )
    assert tool_response.status_code == 201
    tool_id = tool_response.json()["id"]

    responses = [
        client.patch(f"/api/integration-connections/{connection_id}", json={"settings": {"sync_frequency": "daily"}}),
        client.post(f"/api/integration-connections/{connection_id}/sync", json={"sync_type": "full", "entities": ["contacts"]}),
        client.post(
            f"/api/integration-connections/{connection_id}/webhooks",
            json={"event_type": "lead.created", "url": "https://api.follei.com/webhooks/salesforce"},
        ),
        client.post(
            f"/api/webhooks/receive/{integration_id}",
            json={"event_type": "lead.created", "payload": {"email": "lead@company.com"}},
        ),
        client.post(
            f"/api/tools/{tool_id}/execute",
            json={"agent_id": "A001", "parameters": {"query": "Acme Corp"}},
        ),
        client.post(
            f"/api/tools/{tool_id}/permissions",
            json={"agent_id": "A001", "permission": "execute"},
        ),
        client.get("/api/tool-executions"),
        client.get("/api/connector-logs"),
    ]

    assert all(response.status_code < 400 for response in responses)


def test_lead_and_revenue_csv_uploads_are_returned_by_get_endpoints():
    leads_csv = (
        "id,email,full_name,company,status,priority,tags,custom_fields,score,metadata,tenant_id\n"
        'L901,csv@example.com,CSV Lead,CSV Corp,qualified,high,"[""csv""]","{}",88.5,"{}",T001\n'
    )
    lead_import = client.post(
        "/api/leads/import-csv",
        files={"file": ("leads.csv", leads_csv, "text/csv")},
        data={"default_tenant_id": TENANT_ID},
    )
    assert lead_import.status_code == 200
    assert lead_import.json()["imported"] == 1
    assert client.get("/api/leads/L901").json()["email"] == "csv@example.com"

    revenue_csv = (
        "id,lead_id,name,value,stage,probability,expected_close_date,tenant_id,metadata\n"
        'O901,L901,CSV annual deal,10000,proposal,0.75,2026-12-31,T001,"{}"\n'
    )
    revenue_import = client.post(
        "/api/opportunities/import-csv",
        files={"file": ("revenue.csv", revenue_csv, "text/csv")},
        data={"default_tenant_id": TENANT_ID},
    )
    assert revenue_import.status_code == 200
    assert revenue_import.json()["imported"] == 1

    opportunity = client.get("/api/opportunities/O901").json()
    assert opportunity["lead_id"] == "L901"
    assert opportunity["weighted_revenue"] == 7500


def test_lead_csv_import_accepts_different_column_alignments_and_aliases():
    suffix = short_id().lower()
    email = f"alias-{suffix}@example.com"
    first_csv = (
        "Contact Name,Mobile No,Company Name,Email Address,Designation,Website,Lead Score,Labels,Notes\n"
        f'Alias Lead,5551234567,Alias Corp,{email},Director,alias.example.com,91,"sales;hot","Imported from vendor A"\n'
    )

    first_import = client.post(
        "/api/leads/import-csv",
        files={"file": ("vendor-a.csv", first_csv, "text/csv")},
        data={"default_tenant_id": TENANT_ID},
    )

    assert first_import.status_code == 200
    assert first_import.json()["imported"] == 1

    list_response = client.get("/api/leads", params={"tenant_id": TENANT_ID, "source": "csv_upload", "page_size": 100})
    matching_leads = [lead for lead in list_response.json()["items"] if lead["email"] == email]
    assert len(matching_leads) == 1
    lead_id = matching_leads[0]["id"]

    imported_lead = client.get(f"/api/leads/{lead_id}").json()
    assert imported_lead["full_name"] == "Alias Lead"
    assert imported_lead["phone"] == "+15551234567"
    assert imported_lead["company"] == "Alias Corp"
    assert imported_lead["job_title"] == "Director"
    assert imported_lead["website"] == "https://alias.example.com"
    assert imported_lead["score"] == 91
    assert imported_lead["priority"] == "high"
    assert imported_lead["tags"] == ["sales", "hot"]

    second_csv = (
        "Status,Email Address,Custom Column\n"
        f"qualified,{email},Keep this extra value\n"
    )
    second_import = client.post(
        "/api/leads/import-csv",
        files={"file": ("vendor-b.csv", second_csv, "text/csv")},
        data={"default_tenant_id": TENANT_ID},
    )

    assert second_import.status_code == 200
    assert second_import.json()["updated"] == 1

    updated_lead = client.get(f"/api/leads/{lead_id}").json()
    assert updated_lead["status"] == "qualified"
    assert updated_lead["phone"] == "+15551234567"
    assert updated_lead["company"] == "Alias Corp"
    assert updated_lead["metadata"]["source_columns"]["Custom Column"] == "Keep this extra value"
