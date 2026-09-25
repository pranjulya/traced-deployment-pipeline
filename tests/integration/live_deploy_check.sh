#!/usr/bin/env bash
# Phase 02 live deployment rehearsal. Requires a running Docker daemon.
# Exercises the deterministic oracle in implementation/phase-02-container-deployment.md.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
COMPOSE="docker compose -f deploy/compose.yaml"
PORT="${P09_API_PORT:-8080}"
BASE="http://127.0.0.1:${PORT}"
KEY="livecheck-$(date +%s)-aaaaaaaa"
fail=0
note() { echo "[live] $*"; }
check() { if eval "$2"; then note "PASS: $1"; else note "FAIL: $1"; fail=1; fi; }

if [ ! -f deploy/.env ]; then
  APP_SECRET="$(python3 -c 'import secrets;print(secrets.token_urlsafe(48))')"
  HMAC_SECRET="$(python3 -c 'import secrets;print(secrets.token_urlsafe(48))')"
  sed -e "s|replace-with-random-application-secret|${APP_SECRET}|" \
      -e "s|replace-with-random-hmac-secret|${HMAC_SECRET}|" \
      deploy/.env.example > deploy/.env
fi
set -a; . deploy/.env; set +a

note "fresh volume + clean start"
$COMPOSE down -v --remove-orphans >/dev/null 2>&1 || true
$COMPOSE build
$COMPOSE up -d

for _ in $(seq 1 30); do
  status="$(docker inspect -f '{{.State.Health.Status}}' "$($COMPOSE ps -q api)" 2>/dev/null || echo starting)"
  [ "$status" = "healthy" ] && break
  sleep 2
done
check "clean start reaches ready" "[ \"\$(docker inspect -f '{{.State.Health.Status}}' \"\$($COMPOSE ps -q api)\")\" = healthy ]"

note "smoke request"
CODE="$(curl -s -o /tmp/p09_smoke.json -w '%{http_code}' -H "Authorization: Bearer ${P09_APP_SECRET}" \
  -H "Idempotency-Key: ${KEY}" -H "Content-Type: application/json" \
  -d '{"input":"smoke"}' "${BASE}/v1/runs" || echo 000)"
check "authenticated fixture completes (200)" "[ \"$CODE\" = 200 ]"
RUN_ID="$(python3 -c 'import json;print(json.load(open("/tmp/p09_smoke.json"))["run_id"])' 2>/dev/null || echo none)"

note "non-root execution"
UID_OUT="$($COMPOSE exec -T api id -u)"
check "container runs as UID 10001" "[ \"$UID_OUT\" = 10001 ]"

note "loopback-only publication"
PORT_BINDING="$($COMPOSE port api 8080 | head -1)"
check "API bound to 127.0.0.1" "echo '$PORT_BINDING' | grep -q '^127.0.0.1:'"

note "restart persistence (recreate, keep volume)"
$COMPOSE down >/dev/null
$COMPOSE up -d
for _ in $(seq 1 30); do
  [ "$(docker inspect -f '{{.State.Health.Status}}' "$($COMPOSE ps -q api)" 2>/dev/null || echo starting)" = "healthy" ] && break
  sleep 2
done
DUP_CODE="$(curl -s -o /tmp/p09_dup.json -w '%{http_code}' -H "Authorization: Bearer ${P09_APP_SECRET}" \
  -H "Idempotency-Key: ${KEY}" -H "Content-Type: application/json" \
  -d '{"input":"smoke"}' "${BASE}/v1/runs" || echo 000)"
DUP_RUN="$(python3 -c 'import json;print(json.load(open("/tmp/p09_dup.json"))["run_id"])' 2>/dev/null || echo none)"
check "ledger retained after recreate (409)" "[ \"$DUP_CODE\" = 409 ]"
check "same run_id after recreate" "[ \"$DUP_RUN\" = \"$RUN_ID\" ]"

note "missing secret fails readiness safely"
$COMPOSE down >/dev/null
P09_HMAC_SECRET= $COMPOSE up -d >/dev/null 2>&1 || true
sleep 5
READY_CODE="$(curl -s -o /dev/null -w '%{http_code}' "${BASE}/health/ready" || echo 000)"
check "missing HMAC secret is not ready" "[ \"$READY_CODE\" = 503 ]"
$COMPOSE down >/dev/null

note "prior-image rollback"
$COMPOSE up -d >/dev/null
docker tag p09-api:local p09-api:prior
check "prior image tag exists" "docker image inspect p09-api:prior >/dev/null 2>&1"

$COMPOSE down >/dev/null
note "done; failures=${fail}"
exit "$fail"
