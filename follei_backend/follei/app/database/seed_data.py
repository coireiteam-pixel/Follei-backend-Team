"""Load Follei seed data from generated CSV datasets.

This module intentionally avoids hardcoded sample records. It imports rows from
``generated_dataset/csv`` and converts generated UUID keys into the app's short
4-character IDs while preserving foreign-key relationships.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from sqlalchemy import Boolean, Date, DateTime, Integer, JSON, Numeric, String, func, select
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Session

from app.database.base import Base
from app.database.init_db import init_db
from app.database.session import SessionLocal, engine


DEFAULT_LIMIT = 1000
ID_ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"

COLUMN_ALIASES = {
    ("documents", "filename"): "title",
    ("documents", "file_path"): "path",
    ("documents", "file_type"): "mime_type",
}

TABLE_LOAD_ORDER = [
    "tenants",
    "users",
    "agents",
    "agent_tasks",
    "conversations",
    "conversation_messages",
    "documents",
    "analytics_daily",
    "analytics_monthly",
]


def run_seed(
    dataset_dir: Path | None = None,
    limit: int | None = DEFAULT_LIMIT,
    reset: bool = False,
    recreate: bool = False,
) -> dict[str, int]:
    """Load app-compatible records from generated dataset CSV files."""
    if recreate:
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
    else:
        init_db()

    csv_dir = _resolve_csv_dir(dataset_dir)
    if not csv_dir.exists():
        raise FileNotFoundError(f"Dataset CSV directory not found: {csv_dir}")

    db: Session = SessionLocal()
    loader = DatasetSeeder(csv_dir=csv_dir, db=db, limit=limit)
    try:
        if reset:
            loader.reset_loaded_tables()

        counts = loader.load()
        db.commit()
        _print_summary(counts, csv_dir)
        return counts
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


class DatasetSeeder:
    def __init__(self, csv_dir: Path, db: Session, limit: int | None) -> None:
        self.csv_dir = csv_dir
        self.db = db
        self.limit = limit
        self.id_map: dict[str, str] = {}
        self.used_ids: set[str] = set()
        self.inserted_original_ids: dict[str, set[str]] = {
            table_name: set() for table_name in Base.metadata.tables
        }

    def load(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for table_name in self._ordered_table_names():
            table = Base.metadata.tables[table_name]
            csv_path = self.csv_dir / f"{table_name}.csv"
            if not csv_path.exists():
                continue

            if self._table_has_rows(table):
                counts[table_name] = 0
                continue

            counts[table_name] = self._load_table(table_name)

        return counts

    def reset_loaded_tables(self) -> None:
        for table_name in reversed(self._ordered_table_names()):
            table = Base.metadata.tables[table_name]
            if (self.csv_dir / f"{table_name}.csv").exists():
                self.db.execute(table.delete())
        self.db.flush()

    def _ordered_table_names(self) -> list[str]:
        known_tables = set(Base.metadata.tables)
        ordered = [name for name in TABLE_LOAD_ORDER if name in known_tables]
        remaining = sorted(
            name
            for name in known_tables
            if name not in ordered and (self.csv_dir / f"{name}.csv").exists()
        )
        return ordered + remaining

    def _load_table(self, table_name: str) -> int:
        table = Base.metadata.tables[table_name]
        csv_path = self.csv_dir / f"{table_name}.csv"
        inserted = 0

        with csv_path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            for source_row in reader:
                if self.limit is not None and inserted >= self.limit:
                    break

                row = self._prepare_row(table_name, source_row)
                if row is None:
                    continue

                self.db.execute(table.insert().values(**row))
                inserted += 1

                original_id = source_row.get("id")
                if original_id:
                    self.inserted_original_ids[table_name].add(original_id)

                if inserted % 500 == 0:
                    self.db.flush()

        self.db.flush()
        return inserted

    def _prepare_row(self, table_name: str, source_row: dict[str, str]) -> dict[str, Any] | None:
        table = Base.metadata.tables[table_name]
        row: dict[str, Any] = {}

        for column in table.columns:
            source_column = COLUMN_ALIASES.get((table_name, column.name), column.name)
            if source_column not in source_row:
                continue

            raw_value = source_row[source_column]
            value = self._convert_value(raw_value, column)
            if value is _SKIP_ROW:
                return None

            row[column.name] = value

        return row

    def _convert_value(self, raw_value: str, column: Any) -> Any:
        if raw_value == "":
            return None

        if self._is_short_id_column(column):
            return self._convert_id_value(raw_value, column)

        column_type = column.type
        if isinstance(column_type, Boolean):
            return raw_value.lower() in {"1", "true", "yes", "y"}
        if isinstance(column_type, Date) and not isinstance(column_type, DateTime):
            return datetime.fromisoformat(raw_value).date()
        if isinstance(column_type, DateTime):
            return datetime.fromisoformat(raw_value)
        if isinstance(column_type, Integer):
            return int(raw_value)
        if isinstance(column_type, Numeric):
            return Decimal(raw_value)
        if isinstance(column_type, (JSON, ARRAY)):
            return json.loads(raw_value)

        return raw_value

    def _convert_id_value(self, raw_value: str, column: Any) -> str | None | object:
        if raw_value == "":
            return None

        if column.foreign_keys:
            foreign_key = next(iter(column.foreign_keys))
            target_table = foreign_key.column.table.name
            if raw_value not in self.inserted_original_ids.get(target_table, set()):
                return None if column.nullable else _SKIP_ROW

        return self._small_id(raw_value, prefix=_prefix_for_column(column))

    def _is_short_id_column(self, column: Any) -> bool:
        return isinstance(column.type, String) and column.type.length == 4 and (
            column.name == "id"
            or column.name.endswith("_id")
            or bool(column.foreign_keys)
        )

    def _small_id(self, source_id: str, prefix: str) -> str:
        if source_id in self.id_map:
            return self.id_map[source_id]

        digest = hashlib.sha1(source_id.encode("utf-8")).hexdigest()
        number = int(digest[:12], 16)
        suffix_space = len(ID_ALPHABET) ** 3

        for offset in range(suffix_space):
            candidate = prefix + _to_base36((number + offset) % suffix_space).rjust(3, "0")
            if candidate not in self.used_ids:
                self.id_map[source_id] = candidate
                self.used_ids.add(candidate)
                return candidate

        raise RuntimeError(f"No available short IDs for prefix {prefix!r}")

    def _table_has_rows(self, table: Any) -> bool:
        return bool(self.db.execute(select(func.count()).select_from(table)).scalar_one())


class _SkipRow:
    pass


_SKIP_ROW = _SkipRow()


def _resolve_csv_dir(dataset_dir: Path | None) -> Path:
    if dataset_dir is None:
        configured = os.getenv("FOLLEI_DATASET_DIR")
        dataset_dir = Path(configured) if configured else _project_root() / "generated_dataset"

    dataset_dir = dataset_dir.resolve()
    return dataset_dir / "csv" if dataset_dir.name != "csv" else dataset_dir


def _project_root() -> Path:
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "generated_dataset").exists():
            return parent
    return current.parents[4]


def _prefix_for_column(column: Any) -> str:
    if column.name == "tenant_id" or column.table.name == "tenants":
        return "T"
    if column.name == "agent_id" or column.table.name.startswith("agent"):
        return "A"
    if column.name == "conversation_id" or column.table.name.startswith("conversation"):
        return "C"
    if column.name == "customer_id" or column.table.name.startswith("customer"):
        return "U"
    if column.name == "lead_id" or column.table.name.startswith("lead"):
        return "L"
    if column.name in {"document_id", "chunk_id"} or "document" in column.table.name:
        return "D"
    if column.name == "user_id" or column.table.name == "users":
        return "U"
    return "X"


def _to_base36(value: int) -> str:
    if value == 0:
        return "0"

    chars: list[str] = []
    while value:
        value, remainder = divmod(value, len(ID_ALPHABET))
        chars.append(ID_ALPHABET[remainder])
    return "".join(reversed(chars))


def _print_summary(counts: dict[str, int], csv_dir: Path) -> None:
    print(f"Loaded dataset CSVs from {csv_dir}")
    for table_name, count in counts.items():
        status = "skipped existing rows" if count == 0 else f"{count} rows"
        print(f"  {table_name}: {status}")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed the Follei database from generated dataset CSV files.")
    parser.add_argument(
        "--dataset-dir",
        type=Path,
        default=None,
        help="Path to generated_dataset or generated_dataset/csv. Defaults to FOLLEI_DATASET_DIR or repo generated_dataset.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=DEFAULT_LIMIT,
        help="Max rows per table. Use 0 for no limit.",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete existing rows from dataset-backed tables before importing.",
    )
    parser.add_argument(
        "--recreate",
        action="store_true",
        help="Drop and recreate all ORM tables before importing. Use when the local SQLite schema is outdated.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    run_seed(
        dataset_dir=args.dataset_dir,
        limit=None if args.limit == 0 else args.limit,
        reset=args.reset,
        recreate=args.recreate,
    )
