from fastapi import FastAPI

from app.database.init_db import init_db
from app.routers import agents, auth, conversation, database_crud, message, tenant, user

app = FastAPI(
    title="Follei API",
    description="Autonomous Business Operating System Core API",
    version="1.0.0",
)

app.include_router(auth.router)
app.include_router(agents.router)
app.include_router(tenant.router)
app.include_router(user.router)
app.include_router(conversation.router)
app.include_router(message.router)
app.include_router(database_crud.router)


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/", tags=["System"])
def root():
    return {"message": "Follei API", "docs": "/docs", "health": "/health"}


@app.get("/health", tags=["System"])
def health_check():
    return {"status": "ok", "message": "Follei backend is running."}
