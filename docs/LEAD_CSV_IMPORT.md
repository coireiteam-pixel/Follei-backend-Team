# CSV to Leads API Workflow

This workflow reads a raw CSV, cleans it, generates Follei lead payloads, and
imports them into `POST http://127.0.0.1:8000/api/leads`.

It accepts normal contact CSV columns such as `email`, `phone`, `full_name`,
`company`, `job_title`, and `industry`. It also supports the generated
`dummy_import_dataset/documents.csv` by deriving contacts from document owner,
department, filename, and metadata.

## 1. Install dependencies

From the backend application directory:

```powershell
cd "B:\COIREI OFFICE\follei_backend\follei_backend\follei"
pip install -r requirements.txt
```

## 2. Start the API

```powershell
$env:DATABASE_URL="sqlite:///./follei.db"
python -m uvicorn app.main:app --reload
```

Swagger is available at `http://127.0.0.1:8000/docs`.

## 3. Run the complete workflow

Open a second PowerShell terminal:

```powershell
cd "B:\COIREI OFFICE\follei_backend"
python tools\run_lead_csv_workflow.py dummy_import_dataset\documents.csv
```

The command:

1. Reads the uploaded/input CSV.
2. Removes duplicate emails.
3. Rejects explicitly invalid emails.
4. Cleans or replaces invalid phone numbers.
5. Normalizes company names.
6. Fills missing contact fields with deterministic defaults.
7. Writes `lead_import_output/cleaned_leads.csv`.
8. Posts every lead to `/api/leads` with retries and a progress bar.
9. Writes logs and `lead_import_output/failed_records.csv`.

Bad JSON in `tags`, `custom_fields`, or `metadata` is isolated to that row and
written to `failed_records.csv`; it does not stop the remaining import.

## Generate without importing

```powershell
python tools\run_lead_csv_workflow.py dummy_import_dataset\documents.csv --no-import
```

## Run each stage separately

Generate cleaned leads:

```powershell
python tools\lead_csv_pipeline.py dummy_import_dataset\documents.csv
```

Import the generated CSV:

```powershell
python tools\bulk_import_leads.py lead_import_output\cleaned_leads.csv
```

## Custom input and endpoint

```powershell
python tools\run_lead_csv_workflow.py "C:\Users\thang\Downloads\contacts.csv" `
  --tenant-id T001 `
  --endpoint http://127.0.0.1:8000/api/leads `
  --retries 3 `
  --backoff 0.5
```

## Output files

- `cleaned_leads.csv`: validated API-ready lead records.
- `failed_records.csv`: failed payloads, HTTP status, and error message.
- `workflow.log`: success and failure details.

The workflow accepts a CSV file path as its upload input. The input can be a
raw contact CSV, the provided `documents.csv`, or the provided `leads.csv`.

The current leads router stores records in memory. Uvicorn reloads or restarts
clear imported leads.
