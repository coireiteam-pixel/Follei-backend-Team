# Follei-Team

Backend API for the Follei autonomous business operating system.

## Requirements

- Python 3.12
- Docker Desktop for local PostgreSQL development

## Local Development With Python

The local Python setup uses PostgreSQL by default.

1. Open a terminal and go to the backend folder:

```powershell
cd C:\Users\User\Desktop\Follei15pc\Follei-backend-Team\follei_backend\follei
```

2. Start PostgreSQL:

```powershell
docker compose up -d postgres
```

3. Run the backend:

```powershell
python -m uvicorn app.main:app --reload
```

4. Open Swagger docs:

```text
http://127.0.0.1:8000/docs
```

5. Verify health:

```text
http://127.0.0.1:8000/health
```

## Local Development with Docker

1. Open a terminal and go to the backend folder:

```powershell
cd C:\Users\User\Desktop\Follei15pc\Follei-backend-Team\follei_backend\follei
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

## Current API Notes

- **JWT Authentication is fully implemented:**
  - Use `POST /api/auth/register` to create a new tenant and an admin user.
  - Use `POST /api/auth/login` to retrieve your real JWT access token.
  - Use `GET /api/auth/me` to get the authenticated user's details.
- Swagger fully supports the "Authorize" button through FastAPI's `HTTPBearer` scheme. Just click Authorize and paste your JWT access token.
- Secure endpoints (like `/api/agents`) are now successfully extracting your `tenant_id` from your token to safely isolate data.

### Notes

- Local Python uses PostgreSQL:
  `postgresql://postgres:Vignesh%40123@127.0.0.1:5432/follei_db`
- Docker backend connects to PostgreSQL using:
  `postgresql://postgres:Vignesh%40123@postgres:5432/follei_db`
- Local PostgreSQL is exposed on:
  `postgresql://postgres:Vignesh%40123@127.0.0.1:5432/follei_db`
- PostgreSQL data is stored in the `postgres-data` Docker volume.
- If you want, add more services later for Redis, Kafka, or Weaviate.

## Work History

See [docs/WORK_DONE.md](docs/WORK_DONE.md) for a summary of the backend fixes, model work, relationships, and verification done so far.
