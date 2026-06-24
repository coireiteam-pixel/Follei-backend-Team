import csv
import json
import sys
from pathlib import Path
from unittest.mock import Mock, patch

import requests


sys.path.insert(0, str((Path(__file__).resolve().parents[1] / "tools").resolve()))

from bulk_import_leads import import_payloads, read_payloads, write_failed_records  # noqa: E402


def _write_generated_csv(path: Path, rows: list[dict[str, object]]) -> None:
    fieldnames = [
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
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def test_read_payloads_keeps_bad_json_as_a_failed_record(tmp_path: Path) -> None:
    input_path = tmp_path / "leads.csv"
    _write_generated_csv(
        input_path,
        [
            {
                "email": "valid@example.com",
                "tags": json.dumps(["technology"]),
                "custom_fields": "{}",
                "metadata": "{}",
                "tenant_id": "T001",
            },
            {
                "email": "bad@example.com",
                "tags": "not-json",
                "custom_fields": "{}",
                "metadata": "{}",
                "tenant_id": "T001",
            },
        ],
    )

    result = read_payloads(input_path)

    assert len(result.payloads) == 1
    assert len(result.failures) == 1
    assert result.failures[0]["row_number"] == 3


@patch("bulk_import_leads.build_session")
def test_import_payloads_records_http_and_network_failures(build_session: Mock) -> None:
    session = Mock()
    success = Mock(status_code=201)
    success.json.side_effect = ValueError("empty response body")
    failure = Mock(status_code=422, text="invalid lead")
    session.post.side_effect = [success, failure, requests.ConnectionError("offline")]
    build_session.return_value = session
    payloads = [
        (2, {"email": "one@example.com"}),
        (3, {"email": "two@example.com"}),
        (4, {"email": "three@example.com"}),
    ]

    successes, failures = import_payloads(payloads, "http://api.test/leads", 3, 0.1, 1, 0)

    assert successes == 1
    assert len(failures) == 2
    assert failures[0]["status_code"] == 422
    assert "offline" in failures[1]["error"]
    session.close.assert_called_once()


def test_write_failed_records_serializes_nested_payloads(tmp_path: Path) -> None:
    output = tmp_path / "failed_records.csv"
    write_failed_records(
        output,
        [
            {
                "row_number": 2,
                "status_code": 500,
                "error": "server error",
                "payload": {
                    "email": "lead@example.com",
                    "tags": ["technology"],
                    "custom_fields": {"region": "US"},
                    "metadata": {},
                },
            }
        ],
    )

    with output.open(encoding="utf-8", newline="") as handle:
        row = next(csv.DictReader(handle))
    assert json.loads(row["tags"]) == ["technology"]
    assert json.loads(row["custom_fields"]) == {"region": "US"}
