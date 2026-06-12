# Follei-Team
Implement the API endpoints.

## Local Development with Docker

1. Open a terminal and go to the backend folder:

```powershell
cd follei_backend\follei_backend\follei
```

2. Start the backend and database:

```powershell
docker compose up --build
```

3. Verify the service is running:

```powershell
curl http://localhost:8000/health
```

Expected output:

```json
{"status":"healthy","service":"follei-backend"}
```

### Notes

- The backend connects to PostgreSQL using:
  `postgresql://admin:secret@postgres:5432/follei_db`
- PostgreSQL data is stored in the `postgres-data` Docker volume.
- If you want, add more services later for Redis, Kafka, or Weaviate.
