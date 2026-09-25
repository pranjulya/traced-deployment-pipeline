# Source register
Reviewed 2026-09-23. Version-specific configuration must be rechecked and pinned in phase 00. Sources inform choices, not evidence of this project's performance.

- [Docker Compose production guidance](https://docs.docker.com/compose/how-tos/production/): basis for a single-host production override and controlled recreate workflow. Does not confer high availability.
- [OTel Collector architecture](https://opentelemetry.io/docs/collector/architecture/): receiver/processor/exporter pipeline model.
- [OTel Collector overview](https://opentelemetry.io/docs/collector/): central export processing and buffering; privacy controls still begin in application instrumentation.
- [OTel sampling concepts](https://opentelemetry.io/docs/concepts/sampling/): sampling tradeoffs; accounting cannot be derived from sampled traces.
- [Prometheus alerting practices](https://prometheus.io/docs/practices/alerting/): alert on actionable symptoms and test notification delivery end to end.
- [Prometheus histograms](https://prometheus.io/docs/practices/histograms/): aggregate latency distributions with histograms; verify native histogram support across pinned versions before choosing, otherwise fixed explicit buckets.
- [Prometheus alerting overview](https://prometheus.io/docs/alerting/latest/overview/): rules and Alertmanager have distinct responsibilities.
- [Docker Desktop settings](https://docs.docker.com/desktop/settings-and-maintenance/settings/): CPU/RAM allocation on the macOS reference host; images must provide arm64 variants.
