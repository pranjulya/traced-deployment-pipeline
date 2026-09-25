"""Bounded agent execution.

Bounds: one shared deadline, at most MAX_PROVIDER_ATTEMPTS provider attempts
and MAX_TOOL_CALLS tool calls. Commit pending before dispatch; withhold output
when a completion commit fails.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from time import monotonic

from .accounting import LedgerUnavailable
from .money import compute_charge, format_nano
from .providers import Kind, ProviderError
from .tools import ToolError


class AgentError(Exception):
    def __init__(self, safe_error_code, http_status, run_state):
        super().__init__(safe_error_code)
        self.safe_error_code = safe_error_code
        self.http_status = http_status
        self.run_state = run_state


@dataclass
class AgentResult:
    run_id: str
    answer: str
    provider_calls: int
    tool_calls: int
    attempts: list = field(default_factory=list)


class Agent:
    def __init__(self, ledger, provider, tool, price_table, settings):
        self.ledger = ledger
        self.provider = provider
        self.tool = tool
        self.price_table = price_table
        self.settings = settings

    def execute(self, run_id, *, model=None, messages=None, cancel_check=None, price_date=None):
        model = model or self.settings.default_model
        messages = messages or []
        price_date = price_date or datetime.now(timezone.utc).date()
        deadline = monotonic() + self.settings.total_deadline_seconds

        ordinal = 0
        result = None
        while ordinal < self.settings.max_provider_attempts:
            if cancel_check is not None and cancel_check():
                self._best_effort_state(run_id, "failed", "CLIENT_CANCELLED")
                raise AgentError("CLIENT_CANCELLED", None, "failed")
            if monotonic() > deadline:
                self._best_effort_state(run_id, "failed", "DEADLINE_EXCEEDED")
                raise AgentError("DEADLINE_EXCEEDED", 504, "failed")

            ordinal += 1
            try:
                attempt_id = self.ledger.create_pending_attempt(
                    run_id, ordinal, self.provider.alias, model
                )
            except LedgerUnavailable:
                # No external call is made when the pending commit fails.
                raise AgentError("ACCOUNTING_UNAVAILABLE", 503, None)

            try:
                result = self.provider.call(messages, model, deadline)
            except ProviderError as error:
                if error.kind == Kind.TIMEOUT:
                    self._best_effort(lambda: self.ledger.unknown_attempt(attempt_id))
                    self._best_effort_state(run_id, "failed", "PROVIDER_TIMEOUT")
                    raise AgentError("PROVIDER_TIMEOUT", 504, "failed")
                if error.kind == Kind.AUTH:
                    self._best_effort(
                        lambda: self.ledger.fail_attempt(attempt_id, currency=self._currency(model, price_date))
                    )
                    self._best_effort_state(run_id, "failed", "PROVIDER_AUTH_ERROR")
                    raise AgentError("PROVIDER_AUTH_ERROR", 502, "failed")
                # transient / rate limited: account this attempt, then retry if allowed
                self._best_effort(
                    lambda: self.ledger.fail_attempt(attempt_id, currency=self._currency(model, price_date))
                )
                if ordinal >= self.settings.max_provider_attempts or monotonic() > deadline:
                    self._best_effort_state(run_id, "failed", "PROVIDER_UNAVAILABLE")
                    raise AgentError("PROVIDER_UNAVAILABLE", 502, "failed")
                continue
            else:
                self._complete_attempt(run_id, attempt_id, model, result, price_date)
                break

        tool_calls = 0
        while tool_calls < self.settings.max_tool_calls:
            if cancel_check is not None and cancel_check():
                self._best_effort_state(run_id, "failed", "CLIENT_CANCELLED")
                raise AgentError("CLIENT_CANCELLED", None, "failed")
            tool_calls += 1
            try:
                self.tool.lookup("alpha")
            except ToolError:
                self._best_effort_state(run_id, "failed", "TOOL_FAILURE")
                raise AgentError("TOOL_FAILURE", 502, "failed")
            break

        try:
            self.ledger.set_run_state(run_id, "completed")
        except LedgerUnavailable:
            self._best_effort_state(run_id, "accounting_unknown", "ACCOUNTING_UNAVAILABLE")
            raise AgentError("ACCOUNTING_UNAVAILABLE", 503, "accounting_unknown")
        return AgentResult(
            run_id=run_id,
            answer=result.text,
            provider_calls=self.provider.calls,
            tool_calls=tool_calls,
            attempts=self.ledger.attempts_for(run_id),
        )

    # -- helpers -----------------------------------------------------------
    def _currency(self, model, price_date):
        price = self.price_table.price_for(model, price_date)
        return price["currency"] if price else None

    def _complete_attempt(self, run_id, attempt_id, model, result, price_date):
        price = self.price_table.price_for(model, price_date)
        if result.input_tokens is None or result.output_tokens is None:
            usage_origin = "unknown"
            charge = None
            charge_state = "unknown"
            currency = price["currency"] if price else None
            input_tokens = output_tokens = None
        elif price is None:
            usage_origin = "provider"
            charge = None
            charge_state = "unknown"
            currency = None
            input_tokens = result.input_tokens
            output_tokens = result.output_tokens
        else:
            usage_origin = "provider"
            charge = format_nano(
                compute_charge(
                    result.input_tokens,
                    result.output_tokens,
                    price["input_per_million"],
                    price["output_per_million"],
                )
            )
            charge_state = "observed"
            currency = price["currency"]
            input_tokens = result.input_tokens
            output_tokens = result.output_tokens

        try:
            self.ledger.complete_attempt(
                attempt_id,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                usage_origin=usage_origin,
                currency=currency,
                charge=charge,
                charge_state=charge_state,
                price_version=self.price_table.price_version,
            )
        except LedgerUnavailable:
            # Withhold output; preserve uncertainty so restart can classify it.
            self._best_effort(lambda: self.ledger.unknown_attempt(attempt_id))
            self._best_effort_state(run_id, "accounting_unknown", "ACCOUNTING_UNAVAILABLE")
            raise AgentError("ACCOUNTING_UNAVAILABLE", 503, "accounting_unknown")

    def _best_effort(self, action):
        try:
            action()
        except Exception:
            pass

    def _best_effort_state(self, run_id, state, code=None):
        self._best_effort(lambda: self.ledger.set_run_state(run_id, state, code))
