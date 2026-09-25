"""Runtime configuration and bounded limits."""

import os
from dataclasses import dataclass, field

# Idempotency-Key: 16-128 characters from the RFC 4648 URL-safe alphabet.
KEY_MIN = 16
KEY_MAX = 128
KEY_ALPHABET = frozenset(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
)

MAX_BODY_BYTES = 8192
MAX_CONCURRENCY = 10
TOTAL_DEADLINE_SECONDS = 30.0
MAX_PROVIDER_ATTEMPTS = 3
MAX_TOOL_CALLS = 2
REGISTRY_TTL_SECONDS = 24 * 60 * 60

PRINCIPAL_ALIAS = "demo-operator"


@dataclass
class Settings:
    app_secret: str
    hmac_secret: str
    db_path: str
    principal_alias: str = PRINCIPAL_ALIAS
    default_model: str = "fake-small"
    max_body_bytes: int = MAX_BODY_BYTES
    max_concurrency: int = MAX_CONCURRENCY
    total_deadline_seconds: float = TOTAL_DEADLINE_SECONDS
    max_provider_attempts: int = MAX_PROVIDER_ATTEMPTS
    max_tool_calls: int = MAX_TOOL_CALLS
    registry_ttl_seconds: int = REGISTRY_TTL_SECONDS
    extra: dict = field(default_factory=dict)

    @classmethod
    def from_env(cls):
        return cls(
            app_secret=os.environ["P09_APP_SECRET"],
            hmac_secret=os.environ["P09_HMAC_SECRET"],
            db_path=os.environ.get("P09_DB_PATH", "p09-ledger.sqlite"),
        )
