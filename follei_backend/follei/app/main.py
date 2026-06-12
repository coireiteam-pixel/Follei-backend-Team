# Follei application entry point
from fastapi import FastAPI

from app.database.init_db import init_db
from app.routers import auth
from app.routers import agents

app = FastAPI(
    title="Follei API",
    description="Autonomous Business Operating System Core API",
    version="1.0.0"
)

app.include_router(auth.router)
app.include_router(agents.router)

@app.on_event("startup")
def on_startup():
    init_db()

@app.get("/health", tags=["System"])
def health_check():
    return {"status": "ok", "message": "Follei backend is running."}
