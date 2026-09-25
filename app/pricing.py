"""Price table lookup.

The runtime table is app/prices.json. tests/test_pricing.py asserts it matches
the frozen oracle tests/fixtures/prices.json. A missing price returns None so
the caller records an unknown charge rather than zero.
"""

import json
from datetime import date
from pathlib import Path

DEFAULT_PRICES_PATH = Path(__file__).resolve().parent / "prices.json"


class PriceTable:
    def __init__(self, path=DEFAULT_PRICES_PATH):
        with Path(path).open(encoding="utf-8") as handle:
            data = json.load(handle)
        self.price_version = data["price_version"]
        self.money = data["money"]
        self._models = list(data["models"])

    def price_for(self, model_alias: str, when: date):
        """Return the applicable model price row, or None when no price applies."""
        best = None
        for model in self._models:
            if model["alias"] != model_alias:
                continue
            effective_from = date.fromisoformat(model["effective_from"])
            if effective_from <= when:
                if best is None or effective_from > date.fromisoformat(best["effective_from"]):
                    best = model
        return best
