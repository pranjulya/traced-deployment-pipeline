"""Content-free telemetry: allowlisted spans and metrics.

Frozen schema in app/telemetry-allowlist.json (mirrored by the Phase 00
fixture). Only allowlisted attributes and metric labels may be emitted; no
payloads, headers, exception text, ids or identifiers. Telemetry export is
best-effort and never blocks a request.
"""

import json
from collections import deque
from contextlib import contextmanager
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

    def __init__(self, sink, max_queue=256):
        self.sink = sink
        self.max_queue = max_queue
        self.queue = deque()
        self.spans_dropped = 0
        self.spans_exported = 0

    def export(self, spans):
        for span in spans:
            if len(self.queue) >= self.max_queue:
                self.spans_dropped += 1
                continue
            self.queue.append(span)
        try:
            self.sink.export(list(self.queue))
        except Exception:
            self.spans_dropped += len(self.queue)
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

    def render(self):
        return generate_latest(self.registry).decode("utf-8")


class Telemetry:
    def __init__(self, exporter=None, head_sample_rate=1.0, max_queue=256, deployment_revision="dev", allowlist=None):
        self.allowlist = allowlist or load_allowlist()
        self.deployment_revision = deployment_revision
        self.dropped_attributes = 0
        sink = exporter if exporter is not None else InMemorySpanExporter()
        self.exporter = BoundedSpanExporter(sink, max_queue=max_queue)
        self._provider = TracerProvider(
            sampler=ALWAYS_ON if head_sample_rate >= 1.0 else TraceIdRatioBased(head_sample_rate)
        )
        self._provider.add_span_processor(SimpleSpanProcessor(self.exporter))
        self.tracer = self._provider.get_tracer("p09")
        self.metrics = Metrics()

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
