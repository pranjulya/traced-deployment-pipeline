"""Static checks for the Phase 03 Collector configuration (no daemon needed)."""

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
CONFIG = yaml.safe_load((ROOT / "deploy" / "collector" / "collector-config.yaml").read_text(encoding="utf-8"))


def test_memory_limiter_present():
    limiter = CONFIG["processors"]["memory_limiter"]
    assert limiter["limit_mib"] > 0
    assert limiter["spike_limit_mib"] > 0


def test_batch_processor_bounds_events():
    batch = CONFIG["processors"]["batch"]
    assert batch["send_batch_max_size"] >= batch["send_batch_size"]


def test_forbidden_attributes_are_deleted():
    actions = CONFIG["processors"]["attributes/p09_allowlist"]["actions"]
    deleted = {action["key"] for action in actions if action["action"] == "delete"}
    for key in ("prompt", "output", "tool_arguments", "authorization", "idempotency_key", "run_id", "email"):
        assert key in deleted, key


def test_exporter_queue_is_bounded():
    exporter = CONFIG["exporters"]["otlp/tempo"]
    assert exporter["sending_queue"]["enabled"] is True
    assert exporter["sending_queue"]["queue_size"] > 0
    assert exporter["retry_on_failure"]["enabled"] is True


def test_trace_pipeline_wires_receiver_processors_exporter():
    pipeline = CONFIG["service"]["pipelines"]["traces"]
    assert pipeline["receivers"] == ["otlp"]
    assert pipeline["exporters"] == ["otlp/tempo"]
    assert pipeline["processors"] == ["memory_limiter", "attributes/p09_allowlist", "batch"]
