"""Phase 00 fixture oracle checks.

Stdlib-only so it runs on the host Python 3.9.6 and inside the pinned
Python 3.12 image. It validates that the frozen oracle is internally
consistent and honours the accounting and privacy contracts:

* every case is well formed and uniquely identified;
* each actual provider attempt is accounted exactly once;
* known charges equal the fixture price table computed with Decimal;
* unknown charges are never replaced with zero;
* currencies are never summed together;
* span parentage is resolvable;
* canaries are defined and canary cases assert zero leaks;
* the telemetry allowlist excludes forbidden payload/identity fields.

These are fixture-consistency checks, not application tests: the app
arrives in Phase 01.
"""

import json
import unittest
from decimal import Decimal, ROUND_HALF_EVEN
from pathlib import Path

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def load(name):
    with (FIXTURES / name).open(encoding="utf-8") as fh:
        return json.load(fh)


PRICES = load("prices.json")
CASES_DOC = load("cases.json")
CASES = CASES_DOC["cases"]
CANARIES = load("canaries.json")["canaries"]
ALLOWLIST = load("telemetry-allowlist.json")

PRICE_BY_MODEL = {m["alias"]: m for m in PRICES["models"]}
CURRENCIES = {"USD", "EUR"}
PHASES = {"01", "02", "03", "04", "05", "06"}
REQUIREMENTS = {f"R0{i}" for i in range(1, 9)}
MILLION = Decimal(1_000_000)
MONEY = PRICES["money"]
NANO = Decimal(1).scaleb(-int(MONEY["storage_scale"]))


def compute_charge(model, input_tokens, output_tokens):
    price = PRICE_BY_MODEL[model]
    return (
        Decimal(input_tokens) * Decimal(price["input_per_million"]) / MILLION
        + Decimal(output_tokens) * Decimal(price["output_per_million"]) / MILLION
    )


def to_nano(exact):
    """Quantize to the declared storage scale; never round a positive charge to zero."""
    rounded = exact.quantize(NANO, rounding=ROUND_HALF_EVEN)
    if exact > 0 and rounded == 0:
        return NANO
    return rounded


class TestOracleSchema(unittest.TestCase):
    def test_case_ids_unique(self):
        ids = [c["id"] for c in CASES]
        self.assertEqual(len(ids), len(set(ids)))

    def test_required_case_fields(self):
        for case in CASES:
            for key in ("id", "phase", "requirement", "description", "expected"):
                self.assertIn(key, case, case.get("id"))
            for key in ("http_status", "provider_calls", "attempts", "ledger_charge_total"):
                self.assertIn(key, case["expected"], case["id"])

    def test_phase_and_requirement_ids_valid(self):
        for case in CASES:
            self.assertIn(case["phase"], PHASES, case["id"])
            self.assertTrue(case["requirement"], case["id"])
            for req in case["requirement"]:
                self.assertIn(req, REQUIREMENTS, case["id"])


class TestAttemptAccounting(unittest.TestCase):
    def test_each_attempt_counted_once(self):
        for case in CASES:
            expected = case["expected"]
            self.assertEqual(
                expected["provider_calls"],
                len(expected["attempts"]),
                case["id"],
            )

    def test_attempt_ordinals_are_contiguous(self):
        for case in CASES:
            ordinals = [a["ordinal"] for a in case["expected"]["attempts"]]
            self.assertEqual(ordinals, list(range(1, len(ordinals) + 1)), case["id"])


class TestChargeArithmetic(unittest.TestCase):
    def test_known_charges_match_price_table(self):
        for case in CASES:
            for attempt in case["expected"]["attempts"]:
                if attempt["charge_state"] == "unknown":
                    self.assertIsNone(attempt["charge"], (case["id"], attempt["ordinal"]))
                    continue
                model = attempt["model"]
                self.assertIn(model, PRICE_BY_MODEL, case["id"])
                self.assertEqual(
                    attempt["currency"],
                    PRICE_BY_MODEL[model]["currency"],
                    case["id"],
                )
                if attempt["input_tokens"] is None or attempt["output_tokens"] is None:
                    self.assertEqual(
                        Decimal(attempt["charge"]),
                        Decimal(0),
                        (case["id"], attempt["ordinal"]),
                    )
                else:
                    self.assertEqual(
                        Decimal(attempt["charge"]),
                        to_nano(
                            compute_charge(
                                model, attempt["input_tokens"], attempt["output_tokens"]
                            )
                        ),
                        (case["id"], attempt["ordinal"]),
                    )

    def test_prices_are_exact_decimal_strings(self):
        for model in PRICES["models"]:
            for field in ("input_per_million", "output_per_million"):
                Decimal(model[field])
            self.assertIsInstance(model["input_per_million"], str)


class TestMoneyContract(unittest.TestCase):
    def test_money_contract_declared(self):
        self.assertEqual(MONEY["representation"], "exact_decimal_string")
        self.assertEqual(MONEY["storage_scale"], 9)
        self.assertEqual(MONEY["rounding"], "ROUND_HALF_EVEN")
        self.assertTrue(MONEY["never_zero_positive"])

    def test_positive_charge_never_rounds_to_zero(self):
        self.assertEqual(to_nano(Decimal("1E-10")), NANO)
        self.assertEqual(to_nano(Decimal("1E-9")), Decimal("1E-9"))
        self.assertEqual(to_nano(Decimal("0")), Decimal("0"))
        self.assertEqual(to_nano(Decimal("-0.0")), Decimal("0"))

    def test_stored_charges_respect_scale_and_floor(self):
        for case in CASES:
            for attempt in case["expected"]["attempts"]:
                charge = attempt["charge"]
                if charge is None:
                    continue
                value = Decimal(charge)
                self.assertEqual(value, value.quantize(NANO, rounding=ROUND_HALF_EVEN), (case["id"], attempt["ordinal"]))
                if value > 0:
                    self.assertGreaterEqual(value, NANO, (case["id"], attempt["ordinal"]))


class TestEnums(unittest.TestCase):
    def test_attempt_and_run_fields_use_declared_enums(self):
        enums = CASES_DOC["enum"]
        for case in CASES:
            for attempt in case["expected"]["attempts"]:
                self.assertIn(attempt["status"], enums["attempt_status"], case["id"])
                self.assertIn(attempt["usage_origin"], enums["usage_origin"], case["id"])
                self.assertIn(attempt["charge_state"], enums["charge_state"], case["id"])
            run_state = case["expected"]["run_state"]
            if run_state is not None:
                self.assertIn(run_state, enums["run_state"], case["id"])


class TestUnknownNeverZero(unittest.TestCase):
    def test_unknown_count_matches_attempts(self):
        for case in CASES:
            expected = case["expected"]
            unknown = [a for a in expected["attempts"] if a["charge_state"] == "unknown"]
            self.assertEqual(len(unknown), expected["unknown_attempts"], case["id"])

    def test_unknown_attempts_have_no_charge(self):
        for case in CASES:
            for attempt in case["expected"]["attempts"]:
                # charge_state and usage_origin are independent: a price-lookup
                # miss has known (provider) usage but an unknown charge, while
                # a post-dispatch crash has unknown usage and charge.
                if attempt["charge_state"] == "unknown":
                    self.assertIsNone(attempt["charge"], (case["id"], attempt["ordinal"]))
                if attempt["usage_origin"] == "unknown":
                    self.assertEqual(
                        attempt["charge_state"], "unknown", (case["id"], attempt["ordinal"])
                    )

    def test_unknown_only_cases_do_not_zero_the_ledger(self):
        for case in CASES:
            expected = case["expected"]
            if expected["attempts"] and all(
                a["charge_state"] == "unknown" for a in expected["attempts"]
            ):
                self.assertEqual(expected["ledger_charge_total"], {}, case["id"])


class TestCurrencySeparation(unittest.TestCase):
    def test_totals_equal_known_attempts_per_currency(self):
        for case in CASES:
            expected = case["expected"]
            totals = {}
            for attempt in expected["attempts"]:
                if attempt["charge_state"] == "unknown":
                    continue
                totals[attempt["currency"]] = totals.get(
                    attempt["currency"], Decimal(0)
                ) + Decimal(attempt["charge"])
            declared = {k: Decimal(v) for k, v in expected["ledger_charge_total"].items()}
            self.assertEqual(set(declared), set(totals), case["id"])
            for currency, value in totals.items():
                self.assertEqual(declared[currency], value, (case["id"], currency))

    def test_no_mixed_currency_sum(self):
        for case in CASES:
            for attempt in case["expected"]["attempts"]:
                self.assertIn(attempt["currency"], CURRENCIES, case["id"])


class TestSpanParentage(unittest.TestCase):
    def test_parents_resolve_to_known_spans(self):
        for case in CASES:
            spans = case["expected"].get("spans")
            if spans is None:
                continue
            names = [s["name"] for s in spans]
            roots = [s for s in spans if s["parent"] is None]
            if spans:
                self.assertEqual(len(roots), 1, case["id"])
            for span in spans:
                if span["parent"] is not None:
                    self.assertIn(span["parent"], names, case["id"])


class TestPrivacyContract(unittest.TestCase):
    def test_canaries_defined_and_unique(self):
        ids = [c["id"] for c in CANARIES]
        self.assertTrue(ids)
        self.assertEqual(len(ids), len(set(ids)))
        for canary in CANARIES:
            self.assertTrue(canary["value"].strip())

    def test_canary_cases_assert_zero_hits(self):
        known = {c["id"] for c in CANARIES}
        found = 0
        for case in CASES:
            if "canaries_injected" not in case:
                continue
            found += 1
            self.assertEqual(case["expected"].get("canary_hits"), 0, case["id"])
            for canary_id in case["canaries_injected"]:
                self.assertIn(canary_id, known, case["id"])
        self.assertGreater(found, 0, "no canary case exercises the privacy gate")

    def test_allowlist_excludes_forbidden_attributes(self):
        allowed = set()
        for span in ALLOWLIST["spans"].values():
            allowed.update(span["attributes"])
        for forbidden in ALLOWLIST["forbidden_attributes"]:
            self.assertNotIn(forbidden, allowed, forbidden)

    def test_allowlist_excludes_forbidden_metric_labels(self):
        for forbidden in ALLOWLIST["forbidden_metric_labels"]:
            self.assertNotIn(forbidden, ALLOWLIST["metric_labels"], forbidden)

    def test_evaluation_matrix_negative_cases_present(self):
        ids = {c["id"] for c in CASES}
        for required in (
            "tool-failure",
            "client-cancelled-before-dispatch",
            "provider-timeout-unknown",
            "missing-usage",
            "price-lookup-miss",
            "ledger-commit-fail-before-dispatch",
            "ledger-commit-fail-after-provider",
            "crash-before-pending-commit",
            "crash-before-dispatch",
            "crash-after-dispatch",
            "duplicate-same-key",
            "provider-429-then-success",
            "provider-auth-error-not-retried",
        ):
            self.assertIn(required, ids, required)

    def test_truth_paths_are_unsampled(self):
        sampling = ALLOWLIST["sampling"]
        self.assertFalse(sampling["metrics_sampled"])
        self.assertFalse(sampling["accounting_sampled"])
        self.assertFalse(sampling["tail_sampling"])


class TestFixtureVersions(unittest.TestCase):
    def test_all_fixtures_share_one_version(self):
        versions = {
            PRICES["fixtures_version"],
            CASES_DOC["fixtures_version"],
            load("canaries.json")["fixtures_version"],
            ALLOWLIST["fixtures_version"],
        }
        self.assertEqual(len(versions), 1, versions)


if __name__ == "__main__":
    unittest.main(verbosity=2)
