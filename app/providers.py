"""Provider interface and deterministic fake provider.

Behaviors are consumed in order so tests can inject faults deterministically.
"""

from dataclasses import dataclass
from typing import Optional, Sequence


class Kind:
    TRANSIENT = "transient"
    RATE_LIMITED = "rate_limited"
    AUTH = "auth"
    TIMEOUT = "timeout"


@dataclass
class ProviderResult:
    text: str
    input_tokens: Optional[int]
    output_tokens: Optional[int]
    provider_request_id: Optional[str]


class ProviderError(Exception):
    def __init__(self, kind, safe_code):
        super().__init__(safe_code)
        self.kind = kind
        self.safe_code = safe_code


class FakeProvider:
    alias = "fake"

    def __init__(self, behaviors: Optional[Sequence[str]] = None):
        self._behaviors = list(behaviors) if behaviors else []
        self.calls = 0
        self.seen_messages = []

    def call(self, messages, model, deadline):
        self.calls += 1
        behavior = self._behaviors.pop(0) if self._behaviors else "success"
        if behavior == "success":
            return ProviderResult("synthetic answer", 1000, 500, f"req-{self.calls}")
        if behavior == "no_usage":
            return ProviderResult("synthetic answer", None, None, f"req-{self.calls}")
        if behavior == "tiny":
            return ProviderResult("synthetic answer", 1, 1, f"req-{self.calls}")
        if behavior == "rate_limited":
            raise ProviderError(Kind.RATE_LIMITED, "PROVIDER_RATE_LIMITED")
        if behavior == "server_error":
            raise ProviderError(Kind.TRANSIENT, "PROVIDER_UNAVAILABLE")
        if behavior == "auth_error":
            raise ProviderError(Kind.AUTH, "PROVIDER_AUTH_ERROR")
        if behavior == "timeout":
            raise ProviderError(Kind.TIMEOUT, "PROVIDER_TIMEOUT")
        raise ValueError(f"unknown fake behavior: {behavior}")
