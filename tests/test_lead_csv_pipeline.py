import csv
import json
import sys
from pathlib import Path


sys.path.insert(0, str((Path(__file__).resolve().parents[1] / "tools").resolve()))

from lead_csv_pipeline import transform_rows, write_leads_csv  # noqa: E402


def test_transform_rows_cleans_and_deduplicates() -> None:
    rows = [
        {
            "email": " JANE@EXAMPLE.COM ",
            "phone": "(555) 123-4567",
            "full_name": "jane lead",
            "company": "acme corp",
            "score": "110",
            "tenant_id": "T001",
        },
        {
            "email": "jane@example.com",
            "phone": "invalid",
            "full_name": "Duplicate Jane",
            "company": "Acme Corp",
        },
        {
            "email": "not-an-email",
            "phone": "5551234567",
            "full_name": "Invalid Email",
            "company": "Example LLC",
        },
        {
            "email": "",
            "phone": "bad",
            "owner": "arun kumar",
            "department": "HR",
            "metadata": json.dumps({"tags": ["Policy"]}),
        },
    ]

    result = transform_rows(rows)

    assert len(result.leads) == 2
    assert result.input_count == 4
    assert result.duplicate_count == 1
    assert result.invalid_email_count == 1
    assert result.repaired_phone_count == 1
    assert result.leads[0]["email"] == "jane@example.com"
    assert result.leads[0]["phone"] == "+15551234567"
    assert result.leads[0]["company"] == "Acme Corp"
    assert result.leads[0]["score"] == 100.0
    assert result.leads[1]["email"] == "arun.kumar@peoplefirstsolutions.com"
    assert result.leads[1]["phone"].startswith("+1555")
    assert result.leads[1]["company"] == "PeopleFirst Solutions"
    assert result.leads[1]["assigned_to"] == "U004"


def test_write_leads_csv_serializes_nested_fields(tmp_path: Path) -> None:
    result = transform_rows(
        [
            {
                "email": "lead@example.com",
                "phone": "5551234567",
                "full_name": "Jane Lead",
                "company": "Acme Corp",
                "tags": "technology,enterprise",
                "custom_fields": '{"region":"US"}',
            }
        ]
    )
    output = tmp_path / "cleaned_leads.csv"

    write_leads_csv(output, result.leads)

    with output.open(encoding="utf-8", newline="") as handle:
        row = next(csv.DictReader(handle))
    assert json.loads(row["tags"]) == ["technology", "enterprise"]
    assert json.loads(row["custom_fields"]) == {"region": "US"}


def test_markdown_website_is_normalized() -> None:
    result = transform_rows(
        [
            {
                "email": "lead@example.com",
                "full_name": "Jane Lead",
                "company": "Acme Corp",
                "website": "[https://acme.com](https://acme.com)",
            }
        ]
    )

    assert result.leads[0]["website"] == "https://acme.com"
