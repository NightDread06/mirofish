"""Portfolio-level exposure cap with a simple correlation proxy.

Two markets on the same city share risk; we halve their combined size if
exposure to that city would exceed 2x the per-market cap.
"""

from __future__ import annotations

from collections import defaultdict

from weather_alpha.config import get_settings
from weather_alpha.storage import dao


def portfolio_cap(
    *, market_city: str | None, proposed_size_usd: float
) -> float:
    settings = get_settings()
    cap_per_market = settings.max_per_market_pct * settings.bankroll_usd
    city_cap = 2.0 * cap_per_market  # max $ exposure per city

    existing = dao.open_paper_positions()
    by_city: dict[str, float] = defaultdict(float)
    for pos in existing:
        mid = pos["market_id"]
        m = dao.get_market(mid)
        city = (m.city if m else None) or "_unknown"
        by_city[city] += float(pos["size_usd"] or 0.0)

    city_key = market_city or "_unknown"
    available = max(0.0, city_cap - by_city[city_key])
    return max(0.0, min(proposed_size_usd, available))
