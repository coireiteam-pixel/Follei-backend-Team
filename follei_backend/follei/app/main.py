from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import conversation, customers, integrations, leads, message, tools

API_PREFIX = "/api"

app = FastAPI(
    title="Follei API",
    description="APIs for Vignesh domains: conversations, messages, leads, revenue, customers, customer success, integrations, and tools.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

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


@app.get("/", tags=["System"])
def root():
    return {
        "message": "Follei API Running",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health", tags=["System"])
def health_check():
    return {
        "status": "ok",
        "message": "Follei backend is running",
    }
