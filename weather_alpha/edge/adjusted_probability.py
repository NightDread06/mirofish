"""Combine model + historical + crowd + liquidity corrections into p_adj."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Adjustment:
    p_model: float
    b_hist: float
    b_crowd: float
    b_liq: float
    p_adj: float


def adjusted_probability(
    p_model: float, b_hist: float = 0.0, b_crowd: float = 0.0, b_liq: float = 0.0
) -> Adjustment:
    raw = p_model + b_hist + b_crowd + b_liq
    p_adj = max(0.0, min(1.0, raw))
    return Adjustment(p_model=p_model, b_hist=b_hist, b_crowd=b_crowd, b_liq=b_liq, p_adj=p_adj)
