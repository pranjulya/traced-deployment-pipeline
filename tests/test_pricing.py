import json
from datetime import date
from pathlib import Path

from app.pricing import PriceTable

ROOT = Path(__file__).resolve().parents[1]


def test_runtime_table_matches_frozen_fixture():
    runtime = json.loads((ROOT / "app" / "prices.json").read_text(encoding="utf-8"))
    fixture = json.loads((ROOT / "tests" / "fixtures" / "prices.json").read_text(encoding="utf-8"))
    assert runtime["models"] == fixture["models"]
    assert runtime["money"] == fixture["money"]
    assert runtime["price_version"] == fixture["price_version"]


def test_price_for_respects_effective_date():
    table = PriceTable()
    assert table.price_for("fake-small", date(2026, 5, 1))["currency"] == "USD"
    assert table.price_for("fake-small", date(2025, 1, 1)) is None
    assert table.price_for("does-not-exist", date(2026, 5, 1)) is None
