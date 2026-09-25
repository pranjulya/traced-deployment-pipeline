# Morning review

Approved at G0 (2026-09-25): a local single-host Compose observability reference with a fake bounded agent first. Keep cost correctness in an unsampled ledger, diagnostic traces sampled only after baseline, and telemetry content-free. This gives useful operations evidence without requiring P08 or P10.

Key assumptions: one operator, 10 concurrent synthetic requests, macOS 26.5 Apple M4 Mac mini with a 4 vCPU/8 GB Docker Desktop allocation, no external publication or notifications. Risks: host failure defeats local alerting; telemetry stack resource overhead; provider timeout leaves charges uncertain; privacy leakage via automatic instrumentation; currency/price changes make cost estimates stale.

G0 approved 2026-09-25: reference host/resource budget, stack candidates and pins, retention, API authentication approach, and optional real-provider spending. Dedicated repository selected: `https://github.com/pranjulya/traced-deployment-pipeline.git` — currently PUBLIC, so nothing is pushed until publication is authorized. Seven sequential phases are NOT_STARTED; ADRs 001–004 are ACCEPTED.
