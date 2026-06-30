"""Bulk import cleaned lead CSV rows into the Follei Leads API."""

from __future__ import annotations

import argparse
import csv
import json
import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

try:
    from tqdm import tqdm
except ImportError:  # Keep the importer usable without the optional progress UI.
    def tqdm(iterable, **_kwargs):
        return iterable


LOGGER = logging.getLogger("bulk_import_leads")
JSON_FIELDS = {"tags", "custom_fields", "metadata"}
PAYLOAD_FIELDS = {
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


@dataclass
class PayloadReadResult:
    payloads: list[tuple[int, dict[str, Any]]]
    failures: list[dict[str, Any]]


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


def build_session(retries: int, backoff: float) -> requests.Session:
    retry = Retry(
        total=retries,
        connect=retries,
        read=retries,
        status=retries,
        backoff_factor=backoff,
        status_forcelist=(408, 429, 500, 502, 503, 504),
        allowed_methods=frozenset({"POST"}),
        raise_on_status=False,
    )
    session = requests.Session()
    session.mount("http://", HTTPAdapter(max_retries=retry))
    session.mount("https://", HTTPAdapter(max_retries=retry))
    return session


def parse_row(row: dict[str, str]) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    for key in PAYLOAD_FIELDS:
        value = (row.get(key) or "").strip()
        if key in JSON_FIELDS:
            default = [] if key == "tags" else {}
            parsed = json.loads(value) if value else default
            expected_type = list if key == "tags" else dict
            if not isinstance(parsed, expected_type):
                raise ValueError(f"{key} must contain JSON {expected_type.__name__} data")
            payload[key] = parsed
        elif key == "score":
            payload[key] = float(value) if value else None
        elif key == "assigned_to":
            payload[key] = value or None
        else:
            payload[key] = value or None
    return payload


def read_payloads(path: Path) -> PayloadReadResult:
    payloads: list[tuple[int, dict[str, Any]]] = []
    failures: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError(f"CSV file has no header row: {path}")
        missing_fields = PAYLOAD_FIELDS.difference(reader.fieldnames)
        if missing_fields:
            raise ValueError(
                "Generated lead CSV is missing required columns: "
                + ", ".join(sorted(missing_fields))
            )
        for row_number, row in enumerate(reader, start=2):
            try:
                payloads.append((row_number, parse_row(row)))
            except (TypeError, ValueError, json.JSONDecodeError) as exc:
                failures.append(
                    {
                        "row_number": row_number,
                        "payload": row,
                        "status_code": "",
                        "error": f"CSV payload parsing failed: {exc}",
                    }
                )
                LOGGER.error("row=%s payload parsing failed error=%s", row_number, exc)
    return PayloadReadResult(payloads, failures)


def write_failed_records(path: Path, failures: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["row_number", "error", "status_code", *sorted(PAYLOAD_FIELDS)]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for failure in failures:
            payload = failure["payload"]
            writer.writerow(
                {
                    "row_number": failure["row_number"],
                    "error": failure["error"],
                    "status_code": failure.get("status_code", ""),
                    **{
                        key: json.dumps(payload.get(key), separators=(",", ":"))
                        if isinstance(payload.get(key), (dict, list))
                        else payload.get(key)
                        for key in sorted(PAYLOAD_FIELDS)
                    },
                }
            )


def import_payloads(
    payloads: list[tuple[int, dict[str, Any]]],
    endpoint: str,
    retries: int,
    backoff: float,
    timeout: float,
    delay: float,
) -> tuple[int, list[dict[str, Any]]]:
    session = build_session(retries, backoff)
    successes = 0
    failures: list[dict[str, Any]] = []

    try:
        for row_number, payload in tqdm(payloads, desc="Importing leads", unit="lead"):
            try:
                response = session.post(endpoint, json=payload, timeout=timeout)
                if 200 <= response.status_code < 300:
                    successes += 1
                    try:
                        response_data = response.json()
                    except ValueError:
                        response_data = {}
                    created_id = response_data.get("id", "unknown")
                    LOGGER.info(
                        "row=%s success id=%s email=%s",
                        row_number,
                        created_id,
                        payload.get("email"),
                    )
                else:
                    error = response.text[:1000]
                    failures.append(
                        {
                            "row_number": row_number,
                            "payload": payload,
                            "status_code": response.status_code,
                            "error": error,
                        }
                    )
                    LOGGER.error(
                        "row=%s failed status=%s error=%s",
                        row_number,
                        response.status_code,
                        error,
                    )
            except requests.RequestException as exc:
                failures.append(
                    {
                        "row_number": row_number,
                        "payload": payload,
                        "status_code": "",
                        "error": str(exc),
                    }
                )
                LOGGER.exception("row=%s request failed", row_number)
            if delay:
                time.sleep(delay)
    finally:
        session.close()

    return successes, failures


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("leads_csv", type=Path)
    parser.add_argument("--endpoint", default="http://127.0.0.1:8000/api/leads")
    parser.add_argument("--retries", type=int, default=3)
    parser.add_argument("--backoff", type=float, default=0.5)
    parser.add_argument("--timeout", type=float, default=15)
    parser.add_argument("--delay", type=float, default=0)
    parser.add_argument("--failed-output", type=Path, default=Path("lead_import_output/failed_records.csv"))
    parser.add_argument("--log", type=Path, default=Path("lead_import_output/import.log"))
    args = parser.parse_args()

    configure_logging(args.log)
    read_result = read_payloads(args.leads_csv)
    successes, failures = import_payloads(
        read_result.payloads,
        args.endpoint,
        args.retries,
        args.backoff,
        args.timeout,
        args.delay,
    )
    failures = [*read_result.failures, *failures]
    write_failed_records(args.failed_output, failures)
    LOGGER.info(
        "Import complete total=%s success=%s failed=%s failed_file=%s",
        len(read_result.payloads) + len(read_result.failures),
        successes,
        len(failures),
        args.failed_output.resolve(),
    )
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
