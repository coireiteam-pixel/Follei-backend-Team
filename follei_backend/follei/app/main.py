from fastapi import FastAPI
from app.database import engine, Base

# Create tables on startup (for dev)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Follei API")

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "follei-backend"}
