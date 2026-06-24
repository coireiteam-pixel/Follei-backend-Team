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

3. Set the local database URL when you want Python to connect to the Docker PostgreSQL container:

```powershell
$env:DATABASE_URL="postgresql://admin:secret@127.0.0.1:55589/follei_db"
```

If `DATABASE_URL` is not set, the app uses the local Docker PostgreSQL URL:
`postgresql://admin:secret@127.0.0.1:55589/follei_db`.

4. Run the backend:

```powershell
python -m uvicorn app.main:app --reload
```

5. Open Swagger docs:

```text
http://127.0.0.1:8000/docs
```

6. Verify health:

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

## Campaign Email Sending

`POST /api/campaigns/{campaign_id}/send` sends a campaign to the email addresses on the campaign's attached leads.

By default, local development uses a mock sender so Swagger tests can run without email credentials.

Configure Brevo environment variables to send real email with `provider: "brevo"`:

```powershell
$env:BREVO_API_KEY="your-brevo-api-key"
$env:BREVO_FROM_EMAIL="verified-sender@example.com"
$env:BREVO_FROM_NAME="Follei"
```

Alternatively, configure SMTP environment variables:

```powershell
$env:SMTP_HOST="smtp.example.com"
$env:SMTP_PORT="587"
$env:SMTP_USER="your-smtp-user"
$env:SMTP_PASSWORD="your-smtp-password"
$env:SMTP_FROM="noreply@example.com"
$env:SMTP_TLS="true"
```

Without Brevo or SMTP credentials, the API returns successful mock message IDs but does not deliver to inboxes.

### Brevo Inbound Email Webhook

Configure Brevo to POST inbound or reply events to:

```text
https://your-api-host.example.com/api/email/inbound/brevo
```

For local Swagger testing:

```text
http://127.0.0.1:8000/api/email/inbound/brevo
```

The webhook stores inbound messages with `tenant_id`, `campaign_id`, and `lead_id` when those values can be resolved. You can pass them as query parameters in the webhook URL when needed:

```text
/api/email/inbound/brevo?tenant_id=T001&campaign_id=C001&lead_id=L001
```

Received messages can be listed with:

```text
GET /api/email/inbound?tenant_id=T001
```

### Notes

- Local Python uses Docker PostgreSQL by default:
  `postgresql://admin:secret@127.0.0.1:55589/follei_db`
- Docker backend connects to PostgreSQL using:
  `postgresql://admin:secret@postgres:5432/follei_db`
- Local PostgreSQL is exposed on:
  `postgresql://admin:secret@127.0.0.1:55589/follei_db`
- PostgreSQL data is stored in the `postgres-data` Docker volume.
- If you want, add more services later for Redis, Kafka, or Weaviate.

## Imported CUDA Engineer Dataset

The Hugging Face dataset `SakanaAI/AI-CUDA-Engineer-Archive` is saved locally at:

```text
follei_backend/follei/data/ai_cuda_engineer_archive
```

Load it with:

```python
from datasets import load_from_disk

dataset = load_from_disk("data/ai_cuda_engineer_archive")
```

Available splits:

- `level_1`: 12,157 rows
- `level_2`: 12,938 rows
- `level_3`: 5,520 rows

## Realtime Demo Dataset Generator

Generate live demo data into the configured database:

```powershell
cd follei_backend\follei
python generate_realtime_data.py
```

Useful test commands:

```powershell
python generate_realtime_data.py --once
python generate_realtime_data.py --iterations 10 --interval 1
```

The generator creates seed tenants, users, agents, leads, and customers when needed, then keeps adding conversations, messages, events, analytics, model usage, agent tasks, actions, and tool calls.

## Work History

See [docs/WORK_DONE.md](docs/WORK_DONE.md) for a summary of the backend fixes, model work, relationships, and verification done so far.
