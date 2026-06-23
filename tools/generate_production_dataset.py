#!/usr/bin/env python3
"""Generate a realistic production-style dataset for the Follei backend.

The generator is intentionally dependency-free so it can run in restricted
developer environments. It emits full CSV and SQL data plus compact JSON/CSV
samples, an ER mapping, a manifest, and a valid XLSX data dictionary.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import random
import re
import shutil
import uuid
import zipfile
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "generated_dataset"
CSV_DIR = OUT / "csv"
SCHEMA_EXPORTS = ROOT / "database_schema_exports"
SOURCE_SCHEMA = ROOT / "follei_backend" / "follei" / "db" / "init" / "002_complete_domain_schema.sql"
IST = timezone(timedelta(hours=5, minutes=30))
NOW = datetime(2026, 6, 22, 18, 0, 0, tzinfo=IST)
START = NOW - timedelta(days=365)
RNG = random.Random(20260622)


COUNTS = {
    "tenants": 10_000,
    "roles": 10_000,
    "permissions": 96,
    "users": 20_000,
    "user_auth": 20_000,
    "user_roles": 20_000,
    "user_sessions": 20_000,
    "refresh_tokens": 10_000,
    "tenant_api_keys": 10_000,
    "agents": 10_000,
    "projects": 10_000,
    "agent_tasks": 20_000,
    "activities": 20_000,
    "notifications": 10_000,
    "conversations": 10_000,
    "conversation_messages": 20_000,
    "audit_logs": 10_000,
    "documents": 10_000,
    "file_uploads": 10_000,
    "api_request_logs": 20_000,
    "reports": 10_000,
    "analytics_daily": 20_000,
    "analytics_monthly": 10_000,
    "login_attempts": 20_000,
    "password_reset_requests": 10_000,
    "token_usage": 10_000,
    "invalid_test_records": 10_000,
}


TABLE_COLUMNS = {
    "tenants": [
        "id", "name", "domain", "created_at", "slug", "industry", "plan",
        "status", "trial_ends_at", "is_active", "updated_at",
    ],
    "roles": ["id", "tenant_id", "name", "description", "created_at", "updated_at"],
    "permissions": ["id", "resource", "action", "description", "created_at"],
    "users": [
        "id", "tenant_id", "email", "hashed_password", "first_name", "last_name",
        "role", "is_active", "created_at", "full_name", "status", "last_login_at",
        "updated_at",
    ],
    "user_auth": [
        "id", "tenant_id", "user_id", "password_hash", "totp_secret",
        "failed_attempts", "locked_until", "created_at", "updated_at",
    ],
    "user_roles": ["user_id", "role_id", "created_at"],
    "user_sessions": [
        "id", "tenant_id", "user_id", "device", "browser", "ip_address",
        "user_agent", "expires_at", "created_at", "updated_at",
    ],
    "refresh_tokens": [
        "id", "tenant_id", "user_id", "token_hash", "revoked_at", "expires_at", "created_at",
    ],
    "tenant_api_keys": [
        "id", "tenant_id", "name", "key_hash", "scopes", "last_used_at",
        "expires_at", "is_active", "created_at", "updated_at",
    ],
    "agents": [
        "id", "tenant_id", "name", "role", "system_prompt", "tools",
        "created_at", "agent_type", "model", "is_active", "updated_at",
    ],
    "projects": [
        "id", "tenant_id", "owner_user_id", "agent_id", "name", "description",
        "status", "priority", "budget_usd", "starts_at", "due_at", "completed_at",
        "deleted_at", "metadata", "created_at", "updated_at",
    ],
    "agent_tasks": [
        "id", "tenant_id", "agent_id", "assigned_by", "task_type", "title",
        "payload", "status", "due_at", "created_at", "updated_at",
    ],
    "activities": [
        "id", "tenant_id", "user_id", "project_id", "task_id", "activity_type",
        "channel", "status", "description", "metadata", "created_at",
    ],
    "notifications": [
        "id", "tenant_id", "user_id", "notification_type", "title", "body",
        "payload", "read_at", "created_at",
    ],
    "conversations": [
        "id", "tenant_id", "agent_id", "title", "created_at", "customer_id",
        "lead_id", "channel", "status", "started_at", "ended_at", "updated_at",
    ],
    "conversation_messages": [
        "id", "tenant_id", "conversation_id", "role", "content", "created_at",
        "sender_type", "sender_id", "message", "message_type", "metadata",
    ],
    "audit_logs": [
        "id", "tenant_id", "user_id", "action", "entity_type", "entity_id",
        "metadata", "created_at", "resource_type", "resource_id", "payload",
    ],
    "documents": [
        "id", "tenant_id", "title", "source_type", "status", "tags", "created_at",
        "source_id", "source_uri", "mime_type", "path", "metadata", "updated_at",
    ],
    "file_uploads": [
        "id", "tenant_id", "user_id", "project_id", "document_id", "file_name",
        "mime_type", "file_size_bytes", "storage_path", "checksum", "scan_status",
        "status", "deleted_at", "metadata", "created_at",
    ],
    "api_request_logs": [
        "id", "tenant_id", "user_id", "method", "path", "status_code",
        "request_body", "response_body", "ip_address", "user_agent",
        "duration_ms", "created_at",
    ],
    "reports": [
        "id", "tenant_id", "created_by", "project_id", "report_type", "title",
        "status", "period_start", "period_end", "metrics", "file_url",
        "generated_at", "deleted_at", "created_at",
    ],
    "analytics_daily": [
        "id", "tenant_id", "metric_date", "metric_name", "metric_value",
        "dimensions", "created_at",
    ],
    "analytics_monthly": [
        "id", "tenant_id", "metric_month", "metric_name", "metric_value",
        "dimensions", "created_at",
    ],
    "login_attempts": [
        "id", "tenant_id", "user_id", "email", "ip_address", "user_agent",
        "status", "failure_reason", "mfa_required", "risk_score", "created_at",
    ],
    "password_reset_requests": [
        "id", "tenant_id", "user_id", "email", "token_hash", "status",
        "requested_ip", "expires_at", "used_at", "created_at",
    ],
    "token_usage": [
        "id", "tenant_id", "user_id", "agent_id", "model", "token_type",
        "quantity", "created_at",
    ],
    "invalid_test_records": [
        "id", "tenant_id", "source_table", "scenario", "raw_payload",
        "validation_error", "expected_handling", "created_at",
    ],
}

ARRAY_COLUMNS = {
    ("agents", "tools"),
    ("documents", "tags"),
    ("tenant_api_keys", "scopes"),
}

JSON_COLUMNS = {
    "metadata", "payload", "request_body", "response_body", "metrics", "raw_payload",
}


FIRST_NAMES = [
    "Aarav", "Ishaan", "Vivaan", "Ananya", "Diya", "Meera", "Priya", "Riya",
    "Neha", "Kavya", "Arjun", "Rohan", "Kabir", "Aditya", "Nikhil", "Sofia",
    "Emma", "Olivia", "Mia", "Noah", "Liam", "Ethan", "Lucas", "Mason",
    "Ava", "Amelia", "Charlotte", "Harper", "Isabella", "Daniel", "Maya",
    "Nora", "Owen", "Aiden", "Zara", "Fatima", "Amir", "Hana", "Leila", "Mateo",
]
LAST_NAMES = [
    "Sharma", "Patel", "Reddy", "Iyer", "Singh", "Gupta", "Khan", "Mehta",
    "Nair", "Rao", "Johnson", "Smith", "Brown", "Garcia", "Martinez",
    "Wilson", "Davis", "Nguyen", "Chen", "Lee", "Kim", "Rodriguez", "Thomas",
    "Walker", "Young", "Allen", "King", "Wright", "Scott", "Green",
]
COMPANY_PREFIX = [
    "Nimbus", "Cobalt", "Kairo", "Acme", "BrightPath", "Vertex", "Zenith",
    "Northstar", "Clearline", "Evergreen", "BluePeak", "Redwood", "Cloudlane",
    "Sparkgrid", "UrbanLoop", "SignalForge", "CoreAxis", "Silverline",
]
COMPANY_SUFFIX = [
    "Labs", "Systems", "Health", "Retail", "Logistics", "Financial", "AI",
    "Works", "Cloud", "Analytics", "Services", "Commerce", "Networks",
]
INDUSTRIES = [
    "SaaS", "Healthcare", "Fintech", "Retail", "Manufacturing", "Education",
    "Logistics", "Real Estate", "Professional Services", "Travel",
]
PLANS = ["free", "starter", "growth", "business", "enterprise"]
TENANT_STATUS = ["active", "trialing", "past_due", "suspended", "cancelled"]
USER_ROLES = ["admin", "manager", "analyst", "agent_operator", "support", "viewer"]
PROJECT_STATUS = ["planned", "active", "blocked", "completed", "archived", "deleted"]
TASK_STATUS = ["queued", "in_progress", "blocked", "completed", "failed", "cancelled"]
CHANNELS = ["web", "whatsapp", "email", "sms", "slack", "api", "voice"]
MODELS = ["gpt-4.1", "gpt-4.1-mini", "gpt-4o-mini", "o4-mini", "claude-3.5-sonnet"]
ENDPOINTS = [
    ("GET", "/api/v1/users"), ("POST", "/api/v1/auth/login"),
    ("POST", "/api/v1/auth/refresh"), ("GET", "/api/conversations"),
    ("POST", "/api/conversations/{conversation_id}/messages"),
    ("POST", "/api/documents"), ("GET", "/api/analytics/dashboard"),
    ("POST", "/api/knowledge/search"), ("POST", "/api/leads"),
    ("PATCH", "/api/v1/agent-tasks/{task_id}"), ("POST", "/api/v1/agents/{agent_id}/chat"),
    ("GET", "/api/v1/notifications"), ("POST", "/api/retrieval-logs"),
]


def uid() -> str:
    return str(uuid.uuid4())


def slugify(value: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return value or "item"


def choose_weighted(items: list[Any], weights: list[float]) -> Any:
    return RNG.choices(items, weights=weights, k=1)[0]


def rand_ip() -> str:
    if RNG.random() < 0.82:
        return f"103.{RNG.randint(20, 255)}.{RNG.randint(0, 255)}.{RNG.randint(1, 254)}"
    return f"{RNG.randint(13, 223)}.{RNG.randint(0, 255)}.{RNG.randint(0, 255)}.{RNG.randint(1, 254)}"


def random_company(i: int) -> str:
    return f"{RNG.choice(COMPANY_PREFIX)} {RNG.choice(COMPANY_SUFFIX)} {i:05d}"


def random_name() -> tuple[str, str]:
    return RNG.choice(FIRST_NAMES), RNG.choice(LAST_NAMES)


def random_phone() -> str:
    country = RNG.choice(["+1", "+91", "+44", "+61", "+971"])
    return f"{country}-{RNG.randint(200, 999)}-{RNG.randint(100, 999)}-{RNG.randint(1000, 9999)}"


def biased_timestamp() -> datetime:
    days = RNG.randint(0, 364)
    hour = choose_weighted(
        list(range(24)),
        [1, 1, 1, 1, 1, 2, 4, 8, 14, 18, 20, 18, 14, 17, 20, 24, 27, 28, 20, 14, 9, 5, 3, 2],
    )
    minute = RNG.randint(0, 59)
    second = RNG.randint(0, 59)
    ts = START + timedelta(days=days, hours=hour, minutes=minute, seconds=second)
    if RNG.random() < 0.09:
        ts += timedelta(days=RNG.choice([0, 1, 2]), hours=RNG.choice([9, 10, 16, 17]))
    return min(ts, NOW)


def iso(value: datetime | date | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat(timespec="seconds")
    return value.isoformat()


def hash_value(prefix: str, value: str) -> str:
    return f"{prefix}_{hashlib.sha256(value.encode('utf-8')).hexdigest()}"


def row_to_csv(row: dict[str, Any], columns: list[str]) -> list[Any]:
    values = []
    for col in columns:
        value = row.get(col)
        if isinstance(value, (dict, list)):
            values.append(json.dumps(value, separators=(",", ":"), sort_keys=True))
        elif isinstance(value, bool):
            values.append("true" if value else "false")
        elif value is None:
            values.append("")
        else:
            values.append(value)
    return values


def sql_literal(table: str, col: str, value: Any) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
            return "NULL"
        return str(value)
    if (table, col) in ARRAY_COLUMNS:
        items = ", ".join(sql_literal(table, "_array_item", str(item)) for item in value)
        return f"ARRAY[{items}]::text[]"
    if isinstance(value, (dict, list)) or col in JSON_COLUMNS:
        payload = json.dumps(value, separators=(",", ":"), sort_keys=True)
        return "'" + payload.replace("'", "''") + "'::jsonb"
    return "'" + str(value).replace("'", "''") + "'"


class DatasetWriter:
    def __init__(self) -> None:
        if OUT.exists():
            shutil.rmtree(OUT)
        CSV_DIR.mkdir(parents=True, exist_ok=True)
        self.csv_files: dict[str, Any] = {}
        self.csv_writers: dict[str, csv.writer] = {}
        self.sql = (OUT / "sql_insert_scripts.sql").open("w", encoding="utf-8", newline="\n")
        self.sample_csv = (OUT / "sample_data.csv").open("w", encoding="utf-8", newline="")
        self.sample_csv_writer = csv.writer(self.sample_csv)
        self.sample_csv_writer.writerow(["table_name", "sample_index", "row_json"])
        self.samples: dict[str, list[dict[str, Any]]] = defaultdict(list)
        self.counts: dict[str, int] = defaultdict(int)
        self.buffers: dict[str, list[dict[str, Any]]] = defaultdict(list)
        self.sql.write("-- Follei production-grade synthetic dataset inserts\n")
        self.sql.write("-- Generated on 2026-06-22 with deterministic seed 20260622\n")
        self.sql.write("BEGIN;\n")

    def emit(self, table: str, row: dict[str, Any]) -> None:
        columns = TABLE_COLUMNS[table]
        if table not in self.csv_writers:
            handle = (CSV_DIR / f"{table}.csv").open("w", encoding="utf-8", newline="")
            writer = csv.writer(handle)
            writer.writerow(columns)
            self.csv_files[table] = handle
            self.csv_writers[table] = writer
        self.csv_writers[table].writerow(row_to_csv(row, columns))
        self.counts[table] += 1
        if len(self.samples[table]) < 100:
            sample = {col: row.get(col) for col in columns}
            self.samples[table].append(sample)
            self.sample_csv_writer.writerow([table, len(self.samples[table]), json.dumps(sample, default=str, sort_keys=True)])
        self.buffers[table].append(row)
        if len(self.buffers[table]) >= 500:
            self.flush_table(table)

    def flush_table(self, table: str) -> None:
        rows = self.buffers.get(table)
        if not rows:
            return
        columns = TABLE_COLUMNS[table]
        quoted_cols = ", ".join(f'"{col}"' for col in columns)
        self.sql.write(f"\nINSERT INTO {table} ({quoted_cols}) VALUES\n")
        values = []
        for row in rows:
            values.append("(" + ", ".join(sql_literal(table, col, row.get(col)) for col in columns) + ")")
        self.sql.write(",\n".join(values))
        self.sql.write(";\n")
        self.buffers[table] = []

    def close(self) -> None:
        for table in list(self.buffers):
            self.flush_table(table)
        self.sql.write("\nCOMMIT;\n")
        self.sql.close()
        for handle in self.csv_files.values():
            handle.close()
        self.sample_csv.close()


class State:
    def __init__(self) -> None:
        self.tenants: list[dict[str, Any]] = []
        self.roles: list[dict[str, Any]] = []
        self.permissions: list[dict[str, Any]] = []
        self.users: list[dict[str, Any]] = []
        self.user_auth: list[dict[str, Any]] = []
        self.agents: list[dict[str, Any]] = []
        self.projects: list[dict[str, Any]] = []
        self.tasks: list[dict[str, Any]] = []
        self.conversations: list[dict[str, Any]] = []
        self.documents: list[dict[str, Any]] = []
        self.role_by_tenant: dict[str, list[str]] = defaultdict(list)
        self.users_by_tenant: dict[str, list[dict[str, Any]]] = defaultdict(list)
        self.agents_by_tenant: dict[str, list[dict[str, Any]]] = defaultdict(list)
        self.projects_by_tenant: dict[str, list[dict[str, Any]]] = defaultdict(list)
        self.tasks_by_tenant: dict[str, list[dict[str, Any]]] = defaultdict(list)
        self.conversations_by_tenant: dict[str, list[dict[str, Any]]] = defaultdict(list)
        self.documents_by_tenant: dict[str, list[dict[str, Any]]] = defaultdict(list)


def tenant_for(state: State) -> dict[str, Any]:
    return RNG.choice(state.tenants)


def user_for(state: State, tenant_id: str) -> dict[str, Any] | None:
    users = state.users_by_tenant.get(tenant_id)
    return RNG.choice(users) if users else None


def agent_for(state: State, tenant_id: str) -> dict[str, Any] | None:
    agents = state.agents_by_tenant.get(tenant_id)
    return RNG.choice(agents) if agents else None


def project_for(state: State, tenant_id: str) -> dict[str, Any] | None:
    projects = state.projects_by_tenant.get(tenant_id)
    return RNG.choice(projects) if projects else None


def task_for(state: State, tenant_id: str) -> dict[str, Any] | None:
    tasks = state.tasks_by_tenant.get(tenant_id)
    return RNG.choice(tasks) if tasks else None


def conversation_for(state: State, tenant_id: str) -> dict[str, Any] | None:
    conversations = state.conversations_by_tenant.get(tenant_id)
    return RNG.choice(conversations) if conversations else None


def document_for(state: State, tenant_id: str) -> dict[str, Any] | None:
    documents = state.documents_by_tenant.get(tenant_id)
    return RNG.choice(documents) if documents else None


def generate_core(writer: DatasetWriter, state: State) -> None:
    for i in range(COUNTS["tenants"]):
        created = biased_timestamp()
        name = random_company(i)
        slug = slugify(name)
        status = choose_weighted(TENANT_STATUS, [76, 9, 7, 4, 4])
        row = {
            "id": uid(),
            "name": name,
            "domain": f"{slug}.example.com",
            "created_at": iso(created),
            "slug": slug,
            "industry": RNG.choice(INDUSTRIES),
            "plan": choose_weighted(PLANS, [14, 26, 30, 20, 10]),
            "status": status,
            "trial_ends_at": iso(created + timedelta(days=14)) if status == "trialing" else None,
            "is_active": status in {"active", "trialing", "past_due"},
            "updated_at": iso(min(NOW, created + timedelta(days=RNG.randint(0, 180)))),
        }
        state.tenants.append(row)
        writer.emit("tenants", row)

    resources = [
        "tenant", "user", "role", "agent", "conversation", "message", "lead", "customer",
        "document", "knowledge", "integration", "billing", "analytics", "report", "project", "task",
    ]
    actions = ["create", "read", "update", "delete", "export", "approve"]
    for resource in resources:
        for action in actions:
            row = {
                "id": uid(),
                "resource": resource,
                "action": action,
                "description": f"Can {action} {resource} records",
                "created_at": iso(START + timedelta(days=1)),
            }
            state.permissions.append(row)
            writer.emit("permissions", row)

    for i, tenant in enumerate(state.tenants[: COUNTS["roles"]]):
        role_name = USER_ROLES[i % len(USER_ROLES)]
        row = {
            "id": uid(),
            "tenant_id": tenant["id"],
            "name": role_name,
            "description": f"{role_name.replace('_', ' ').title()} access for {tenant['name']}",
            "created_at": tenant["created_at"],
            "updated_at": tenant["updated_at"],
        }
        state.roles.append(row)
        state.role_by_tenant[tenant["id"]].append(row["id"])
        writer.emit("roles", row)

    for i in range(COUNTS["users"]):
        tenant = state.tenants[i % len(state.tenants)] if i < len(state.tenants) else tenant_for(state)
        first, last = random_name()
        role = USER_ROLES[i % len(USER_ROLES)]
        created = biased_timestamp()
        status = choose_weighted(["active", "inactive", "invited", "locked", "deleted"], [82, 8, 4, 3, 3])
        last_login = created + timedelta(days=RNG.randint(0, max(1, (NOW - created).days)))
        if status in {"invited", "deleted"}:
            last_login = None
        email = f"{first}.{last}.{i:06d}@{slugify(tenant['name'])}.example.com".lower()
        row = {
            "id": uid(),
            "tenant_id": tenant["id"],
            "email": email,
            "hashed_password": hash_value("$argon2id$v=19", email)[:96],
            "first_name": first,
            "last_name": last,
            "role": role,
            "is_active": status == "active",
            "created_at": iso(created),
            "full_name": f"{first} {last}",
            "status": status,
            "last_login_at": iso(last_login) if last_login else None,
            "updated_at": iso(min(NOW, created + timedelta(days=RNG.randint(1, 90)))),
        }
        state.users.append(row)
        state.users_by_tenant[tenant["id"]].append(row)
        writer.emit("users", row)

    for user in state.users:
        failed = choose_weighted([0, 1, 2, 3, 4, 5, 8], [72, 10, 6, 4, 3, 3, 2])
        locked_until = NOW + timedelta(minutes=RNG.randint(5, 120)) if failed >= 5 and RNG.random() < 0.35 else None
        row = {
            "id": uid(),
            "tenant_id": user["tenant_id"],
            "user_id": user["id"],
            "password_hash": user["hashed_password"],
            "totp_secret": hash_value("totp", user["id"])[:32] if RNG.random() < 0.42 else None,
            "failed_attempts": failed,
            "locked_until": iso(locked_until),
            "created_at": user["created_at"],
            "updated_at": user["updated_at"],
        }
        state.user_auth.append(row)
        writer.emit("user_auth", row)
        role_ids = state.role_by_tenant.get(user["tenant_id"]) or [state.roles[0]["id"]]
        writer.emit("user_roles", {"user_id": user["id"], "role_id": role_ids[0], "created_at": user["created_at"]})

    for i in range(COUNTS["refresh_tokens"]):
        user = state.users[i % len(state.users)]
        created = biased_timestamp()
        revoked = created + timedelta(days=RNG.randint(1, 30)) if RNG.random() < 0.14 else None
        writer.emit("refresh_tokens", {
            "id": uid(),
            "tenant_id": user["tenant_id"],
            "user_id": user["id"],
            "token_hash": hash_value("rt", f"{user['id']}:{i}"),
            "revoked_at": iso(revoked),
            "expires_at": iso(created + timedelta(days=30)),
            "created_at": iso(created),
        })

    for i in range(COUNTS["user_sessions"]):
        user = RNG.choice(state.users)
        created = biased_timestamp()
        browser = RNG.choice(["Chrome", "Edge", "Safari", "Firefox", "Mobile Safari"])
        device = RNG.choice(["Windows Laptop", "MacBook", "iPhone", "Android", "Linux Workstation", "iPad"])
        writer.emit("user_sessions", {
            "id": uid(),
            "tenant_id": user["tenant_id"],
            "user_id": user["id"],
            "device": device,
            "browser": browser,
            "ip_address": rand_ip(),
            "user_agent": f"Mozilla/5.0 ({device}) AppleWebKit/537.36 {browser}/126.0",
            "expires_at": iso(created + timedelta(hours=RNG.randint(2, 720))),
            "created_at": iso(created),
            "updated_at": iso(min(NOW, created + timedelta(minutes=RNG.randint(1, 240)))),
        })

    for i in range(COUNTS["tenant_api_keys"]):
        tenant = state.tenants[i % len(state.tenants)]
        created = biased_timestamp()
        writer.emit("tenant_api_keys", {
            "id": uid(),
            "tenant_id": tenant["id"],
            "name": RNG.choice(["production", "staging", "webhook", "mcp-gateway", "analytics-export"]),
            "key_hash": hash_value("ak", f"{tenant['id']}:{i}"),
            "scopes": RNG.sample(["agents:read", "agents:write", "chat:write", "analytics:read", "documents:write"], RNG.randint(1, 4)),
            "last_used_at": iso(created + timedelta(days=RNG.randint(0, 60))) if RNG.random() < 0.83 else None,
            "expires_at": iso(created + timedelta(days=365)) if RNG.random() < 0.55 else None,
            "is_active": RNG.random() > 0.07,
            "created_at": iso(created),
            "updated_at": iso(min(NOW, created + timedelta(days=RNG.randint(1, 120)))),
        })


def generate_workflows(writer: DatasetWriter, state: State) -> None:
    agent_roles = ["sales_assistant", "support_agent", "knowledge_retriever", "billing_helper", "success_coach"]
    for i in range(COUNTS["agents"]):
        tenant = state.tenants[i % len(state.tenants)]
        created = biased_timestamp()
        role = RNG.choice(agent_roles)
        row = {
            "id": uid(),
            "tenant_id": tenant["id"],
            "name": f"{role.replace('_', ' ').title()} {i % 7 + 1}",
            "role": role,
            "system_prompt": f"You are Follei's {role.replace('_', ' ')} for {tenant['industry']} workflows.",
            "tools": RNG.sample(["crm.search", "calendar.book", "knowledge.search", "email.send", "billing.lookup"], RNG.randint(2, 4)),
            "created_at": iso(created),
            "agent_type": RNG.choice(["autonomous", "copilot", "retrieval", "workflow"]),
            "model": RNG.choice(MODELS),
            "is_active": RNG.random() > 0.06,
            "updated_at": iso(min(NOW, created + timedelta(days=RNG.randint(1, 90)))),
        }
        state.agents.append(row)
        state.agents_by_tenant[tenant["id"]].append(row)
        writer.emit("agents", row)

    for i in range(COUNTS["projects"]):
        tenant = state.tenants[i % len(state.tenants)]
        owner = user_for(state, tenant["id"])
        agent = agent_for(state, tenant["id"])
        created = biased_timestamp()
        status = choose_weighted(PROJECT_STATUS, [8, 54, 8, 20, 6, 4])
        due = created + timedelta(days=RNG.randint(7, 120))
        completed = created + timedelta(days=RNG.randint(3, 110)) if status == "completed" else None
        deleted = created + timedelta(days=RNG.randint(10, 180)) if status == "deleted" else None
        row = {
            "id": uid(),
            "tenant_id": tenant["id"],
            "owner_user_id": owner["id"] if owner else None,
            "agent_id": agent["id"] if agent else None,
            "name": f"{RNG.choice(['QBR Automation', 'Lead Routing', 'Knowledge Cleanup', 'Retention Playbook', 'Support Deflection'])} {i:05d}",
            "description": "Operational workflow project generated from Follei usage patterns.",
            "status": status,
            "priority": choose_weighted(["low", "medium", "high", "urgent"], [20, 48, 25, 7]),
            "budget_usd": RNG.randint(1_000, 95_000),
            "starts_at": iso(created),
            "due_at": iso(due),
            "completed_at": iso(completed),
            "deleted_at": iso(deleted),
            "metadata": {
                "industry": tenant["industry"],
                "workflow": RNG.choice(["sales", "support", "knowledge", "customer_success"]),
                "soft_deleted": deleted is not None,
            },
            "created_at": iso(created),
            "updated_at": iso(min(NOW, created + timedelta(days=RNG.randint(1, 120)))),
        }
        state.projects.append(row)
        state.projects_by_tenant[tenant["id"]].append(row)
        writer.emit("projects", row)

    for i in range(COUNTS["agent_tasks"]):
        tenant = tenant_for(state)
        user = user_for(state, tenant["id"])
        agent = agent_for(state, tenant["id"])
        project = project_for(state, tenant["id"])
        created = biased_timestamp()
        status = choose_weighted(TASK_STATUS, [10, 28, 8, 42, 8, 4])
        title = RNG.choice([
            "Qualify inbound lead", "Draft renewal summary", "Summarize conversation",
            "Index uploaded policy", "Prepare account health report", "Follow up on pricing objection",
        ])
        row = {
            "id": uid(),
            "tenant_id": tenant["id"],
            "agent_id": agent["id"] if agent else None,
            "assigned_by": user["id"] if user else None,
            "task_type": RNG.choice(["lead_qualification", "rag_indexing", "customer_health", "report_generation", "follow_up"]),
            "title": title,
            "payload": {
                "project_id": project["id"] if project else None,
                "source": RNG.choice(["api", "scheduler", "dashboard", "webhook"]),
                "retry_count": RNG.choice([0, 0, 0, 1, 2, 3]),
            },
            "status": status,
            "due_at": iso(created + timedelta(hours=RNG.randint(2, 240))),
            "created_at": iso(created),
            "updated_at": iso(min(NOW, created + timedelta(hours=RNG.randint(1, 96)))),
        }
        state.tasks.append(row)
        state.tasks_by_tenant[tenant["id"]].append(row)
        writer.emit("agent_tasks", row)

    for i in range(COUNTS["activities"]):
        tenant = tenant_for(state)
        user = user_for(state, tenant["id"])
        project = project_for(state, tenant["id"])
        task = task_for(state, tenant["id"])
        created = biased_timestamp()
        activity_type = RNG.choice(["login", "task_update", "comment", "file_upload", "report_view", "agent_chat", "export"])
        writer.emit("activities", {
            "id": uid(),
            "tenant_id": tenant["id"],
            "user_id": user["id"] if user else None,
            "project_id": project["id"] if project else None,
            "task_id": task["id"] if task else None,
            "activity_type": activity_type,
            "channel": RNG.choice(CHANNELS),
            "status": choose_weighted(["success", "failed", "skipped"], [91, 7, 2]),
            "description": f"{activity_type.replace('_', ' ').title()} recorded during production simulation",
            "metadata": {"device": RNG.choice(["desktop", "mobile", "api"]), "duration_ms": RNG.randint(40, 9000)},
            "created_at": iso(created),
        })


def generate_messages_and_files(writer: DatasetWriter, state: State) -> None:
    for i in range(COUNTS["documents"]):
        tenant = state.tenants[i % len(state.tenants)]
        created = biased_timestamp()
        mime = RNG.choice(["application/pdf", "text/markdown", "text/csv", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"])
        title = f"{RNG.choice(['Pricing Guide', 'Security Policy', 'Onboarding SOP', 'Support FAQ', 'Product Brief'])} {i:05d}"
        row = {
            "id": uid(),
            "tenant_id": tenant["id"],
            "title": title,
            "source_type": RNG.choice(["upload", "google_drive", "notion", "confluence", "api"]),
            "status": choose_weighted(["indexed", "processing", "failed", "archived", "deleted"], [76, 9, 6, 6, 3]),
            "tags": RNG.sample(["sales", "support", "security", "pricing", "onboarding", "legal"], RNG.randint(1, 3)),
            "created_at": iso(created),
            "source_id": None,
            "source_uri": f"https://files.example.com/{slugify(title)}",
            "mime_type": mime,
            "path": f"/tenants/{tenant['id']}/documents/{slugify(title)}",
            "metadata": {
                "version": RNG.randint(1, 8),
                "uploaded_from": RNG.choice(["dashboard", "sync", "api"]),
                "soft_deleted": False,
            },
            "updated_at": iso(min(NOW, created + timedelta(days=RNG.randint(1, 90)))),
        }
        state.documents.append(row)
        state.documents_by_tenant[tenant["id"]].append(row)
        writer.emit("documents", row)

    for i in range(COUNTS["conversations"]):
        tenant = state.tenants[i % len(state.tenants)]
        agent = agent_for(state, tenant["id"])
        created = biased_timestamp()
        status = choose_weighted(["open", "pending", "resolved", "archived", "escalated"], [20, 16, 48, 10, 6])
        ended = created + timedelta(minutes=RNG.randint(3, 240)) if status in {"resolved", "archived"} else None
        row = {
            "id": uid(),
            "tenant_id": tenant["id"],
            "agent_id": agent["id"] if agent else None,
            "title": RNG.choice(["Pricing question", "Implementation help", "Lead qualification", "Billing issue", "Knowledge search"]),
            "created_at": iso(created),
            "customer_id": None,
            "lead_id": None,
            "channel": RNG.choice(CHANNELS),
            "status": status,
            "started_at": iso(created),
            "ended_at": iso(ended),
            "updated_at": iso(min(NOW, created + timedelta(hours=RNG.randint(1, 96)))),
        }
        state.conversations.append(row)
        state.conversations_by_tenant[tenant["id"]].append(row)
        writer.emit("conversations", row)

    message_texts = [
        "Can you summarize the latest account activity?",
        "I need pricing details for the enterprise plan.",
        "The document upload failed with a timeout.",
        "Here is the recommended next best action.",
        "Please schedule a follow-up meeting tomorrow.",
        "The customer is asking about SOC 2 and data retention.",
        "I found three relevant knowledge chunks with high confidence.",
    ]
    for i in range(COUNTS["conversation_messages"]):
        tenant = tenant_for(state)
        conversation = conversation_for(state, tenant["id"])
        if not conversation:
            continue
        user = user_for(state, tenant["id"])
        created = biased_timestamp()
        role = choose_weighted(["user", "assistant", "system"], [46, 50, 4])
        content = RNG.choice(message_texts)
        row = {
            "id": uid(),
            "tenant_id": tenant["id"],
            "conversation_id": conversation["id"],
            "role": role,
            "content": content,
            "created_at": iso(created),
            "sender_type": "agent" if role == "assistant" else "user",
            "sender_id": conversation["agent_id"] if role == "assistant" else (user["id"] if user else None),
            "message": content,
            "message_type": RNG.choice(["text", "tool_result", "citation", "error"]),
            "metadata": {
                "confidence": round(RNG.uniform(0.52, 0.99), 3),
                "latency_ms": RNG.randint(120, 6500),
                "contains_pii": RNG.random() < 0.03,
            },
        }
        writer.emit("conversation_messages", row)

    for i in range(COUNTS["file_uploads"]):
        tenant = tenant_for(state)
        user = user_for(state, tenant["id"])
        project = project_for(state, tenant["id"])
        document = document_for(state, tenant["id"])
        created = biased_timestamp()
        status = choose_weighted(["available", "processing", "quarantined", "failed", "deleted"], [80, 8, 2, 6, 4])
        ext, mime = RNG.choice([("pdf", "application/pdf"), ("csv", "text/csv"), ("png", "image/png"), ("docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")])
        deleted = created + timedelta(days=RNG.randint(1, 180)) if status == "deleted" else None
        filename = f"{RNG.choice(['contract', 'pricing', 'usage', 'invoice', 'screenshot'])}_{i:05d}.{ext}"
        writer.emit("file_uploads", {
            "id": uid(),
            "tenant_id": tenant["id"],
            "user_id": user["id"] if user else None,
            "project_id": project["id"] if project else None,
            "document_id": document["id"] if document else None,
            "file_name": filename,
            "mime_type": mime,
            "file_size_bytes": RNG.randint(5_000, 25_000_000),
            "storage_path": f"s3://follei-prod/{tenant['id']}/{filename}",
            "checksum": hashlib.md5(f"{tenant['id']}:{filename}".encode()).hexdigest(),
            "scan_status": choose_weighted(["clean", "pending", "infected", "scan_error"], [91, 6, 1, 2]),
            "status": status,
            "deleted_at": iso(deleted),
            "metadata": {"source": RNG.choice(["dashboard", "api", "chat_attachment"]), "edge_case": status in {"quarantined", "failed"}},
            "created_at": iso(created),
        })


def generate_security_api_analytics(writer: DatasetWriter, state: State) -> None:
    for i in range(COUNTS["notifications"]):
        user = state.users[i % len(state.users)]
        created = biased_timestamp()
        read = created + timedelta(minutes=RNG.randint(1, 240)) if RNG.random() < 0.68 else None
        ntype = RNG.choice(["task_assigned", "mention", "failed_job", "report_ready", "billing_alert", "security_alert"])
        writer.emit("notifications", {
            "id": uid(),
            "tenant_id": user["tenant_id"],
            "user_id": user["id"],
            "notification_type": ntype,
            "title": ntype.replace("_", " ").title(),
            "body": f"{ntype.replace('_', ' ')} notification for {user['full_name']}",
            "payload": {"severity": RNG.choice(["info", "warning", "critical"]), "deep_link": f"/app/notifications/{i}"},
            "read_at": iso(read),
            "created_at": iso(created),
        })

    for i in range(COUNTS["login_attempts"]):
        user = RNG.choice(state.users)
        created = biased_timestamp()
        success = RNG.random() < 0.86 and user["status"] == "active"
        failure_reason = None if success else RNG.choice(["bad_password", "mfa_failed", "locked_account", "unknown_email", "rate_limited"])
        email = user["email"] if RNG.random() > 0.04 else user["email"].replace("@", "+typo@")
        writer.emit("login_attempts", {
            "id": uid(),
            "tenant_id": user["tenant_id"],
            "user_id": user["id"] if success or RNG.random() > 0.15 else None,
            "email": email,
            "ip_address": rand_ip(),
            "user_agent": RNG.choice(["Chrome/126", "Safari/17", "Edge/126", "curl/8.4", "PostmanRuntime/7.39"]),
            "status": "success" if success else "failed",
            "failure_reason": failure_reason,
            "mfa_required": RNG.random() < 0.38,
            "risk_score": RNG.randint(1, 100) if not success else RNG.randint(1, 45),
            "created_at": iso(created),
        })

    for i in range(COUNTS["password_reset_requests"]):
        user = RNG.choice(state.users)
        created = biased_timestamp()
        status = choose_weighted(["requested", "used", "expired", "revoked", "invalidated"], [30, 48, 14, 5, 3])
        used = created + timedelta(minutes=RNG.randint(2, 60)) if status == "used" else None
        writer.emit("password_reset_requests", {
            "id": uid(),
            "tenant_id": user["tenant_id"],
            "user_id": user["id"],
            "email": user["email"],
            "token_hash": hash_value("pr", f"{user['id']}:{i}"),
            "status": status,
            "requested_ip": rand_ip(),
            "expires_at": iso(created + timedelta(hours=2)),
            "used_at": iso(used),
            "created_at": iso(created),
        })

    status_weights = {200: 73, 201: 7, 204: 4, 400: 4, 401: 3, 403: 2, 404: 2, 409: 1, 422: 2, 429: 1, 500: 1}
    status_codes = list(status_weights)
    weights = list(status_weights.values())
    for i in range(COUNTS["api_request_logs"]):
        tenant = tenant_for(state)
        user = user_for(state, tenant["id"])
        method, path = RNG.choice(ENDPOINTS)
        code = RNG.choices(status_codes, weights=weights, k=1)[0]
        created = biased_timestamp()
        error = None if code < 400 else RNG.choice(["validation_error", "auth_failed", "rate_limited", "upstream_timeout", "not_found"])
        writer.emit("api_request_logs", {
            "id": uid(),
            "tenant_id": tenant["id"],
            "user_id": user["id"] if user and RNG.random() > 0.08 else None,
            "method": method,
            "path": path,
            "status_code": code,
            "request_body": {
                "request_id": uid(),
                "tenant_id": tenant["id"],
                "sample": RNG.random() < 0.04,
            },
            "response_body": {"ok": code < 400, "error": error, "records": RNG.randint(0, 100) if code < 400 else 0},
            "ip_address": rand_ip(),
            "user_agent": RNG.choice(["FolleiWeb/1.0", "FolleiSDK-Python/0.8", "Chrome/126", "PostmanRuntime/7.39"]),
            "duration_ms": int(RNG.lognormvariate(5.4, 0.55)) + (RNG.randint(800, 4000) if code >= 500 else 0),
            "created_at": iso(created),
        })

    audit_actions = ["created", "updated", "deleted", "archived", "exported", "login", "logout", "permission_changed"]
    entity_types = ["user", "agent", "project", "task", "document", "conversation", "tenant_api_key", "report"]
    for i in range(COUNTS["audit_logs"]):
        tenant = tenant_for(state)
        user = user_for(state, tenant["id"])
        entity_type = RNG.choice(entity_types)
        entity_id = (project_for(state, tenant["id"]) or {}).get("id") if entity_type == "project" else uid()
        action = RNG.choice(audit_actions)
        created = biased_timestamp()
        writer.emit("audit_logs", {
            "id": uid(),
            "tenant_id": tenant["id"],
            "user_id": user["id"] if user else None,
            "action": action,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "metadata": {"ip_address": rand_ip(), "source": RNG.choice(["web", "api", "system"])},
            "created_at": iso(created),
            "resource_type": entity_type,
            "resource_id": entity_id,
            "payload": {"before": {}, "after": {"action": action}, "compliance_hold": RNG.random() < 0.02},
        })

    metrics = [
        "daily_active_users", "monthly_active_users", "session_duration_seconds",
        "login_frequency", "api_calls", "error_rate", "lead_conversion_rate",
        "trial_to_paid_conversion", "retention_rate", "churn_rate", "messages_sent",
        "agent_resolution_rate", "document_index_success_rate",
    ]
    for i in range(COUNTS["analytics_daily"]):
        tenant = state.tenants[i % len(state.tenants)]
        metric = metrics[i % len(metrics)]
        metric_date = (NOW - timedelta(days=RNG.randint(0, 364))).date()
        base = RNG.randint(20, 2_000)
        if "rate" in metric:
            value = round(RNG.uniform(0.01, 0.98), 4)
        elif "duration" in metric:
            value = RNG.randint(40, 2400)
        else:
            value = int(base * (1.25 if metric_date.weekday() < 5 else 0.62))
        writer.emit("analytics_daily", {
            "id": uid(),
            "tenant_id": tenant["id"],
            "metric_date": iso(metric_date),
            "metric_name": metric,
            "metric_value": value,
            "dimensions": {"channel": RNG.choice(CHANNELS), "plan": tenant["plan"], "industry": tenant["industry"]},
            "created_at": iso(NOW),
        })

    for i in range(COUNTS["analytics_monthly"]):
        tenant = state.tenants[i % len(state.tenants)]
        months_back = RNG.randint(0, 11)
        month_date = date(NOW.year, NOW.month, 1)
        month = month_date - timedelta(days=months_back * 30)
        month = date(month.year, month.month, 1)
        metric = metrics[i % len(metrics)]
        value = round(RNG.uniform(0.02, 0.95), 4) if "rate" in metric else RNG.randint(300, 80_000)
        writer.emit("analytics_monthly", {
            "id": uid(),
            "tenant_id": tenant["id"],
            "metric_month": iso(month),
            "metric_name": metric,
            "metric_value": value,
            "dimensions": {"plan": tenant["plan"], "segment": RNG.choice(["smb", "mid_market", "enterprise"])},
            "created_at": iso(NOW),
        })

    for i in range(COUNTS["token_usage"]):
        tenant = tenant_for(state)
        user = user_for(state, tenant["id"])
        agent = agent_for(state, tenant["id"])
        writer.emit("token_usage", {
            "id": uid(),
            "tenant_id": tenant["id"],
            "user_id": user["id"] if user else None,
            "agent_id": agent["id"] if agent else None,
            "model": RNG.choice(MODELS),
            "token_type": RNG.choice(["prompt", "completion", "embedding", "rerank"]),
            "quantity": RNG.randint(64, 16_000),
            "created_at": iso(biased_timestamp()),
        })


def generate_reports_and_invalids(writer: DatasetWriter, state: State) -> None:
    for i in range(COUNTS["reports"]):
        tenant = state.tenants[i % len(state.tenants)]
        user = user_for(state, tenant["id"])
        project = project_for(state, tenant["id"])
        created = biased_timestamp()
        period_end = created.date()
        period_start = period_end - timedelta(days=RNG.choice([7, 30, 90]))
        status = choose_weighted(["generated", "queued", "failed", "expired", "deleted"], [74, 8, 8, 6, 4])
        deleted = created + timedelta(days=RNG.randint(10, 120)) if status == "deleted" else None
        writer.emit("reports", {
            "id": uid(),
            "tenant_id": tenant["id"],
            "created_by": user["id"] if user else None,
            "project_id": project["id"] if project else None,
            "report_type": RNG.choice(["usage", "security", "conversion", "retention", "agent_performance", "billing"]),
            "title": f"{RNG.choice(['Weekly', 'Monthly', 'Quarterly'])} {tenant['industry']} Report {i:05d}",
            "status": status,
            "period_start": iso(period_start),
            "period_end": iso(period_end),
            "metrics": {
                "dau": RNG.randint(5, 1800),
                "mau": RNG.randint(100, 45_000),
                "api_calls": RNG.randint(500, 500_000),
                "error_rate": round(RNG.uniform(0.001, 0.08), 4),
                "retention_rate": round(RNG.uniform(0.45, 0.97), 4),
            },
            "file_url": f"https://reports.example.com/{tenant['slug']}/report-{i:05d}.pdf" if status == "generated" else None,
            "generated_at": iso(created + timedelta(minutes=RNG.randint(1, 30))) if status == "generated" else None,
            "deleted_at": iso(deleted),
            "created_at": iso(created),
        })

    scenarios = [
        ("users", "duplicate_email", {"email": "duplicate@example.com"}, "unique_violation"),
        ("users", "invalid_email", {"email": "not-an-email"}, "format_validation_error"),
        ("api_request_logs", "oversized_payload", {"body": "x" * 128}, "payload_too_large"),
        ("file_uploads", "blocked_mime_type", {"mime_type": "application/x-msdownload"}, "unsupported_file_type"),
        ("login_attempts", "credential_stuffing", {"attempts": 220}, "rate_limit"),
        ("projects", "past_due_deleted_project", {"deleted_at": iso(NOW), "status": "active"}, "state_conflict"),
    ]
    for i in range(COUNTS["invalid_test_records"]):
        tenant = state.tenants[i % len(state.tenants)]
        source_table, scenario, raw, error = RNG.choice(scenarios)
        writer.emit("invalid_test_records", {
            "id": uid(),
            "tenant_id": tenant["id"],
            "source_table": source_table,
            "scenario": scenario,
            "raw_payload": {**raw, "row_number": i, "tenant_id": tenant["id"]},
            "validation_error": error,
            "expected_handling": RNG.choice(["reject", "quarantine", "deduplicate", "soft_delete", "alert_security"]),
            "created_at": iso(biased_timestamp()),
        })


def write_database_schema() -> None:
    schema_text = SOURCE_SCHEMA.read_text(encoding="utf-8")
    supplemental = """

-- Supplemental dataset tables for project, report, file upload, security, and QA scenarios.
CREATE TABLE IF NOT EXISTS projects (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    owner_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    agent_id UUID REFERENCES agents(id) ON DELETE SET NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(80) NOT NULL,
    priority VARCHAR(40) NOT NULL,
    budget_usd NUMERIC(14, 2),
    starts_at TIMESTAMPTZ,
    due_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    deleted_at TIMESTAMPTZ,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS activities (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    project_id UUID REFERENCES projects(id) ON DELETE SET NULL,
    task_id UUID REFERENCES agent_tasks(id) ON DELETE SET NULL,
    activity_type VARCHAR(120) NOT NULL,
    channel VARCHAR(80),
    status VARCHAR(80) NOT NULL,
    description TEXT,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS file_uploads (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    project_id UUID REFERENCES projects(id) ON DELETE SET NULL,
    document_id UUID REFERENCES documents(id) ON DELETE SET NULL,
    file_name VARCHAR(255),
    mime_type VARCHAR(160),
    file_size_bytes BIGINT,
    storage_path TEXT,
    checksum VARCHAR(64),
    scan_status VARCHAR(80),
    status VARCHAR(80),
    deleted_at TIMESTAMPTZ,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS reports (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    project_id UUID REFERENCES projects(id) ON DELETE SET NULL,
    report_type VARCHAR(120) NOT NULL,
    title VARCHAR(255) NOT NULL,
    status VARCHAR(80) NOT NULL,
    period_start DATE,
    period_end DATE,
    metrics JSONB NOT NULL DEFAULT '{}'::jsonb,
    file_url TEXT,
    generated_at TIMESTAMPTZ,
    deleted_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS login_attempts (
    id UUID PRIMARY KEY,
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    email VARCHAR(320),
    ip_address INET,
    user_agent TEXT,
    status VARCHAR(80) NOT NULL,
    failure_reason VARCHAR(160),
    mfa_required BOOLEAN NOT NULL DEFAULT FALSE,
    risk_score INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS password_reset_requests (
    id UUID PRIMARY KEY,
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    email VARCHAR(320),
    token_hash TEXT NOT NULL,
    status VARCHAR(80) NOT NULL,
    requested_ip INET,
    expires_at TIMESTAMPTZ NOT NULL,
    used_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS invalid_test_records (
    id UUID PRIMARY KEY,
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    source_table VARCHAR(160) NOT NULL,
    scenario VARCHAR(160) NOT NULL,
    raw_payload JSONB NOT NULL,
    validation_error TEXT NOT NULL,
    expected_handling VARCHAR(120) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_projects_tenant_status ON projects(tenant_id, status);
CREATE INDEX IF NOT EXISTS idx_activities_tenant_created ON activities(tenant_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_file_uploads_tenant_created ON file_uploads(tenant_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_reports_tenant_created ON reports(tenant_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_login_attempts_email_created ON login_attempts(email, created_at DESC);
"""
    (OUT / "database_schema.sql").write_text(schema_text + supplemental, encoding="utf-8")


def read_csv_dict(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def supplemental_dictionary_rows() -> list[dict[str, str]]:
    rows = []
    for table, columns in TABLE_COLUMNS.items():
        if table in {"projects", "activities", "file_uploads", "reports", "login_attempts", "password_reset_requests", "invalid_test_records"}:
            for pos, col in enumerate(columns, start=1):
                dtype = "jsonb" if col in JSON_COLUMNS else "uuid" if col.endswith("_id") or col == "id" else "timestamp with time zone" if col.endswith("_at") else "text"
                rows.append({
                    "table_name": table,
                    "column_name": col,
                    "ordinal_position": str(pos),
                    "data_type": dtype,
                    "udt_name": dtype,
                    "is_nullable": "YES" if col not in {"id", "tenant_id"} else "NO",
                    "column_default": "",
                })
    return rows


def xlsx_col_name(index: int) -> str:
    name = ""
    while index:
        index, rem = divmod(index - 1, 26)
        name = chr(65 + rem) + name
    return name


def sheet_xml(rows: list[list[Any]]) -> str:
    body = []
    for r_idx, row in enumerate(rows, start=1):
        cells = []
        for c_idx, value in enumerate(row, start=1):
            ref = f"{xlsx_col_name(c_idx)}{r_idx}"
            text = "" if value is None else str(value)
            cells.append(f'<c r="{ref}" t="inlineStr"><is><t>{escape(text)}</t></is></c>')
        body.append(f'<row r="{r_idx}">{"".join(cells)}</row>')
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f'<sheetData>{"".join(body)}</sheetData></worksheet>'
    )


def write_xlsx(path: Path, sheets: dict[str, list[list[Any]]]) -> None:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
""" + "".join(f'<Override PartName="/xl/worksheets/sheet{i}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>' for i in range(1, len(sheets) + 1)) + "</Types>")
        zf.writestr("_rels/.rels", """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>""")
        sheet_defs = []
        rel_defs = []
        for i, name in enumerate(sheets, start=1):
            sheet_defs.append(f'<sheet name="{escape(name)}" sheetId="{i}" r:id="rId{i}"/>')
            rel_defs.append(f'<Relationship Id="rId{i}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{i}.xml"/>')
        zf.writestr("xl/workbook.xml", """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets>""" + "".join(sheet_defs) + "</sheets></workbook>")
        zf.writestr("xl/_rels/workbook.xml.rels", """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">""" + "".join(rel_defs) + "</Relationships>")
        for i, rows in enumerate(sheets.values(), start=1):
            zf.writestr(f"xl/worksheets/sheet{i}.xml", sheet_xml(rows))


def write_dictionary_and_er(counts: dict[str, int]) -> None:
    columns = read_csv_dict(SCHEMA_EXPORTS / "columns.csv") + supplemental_dictionary_rows()
    relations = read_csv_dict(SCHEMA_EXPORTS / "relations.csv")
    supplemental_relations = [
        ("projects", "tenant_id", "tenants", "id"), ("projects", "owner_user_id", "users", "id"),
        ("projects", "agent_id", "agents", "id"), ("activities", "project_id", "projects", "id"),
        ("activities", "task_id", "agent_tasks", "id"), ("file_uploads", "project_id", "projects", "id"),
        ("file_uploads", "document_id", "documents", "id"), ("reports", "project_id", "projects", "id"),
        ("reports", "created_by", "users", "id"), ("login_attempts", "user_id", "users", "id"),
        ("password_reset_requests", "user_id", "users", "id"),
    ]
    for table, column, ref_table, ref_col in supplemental_relations:
        relations.append({
            "table_name": table,
            "column_name": column,
            "references_table": ref_table,
            "references_column": ref_col,
            "update_rule": "NO ACTION",
            "delete_rule": "SET NULL" if column != "tenant_id" else "CASCADE",
            "constraint_name": f"{table}_{column}_fkey",
        })

    table_rows = [["table_name", "generated_rows", "purpose"]]
    purpose = {
        "tenants": "Organizations and tenant isolation root",
        "users": "Application users across active, inactive, invited, locked, and deleted states",
        "agent_tasks": "Task workflow table used as Follei's operational task surface",
        "projects": "Supplemental project/workstream table for test planning and load scenarios",
        "api_request_logs": "Realistic API observability logs with request/response bodies and failures",
        "analytics_daily": "Daily product, conversion, retention, API, and error metrics",
    }
    for table in sorted(TABLE_COLUMNS):
        table_rows.append([table, counts.get(table, 0), purpose.get(table, "Synthetic production-style relational data")])

    column_rows = [["table_name", "column_name", "data_type", "nullable", "default", "generated_notes"]]
    for row in columns:
        table = row["table_name"]
        if table in TABLE_COLUMNS or table in {"leads", "customers", "documents", "conversations"}:
            column_rows.append([
                table, row["column_name"], row["data_type"], row["is_nullable"],
                row.get("column_default", ""),
                "Uses deterministic generation with tenant-aware relationships" if table in TABLE_COLUMNS else "Source schema column",
            ])

    relation_rows = [["from_table", "from_column", "to_table", "to_column", "delete_rule"]]
    for rel in relations:
        if rel["table_name"] in TABLE_COLUMNS or rel["references_table"] in TABLE_COLUMNS:
            relation_rows.append([rel["table_name"], rel["column_name"], rel["references_table"], rel["references_column"], rel["delete_rule"]])

    rules_rows = [
        ["rule", "implementation"],
        ["History window", "Last 12 months ending 2026-06-22"],
        ["Peak usage", "Timestamps are biased toward weekday business hours and late-afternoon support peaks"],
        ["Security", "Includes success/failure login attempts, locked users, MFA, refresh tokens, reset requests"],
        ["Errors", "API logs include 4xx/5xx statuses, validation errors, rate limits, and upstream timeouts"],
        ["Edge cases", "invalid_test_records stores duplicate, invalid, oversized, blocked, and state-conflict records"],
        ["Soft delete", "Projects, reports, file uploads, documents, users use status/deleted metadata"],
    ]
    write_xlsx(OUT / "data_dictionary.xlsx", {
        "Tables": table_rows,
        "Columns": column_rows,
        "Relationships": relation_rows,
        "GenerationRules": rules_rows,
    })

    er = {
        "application": "Follei autonomous business operating system",
        "generated_at": iso(NOW),
        "source_schema_exports": {
            "columns": str(SCHEMA_EXPORTS / "columns.csv"),
            "relations": str(SCHEMA_EXPORTS / "relations.csv"),
            "indexes": str(SCHEMA_EXPORTS / "indexes.csv"),
        },
        "nodes": [
            {
                "table": table,
                "columns": TABLE_COLUMNS[table],
                "generated_rows": counts.get(table, 0),
                "domain": domain_for_table(table),
            }
            for table in sorted(TABLE_COLUMNS)
        ],
        "edges": [
            {
                "from": f"{rel['table_name']}.{rel['column_name']}",
                "to": f"{rel['references_table']}.{rel['references_column']}",
                "relationship": "many-to-one",
                "delete_rule": rel["delete_rule"],
            }
            for rel in relations
            if rel["table_name"] in TABLE_COLUMNS or rel["references_table"] in TABLE_COLUMNS
        ],
        "logical_mappings": {
            "Organizations/Tenants": "tenants",
            "Projects": "projects",
            "Tasks": "agent_tasks",
            "Activities": "activities",
            "Chat Messages": "conversation_messages",
            "File Uploads": "file_uploads plus documents",
            "Reports": "reports",
            "Security Dataset": "login_attempts, user_sessions, refresh_tokens, password_reset_requests, token_usage",
        },
    }
    (OUT / "er_diagram_structure.json").write_text(json.dumps(er, indent=2), encoding="utf-8")


def domain_for_table(table: str) -> str:
    if table in {"tenants", "users", "roles", "permissions", "user_auth", "user_roles", "user_sessions", "refresh_tokens", "tenant_api_keys"}:
        return "Identity and Tenancy"
    if table in {"agents", "agent_tasks", "projects", "activities"}:
        return "AI Workforce and Workflow"
    if table in {"conversations", "conversation_messages", "notifications"}:
        return "Conversations and Collaboration"
    if table in {"documents", "file_uploads"}:
        return "Knowledge and Files"
    if table in {"api_request_logs", "audit_logs", "login_attempts", "password_reset_requests", "invalid_test_records"}:
        return "Security and Observability"
    if table in {"reports", "analytics_daily", "analytics_monthly", "token_usage"}:
        return "Analytics and Reporting"
    return "Application"


def write_samples_and_manifest(writer: DatasetWriter) -> None:
    sample_payload = {
        "generated_at": iso(NOW),
        "row_counts": dict(sorted(writer.counts.items())),
        "samples_per_table": 100,
        "data": writer.samples,
    }
    (OUT / "sample_data.json").write_text(json.dumps(sample_payload, indent=2), encoding="utf-8")
    manifest = {
        "generated_at": iso(NOW),
        "seed": 20260622,
        "history_window": {"start": iso(START), "end": iso(NOW)},
        "row_counts": dict(sorted(writer.counts.items())),
        "files": {
            "database_schema": "database_schema.sql",
            "json_sample": "sample_data.json",
            "csv_sample": "sample_data.csv",
            "full_csv_directory": "csv/",
            "sql_insert_scripts": "sql_insert_scripts.sql",
            "data_dictionary": "data_dictionary.xlsx",
            "er_diagram": "er_diagram_structure.json",
        },
        "workload_characteristics": [
            "Tenant-isolated data with app-compatible foreign keys",
            "12 months of biased real-time timestamps with peak usage hours",
            "Successful and failed transactions across auth, API, uploads, reports, and tasks",
            "Soft-deleted, inactive, duplicate-candidate, invalid, and quarantined test scenarios",
            "Analytics metrics for DAU, MAU, session duration, API calls, error rates, conversion, and retention",
        ],
    }
    (OUT / "dataset_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def main() -> None:
    writer = DatasetWriter()
    state = State()
    try:
        generate_core(writer, state)
        generate_workflows(writer, state)
        generate_messages_and_files(writer, state)
        generate_security_api_analytics(writer, state)
        generate_reports_and_invalids(writer, state)
    finally:
        writer.close()
    write_database_schema()
    write_dictionary_and_er(writer.counts)
    write_samples_and_manifest(writer)
    print(json.dumps({"output_dir": str(OUT), "row_counts": dict(sorted(writer.counts.items()))}, indent=2))


if __name__ == "__main__":
    main()
