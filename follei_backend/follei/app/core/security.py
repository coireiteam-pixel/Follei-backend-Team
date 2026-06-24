import base64
import hashlib
import hmac
import json
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any


SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
HASH_ITERATIONS = 120_000


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        HASH_ITERATIONS,
    ).hex()
    return f"pbkdf2_sha256${HASH_ITERATIONS}${salt}${digest}"


def verify_password(password: str, password_hash: str) -> bool:
    if password_hash.startswith("dev:"):
        return hmac.compare_digest(password_hash, f"dev:{password}")

    try:
        algorithm, iterations, salt, expected = password_hash.split("$", 3)
    except ValueError:
        return False

    if algorithm != "pbkdf2_sha256":
        return False

    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        int(iterations),
    ).hex()
    return hmac.compare_digest(digest, expected)


def create_access_token(data: dict[str, Any] | str, tenant_id: str | None = None) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    if isinstance(data, dict):
        payload = data.copy()
    else:
        if tenant_id is None:
            raise ValueError("tenant_id is required when creating a token from a user id")
        payload = {"sub": str(data), "tenant_id": str(tenant_id)}

    payload["sub"] = str(payload["sub"])
    payload["tenant_id"] = str(payload["tenant_id"])
    payload["exp"] = int(expires_at.timestamp())
    return _encode_jwt(payload)


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        header_b64, payload_b64, signature_b64 = token.split(".", 2)
    except ValueError as exc:
        raise ValueError("Invalid token") from exc

    header = json.loads(_base64url_decode(header_b64))
    if header.get("alg") != ALGORITHM:
        raise ValueError("Invalid token")

    message = f"{header_b64}.{payload_b64}".encode("utf-8")
    expected_signature = _sign(message)
    actual_signature = _base64url_decode(signature_b64)
    if not hmac.compare_digest(actual_signature, expected_signature):
        raise ValueError("Invalid token")

    payload = json.loads(_base64url_decode(payload_b64))
    if int(payload.get("exp", 0)) < int(datetime.now(timezone.utc).timestamp()):
        raise ValueError("Token expired")
    return payload


def _encode_jwt(payload: dict[str, Any]) -> str:
    header = {"alg": ALGORITHM, "typ": "JWT"}
    header_b64 = _base64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_b64 = _base64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    message = f"{header_b64}.{payload_b64}".encode("utf-8")
    signature_b64 = _base64url_encode(_sign(message))
    return f"{header_b64}.{payload_b64}.{signature_b64}"


def _sign(message: bytes) -> bytes:
    if ALGORITHM != "HS256":
        raise ValueError("Only HS256 JWT signing is supported")
    return hmac.new(SECRET_KEY.encode("utf-8"), message, hashlib.sha256).digest()


def _base64url_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _base64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)
