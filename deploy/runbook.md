# Deployment runbook — single-host reference (P09)

Scope: one macOS reference host running Docker Desktop (arm64 Linux container
runtime). This is a reproducible reference deployment, not a high-availability
service. All commands run from the repository root.

## 0. Prerequisites
- Docker Desktop running; at least 4 vCPU / 8 GB allocated (one API container is capped at 1 CPU / 512 MB).
- `deploy/.env` created from `deploy/.env.example` with strong random secrets:
  `python3 -c "import secrets;print(secrets.token_urlsafe(48))"`
- Never commit `deploy/.env`.

## 1. Fresh-volume bootstrap and clean start
```
cp deploy/.env.example deploy/.env   # then edit in strong secrets
docker compose -f deploy/compose.yaml build
docker compose -f deploy/compose.yaml up -d
docker compose -f deploy/compose.yaml ps      # wait for healthy
```
Readiness (`/health/ready`) requires valid secrets and a writable ledger; it
does not depend on telemetry. `docker compose up -d` only reaches `healthy`
when the ledger volume is writable.

## 2. Smoke check
```
set -a; . deploy/.env; set +a
curl -sf -H "Authorization: Bearer $P09_APP_SECRET" \
     -H "Idempotency-Key: smoke-$(date +%s)-aaaaaaaa" \
     -H "Content-Type: application/json" \
     -d '{"input":"smoke"}' http://127.0.0.1:${P09_API_PORT:-8080}/v1/runs
```
A duplicate of the same key returns `409 DUPLICATE_REQUEST` with the original
`run_id` and never re-dispatches.

## 3. Restart / recreate persistence
```
docker compose -f deploy/compose.yaml down      # keep the named volume
docker compose -f deploy/compose.yaml up -d
```
The ledger volume survives; the same idempotency key still returns `409`.
`down -v` deletes the ledger and is never part of a routine restart.

## 4. Consistent backup
SQLite must be backed up with the online backup API, never a raw copy of a live
WAL file:
```
deploy/backup-ledger.sh
```

## 5. Prior-image rollback
```
docker tag p09-api:local p09-api:prior            # stage before a change
# ... build and deploy the new image ...
# rollback:
docker compose -f deploy/compose.yaml down
# point the service image at p09-api:prior, then:
docker compose -f deploy/compose.yaml up -d
```
Rollback is only safe when the prior image is compatible with the current
ledger schema. If a schema migration is not backward compatible, restore the
tested backup first; the runbook must refuse an unsafe downgrade rather than
run it.

## 6. Ledger schema migration policy
- Migrations are additive and backward compatible by default.
- Before accepting a schema change, rehearse: back up, deploy the new image,
  verify smoke + totals, then deploy the prior image and verify totals again.
- A change that cannot be reversed requires its own tested backup and an
  explicit, reviewed exception.

## 7. Bounds and exposure (verify)
- No public admin ports: only `127.0.0.1:${P09_API_PORT:-8080}` is published.
- The `telemetry` network is `internal: true`.
- Container runs as UID/GID 10001 (non-root), `read_only` root filesystem,
  `cap_drop: ALL`, `no-new-privileges`, 1 CPU / 512 MB limit.
- Secrets are injected via `env_file`; none are baked into the image.

## 8. Teardown
```
docker compose -f deploy/compose.yaml down      # add -v only to discard the ledger
```
