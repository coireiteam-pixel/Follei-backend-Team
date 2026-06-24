"""Clean raw CSV records and convert them into Follei lead API payloads."""

from __future__ import annotations

import argparse
import csv
import json
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlparse


LOGGER = logging.getLogger("lead_csv_pipeline")

EMAIL_PATTERN = re.compile(r"^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$", re.IGNORECASE)
NON_DIGIT_PATTERN = re.compile(r"\D")
COMPANY_SUFFIXES = {
    "corp": "Corp",
    "corporation": "Corporation",
    "inc": "Inc",
    "incorporated": "Incorporated",
    "llc": "LLC",
    "ltd": "Ltd",
    "limited": "Limited",
    "co": "Co",
}

DEPARTMENT_DEFAULTS = {
    "hr": ("Human Resources", "VP People", "PeopleFirst Solutions"),
    "sales": ("Technology", "VP Sales", "Acme Corp"),
    "projects": ("Technology", "CTO", "Nova Projects"),
    "legal": ("Legal Services", "General Counsel", "Lexora Legal"),
    "marketing": ("Marketing", "CMO", "BrightWave Media"),
}

OUTPUT_FIELDS = [
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
]


@dataclass
class PipelineResult:
    leads: list[dict[str, Any]]
    input_count: int
    duplicate_count: int
    invalid_email_count: int
    repaired_phone_count: int


def first_value(row: dict[str, str], *keys: str) -> str:
    for key in keys:
        value = row.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return ""


def parse_json_value(value: str, default: Any) -> Any:
    if not value:
        return default
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return default
    return parsed


def parse_tags(value: str) -> list[str]:
    parsed = parse_json_value(value, None)
    if isinstance(parsed, list):
        tags = [str(item).strip().lower() for item in parsed if str(item).strip()]
    else:
        tags = [
            item.strip().lower()
            for item in re.split(r"[,;|]", value or "")
            if item.strip()
        ]
    return list(dict.fromkeys(tags))


def normalize_company(value: str) -> str:
    words = re.sub(r"\s+", " ", value.strip()).split()
    normalized: list[str] = []
    for word in words:
        bare_word = word.strip(".,")
        suffix = COMPANY_SUFFIXES.get(bare_word.lower())
        if suffix:
            normalized.append(suffix)
        elif any(character.isupper() for character in bare_word[1:]):
            normalized.append(bare_word)
        elif bare_word.isupper() and len(bare_word) <= 5:
            normalized.append(bare_word)
        else:
            normalized.append(bare_word.capitalize())
    return " ".join(normalized) or "Independent Business"


def normalize_name(value: str, row_number: int) -> str:
    name = re.sub(r"\s+", " ", value.strip())
    return name.title() if name else f"Business Contact {row_number:03d}"


def company_domain(company: str) -> str:
    compact = re.sub(
        r"[^a-z0-9]",
        "",
        re.sub(
            r"\b(corp|corporation|inc|incorporated|llc|ltd|limited|co)\b",
            "",
            company.lower(),
        ),
    )
    return f"{compact or 'business'}.com"


def normalize_email(value: str, full_name: str, company: str) -> str | None:
    email = value.strip().lower()
    if email and EMAIL_PATTERN.fullmatch(email):
        return email
    if email:
        return None
    name_part = re.sub(r"[^a-z0-9]+", ".", full_name.lower()).strip(".")
    return f"{name_part or 'contact'}@{company_domain(company)}"


def normalize_phone(value: str, row_number: int) -> tuple[str, bool]:
    digits = NON_DIGIT_PATTERN.sub("", value)
    if 10 <= len(digits) <= 15:
        if len(digits) == 10:
            digits = f"1{digits}"
        return f"+{digits}", False
    return f"+1555{200 + row_number:04d}", True


def normalize_website(value: str, company: str) -> str:
    website = value.strip()
    if not website:
        return f"https://{company_domain(company)}"
    markdown_link = re.fullmatch(r"\[([^\]]+)\]\([^)]+\)", website)
    if markdown_link:
        website = markdown_link.group(1).strip()
    if not website.startswith(("http://", "https://")):
        website = f"https://{website}"
    parsed = urlparse(website)
    if not parsed.netloc:
        return f"https://{company_domain(company)}"
    return website


def clamp_score(value: str, default: float = 65.0) -> float:
    try:
        score = float(value)
    except (TypeError, ValueError):
        score = default
    return round(min(100.0, max(0.0, score)), 2)


def document_metadata(row: dict[str, str]) -> dict[str, Any]:
    metadata = parse_json_value(first_value(row, "metadata"), {})
    return metadata if isinstance(metadata, dict) else {}


def row_to_lead(row: dict[str, str], row_number: int, default_tenant: str) -> dict[str, Any] | None:
    metadata = document_metadata(row)
    department = first_value(row, "department") or str(metadata.get("department") or "")
    profile = DEPARTMENT_DEFAULTS.get(department.lower())

    full_name = normalize_name(
        first_value(row, "full_name", "name", "contact_name", "owner")
        or str(metadata.get("owner") or ""),
        row_number,
    )
    company = normalize_company(
        first_value(row, "company", "company_name", "organization")
        or (profile[2] if profile else "")
    )
    email = normalize_email(first_value(row, "email", "email_address"), full_name, company)
    if email is None:
        return None

    phone, repaired_phone = normalize_phone(
        first_value(row, "phone", "phone_number", "mobile"),
        row_number,
    )
    tags = parse_tags(first_value(row, "tags"))
    metadata_tags = metadata.get("tags")
    if isinstance(metadata_tags, list):
        tags.extend(str(tag).strip().lower() for tag in metadata_tags if str(tag).strip())
    if department:
        tags.append(department.lower())
    tags = list(dict.fromkeys(tags or ["csv-import"]))

    raw_custom_fields = parse_json_value(first_value(row, "custom_fields"), {})
    custom_fields = raw_custom_fields if isinstance(raw_custom_fields, dict) else {}
    document_id = first_value(row, "document_id", "id")
    filename = first_value(row, "filename", "file_name")
    if document_id:
        custom_fields.setdefault("document_id", document_id)
    if filename:
        custom_fields.setdefault("source_filename", filename)

    source = first_value(row, "source") or "csv_upload"
    status = first_value(row, "status")
    if status not in {"new", "contacted", "qualified", "proposal", "converted", "lost"}:
        status = "new"
    priority = first_value(row, "priority").lower()
    if priority not in {"low", "medium", "high"}:
        priority = "high" if clamp_score(first_value(row, "score")) >= 80 else "medium"

    metadata.update(
        {
            "import_source": "csv",
            "source_row": row_number,
            "phone_repaired": repaired_phone,
        }
    )

    return {
        "email": email,
        "phone": phone,
        "full_name": full_name,
        "company": company,
        "job_title": first_value(row, "job_title", "title")
        or (profile[1] if profile else "Business Decision Maker"),
        "industry": first_value(row, "industry")
        or (profile[0] if profile else department or "Business Services"),
        "website": normalize_website(first_value(row, "website", "company_website"), company),
        "source": source,
        "status": status,
        "priority": priority,
        "tags": tags,
        "custom_fields": custom_fields,
        "score": clamp_score(first_value(row, "score")),
        "assigned_to": first_value(row, "assigned_to")
        or f"U{((row_number - 2) % 5) + 1:03d}",
        "metadata": metadata,
        "tenant_id": first_value(row, "tenant_id") or default_tenant,
    }


def transform_rows(rows: Iterable[dict[str, str]], default_tenant: str = "T001") -> PipelineResult:
    leads: list[dict[str, Any]] = []
    seen_emails: set[str] = set()
    input_count = 0
    duplicates = 0
    invalid_emails = 0
    repaired_phones = 0

    for row_number, row in enumerate(rows, start=2):
        input_count += 1
        lead = row_to_lead(row, row_number, default_tenant)
        if lead is None:
            invalid_emails += 1
            continue
        if lead["email"] in seen_emails:
            duplicates += 1
            continue
        seen_emails.add(lead["email"])
        repaired_phones += int(bool(lead["metadata"]["phone_repaired"]))
        leads.append(lead)

    return PipelineResult(leads, input_count, duplicates, invalid_emails, repaired_phones)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError(f"CSV file has no header row: {path}")
        rows = []
        for row in reader:
            if None in row:
                raise ValueError(
                    f"CSV row {reader.line_num} has more values than the header defines"
                )
            if any(str(value or "").strip() for value in row.values()):
                rows.append(row)
        return rows


def write_leads_csv(path: Path, leads: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        for lead in leads:
            writer.writerow(
                {
                    key: json.dumps(value, separators=(",", ":"))
                    if isinstance(value, (dict, list))
                    else value
                    for key, value in lead.items()
                }
            )


def configure_logging(log_path: Path) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[
            logging.FileHandler(log_path, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_csv", type=Path)
    parser.add_argument("--output", type=Path, default=Path("lead_import_output/cleaned_leads.csv"))
    parser.add_argument("--tenant-id", default="T001")
    parser.add_argument("--log", type=Path, default=Path("lead_import_output/pipeline.log"))
    args = parser.parse_args()

    configure_logging(args.log)
    result = transform_rows(read_csv(args.input_csv), args.tenant_id)
    write_leads_csv(args.output, result.leads)
    LOGGER.info("Generated %s cleaned lead records at %s", len(result.leads), args.output.resolve())
    LOGGER.info(
        "Removed duplicates=%s invalid_emails=%s repaired_phones=%s",
        result.duplicate_count,
        result.invalid_email_count,
        result.repaired_phone_count,
    )


if __name__ == "__main__":
    main()
