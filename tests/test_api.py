"""HTTP-level checks for the Phase 01 contract."""

from fastapi.testclient import TestClient

from app.agent import Agent
from app.api import create_app
from app.pricing import PriceTable
from app.providers import FakeProvider
from app.tools import LookupTool

KEY = "k" * 16
AUTH = {"Authorization": "Bearer app-secret"}


def make_client(settings, ledger, behaviors=None, fail_tool_next=0):
    provider = FakeProvider(behaviors)
    tool = LookupTool(fail_next=fail_tool_next)
    agent = Agent(ledger, provider, tool, PriceTable(), settings)
    return TestClient(create_app(settings, ledger, agent)), provider


def test_missing_credential_returns_401(settings, ledger):
    client, _ = make_client(settings, ledger)
    response = client.post("/v1/runs", headers={"Idempotency-Key": KEY}, json={"input": "hi"})
    assert response.status_code == 401
    assert response.json()["safe_error_code"] == "UNAUTHENTICATED"


def test_missing_idempotency_key_returns_400(settings, ledger):
    client, _ = make_client(settings, ledger)
    response = client.post("/v1/runs", headers=AUTH, json={"input": "hi"})
    assert response.status_code == 400
    assert response.json()["safe_error_code"] == "MISSING_IDEMPOTENCY_KEY"


def test_oversized_body_returns_400(settings, ledger):
    client, _ = make_client(settings, ledger)
    response = client.post(
        "/v1/runs", headers={**AUTH, "Idempotency-Key": KEY}, content=b"x" * 9000
    )
    assert response.status_code == 400
    assert response.json()["safe_error_code"] == "PAYLOAD_TOO_LARGE"


def test_success_then_duplicate(settings, ledger):
    client, provider = make_client(settings, ledger)
    headers = {**AUTH, "Idempotency-Key": KEY}

    first = client.post("/v1/runs", headers=headers, json={"input": "hi"})
    assert first.status_code == 200
    assert first.json()["status"] == "completed"
    assert "answer" in first.json()

    second = client.post("/v1/runs", headers=headers, json={"input": "hi"})
    assert second.status_code == 409
    assert second.json()["safe_error_code"] == "DUPLICATE_REQUEST"
    assert second.json()["run_id"] == first.json()["run_id"]
    assert provider.calls == 1


def test_health_endpoints(settings, ledger):
    client, _ = make_client(settings, ledger)
    assert client.get("/health/live").status_code == 200
    assert client.get("/health/ready").json()["status"] == "ready"
