# Traced Deployment Pipeline

A reproducible single-host reference deployment of a bounded, read-only agent API. It is instrumented so an operator can diagnose provider, tool, deployment and telemetry failures using correlated traces, operational metrics, durable usage accounting, dashboards and alerts. This is a production-minded learning deployment, not a high-availability service.

> **Status:** Phases 00–01 are complete. Phases 02–04 are implemented and tested on the paths that don't need Docker, but their live verification is blocked until a Docker daemon is available. Phases 05–06 have not started. See [Implementation.md](Implementation.md) for the authoritative status.

## Features

- **Bounded agent API** (FastAPI): a deterministic fake provider plus one local read-only lookup tool. Each request has a shared 30 s deadline, at most 3 provider attempts and at most 2 tool calls. Bodies are limited to 8 KiB and concurrency to 10.
- **Authentication and idempotency**: a single bearer secret maps to the `demo-operator` principal. Every request requires an `Idempotency-Key` header, and repeating a key returns `409 DUPLICATE_REQUEST` with the original `run_id`.
- **Durable usage accounting**: an SQLite ledger records every run without sampling, survives restarts, and reclassifies unfinished runs on startup.
- **Content-free telemetry**: OpenTelemetry traces are exported via OTLP to an OTel Collector and stored in Tempo. Attributes are restricted by an allowlist (`app/telemetry-allowlist.json`), and Prometheus metrics are served at `/metrics`.
- **Dashboards and alerts**: a Grafana dashboard (`dashboards/p09-overview.json`), Prometheus alert rules, and Alertmanager routing to a local notification sink.
- **Hardened Compose stack**: containers run non-root with a read-only root filesystem, `cap_drop: ALL` and resource limits. Only loopback ports are published, and the telemetry network is internal.

## API

| Endpoint | Description |
|---|---|
| `POST /v1/runs` | Run the bounded agent. Requires `Authorization: Bearer <P09_APP_SECRET>` and `Idempotency-Key` (16–128 URL-safe characters). |
| `GET /health/live` | Liveness |
| `GET /health/ready` | Readiness: secrets are set and the ledger is writable |
| `GET /metrics` | Prometheus metrics |

See [docs/architecture/accounting-and-api-contract.md](docs/architecture/accounting-and-api-contract.md) for the full contract.

## Run the tests

This needs Python 3.12.

```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements-deploy-dev.txt
pytest -q
```

The live rehearsal (`tests/integration/live_deploy_check.sh`) requires a running Docker daemon.

## Run the API locally (without Docker)

```bash
pip install -r requirements.txt
export P09_APP_SECRET=change-me P09_HMAC_SECRET=change-me-too P09_DB_PATH=./p09-ledger.sqlite
uvicorn app.main:app --port 8080

curl -s -H "Authorization: Bearer $P09_APP_SECRET" \
     -H "Idempotency-Key: smoke-$(date +%s)-aaaaaaaa" \
     -H "Content-Type: application/json" \
     -d '{"input":"smoke"}' http://127.0.0.1:8080/v1/runs
```

Traces are exported only when `P09_OTLP_ENDPOINT` is set.

## Run the full stack (Docker Compose)

```bash
cp deploy/.env.example deploy/.env   # fill in strong random secrets
docker compose -f deploy/compose.yaml build
docker compose -f deploy/compose.yaml up -d
docker compose -f deploy/compose.yaml ps
```

The stack includes the API, OTel Collector, Tempo, Prometheus (`127.0.0.1:9090`), Alertmanager (`127.0.0.1:9093`), Grafana (`127.0.0.1:3000`), a local alert sink and node-exporter. See [deploy/runbook.md](deploy/runbook.md) for the smoke check, restart persistence, backup, rollback and teardown.

## Project structure

```
app/          # FastAPI app, agent, fake provider, lookup tool, ledger, pricing, telemetry
deploy/       # Dockerfile, compose.yaml, Collector/Tempo/Prometheus/Grafana config, runbook, backup script, alert sink
alerts/       # Prometheus alert rules and Alertmanager config
dashboards/   # Grafana dashboard JSON
tests/        # unit, telemetry, ops and deployment-config tests; live rehearsal script
docs/         # PRD, HLD, LLD, ADRs, evaluation strategy, operations/runbooks
implementation/  # per-phase plans (00-06)
Learning/     # concept notes, scenarios, interview Q&A
```

## Documentation

- [PRD](docs/product/PRD.md), [HLD](docs/architecture/HLD.md), [LLD](docs/architecture/LLD.md), [ADRs](docs/architecture/ADRs/)
- [Versions and pins](docs/architecture/versions-and-pins.md)
- [Operations](docs/operations/production-scenarios.md), [Learning guide](Learning/README.md)
