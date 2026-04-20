"""Spread / depth distortion signals.

Returns:
  (distortion_correction, liquidity_score)

`distortion_correction`: additive fair-value tweak. Wide spreads tell us the
last trade is stale; we collapse toward mid.

`liquidity_score`: 0..1, used by the Opportunity Score.
"""

from __future__ import annotations

from weather_alpha.data.market.polymarket_clob import OrderBook


WIDE_SPREAD_THRESHOLD = 0.08  # 8% of mid — anything wider is "fake price" territory


def liquidity_distortion(book: OrderBook) -> tuple[float, float]:
    spread = book.spread_pct
    if spread is None:
        return (0.0, 0.0)

    bid_depth, ask_depth = book.depth_within(0.01)
    total_depth = bid_depth + ask_depth
    # Logistic on $500 typical depth — tuned empirically later.
    liquidity_score = min(1.0, total_depth / 1000.0)

    distortion = 0.0
    if spread > WIDE_SPREAD_THRESHOLD:
        # Discount any price-based signal — the book is thin. No fair-value
        # adjustment but score will be low.
        distortion = 0.0

    return (distortion, liquidity_score)
