from __future__ import annotations

import math
import re
from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable, List

OCC_PATTERN = re.compile(r"^O:(?P<root>[A-Z]{1,6})(?P<yy>\d{2})(?P<mm>\d{2})(?P<dd>\d{2})(?P<cp>[CP])(?P<strike>\d{8})$")


def parse_occ_strike(ticker: str) -> float:
    """
    Parse an OCC-formatted option ticker and return the strike as float.

    Example: O:RZLV251107C00005500 -> 5.5
    """
    match = OCC_PATTERN.match(ticker)
    if not match:
        raise ValueError(f"Invalid OCC option ticker: {ticker}")
    strike_int = int(match.group("strike"))
    return strike_int / 1000.0


def build_occ_option_ticker(underlying: str, expiration_date: str, contract_type: str, strike: float) -> str:
    """
    Build an OCC-formatted option ticker from pieces.

    expiration_date must be YYYY-MM-DD.
    contract_type should be 'call' or 'put'.
    """
    exp = expiration_date.replace("-", "")
    if len(exp) != 8:
        raise ValueError("expiration_date must be in YYYY-MM-DD format")
    yy = exp[2:4]
    mm = exp[4:6]
    dd = exp[6:8]
    cp = "C" if contract_type.lower().startswith("c") else "P"
    strike_int = int(Decimal(strike).scaleb(3).to_integral_value(rounding=ROUND_HALF_UP))
    strike_str = f"{strike_int:08d}"
    return f"O:{underlying.upper()}{yy}{mm}{dd}{cp}{strike_str}"


def build_occ_option_list(
    underlying: str, expiration_date: str, contract_type: str, strikes: Iterable[float]
) -> List[str]:
    """Build a list of OCC tickers for the given strikes."""
    return [
        build_occ_option_ticker(underlying, expiration_date, contract_type, strike)
        for strike in strikes
    ]


def generate_strike_ladder(
    strike: float | None,
    strike_gte: float | None,
    strike_lte: float | None,
    step: float = 0.5,
) -> List[float]:
    """
    Generate a list of strikes based on provided filters.

    If strike is provided, returns [strike].
    Otherwise uses gte/lte boundaries (defaults to 0.5-10).
    """
    if strike is not None:
        return [strike]

    start = strike_gte if strike_gte is not None else 0.5
    end = strike_lte if strike_lte is not None else 10.0
    if end < start:
        start, end = end, start
    strikes = []
    current = Decimal(str(start))
    end_dec = Decimal(str(end))
    step_dec = Decimal(str(step))

    while current <= end_dec + Decimal("0.0001"):
        strikes.append(float(current))
        current += step_dec

    return strikes
