from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import app.models
from app.crm_integrations.config import settings
from app.crm_integrations.database import Base, engine
from app.crm_integrations.routers import auth, crm, crm_auth, crm_sync, crm_webhooks


OPENAPI_TAGS = [
    {"name": "01 Authentication", "description": "Get the bearer token used by Swagger Authorize."},
    {"name": "02 System", "description": "Root and health endpoints."},
    {"name": "CRM", "description": "CRM providers, connections, OAuth, sync, and webhooks."},
]


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version="1.0.0",
        description="Backend API for connecting and syncing multiple CRM providers.",
        openapi_tags=OPENAPI_TAGS,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth.router)
    app.include_router(crm_auth.router)
    app.include_router(crm.router)
    app.include_router(crm_auth.alias_router)
    app.include_router(crm_sync.router)
    app.include_router(crm_webhooks.router)

    @app.get("/", tags=["02 System"], summary="API overview")
    def root():
        return {"message": "API is running"}

    @app.get("/health", tags=["02 System"], summary="Health check")
    def health_check():
        return {"status": "healthy", "service": settings.app_name}

    return app


Base.metadata.create_all(bind=engine)
app = create_app()
