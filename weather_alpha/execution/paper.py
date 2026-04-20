"""Paper-trading executor. Fills at the limit price (marketable) and journals."""

from __future__ import annotations

from weather_alpha.storage import dao

from .router import Order, FillResult


def submit_paper(order: Order) -> FillResult:
    # Simulated marketable fill at the limit price (caller sets it to ask for
    # BUY and bid for SELL, so this is conservative).
    trade_id = dao.record_paper_trade(
        market_id=order.market_id,
        side=order.side,
        size_usd=order.size_usd,
        price=order.limit_price,
        reason=order.reason,
    )
    return FillResult(
        ok=True,
        mode="paper",
        trade_id=trade_id,
        fill_price=order.limit_price,
        message="paper-filled",
    )
