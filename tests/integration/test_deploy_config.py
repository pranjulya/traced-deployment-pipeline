"""Static checks for the Phase 02 deployment contract.

These run without a Docker daemon and enforce the security and reproducibility
properties the oracle requires. Live checks (clean start, restart, rollback,
non-root execution) are in live_deploy_check.sh and need Docker Desktop.
"""

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
COMPOSE = yaml.safe_load((ROOT / "deploy" / "compose.yaml").read_text(encoding="utf-8"))
DOCKERFILE = (ROOT / "deploy" / "Dockerfile").read_text(encoding="utf-8")
ENV_EXAMPLE = (ROOT / "deploy" / ".env.example").read_text(encoding="utf-8")
API = COMPOSE["services"]["api"]


def test_two_networks_with_internal_telemetry():
    assert COMPOSE["networks"]["telemetry"]["internal"] is True
    assert not COMPOSE["networks"]["ingress"].get("internal", False)
    assert set(API["networks"]) == {"ingress", "telemetry"}


def test_api_published_on_loopback_only():
    published = API["ports"]
    assert published and all(port.startswith("127.0.0.1:") for port in published)


def test_no_privileged_services_or_public_admin_ports():
    for name, service in COMPOSE["services"].items():
        assert service.get("privileged", False) is False, name
        for port in service.get("ports", []):
            assert "127.0.0.1:" in port, (name, port)


def test_bounded_resources_and_caps():
    limits = API["deploy"]["resources"]["limits"]
    assert "cpus" in limits and "memory" in limits
    assert API["read_only"] is True
    assert "ALL" in API["cap_drop"]
    assert "no-new-privileges:true" in API["security_opt"]


def test_ledger_volume_mounted_and_secrets_injected_not_baked():
    assert "ledger-data:/data" in API["volumes"]
    assert API["env_file"] == [".env"]
    literal_env = API["environment"]
    assert "P09_APP_SECRET" not in literal_env
    assert "P09_HMAC_SECRET" not in literal_env


def test_readiness_healthcheck_uses_ready_endpoint():
    test_cmd = " ".join(API["healthcheck"]["test"])
    assert "/health/ready" in test_cmd


def test_dockerfile_runs_as_non_root_and_is_digest_pinned():
    assert "@sha256:" in DOCKERFILE
    assert re.search(r"^USER 10001:10001$", DOCKERFILE, re.MULTILINE)
    assert "useradd" in DOCKERFILE


def test_dockerfile_bakes_no_secrets():
    for line in DOCKERFILE.splitlines():
        if line.strip().upper().startswith("ENV"):
            assert "SECRET" not in line.upper()
            assert "PASSWORD" not in line.upper()


def test_env_example_contains_placeholders_only():
    assert "replace-with" in ENV_EXAMPLE
    for line in ENV_EXAMPLE.splitlines():
        if line.startswith("P09_APP_SECRET=") or line.startswith("P09_HMAC_SECRET="):
            assert "replace-with" in line


def test_compose_declares_pinned_local_image_tag():
    assert API["image"] == "p09-api:local"


def test_full_observability_stack_services_present():
    services = set(COMPOSE["services"])
    assert {
        "api",
        "collector",
        "tempo",
        "prometheus",
        "alertmanager",
        "grafana",
        "sink",
        "node-exporter",
    } <= services


def test_all_published_ports_are_loopback():
    for name, service in COMPOSE["services"].items():
        for port in service.get("ports", []):
            assert port.startswith("127.0.0.1:"), (name, port)


def test_internal_services_publish_no_ports():
    for name in ("collector", "tempo", "sink", "node-exporter"):
        assert not COMPOSE["services"][name].get("ports"), name


def test_stack_configs_are_mounted_read_only():
    assert (
        "./collector/collector-config.yaml:/etc/otelcol/config.yaml:ro"
        in COMPOSE["services"]["collector"]["volumes"]
    )
    assert any("prometheus-rules.yaml" in v for v in COMPOSE["services"]["prometheus"]["volumes"])
    assert any("alertmanager.yaml" in v for v in COMPOSE["services"]["alertmanager"]["volumes"])
    assert any("grafana/provisioning" in v for v in COMPOSE["services"]["grafana"]["volumes"])


def test_api_exports_to_collector_but_readiness_is_independent():
    env = COMPOSE["services"]["api"]["environment"]
    assert env["P09_OTLP_ENDPOINT"].startswith("http://collector:")
    assert "collector" not in (COMPOSE["services"]["api"].get("depends_on") or [])


def test_pinned_image_digests_for_third_party_services():
    for name in ("collector", "tempo", "prometheus", "alertmanager", "grafana", "node-exporter"):
        assert "@sha256:" in COMPOSE["services"][name]["image"], name
