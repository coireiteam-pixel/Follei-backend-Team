from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database.init_db import init_db
from app.routers import agents, auth, billing, chunks, commerce, conversation, documents, entities, knowledge, message, observability, tenant, user

API_PREFIX = "/api/v1"


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Follei API",
    description="Autonomous Business Operating System Core API",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(agents.router, prefix=API_PREFIX)
app.include_router(tenant.router, prefix=API_PREFIX)
app.include_router(user.router, prefix=API_PREFIX)
app.include_router(conversation.router, prefix=API_PREFIX)
app.include_router(message.router, prefix=API_PREFIX)
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
app.include_router(observability.events_router, prefix=API_PREFIX)
app.include_router(observability.analytics_router, prefix=API_PREFIX)
app.include_router(observability.retrieval_router, prefix=API_PREFIX)
app.include_router(observability.evaluation_router, prefix=API_PREFIX)
app.include_router(billing.plans_router, prefix=API_PREFIX)
app.include_router(billing.subscriptions_router, prefix=API_PREFIX)
app.include_router(billing.invoices_router, prefix=API_PREFIX)
app.include_router(billing.payments_router, prefix=API_PREFIX)
app.include_router(billing.credits_router, prefix=API_PREFIX)


@app.get("/", tags=["System"])
def root():
    return {"message": "Follei API", "docs": "/docs", "health": "/health"}


@app.get("/health", tags=["System"])
def health_check():
    return {"status": "ok", "message": "Follei backend is running."}
