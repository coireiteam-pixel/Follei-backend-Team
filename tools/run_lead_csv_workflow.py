"""Run CSV cleaning, lead generation, and API import as one workflow."""

from __future__ import annotations

import argparse
from pathlib import Path

from bulk_import_leads import configure_logging, import_payloads, read_payloads, write_failed_records
from lead_csv_pipeline import read_csv, transform_rows, write_leads_csv


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_csv", type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path("lead_import_output"))
    parser.add_argument("--tenant-id", default="T001")
    parser.add_argument("--endpoint", default="http://127.0.0.1:8000/api/leads")
    parser.add_argument("--retries", type=int, default=3)
    parser.add_argument("--backoff", type=float, default=0.5)
    parser.add_argument("--timeout", type=float, default=15)
    parser.add_argument("--delay", type=float, default=0)
    parser.add_argument("--no-import", action="store_true")
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    cleaned_path = args.output_dir / "cleaned_leads.csv"
    failed_path = args.output_dir / "failed_records.csv"
    configure_logging(args.output_dir / "workflow.log")

    result = transform_rows(read_csv(args.input_csv), args.tenant_id)
    write_leads_csv(cleaned_path, result.leads)
    print(
        f"Input rows={result.input_count} cleaned_leads={len(result.leads)} "
        f"duplicates_removed={result.duplicate_count} "
        f"invalid_emails_removed={result.invalid_email_count} "
        f"phones_repaired={result.repaired_phone_count}"
    )
    print(f"Generated CSV: {cleaned_path.resolve()}")

    if args.no_import:
        return

    read_result = read_payloads(cleaned_path)
    successes, failures = import_payloads(
        read_result.payloads,
        args.endpoint,
        args.retries,
        args.backoff,
        args.timeout,
        args.delay,
    )
    failures = [*read_result.failures, *failures]
    write_failed_records(failed_path, failures)
    print(f"Imported={successes} failed={len(failures)}")
    print(f"Failed records: {failed_path.resolve()}")
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
