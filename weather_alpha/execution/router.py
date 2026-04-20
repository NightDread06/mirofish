"""Single entry point for placing an order. Routes to paper or live.

Paper is the default. Live requires LIVE_TRADING=1 + a wallet key.
All orders are journaled to the DB *before* we attempt to submit them.
"""

from __future__ import annotations

from dataclasses import dataclass

from weather_alpha.config import get_settings
from weather_alpha.risk.bankroll import drawdown_tripped


@dataclass(slots=True)
class Order:
    market_id: str
    side: str                # BUY_YES | BUY_NO | SELL_YES | SELL_NO
    size_usd: float
    limit_price: float       # 0..1
    reason: str
    token_id: str | None = None


@dataclass(slots=True)
class FillResult:
    ok: bool
    mode: str                # 'paper' | 'live' | 'rejected'
    trade_id: int | None
    fill_price: float | None
    message: str


def place_order(order: Order) -> FillResult:
    settings = get_settings()

    tripped, reason = drawdown_tripped()
    if tripped:
        return FillResult(ok=False, mode="rejected", trade_id=None, fill_price=None,
                          message=f"kill-switch: {reason}")

    if order.size_usd <= 0:
        return FillResult(ok=False, mode="rejected", trade_id=None, fill_price=None,
                          message="size_usd <= 0")

    if settings.live_trading:
        settings.assert_live_ready()
        from .live import submit_live   # imported lazily so py-clob-client stays optional
        return submit_live(order)

    from .paper import submit_paper
    return submit_paper(order)
