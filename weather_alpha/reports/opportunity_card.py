"""Renders the spec-mandated opportunity card block."""

from __future__ import annotations

from weather_alpha.edge.opportunity_score import Opportunity


def render_card(o: Opportunity, *, size_pct_bankroll: float) -> str:
    error_bias = "Underpriced YES" if o.historical_error > 0 else (
        "Overpriced YES" if o.historical_error < 0 else "Neutral"
    )
    hedge = o.hedge_suggestion or "(none)"
    return (
        f"MARKET: {o.question}\n"
        f"- Historical Poly Accuracy (city): {100 * (1 - abs(o.historical_error)):.0f}%\n"
        f"- Historical Error Bias: {error_bias}\n"
        f"- Model Probability: {100 * o.p_model:.0f}%\n"
        f"- Adjusted Probability: {100 * o.p_adj:.0f}%\n"
        f"- Market Price: {100 * o.market_price:.0f}%\n"
        f"- Edge: {100 * o.edge:+.1f}%\n"
        f"- Hedge Pair: {hedge}\n"
        f"- Action: {o.action}\n"
        f"- Size: {100 * size_pct_bankroll:.2f}% bankroll\n"
        f"- Confidence: {o.confidence:.1f}/10\n"
        f"- Reason: score={o.score:.1f}, liq={o.liquidity:.2f}, fresh={o.freshness:.2f}"
    )
