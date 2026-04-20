"""Fractional Kelly sizing for binary markets.

Polymarket contracts pay $1 for a YES that resolves true. Buying YES at
price p has payoff (1/p - 1) per dollar won, and loses 1 per dollar lost.

Edge (for BUY_YES at price `price` when true probability is `p_true`):
    b = (1/price) - 1          # odds received on win
    f* = p_true - (1 - p_true) / b
"""

from __future__ import annotations


def fractional_kelly(
    *, p_true: float, price: float, fraction: float = 0.33
) -> float:
    """Return size as a fraction of bankroll in [0, 1]. Negative => don't take."""
    if not (0.0 < price < 1.0):
        return 0.0
    b = (1.0 / price) - 1.0
    if b <= 0:
        return 0.0
    f_star = p_true - (1.0 - p_true) / b
    if f_star <= 0:
        return 0.0
    return max(0.0, min(1.0, f_star * fraction))
