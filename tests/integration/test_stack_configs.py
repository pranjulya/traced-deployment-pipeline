"""Static checks for the observability stack config files (Phases 03–04)."""

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]


def test_prometheus_scrapes_api_collector_and_loads_rules():
    cfg = yaml.safe_load((ROOT / "deploy" / "prometheus" / "prometheus.yml").read_text(encoding="utf-8"))
    jobs = {job["job_name"]: job for job in cfg["scrape_configs"]}
    assert "p09-api" in jobs
    assert "collector:8888" in jobs["p09-collector"]["static_configs"][0]["targets"]
    assert cfg["rule_files"]
    assert cfg["alerting"]["alertmanagers"][0]["static_configs"][0]["targets"] == ["alertmanager:9093"]


def test_tempo_receives_otlp_and_bounds_trace_retention():
    cfg = yaml.safe_load((ROOT / "deploy" / "tempo" / "tempo.yaml").read_text(encoding="utf-8"))
    assert cfg["server"]["http_listen_port"] == 3200
    assert "otlp" in cfg["distributor"]["receivers"]
    assert cfg["compactor"]["compaction"]["block_retention"] == "24h"


def test_grafana_datasources_provisioned():
    cfg = yaml.safe_load(
        (ROOT / "deploy" / "grafana" / "provisioning" / "datasources" / "prometheus.yaml").read_text(encoding="utf-8")
    )
    names = {datasource["name"] for datasource in cfg["datasources"]}
    assert {"Prometheus", "Tempo"} <= names


def test_grafana_dashboard_provider_points_at_mounted_dir():
    cfg = yaml.safe_load(
        (ROOT / "deploy" / "grafana" / "provisioning" / "dashboards" / "dashboards.yaml").read_text(encoding="utf-8")
    )
    assert cfg["providers"][0]["options"]["path"] == "/var/lib/grafana/dashboards"


def test_collector_internal_metrics_use_pull_reader_not_removed_address_key():
    cfg = yaml.safe_load((ROOT / "deploy" / "collector" / "collector-config.yaml").read_text(encoding="utf-8"))
    metrics = cfg["service"]["telemetry"]["metrics"]
    # `address` was removed upstream and makes the Collector exit at startup.
    assert "address" not in metrics
    prom = metrics["readers"][0]["pull"]["exporter"]["prometheus"]
    assert prom["port"] == 8888


def test_absent_is_never_called_with_a_range_vector():
    rules = yaml.safe_load((ROOT / "alerts" / "prometheus-rules.yaml").read_text(encoding="utf-8"))
    for group in rules["groups"]:
        for rule in group["rules"]:
            expr = rule["expr"]
            # absent() takes an instant vector; Prometheus refuses to load
            # the whole rule file otherwise. Use absent_over_time for ranges.
            assert not re.search(r"(?<![_\w])absent\([^)]*\]\)", expr), rule["alert"]


def test_sink_listens_on_all_interfaces_inside_compose_only():
    compose = yaml.safe_load((ROOT / "deploy" / "compose.yaml").read_text(encoding="utf-8"))
    sink = compose["services"]["sink"]
    assert sink["environment"]["P09_SINK_HOST"] == "0.0.0.0"
    assert "ports" not in sink


def test_image_precreates_receipts_volume_mount_for_non_root_user():
    dockerfile = (ROOT / "deploy" / "Dockerfile").read_text(encoding="utf-8")
    assert re.search(r"mkdir -p [^\n]*/receipts", dockerfile)
    assert re.search(r"chown -R app:app [^\n]*/receipts", dockerfile)
