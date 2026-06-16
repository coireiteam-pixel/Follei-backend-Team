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

- **JWT Authentication is fully implemented:**
  - Use `POST /api/v1/auth/register` to create a new tenant and an admin user.
  - Use `POST /api/v1/auth/login` to retrieve your real JWT access token.
  - Use `GET /api/v1/auth/me` to get the authenticated user's details.
- Swagger fully supports the "Authorize" button through FastAPI's `HTTPBearer` scheme. Just click Authorize and paste your JWT access token.
- Secure endpoints (like `/api/v1/agents`) are now successfully extracting your `tenant_id` from your token to safely isolate data.

### Notes

- The backend connects to PostgreSQL using:
  `postgresql://admin:secret@postgres:5432/follei_db`
- Local Python runs connect to:
  `postgresql://admin:secret@127.0.0.1:55589/follei_db`
- PostgreSQL data is stored in the `postgres-data` Docker volume.
- If you want, add more services later for Redis, Kafka, or Weaviate.
