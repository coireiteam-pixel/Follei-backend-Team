from fastapi import FastAPI

app = FastAPI(title="AI Product Backend")

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "ai-product-backend"}
