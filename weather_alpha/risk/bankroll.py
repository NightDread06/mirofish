"""Per-market caps and daily-drawdown kill switch."""

from __future__ import annotations

from weather_alpha.config import get_settings
from weather_alpha.storage import dao


def clip_size(size_fraction: float) -> float:
    """Clamp a raw Kelly fraction to the per-market cap."""
    cap = get_settings().max_per_market_pct
    return max(0.0, min(cap, size_fraction))


def drawdown_tripped() -> tuple[bool, str | None]:
    """True if today's realized loss breaches the daily kill-switch."""
    settings = get_settings()
    limit = -abs(settings.daily_drawdown_kill_pct) * settings.bankroll_usd
    realized = dao.daily_realized_pnl()

    # If already tripped, stay tripped for the day.
    tripped, reason = dao.kill_switch_status()
    if tripped:
        return (True, reason)

    if realized <= limit:
        msg = f"daily-drawdown-tripped realized={realized:.2f} limit={limit:.2f}"
        dao.trip_kill_switch(msg)
        return (True, msg)
    return (False, None)
