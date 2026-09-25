"""Functional test of the local notification sink (Phase 04, R06 delivery path)."""

import importlib.util
import json
import threading
import urllib.request
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def load(name, rel):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


sink_mod = load("notify_sink", "deploy/sink/notify_sink.py")


def post(url, payload):
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}, method="POST"
    )
    with urllib.request.urlopen(request, timeout=5) as response:
        return response.status


def test_receipt_resolution_and_grouped_batch():
    sink = sink_mod.Sink()
    server = sink_mod.create_server(sink, port=0)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        label = {"alertname": "P09LedgerWriteFailure", "service": "p09-api", "severity": "critical"}
        firing = {"version": "4", "status": "firing", "alerts": [{"status": "firing", "labels": label}] * 2}
        resolved = {"version": "4", "status": "resolved", "alerts": [{"status": "resolved", "labels": label}]}

        assert post(f"http://127.0.0.1:{port}/alerts", firing) == 200
        assert post(f"http://127.0.0.1:{port}/alerts", resolved) == 200

        received = sink.received()
        assert [r["status"] for r in received] == ["firing", "resolved"]
        # Grouped/deduplicated alerts arrive as one notification with two alerts.
        assert len(received[0]["alerts"]) == 2
    finally:
        server.shutdown()
        server.server_close()


def test_receiver_down_is_detectable_not_silent():
    with pytest.raises(Exception):
        post("http://127.0.0.1:1/alerts", {"status": "firing", "alerts": []})


def test_sink_rejects_malformed_and_missing_paths():
    sink = sink_mod.Sink()
    server = sink_mod.create_server(sink, port=0)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        request = urllib.request.Request(
            f"http://127.0.0.1:{port}/nope", data=b"{}", method="POST"
        )
        with pytest.raises(urllib.error.HTTPError) as excinfo:
            urllib.request.urlopen(request, timeout=5)
        assert excinfo.value.code == 404
        assert sink.received() == []
    finally:
        server.shutdown()
        server.server_close()
