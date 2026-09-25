"""Content-free telemetry: allowlisted spans and metrics.

Frozen schema in app/telemetry-allowlist.json (mirrored by the Phase 00
fixture). Only allowlisted attributes and metric labels may be emitted; no
payloads, headers, exception text, ids or identifiers. Telemetry export is
best-effort and never blocks a request.
"""

import json
from collections import deque
from contextlib import contextmanager
from decimal import Decimal
from pathlib import Path

from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, SpanExporter, SpanExportResult
from opentelemetry.sdk.trace.sampling import ALWAYS_ON, TraceIdRatioBased
from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram, generate_latest

ALLOWLIST_PATH = Path(__file__).resolve().parent / "telemetry-allowlist.json"


def load_allowlist(path=ALLOWLIST_PATH):
    with Path(path).open(encoding="utf-8") as handle:
        return json.load(handle)


class InMemorySpanExporter(SpanExporter):
    """Test sink that keeps exported spans."""

    def __init__(self):
        self.spans = []

    def export(self, spans):
        self.spans.extend(spans)
        return SpanExportResult.SUCCESS

    def shutdown(self):
        return None

    def force_flush(self, timeout_millis=0):
        return True


class NoopSpanExporter(SpanExporter):
    """Discards spans when no export endpoint is configured (bounded memory)."""

    def export(self, spans):
        return SpanExportResult.SUCCESS

    def shutdown(self):
        return None

    def force_flush(self, timeout_millis=0):
        return True


class FailingSpanExporter(SpanExporter):
    """Simulates an unreachable export endpoint."""

    def export(self, spans):
        raise RuntimeError("export endpoint down")

    def shutdown(self):
        return None

    def force_flush(self, timeout_millis=0):
        return True


class BoundedSpanExporter(SpanExporter):
    """Bounded queue in front of a sink; counts drops and never raises."""

    def __init__(self, sink, max_queue=256, on_drop=None):
        self.sink = sink
        self.max_queue = max_queue
        self.on_drop = on_drop
        self.queue = deque()
        self.spans_dropped = 0
        self.spans_exported = 0

    def _drop(self, count):
        self.spans_dropped += count
        if self.on_drop is not None:
            self.on_drop(count)

    def export(self, spans):
        for span in spans:
            if len(self.queue) >= self.max_queue:
                self._drop(1)
                continue
            self.queue.append(span)
        try:
            self.sink.export(list(self.queue))
        except Exception:
            self._drop(len(self.queue))
        else:
            self.spans_exported += len(self.queue)
        finally:
            self.queue.clear()
        return SpanExportResult.SUCCESS

    def shutdown(self):
        return None

    def force_flush(self, timeout_millis=0):
        return True


class Metrics:
    """Application metrics with allowlisted labels only."""

    def __init__(self, registry=None):
        self.registry = registry or CollectorRegistry()
        self.requests = Counter(
            "p09_requests_total", "Requests.", ["route_template", "operation", "outcome"], registry=self.registry
        )
        self.latency = Histogram(
            "p09_request_latency_seconds", "Request latency.", ["route_template", "operation"], registry=self.registry
        )
        self.in_flight = Gauge("p09_in_flight_requests", "In-flight requests.", registry=self.registry)
        self.provider_attempts = Counter(
            "p09_provider_attempts_total", "Provider attempts.", ["model_alias", "outcome"], registry=self.registry
        )
        self.tool_outcomes = Counter("p09_tool_outcomes_total", "Tool outcomes.", ["outcome"], registry=self.registry)
        self.timeouts = Counter("p09_provider_timeouts_total", "Provider timeouts.", registry=self.registry)
        self.telemetry_drops = Counter("p09_telemetry_drops_total", "Dropped telemetry items.", registry=self.registry)
        self.ledger_write_failures = Counter(
            "p09_ledger_write_failures_total", "Ledger commit failures.", registry=self.registry
        )
        self.known_charge_nano = Gauge(
            "p09_known_charge_nano_total", "Known charge in nano units.", ["currency"], registry=self.registry
        )
        self.unknown_attempts = Gauge(
            "p09_unknown_attempts", "Attempts whose charge is unknown.", registry=self.registry
        )
        self.usage_coverage = Gauge(
            "p09_usage_coverage_ratio", "Known / total attempts.", registry=self.registry
        )
        self.reconciliation_lag = Gauge(
            "p09_reconciliation_lag_seconds", "Age of the oldest unknown attempt.", registry=self.registry
        )

    def set_ledger_aggregates(self, aggregate):
        self.known_charge_nano.clear()
        for currency, amount in aggregate["known_charge"].items():
            self.known_charge_nano.labels(currency=currency).set(
                float(Decimal(amount) * Decimal(1_000_000_000))
            )
        self.unknown_attempts.set(aggregate["unknown_attempts"])
        self.usage_coverage.set(aggregate["coverage_ratio"])
        self.reconciliation_lag.set(aggregate["reconciliation_lag_seconds"])

    def render(self):
        return generate_latest(self.registry).decode("utf-8")


class Telemetry:
    def __init__(self, exporter=None, head_sample_rate=1.0, max_queue=256, deployment_revision="dev", allowlist=None):
        self.allowlist = allowlist or load_allowlist()
        self.deployment_revision = deployment_revision
        self.dropped_attributes = 0
        self.metrics = Metrics()
        sink = exporter if exporter is not None else InMemorySpanExporter()
        self.exporter = BoundedSpanExporter(
            sink, max_queue=max_queue, on_drop=lambda n: self.metrics.telemetry_drops.inc(n)
        )
        self._provider = TracerProvider(
            sampler=ALWAYS_ON if head_sample_rate >= 1.0 else TraceIdRatioBased(head_sample_rate)
        )
        self._provider.add_span_processor(SimpleSpanProcessor(self.exporter))
        self.tracer = self._provider.get_tracer("p09")

    # -- schema enforcement -------------------------------------------------
    def _allowed(self, name):
        return set(self.allowlist["spans"].get(name, {}).get("attributes", []))

    def _filter(self, name, attributes):
        allowed = self._allowed(name)
        forbidden = set(self.allowlist["forbidden_attributes"])
        clean = {}
        for key, value in (attributes or {}).items():
            if value is None:
                continue
            if key in allowed and key not in forbidden:
                clean[key] = value
            else:
                self.dropped_attributes += 1
        return clean

    # -- spans -------------------------------------------------------------
    @contextmanager
    def span(self, name, attributes=None):
        # record_exception=False is essential: OTel would otherwise attach the
        # exception message (payload/secret leak) to the span. We only set a
        # bounded error_class.
        with self.tracer.start_as_current_span(
            name, record_exception=False, set_status_on_exception=False
        ) as span:
            for key, value in self._filter(name, attributes).items():
                span.set_attribute(key, value)
            try:
                yield span
            except Exception as exc:
                safe_code = getattr(exc, "safe_error_code", None)
                from opentelemetry.trace import Status, StatusCode

                span.set_status(Status(StatusCode.ERROR))
                if safe_code:
                    span.set_attribute("error_class", safe_code)
                raise

    @property
    def spans_dropped(self):
        return self.exporter.spans_dropped

    @property
    def spans_exported(self):
        return self.exporter.spans_exported


class NullTelemetry:
    """No-op used when telemetry is disabled or unavailable."""

    deployment_revision = "dev"
    dropped_attributes = 0
    spans_dropped = 0
    spans_exported = 0

    @contextmanager
    def span(self, name, attributes=None):
        yield None

    class _Metrics:
        def __getattr__(self, item):
            return _Noop()

        def set_ledger_aggregates(self, aggregate):
            return None

    metrics = _Metrics()


class _Noop:
    def labels(self, *args, **kwargs):
        return self

    def inc(self, *args, **kwargs):
        return None

    def dec(self, *args, **kwargs):
        return None

    def observe(self, *args, **kwargs):
        return None

    def set(self, *args, **kwargs):
        return None
