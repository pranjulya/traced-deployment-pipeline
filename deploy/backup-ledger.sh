#!/usr/bin/env bash
# Consistent SQLite backup using the online backup API (never a raw WAL copy).
set -euo pipefail

COMPOSE="docker compose -f $(dirname "$0")/compose.yaml"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
OUTDIR="${1:-./backups}"
mkdir -p "$OUTDIR"

$COMPOSE exec -T api python - "$STAMP" <<'PY'
import sqlite3, sys
stamp = sys.argv[1]
src = sqlite3.connect("/data/p09-ledger.sqlite")
dst = sqlite3.connect(f"/data/backup-ledger-{stamp}.sqlite")
with dst:
    src.backup(dst)
print(f"wrote /data/backup-ledger-{stamp}.sqlite")
PY

$COMPOSE cp "api:/data/backup-ledger-${STAMP}.sqlite" "${OUTDIR}/backup-ledger-${STAMP}.sqlite"
echo "backup saved to ${OUTDIR}/backup-ledger-${STAMP}.sqlite"
