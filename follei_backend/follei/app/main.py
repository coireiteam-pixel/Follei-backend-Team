from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware

from app.database.init_db import init_db
from app.routers import (
    agents,
    api_v1,
    auth,
    billing,
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
    tenant,
    tools,
    user,
)

API_PREFIX = "/api"
FAVICON_SVG = b"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="12" fill="#111827"/><path d="M18 47V17h29v8H28v6h16v8H28v8z" fill="#22c55e"/></svg>"""

app = FastAPI(
    title="Follei API",
    description="APIs for Vignesh domains: conversations, messages, leads, revenue, customers, and customer success.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(api_v1.router)
app.include_router(agents.router)
app.include_router(tenant.router)
app.include_router(user.router)
app.include_router(database_crud.router)

app.include_router(conversation.router, prefix=API_PREFIX)
app.include_router(message.router, prefix=API_PREFIX)
app.include_router(leads.router, prefix=API_PREFIX)
app.include_router(leads.frameworks_router, prefix=API_PREFIX)
app.include_router(leads.opportunities_router, prefix=API_PREFIX)
app.include_router(leads.meetings_router, prefix=API_PREFIX)
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


@app.on_event("startup")
def on_startup():
    init_db()


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
