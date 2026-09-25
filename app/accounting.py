"""Durable usage ledger: run registry and per-attempt accounting.

SQLite in WAL mode, one connection guarded by a lock. Commit paths raise
LedgerUnavailable so callers can withhold output and preserve uncertainty.
See docs/architecture/accounting-and-api-contract.md.
"""

import sqlite3
import threading
import uuid
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from .money import format_nano

SCHEMA = """
CREATE TABLE IF NOT EXISTS run_registry (
    run_id TEXT PRIMARY KEY,
    principal_alias TEXT NOT NULL,
    key_digest TEXT NOT NULL,
    admitted_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    state TEXT NOT NULL,
    safe_outcome_code TEXT,
    completed_at TEXT,
    UNIQUE (principal_alias, key_digest)
);
CREATE TABLE IF NOT EXISTS usage_attempt (
    attempt_id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES run_registry(run_id),
    ordinal INTEGER NOT NULL,
    provider TEXT NOT NULL,
    model TEXT NOT NULL,
    started_at TEXT NOT NULL,
    ended_at TEXT,
    status TEXT NOT NULL,
    input_tokens INTEGER,
    output_tokens INTEGER,
    usage_origin TEXT NOT NULL,
    price_version TEXT,
    currency TEXT,
    charge TEXT,
    charge_state TEXT NOT NULL,
    UNIQUE (run_id, ordinal)
);
"""

ZERO = format_nano(Decimal(0))


class LedgerUnavailable(RuntimeError):
    """Raised when a durable ledger commit cannot complete."""


def _utcnow():
    return datetime.now(timezone.utc)


def _iso(value):
    return value.astimezone(timezone.utc).isoformat()


class Ledger:
    def __init__(self, db_path, registry_ttl_seconds=24 * 60 * 60):
        self.db_path = db_path
        self.registry_ttl_seconds = registry_ttl_seconds
        self._lock = threading.RLock()
        self._conn = sqlite3.connect(db_path, check_same_thread=False, isolation_level=None)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA busy_timeout=5000")
        self._conn.execute("PRAGMA foreign_keys=ON")
        with self._lock:
            self._conn.executescript(SCHEMA)

    def close(self):
        with self._lock:
            self._conn.close()

    def is_writable(self):
        """Readiness requires a writable ledger; telemetry availability does not affect it."""
        try:
            with self._transaction():
                pass
            return True
        except LedgerUnavailable:
            return False

    @contextmanager
    def _transaction(self):
        with self._lock:
            try:
                self._conn.execute("BEGIN IMMEDIATE")
            except sqlite3.Error as exc:  # pragma: no cover - environment specific
                raise LedgerUnavailable(str(exc)) from exc
            try:
                yield self._conn
            except sqlite3.Error as exc:
                self._conn.execute("ROLLBACK")
                raise LedgerUnavailable(str(exc)) from exc
            except Exception:
                self._conn.execute("ROLLBACK")
                raise
            else:
                self._conn.execute("COMMIT")

    # -- admission ---------------------------------------------------------
    def get_run(self, run_id):
        with self._lock:
            row = self._conn.execute(
                "SELECT * FROM run_registry WHERE run_id=?", (run_id,)
            ).fetchone()
        return dict(row) if row else None

    def get_run_by_key(self, principal_alias, key_digest):
        with self._lock:
            row = self._conn.execute(
                "SELECT * FROM run_registry WHERE principal_alias=? AND key_digest=?",
                (principal_alias, key_digest),
            ).fetchone()
        return dict(row) if row else None

    def admit(self, principal_alias, key_digest, now=None):
        """Atomically admit a run. Returns (run_id, None) or (None, existing_row)."""
        now = now or _utcnow()
        run_id = str(uuid.uuid4())
        with self._transaction() as conn:
            existing = conn.execute(
                "SELECT * FROM run_registry WHERE principal_alias=? AND key_digest=?",
                (principal_alias, key_digest),
            ).fetchone()
            if existing:
                return None, dict(existing)
            conn.execute(
                "INSERT INTO run_registry (run_id, principal_alias, key_digest, admitted_at, expires_at, state)"
                " VALUES (?,?,?,?,?,?)",
                (
                    run_id,
                    principal_alias,
                    key_digest,
                    _iso(now),
                    _iso(now + timedelta(seconds=self.registry_ttl_seconds)),
                    "accepted",
                ),
            )
        return run_id, None

    # -- attempts ----------------------------------------------------------
    def create_pending_attempt(self, run_id, ordinal, provider, model, now=None):
        now = now or _utcnow()
        attempt_id = str(uuid.uuid4())
        with self._transaction() as conn:
            conn.execute(
                "INSERT INTO usage_attempt (attempt_id, run_id, ordinal, provider, model,"
                " started_at, status, usage_origin, charge_state) VALUES (?,?,?,?,?,?,?,?,?)",
                (attempt_id, run_id, ordinal, provider, model, _iso(now), "pending", "unknown", "unknown"),
            )
            conn.execute(
                "UPDATE run_registry SET state='running' WHERE run_id=? AND state IN ('accepted','running')",
                (run_id,),
            )
        return attempt_id

    def complete_attempt(self, attempt_id, *, input_tokens, output_tokens, usage_origin,
                         currency, charge, charge_state, price_version, now=None):
        now = now or _utcnow()
        with self._transaction() as conn:
            conn.execute(
                "UPDATE usage_attempt SET ended_at=?, status='completed', input_tokens=?, output_tokens=?,"
                " usage_origin=?, currency=?, charge=?, charge_state=?, price_version=? WHERE attempt_id=?",
                (_iso(now), input_tokens, output_tokens, usage_origin, currency, charge, charge_state,
                 price_version, attempt_id),
            )

    def fail_attempt(self, attempt_id, *, usage_origin="provider", currency, now=None):
        """A provider error known not to have processed the request: observed zero."""
        now = now or _utcnow()
        with self._transaction() as conn:
            conn.execute(
                "UPDATE usage_attempt SET ended_at=?, status='failed', input_tokens=NULL, output_tokens=NULL,"
                " usage_origin=?, currency=?, charge=?, charge_state='observed' WHERE attempt_id=?",
                (_iso(now), usage_origin, currency, ZERO, attempt_id),
            )

    def unknown_attempt(self, attempt_id, now=None):
        now = now or _utcnow()
        with self._transaction() as conn:
            conn.execute(
                "UPDATE usage_attempt SET ended_at=?, status='unknown', input_tokens=NULL, output_tokens=NULL,"
                " usage_origin='unknown', charge=NULL, charge_state='unknown' WHERE attempt_id=?",
                (_iso(now), attempt_id),
            )

    # -- run state ---------------------------------------------------------
    def set_run_state(self, run_id, state, safe_outcome_code=None, now=None):
        now = now or _utcnow()
        completed = _iso(now) if state in ("completed", "failed", "accounting_unknown") else None
        with self._transaction() as conn:
            conn.execute(
                "UPDATE run_registry SET state=?, safe_outcome_code=?, completed_at=? WHERE run_id=?",
                (state, safe_outcome_code, completed, run_id),
            )

    def attempts_for(self, run_id):
        with self._lock:
            rows = self._conn.execute(
                "SELECT * FROM usage_attempt WHERE run_id=? ORDER BY ordinal", (run_id,)
            ).fetchall()
        return [dict(r) for r in rows]

    def run_totals(self, run_id):
        totals = {}
        for attempt in self.attempts_for(run_id):
            if attempt["charge_state"] == "unknown" or attempt["charge"] is None:
                continue
            totals[attempt["currency"]] = totals.get(attempt["currency"], Decimal(0)) + Decimal(attempt["charge"])
        return {currency: format_nano(value) for currency, value in totals.items()}

    # -- restart classification -------------------------------------------
    def recover_on_startup(self, now=None):
        now = now or _utcnow()
        with self._transaction() as conn:
            runs = conn.execute(
                "SELECT run_id FROM run_registry WHERE state IN ('accepted','running')"
            ).fetchall()
            actions = []
            for row in runs:
                run_id = row["run_id"]
                pending = conn.execute(
                    "SELECT COUNT(*) AS n FROM usage_attempt WHERE run_id=? AND status='pending'",
                    (run_id,),
                ).fetchone()["n"]
                if pending:
                    conn.execute(
                        "UPDATE usage_attempt SET status='unknown', ended_at=?, usage_origin='unknown',"
                        " charge=NULL, charge_state='unknown' WHERE run_id=? AND status='pending'",
                        (_iso(now), run_id),
                    )
                    conn.execute(
                        "UPDATE run_registry SET state='accounting_unknown', completed_at=? WHERE run_id=?",
                        (_iso(now), run_id),
                    )
                    actions.append((run_id, "accounting_unknown"))
                else:
                    conn.execute(
                        "UPDATE run_registry SET state='failed', completed_at=? WHERE run_id=?",
                        (_iso(now), run_id),
                    )
                    actions.append((run_id, "failed"))
        return actions
