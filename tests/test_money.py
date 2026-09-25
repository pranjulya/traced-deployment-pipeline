from decimal import Decimal

from app.money import NANO, compute_charge, format_nano, to_nano


def test_known_charge_is_exact():
    assert compute_charge(1000, 500, "0.15", "0.60") == Decimal("0.00045")


def test_format_is_nano_scaled_string():
    assert format_nano(Decimal("0.00045")) == "0.000450000"


def test_tiny_charge_is_not_zeroed():
    assert compute_charge(1, 1, "0.15", "0.60") == Decimal("0.000000750")


def test_positive_below_scale_floors_to_one_nano():
    assert to_nano(Decimal("1E-10")) == NANO


def test_exact_zero_stays_zero():
    assert to_nano(Decimal(0)) == Decimal(0)
