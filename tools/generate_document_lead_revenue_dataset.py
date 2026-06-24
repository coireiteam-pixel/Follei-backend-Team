"""Create document, lead, and revenue dummy data from a document CSV."""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


MIME_TYPES = {
    "PDF": "application/pdf",
    "XLSX": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "DOCX": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "PPTX": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "CSV": "text/csv",
}

DEPARTMENT_PROFILES = {
    "HR": ("Human Resources", "VP People", "PeopleFirst Solutions"),
    "Sales": ("Technology", "VP Sales", "Acme Corp"),
    "Projects": ("Technology", "CTO", "Nova Projects"),
    "Legal": ("Legal Services", "General Counsel", "Lexora Legal"),
    "Marketing": ("Marketing", "CMO", "BrightWave Media"),
}

STATUSES = ["qualified", "contacted", "new", "qualified", "proposal"]
PRIORITIES = ["high", "high", "medium", "high", "medium"]
SOURCES = ["website", "referral", "event", "partner", "campaign"]
STAGES = ["qualification", "discovery", "proposal", "negotiation", "proposal"]
PROBABILITIES = [0.70, 0.55, 0.35, 0.85, 0.65]
SCORES = [85.5, 78.0, 64.5, 91.0, 82.5]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def split_name(full_name: str) -> tuple[str, str]:
    parts = full_name.strip().split()
    if not parts:
        return "lead", "contact"
    return parts[0], parts[-1]


def slug(value: str) -> str:
    return "".join(character.lower() for character in value if character.isalnum())


def parse_tags(value: str) -> list[str]:
    return [tag.strip() for tag in value.split(",") if tag.strip()]


def iso_timestamp(value: str, fallback: datetime) -> str:
    if not value:
        return fallback.isoformat().replace("+00:00", "Z")
    if value.endswith("Z"):
        return value
    return value.replace("+00:00", "Z")


def build_dataset(rows: list[dict[str, str]]) -> dict[str, list[dict[str, Any]]]:
    base_time = datetime(2026, 6, 24, 6, 57, 14, 830000, tzinfo=timezone.utc)
    documents: list[dict[str, Any]] = []
    leads: list[dict[str, Any]] = []
    revenue: list[dict[str, Any]] = []

    for index, row in enumerate(rows):
        sequence = index + 1
        tenant_id = row.get("tenant_id") or "T001"
        owner = row.get("owner") or f"Lead {sequence}"
        department = row.get("department") or "Business"
        first_name, last_name = split_name(owner)
        industry, job_title, company = DEPARTMENT_PROFILES.get(
            department,
            (department, f"Head of {department}", f"{department} Solutions"),
        )
        company_domain = f"{slug(company)}.com"
        created_at = iso_timestamp(row.get("created_at", ""), base_time)
        updated_at = iso_timestamp(
            row.get("updated_at", ""),
            base_time + timedelta(minutes=sequence),
        )
        document_id = row.get("document_id") or f"D{sequence:03d}"
        lead_id = f"L{sequence:03d}"
        opportunity_id = f"O{sequence:03d}"
        file_size_kb = int(float(row.get("file_size_kb") or 0))
        tags = parse_tags(row.get("tags", ""))

        documents.append(
            {
                "id": document_id,
                "source_id": None,
                "filename": row.get("file_name") or row.get("title") or f"document-{sequence}",
                "file_path": f"/uploads/{row.get('file_name') or f'document-{sequence}'}",
                "file_type": MIME_TYPES.get(
                    (row.get("document_type") or "").upper(),
                    "application/octet-stream",
                ),
                "file_size": file_size_kb * 1024,
                "status": row.get("status") or "pending",
                "tenant_id": tenant_id,
                "metadata": {
                    "title": row.get("title"),
                    "owner": owner,
                    "department": department,
                    "tags": tags,
                    "original_document_type": row.get("document_type"),
                },
                "created_at": created_at,
                "updated_at": updated_at,
            }
        )

        leads.append(
            {
                "email": f"{first_name.lower()}.{last_name.lower()}@{company_domain}",
                "phone": f"+1-555-{200 + sequence:04d}",
                "full_name": owner,
                "company": company,
                "job_title": job_title,
                "industry": industry,
                "website": f"https://{company_domain}",
                "source": SOURCES[index % len(SOURCES)],
                "status": STATUSES[index % len(STATUSES)],
                "priority": PRIORITIES[index % len(PRIORITIES)],
                "tags": list(dict.fromkeys(tags + [department.lower(), "dummy-lead"])),
                "custom_fields": {
                    "document_id": document_id,
                    "document_title": row.get("title"),
                    "department": department,
                },
                "score": SCORES[index % len(SCORES)],
                "assigned_to": f"U{sequence:03d}",
                "metadata": {
                    "generated_from": "document.csv",
                    "document_status": row.get("status"),
                },
                "id": lead_id,
                "tenant_id": tenant_id,
                "created_at": created_at,
                "updated_at": updated_at,
            }
        )

        value = round(10000 + (file_size_kb * 8.5) + (sequence * 2500), 2)
        probability = PROBABILITIES[index % len(PROBABILITIES)]
        revenue.append(
            {
                "id": opportunity_id,
                "lead_id": lead_id,
                "name": f"{company} - {row.get('title') or 'Business Opportunity'}",
                "value": value,
                "stage": STAGES[index % len(STAGES)],
                "probability": probability,
                "weighted_revenue": round(value * probability, 2),
                "expected_close_date": (
                    base_time.date() + timedelta(days=30 + sequence * 14)
                ).isoformat(),
                "tenant_id": tenant_id,
                "metadata": {
                    "document_id": document_id,
                    "source": "document.csv",
                    "currency": "USD",
                },
                "created_at": created_at,
                "updated_at": updated_at,
            }
        )

    return {"documents": documents, "leads": leads, "revenue": revenue}


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    key: json.dumps(value, separators=(",", ":"))
                    if isinstance(value, (dict, list))
                    else value
                    for key, value in row.items()
                }
            )


def api_payloads(dataset: dict[str, list[dict[str, Any]]]) -> dict[str, list[dict[str, Any]]]:
    document_fields = {
        "source_id",
        "filename",
        "file_path",
        "file_type",
        "file_size",
        "tenant_id",
        "metadata",
    }
    lead_fields = {
        "email",
        "phone",
        "full_name",
        "company",
        "job_title",
        "industry",
        "website",
        "source",
        "status",
        "priority",
        "tags",
        "custom_fields",
        "score",
        "assigned_to",
        "metadata",
        "tenant_id",
    }
    revenue_fields = {
        "lead_id",
        "name",
        "value",
        "stage",
        "probability",
        "expected_close_date",
        "tenant_id",
        "metadata",
    }
    return {
        "documents": [
            {key: value for key, value in row.items() if key in document_fields}
            for row in dataset["documents"]
        ],
        "leads": [
            {key: value for key, value in row.items() if key in lead_fields}
            for row in dataset["leads"]
        ],
        "revenue": [
            {key: value for key, value in row.items() if key in revenue_fields}
            for row in dataset["revenue"]
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_csv", type=Path)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("dummy_import_dataset"),
    )
    args = parser.parse_args()

    rows = read_csv(args.input_csv)
    dataset = build_dataset(rows)
    payloads = api_payloads(dataset)
    args.output.mkdir(parents=True, exist_ok=True)

    for name, records in dataset.items():
        write_csv(args.output / f"{name}.csv", records)

    (args.output / "dummy_dataset.json").write_text(
        json.dumps(dataset, indent=2),
        encoding="utf-8",
    )
    (args.output / "api_import_payloads.json").write_text(
        json.dumps(payloads, indent=2),
        encoding="utf-8",
    )
    print(
        f"Created {len(dataset['documents'])} documents, "
        f"{len(dataset['leads'])} leads, and "
        f"{len(dataset['revenue'])} revenue opportunities in {args.output.resolve()}"
    )


if __name__ == "__main__":
    main()
