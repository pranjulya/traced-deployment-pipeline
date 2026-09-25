"""Static checks for the observability stack config files (Phases 03–04)."""

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
