from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi


from app.database.init_db import init_db
from app.routers import (
    agents,
    api_v1,
    auth,
    billing,
    campaigns,
    chunks,
    commerce,
    conversation,
    customers,
    database_crud,
    documents,
    entities,
    integrations,
    knowledge,
    leads,
    message,
    observability,
    sms,
    tenant,
    tools,
    user,
)

API_PREFIX = "/api"
FAVICON_SVG = b"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="12" fill="#111827"/><path d="M18 47V17h29v8H28v6h16v8H28v8z" fill="#22c55e"/></svg>"""
OPENAPI_TAGS = [
    {"name": "Identity & Auth"},
    {"name": "Domain 1 - Auth"},
    {"name": "Domain 2 - Tenants & Users"},
    {"name": "Domain 3 - Agents & AI Workforce"},
    {"name": "Domain 4 - System, Health & Jobs"},
    {"name": "AI Agents"},
    {"name": "tenants"},
    {"name": "users"},
    {"name": "Database CRUD"},
    {"name": "Conversations & Messages"},
    {"name": "Leads & Revenue"},
    {"name": "Campaigns"},
    {"name": "Customers & Customer Success"},
    {"name": "Integrations"},
    {"name": "Webhooks & Events"},
    {"name": "Tools, MCP & Registry"},
    {"name": "Documents"},
    {"name": "Chunks"},
    {"name": "Entities"},
    {"name": "Knowledge & RAG"},
    {"name": "Products & Pricing"},
    {"name": "Billing"},
    {"name": "Analytics & Observability"},
    {"name": "System"},
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Follei API",
    version="1.0.0",
    lifespan=lifespan,
    openapi_tags=OPENAPI_TAGS,
)
init_db()


def _remove_swagger_placeholder_props(schema_node: Any) -> None:
    if isinstance(schema_node, dict):
        for key in list(schema_node):
            if key.startswith("additionalProp"):
                schema_node.pop(key, None)

        if schema_node.get("additionalProperties") is True:
            schema_node.pop("additionalProperties", None)

        for value in schema_node.values():
            _remove_swagger_placeholder_props(value)
    elif isinstance(schema_node, list):
        for item in schema_node:
            _remove_swagger_placeholder_props(item)


def custom_openapi() -> dict[str, Any]:
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        routes=app.routes,
        tags=app.openapi_tags,
    )
    _remove_swagger_placeholder_props(openapi_schema)
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(api_v1.router)
app.include_router(agents.router)
app.include_router(tenant.router)
app.include_router(user.router)
app.include_router(database_crud.router)

app.include_router(conversation.router, prefix=API_PREFIX)
app.include_router(message.router, prefix=API_PREFIX)
app.include_router(sms.router, prefix=API_PREFIX)
app.include_router(leads.router, prefix=API_PREFIX)
app.include_router(leads.frameworks_router, prefix=API_PREFIX)
app.include_router(leads.opportunities_router, prefix=API_PREFIX)
app.include_router(leads.meetings_router, prefix=API_PREFIX)
app.include_router(campaigns.router, prefix=API_PREFIX)
app.include_router(campaigns.metrics_router, prefix=API_PREFIX)
app.include_router(campaigns.inbound_router, prefix=API_PREFIX)
app.include_router(customers.router, prefix=API_PREFIX)
app.include_router(customers.renewals_router, prefix=API_PREFIX)
app.include_router(integrations.integrations_router, prefix=API_PREFIX)
app.include_router(integrations.connections_router, prefix=API_PREFIX)
app.include_router(integrations.webhooks_receive_router, prefix=API_PREFIX)
app.include_router(integrations.webhook_events_router, prefix=API_PREFIX)
app.include_router(tools.tools_router, prefix=API_PREFIX)
app.include_router(tools.executions_router, prefix=API_PREFIX)
app.include_router(tools.logs_router, prefix=API_PREFIX)
app.include_router(documents.router, prefix=API_PREFIX)
app.include_router(chunks.router, prefix=API_PREFIX)
app.include_router(entities.router, prefix=API_PREFIX)
app.include_router(knowledge.router, prefix=API_PREFIX)
app.include_router(knowledge.faq_router, prefix=API_PREFIX)
app.include_router(knowledge.policy_router, prefix=API_PREFIX)
app.include_router(knowledge.procedure_router, prefix=API_PREFIX)
app.include_router(commerce.products_router, prefix=API_PREFIX)
app.include_router(commerce.services_router, prefix=API_PREFIX)
app.include_router(commerce.pricing_router, prefix=API_PREFIX)
app.include_router(commerce.competitors_router, prefix=API_PREFIX)
app.include_router(billing.plans_router, prefix=API_PREFIX)
app.include_router(billing.subscriptions_router, prefix=API_PREFIX)
app.include_router(billing.invoices_router, prefix=API_PREFIX)
app.include_router(billing.payments_router, prefix=API_PREFIX)
app.include_router(billing.credits_router, prefix=API_PREFIX)
app.include_router(observability.events_router, prefix=API_PREFIX)
app.include_router(observability.analytics_router, prefix=API_PREFIX)
app.include_router(observability.retrieval_router, prefix=API_PREFIX)
app.include_router(observability.evaluation_router, prefix=API_PREFIX)

@app.get("/", tags=["System"])
def root():
    return {
        "message": "Follei API Running",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return Response(content=FAVICON_SVG, media_type="image/svg+xml")


@app.get("/health", tags=["System"])
def health_check():
    return {
        "status": "ok",
        "message": "Follei backend is running",
    }
