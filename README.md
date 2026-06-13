# Follei-Team
Implement the API endpoints.

## Requirements

- Python 3.12
- Docker Desktop
- PostgreSQL is started by Docker Compose

## Local Development with Docker

1. Open a terminal and go to the backend folder:

```bash
cd /b/follei_backend/follei_backend/follei
```

2. Start the backend and database:

```bash
docker compose up --build
```

3. Verify the service is running:

```bash
curl http://localhost:8000/health
```

Expected output:

```json
{"status":"ok","message":"Follei backend is running."}
```

Open Swagger docs:

```text
http://localhost:8000/docs
```

## Local Development with Python

Start PostgreSQL first:

```bash
cd /b/follei_backend/follei_backend/follei
docker compose up -d postgres
```

Run the backend:

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Use `localhost` in the browser, not `0.0.0.0`:

```text
http://localhost:8000/docs
```

## Current API Notes

- `POST /api/v1/auth/login` returns a placeholder token:
  `{"access_token":"placeholder_token","token_type":"bearer"}`
- Swagger shows the Authorize button through FastAPI's bearer auth scheme.
- Use `Bearer placeholder_token` while real JWT auth is pending.
- `GET /api/v1/auth/me` still returns `501 Not Implemented`.
- `POST /tenants/` accepts:

```json
{
  "name": "Demo Company",
  "domain": "demo.com"
}
```

### Notes

- The backend connects to PostgreSQL using:
  `postgresql://admin:secret@postgres:5432/follei_db`
- Local Python runs connect to:
  `postgresql://admin:secret@127.0.0.1:55432/follei_db`
- PostgreSQL data is stored in the `postgres-data` Docker volume.
- If you want, add more services later for Redis, Kafka, or Weaviate.
