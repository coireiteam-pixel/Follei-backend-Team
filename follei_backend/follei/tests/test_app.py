from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_check():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "message": "Follei backend is running."}


def test_api_v1_routes_are_mounted():
    assert client.get("/api/v1/auth/me").status_code == 401
    assert client.get("/api/v1/agents").status_code == 401
    assert client.get("/auth/me").status_code == 404
