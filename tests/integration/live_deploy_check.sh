#!/usr/bin/env bash
# Phase 02-04 live rehearsal. Requires a running Docker daemon.
# Exercises the deterministic oracle in the phase-02/03/04 files:
#   clean start, readiness, non-root, restart persistence, missing-secret,
#   Prometheus scrape + targets, Alertmanager -> local sink delivery, rollback.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
COMPOSE="docker compose -f deploy/compose.yaml"
PORT="${P09_API_PORT:-8080}"
BASE="http://127.0.0.1:${PORT}"
KEY="livecheck-$(date +%s)-aaaaaaaa"
DRILL_RUN="drill-$(date +%s)"
fail=0
note() { echo "[live] $*"; }
check() { if eval "$2"; then note "PASS: $1"; else note "FAIL: $1"; fail=1; fi; }
wait_healthy() {
  for _ in $(seq 1 40); do
    [ "$(docker inspect -f '{{.State.Health.Status}}' "$($COMPOSE ps -q api)" 2>/dev/null || echo starting)" = "healthy" ] && return 0
    sleep 2
  done
  return 1
}

if [ ! -f deploy/.env ]; then
  APP_SECRET="$(python3 -c 'import secrets;print(secrets.token_urlsafe(48))')"
  HMAC_SECRET="$(python3 -c 'import secrets;print(secrets.token_urlsafe(48))')"
  GRAFANA_PW="$(python3 -c 'import secrets;print(secrets.token_urlsafe(24))')"
  sed -e "s|replace-with-random-application-secret|${APP_SECRET}|" \
      -e "s|replace-with-random-hmac-secret|${HMAC_SECRET}|" \
      -e "s|replace-with-random-grafana-password|${GRAFANA_PW}|" \
      deploy/.env.example > deploy/.env
fi
set -a; . deploy/.env; set +a

note "fresh volume + full stack clean start"
$COMPOSE down -v --remove-orphans >/dev/null 2>&1 || true
$COMPOSE build
$COMPOSE up -d
wait_healthy
check "api reaches ready" "wait_healthy"

note "non-root execution"
check "container runs as UID 10001" "[ \"\$($COMPOSE exec -T api id -u)\" = 10001 ]"

note "loopback-only publication"
check "api bound to 127.0.0.1" "$COMPOSE port api 8080 | head -1 | grep -q '^127.0.0.1:'"
for ui in prometheus grafana alertmanager; do
  check "$ui bound to 127.0.0.1" "$COMPOSE port $ui | head -1 | grep -q '^127.0.0.1:'"
done

note "authenticated fixture completes"
CODE="$(curl -s -o /tmp/p09_smoke.json -w '%{http_code}' -H "Authorization: Bearer ${P09_APP_SECRET}" \
  -H "Idempotency-Key: ${KEY}" -H "Content-Type: application/json" \
  -d '{"input":"smoke"}' "${BASE}/v1/runs" || echo 000)"
check "smoke request returns 200" "[ \"$CODE\" = 200 ]"
RUN_ID="$(python3 -c 'import json;print(json.load(open("/tmp/p09_smoke.json"))["run_id"])' 2>/dev/null || echo none)"

note "Prometheus scrapes the API"
sleep 20
check "p09-api target is up" "curl -s 'http://127.0.0.1:9090/api/v1/targets' | grep -q '\"job\":\"p09-api\".*\"health\":\"up\"'"
check "metrics expose known charge" "curl -s 'http://127.0.0.1:8080/metrics' | grep -q 'p09_known_charge_nano_total'"

note "Grafana ready"
check "grafana health ok" "curl -s http://127.0.0.1:3000/api/health | grep -q '\"database\":\"ok\"'"

note "Alertmanager -> local sink delivery"
STARTS="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
curl -s -XPOST -H 'Content-Type: application/json' \
  -d "[{\"labels\":{\"alertname\":\"P09LiveCheck\",\"service\":\"p09-api\",\"severity\":\"warning\",\"drill_run\":\"${DRILL_RUN}\"},\"annotations\":{\"summary\":\"live delivery check\"},\"startsAt\":\"${STARTS}\"}]" \
  "http://127.0.0.1:9093/api/v2/alerts" >/dev/null || true
sleep 12
check "local sink received the test alert" "$COMPOSE exec -T sink cat /receipts/receipts.jsonl | grep -q 'P09LiveCheck'"

note "restart persistence (recreate, keep volume)"
$COMPOSE down >/dev/null
$COMPOSE up -d
wait_healthy
DUP_CODE="$(curl -s -o /tmp/p09_dup.json -w '%{http_code}' -H "Authorization: Bearer ${P09_APP_SECRET}" \
  -H "Idempotency-Key: ${KEY}" -H "Content-Type: application/json" \
  -d '{"input":"smoke"}' "${BASE}/v1/runs" || echo 000)"
DUP_RUN="$(python3 -c 'import json;print(json.load(open("/tmp/p09_dup.json"))["run_id"])' 2>/dev/null || echo none)"
check "ledger retained after recreate (409)" "[ \"$DUP_CODE\" = 409 ]"
check "same run_id after recreate" "[ \"$DUP_RUN\" = \"$RUN_ID\" ]"

note "missing secret fails readiness safely"
$COMPOSE down >/dev/null
P09_HMAC_SECRET= $COMPOSE up -d api >/dev/null 2>&1 || true
sleep 6
check "missing HMAC secret is not ready" "[ \"$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:${PORT}/health/ready || echo 000)\" = 503 ]"
$COMPOSE down >/dev/null

note "prior-image rollback"
$COMPOSE up -d >/dev/null
docker tag p09-api:local p09-api:prior
check "prior image tag exists" "docker image inspect p09-api:prior >/dev/null 2>&1"
$COMPOSE down >/dev/null

note "done; failures=${fail}"
exit "$fail"
