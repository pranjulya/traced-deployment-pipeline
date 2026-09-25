# Security and privacy plan

Threats: malicious input contaminates logs; stolen provider secret; arbitrary tool/URL access; public metrics expose metadata; vulnerable container; backup leakage; telemetry flood exhausts disk. Mitigate through fixed tool/endpoint allowlists, input/body/deadline limits, authentication, internal-only observability network, least-privilege non-root images, pinned digests, secret injection at runtime, resource limits, and volume retention.

Never commit secrets, scrape request headers, log bodies, record raw exception messages or expose dashboard administration publicly. Synthetic canaries represent PII and secrets in tests; scan application logs, Collector output, Tempo records, metric labels, notifications and evidence exports. Redaction alone is not a guarantee. Provider responses stay in the user response and out of diagnostic storage; idempotency state stores only execution status in V1, so replay may report prior completion without replaying the answer.

Review dependency/image vulnerabilities at release with documented severity exceptions, verify backup access and deletion, and record retention decisions. TLS required before non-loopback use. Local demo is not an enterprise security certification. Optional P10 adds defense but cannot replace these controls.

Incident: stop ingestion of affected telemetry, restrict access, rotate compromised credentials, preserve minimal safe audit evidence, delete exposed content following destination procedures, verify canary regression check, document impact without copying secrets.

## Authentication and duplicate privacy
The injected application secret maps to a trusted principal alias; client identity fields cannot select another namespace. Idempotency stores a principal-scoped HMAC digest and safe run state, not raw keys or answers. Registry retention is at least 24 h for terminal records; unresolved records survive until explicit resolution. Duplicate requests return 409 metadata without execution or answer replay. HMAC-key rotation is a reviewed drain/migration operation.
