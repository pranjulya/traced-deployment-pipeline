"""Money handling.

Exact decimal arithmetic at nano scale, never floats. Frozen by
docs/architecture/accounting-and-api-contract.md: a positive charge is never
rounded to zero.
"""

from decimal import Decimal, ROUND_HALF_EVEN

NANO_SCALE = 9
NANO = Decimal(1).scaleb(-NANO_SCALE)
MILLION = Decimal(1_000_000)


def to_nano(exact: Decimal) -> Decimal:
    """Quantize to nano scale; floor a positive charge to one nano-unit."""
    rounded = exact.quantize(NANO, rounding=ROUND_HALF_EVEN)
    if exact > 0 and rounded == 0:
        return NANO
    return rounded


def format_nano(value: Decimal) -> str:
    """Render a nano-scaled decimal as a fixed 9-place string, never a float."""
    return f"{to_nano(value):.9f}"


def compute_charge(
    input_tokens: int,
    output_tokens: int,
    input_per_million: str,
    output_per_million: str,
) -> Decimal:
    return to_nano(
        Decimal(input_tokens) * Decimal(input_per_million) / MILLION
        + Decimal(output_tokens) * Decimal(output_per_million) / MILLION
    )
