"""Opportunity Score = weighted sum of our edge signals (see plan/spec)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Opportunity:
    market_id: str
    question: str
    p_model: float
    p_adj: float
    market_price: float       # YES probability implied by the book (best ask for BUY_YES)
    edge: float               # p_adj - market_price (signed)
    action: str               # BUY_YES | BUY_NO | SPREAD | WAIT
    score: float
    liquidity: float
    freshness: float
    convexity: float
    hedgeability: float
    historical_error: float
    hedge_suggestion: str | None
    confidence: float         # 0..10


def opportunity_score(
    *,
    edge: float,
    historical_error: float = 0.0,
    liquidity: float = 0.0,
    freshness: float = 0.5,
    convexity: float = 0.5,
    hedgeability: float = 0.5,
) -> float:
    """Weights match the spec's formula; inputs should all be 0..1."""
    return (
        30.0 * abs(edge)
        + 25.0 * abs(historical_error)
        + 15.0 * liquidity
        + 15.0 * freshness
        + 10.0 * convexity
        + 5.0 * hedgeability
    )


def decide_action(edge: float, min_edge: float) -> str:
    if edge >= min_edge:
        return "BUY_YES"
    if edge <= -min_edge:
        return "BUY_NO"
    if abs(edge) >= min_edge * 0.5:
        return "SPREAD"
    return "WAIT"


def confidence_from(score: float) -> float:
    # 0..10 scaled from score; ~30 points == 7/10.
    return max(0.0, min(10.0, score / 5.0))
