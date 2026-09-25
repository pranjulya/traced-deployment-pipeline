"""Static validation of Alertmanager routing (Phase 04, R06)."""

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
AM = yaml.safe_load((ROOT / "alerts" / "alertmanager.yaml").read_text(encoding="utf-8"))


def test_routes_only_to_local_sink():
    assert AM["route"]["receiver"] == "local-sink"
    webhooks = [w for receiver in AM["receivers"] for w in receiver.get("webhook_configs", [])]
    assert webhooks
    for webhook in webhooks:
        assert webhook["url"].startswith("http://127.0.0.1:")


def test_grouping_is_bounded():
    group_by = AM["route"]["group_by"]
    assert set(group_by) == {"alertname", "service", "severity"}
    for forbidden in ("run_id", "trace_id", "instance", "pod"):
        assert forbidden not in group_by


def test_resolution_notifications_enabled():
    webhooks = [w for receiver in AM["receivers"] for w in receiver.get("webhook_configs", [])]
    assert all(webhook["send_resolved"] for webhook in webhooks)


def test_no_external_destination_configured():
    text = (ROOT / "alerts" / "alertmanager.yaml").read_text(encoding="utf-8")
    assert "REPLACE_ME" not in text.replace("#      - url: REPLACE_ME", "")
