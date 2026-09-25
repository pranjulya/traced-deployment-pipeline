"""HTTP ingress for the bounded agent.

Authentication is checked before any work; the API is the only application
ingress. Bodies are never logged or stored. See
docs/architecture/accounting-and-api-contract.md.
"""

import asyncio
import hashlib
import hmac
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, PlainTextResponse
from prometheus_client import CONTENT_TYPE_LATEST
from starlette.concurrency import run_in_threadpool

from .agent import AgentError
from .config import KEY_ALPHABET, KEY_MAX, KEY_MIN
from .telemetry import NullTelemetry


def key_is_valid(key):
    return (
        isinstance(key, str)
        and KEY_MIN <= len(key) <= KEY_MAX
        and all(ch in KEY_ALPHABET for ch in key)
    )


def key_digest(hmac_secret, principal_alias, key):
    message = f"{principal_alias}:{key}".encode("utf-8")
    return hmac.new(hmac_secret.encode("utf-8"), message, hashlib.sha256).hexdigest()


def _error(status, code, run_id=None):
    body = {"safe_error_code": code}
    if run_id:
        body["run_id"] = run_id
    return JSONResponse(status_code=status, content=body)


def create_app(settings, ledger, agent, telemetry=None):
    telemetry = telemetry or NullTelemetry()
    app = FastAPI(title="P09 bounded agent", docs_url=None, redoc_url=None, openapi_url=None)
    capacity = asyncio.Semaphore(settings.max_concurrency)

    @app.middleware("http")
    async def _record_metrics(request: Request, call_next):
        telemetry.metrics.in_flight.inc()
        start = time.perf_counter()
        try:
            response = await call_next(request)
        finally:
            telemetry.metrics.in_flight.dec()
        route = "/v1/runs" if request.url.path == "/v1/runs" else "other"
        telemetry.metrics.latency.labels(route_template=route, operation="http").observe(
            time.perf_counter() - start
        )
        telemetry.metrics.requests.labels(
            route_template=route, operation="http", outcome=f"{response.status_code // 100}xx"
        ).inc()
        return response

    @app.get("/metrics")
    async def metrics():
        # Internal-only: served on the same loopback-bound port.
        return PlainTextResponse(telemetry.metrics.render(), media_type=CONTENT_TYPE_LATEST)

    @app.get("/health/live")
    async def live():
        return {"status": "live"}

    @app.get("/health/ready")
    async def ready():
        if not settings.app_secret or not settings.hmac_secret:
            return JSONResponse(status_code=503, content={"status": "not_ready"})
        if not ledger.is_writable():
            return JSONResponse(status_code=503, content={"status": "not_ready"})
        return {"status": "ready"}

    @app.post("/v1/runs")
    async def create_run(request: Request):
        header = request.headers.get("authorization", "")
        token = header[7:] if header.lower().startswith("bearer ") else ""
        if (
            not settings.app_secret
            or not token
            or not hmac.compare_digest(token.encode("utf-8"), settings.app_secret.encode("utf-8"))
        ):
            return _error(401, "UNAUTHENTICATED")

        body = await request.body()
        if len(body) > settings.max_body_bytes:
            return _error(400, "PAYLOAD_TOO_LARGE")

        key = request.headers.get("idempotency-key")
        if not key_is_valid(key):
            return _error(400, "MISSING_IDEMPOTENCY_KEY")

        principal = settings.principal_alias
        digest = key_digest(settings.hmac_secret, principal, key)
        run_id, existing = ledger.admit(principal, digest)
        if existing is not None:
            return JSONResponse(
                status_code=409,
                content={
                    "safe_error_code": "DUPLICATE_REQUEST",
                    "run_id": existing["run_id"],
                    "state": existing["state"],
                    "expires_at": existing["expires_at"],
                },
            )

        try:
            await asyncio.wait_for(capacity.acquire(), timeout=0.001)
        except asyncio.TimeoutError:
            return _error(429, "TOO_MANY_REQUESTS", run_id)
        try:
            # Body content is intentionally not forwarded into audit storage.
            result = await run_in_threadpool(agent.execute, run_id)
        except AgentError as exc:
            return _error(exc.http_status or 503, exc.safe_error_code, run_id)
        finally:
            capacity.release()

        return JSONResponse(
            status_code=200,
            content={
                "run_id": run_id,
                "status": "completed",
                "answer": result.answer,
                "correlation_id": str(uuid.uuid4()),
            },
        )

    return app
