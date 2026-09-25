# Versions, images and resource budget

Status: SELECTED at Phase 00 (2026-09-25). Digests resolved from the Docker Hub tag API on 2026-09-25 and must be re-verified at image pull in Phase 02. This file is the pinning contract for ADR 001; it authorizes no deployment.

## Reference host
- Mac mini, Apple M4 (arm64), macOS 26.5, 16 GB RAM.
- Docker Desktop, Linux container runtime. The daemon must be started and allocated at least the resource budget below before Phase 02.
- Host Python 3.9.6 is used only for the stdlib fixture checks. The application targets the pinned Python 3.12 image.

## Resource budget (proposed, to be measured)
- 4 vCPU and 8 GB RAM allocated to the Compose stack.
- One API process, max concurrency 10, 30 s total deadline, at most 3 provider attempts and 2 tool calls.
- Measure idle and loaded use before adding components; a miss triggers review, not edited results.

## Pinned images
Every image publishes an `arm64` variant. Digests are immutable; a tag re-point must be treated as a new pin.

| Component | Image | Tag | Manifest-list digest | arm64 digest |
|---|---|---|---|---|
| API runtime | `library/python` | `3.12.14-slim-bookworm` | `sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e` | `sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e` (single linux digests) |
| OTel Collector | `otel/opentelemetry-collector-contrib` | `0.161.0` | `sha256:fd328de2552466ad78385e1b1289c3f2402b1c45f265b252aab1955b42845ac1` | `sha256:d497a11a3088097e4054ffbfd4b4f5244a8c036dc77c96cf2f14f86113ee9b86` |
| Traces | `grafana/tempo` | `2.9.0` | `sha256:65a5789759435f1ef696f1953258b9bbdb18eb571d5ce711ff812d2e128288a4` | `sha256:0ea6e47231c1c993abed41bddf67d524ff5508954463759f0bcc1e97543f3386` |
| Metrics | `prom/prometheus` | `v3.15.0` | `sha256:efd719c99d83b060d9daefdcf00360461adf279f45ef5391f8d111892118753e` | `sha256:6b41f7a45cfbd1d259a78701ee5e14fc2ad9383c9aa5d0427345a18539bc3c91` |
| Dashboards | `grafana/grafana` | `13.2.2` | `sha256:ac461fb352abc50da10a51c7d02462e9c05488f11f53f14b3ad79a8145f638a0` | `sha256:d523f1346c0cd277de119bc1acb21b39ec89427975ae8b0815561698e859f725` |
| Alerts | `prom/alertmanager` | `v0.34.1` | `sha256:e9733bafb1bdef9b00e25a21f8f99dc26a22224bf16641ad754d1649f4c3357a` | `sha256:47a1dc7e74f1e755e29f74d392262f8d1da41f2ada5653911199bf07219e41d9` |
| Host metrics | `prom/node-exporter` | `v1.12.1` | `sha256:1b4e4438faca4dd7e001dd445d161a4a2091b0fededa84093b3a8dfeae1f1be0` | `sha256:c9ef89f9464f09e7234decaae68a80ab856ff0014435677a99fd48b03dd410ea` |

## Native histogram decision
Prometheus histograms are the default for latency. Whether native histograms are used depends on the pinned Prometheus/Grafana support and will be confirmed in Phase 03; otherwise explicit fixed buckets are used. This is left open here because the failure scenario "unsupported histogram integration" is a Phase 00 concern to record, not to assume.

## Not yet pinned (not needed before Phase 01)
- Optional real-provider adapter version (Project 08) — only if the optional integration is pursued; fake provider is the default.
- Exact application dependency lockfile — created in Phase 01 and matched to Python 3.12.
