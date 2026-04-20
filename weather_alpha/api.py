"""FastAPI dashboard.

Pages:
  /               Portfolio dashboard (current money + open positions summary).
  /portfolio      Detailed open positions table.
  /history        All historical trades (paper + live).
  /opportunities  Latest scanner output (JSON).

Endpoints (JSON):
  /api/status
  /api/balance
  /api/positions
  /api/history
  /api/opportunities
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy import text

from weather_alpha.config import get_settings
from weather_alpha.engine import TickResult, run_tick
from weather_alpha.storage import dao, get_engine


TEMPLATE_DIR = Path(__file__).with_name("templates")

_LAST_TICK: TickResult | None = None
_LAST_TICK_AT: str | None = None


def create_app() -> FastAPI:
    app = FastAPI(title="Weather Alpha", version="0.1.0")

    @app.get("/api/status")
    def status() -> dict:
        tripped, reason = dao.kill_switch_status()
        return {
            "live_trading": get_settings().live_trading,
            "kill_switch_tripped": tripped,
            "kill_switch_reason": reason,
            "last_tick_at": _LAST_TICK_AT,
            "now": datetime.now(timezone.utc).isoformat(),
        }

    @app.get("/api/balance")
    def balance() -> dict:
        s = get_settings()
        realized = dao.daily_realized_pnl()
        positions = dao.open_paper_positions()
        at_risk = sum(float(p["size_usd"] or 0.0) for p in positions)
        # Simple unrealized proxy: mark open positions at last known mid.
        unrealized = 0.0
        for p in positions:
            snap = dao.latest_snapshot(p["market_id"])
            mid = snap.yes_mid if snap else None
            if mid is None:
                continue
            side = p["side"]
            avg_price = float(p["avg_price"])
            size = float(p["size_usd"])
            if side == "BUY_YES":
                unrealized += size * (mid - avg_price) / max(avg_price, 1e-4)
            elif side == "BUY_NO":
                unrealized += size * ((1 - mid) - (1 - avg_price)) / max(1 - avg_price, 1e-4)

        return {
            "bankroll_usd": s.bankroll_usd,
            "realized_pnl_today": realized,
            "unrealized_pnl": unrealized,
            "at_risk_usd": at_risk,
            "free_cash_usd": s.bankroll_usd - at_risk,
        }

    @app.get("/api/positions")
    def positions() -> list[dict]:
        rows = dao.open_paper_positions()
        out = []
        for p in rows:
            m = dao.get_market(p["market_id"])
            snap = dao.latest_snapshot(p["market_id"])
            out.append({
                "market_id": p["market_id"],
                "question": m.question if m else p["market_id"],
                "city": m.city if m else None,
                "side": p["side"],
                "size_usd": float(p["size_usd"]),
                "avg_price": float(p["avg_price"]),
                "last_mid": snap.yes_mid if snap else None,
                "opened_at": p["opened_at"],
            })
        return out

    @app.get("/api/history")
    def history(limit: int = 200) -> list[dict]:
        engine = get_engine()
        with engine.connect() as conn:
            rows = conn.execute(
                text(
                    """
                    SELECT 'paper' AS venue, id, market_id, side, size_usd, price,
                           status, pnl_usd, opened_at, closed_at, reason
                    FROM trades_paper
                    UNION ALL
                    SELECT 'live' AS venue, id, market_id, side, size_usd, price,
                           status, pnl_usd, opened_at, closed_at, reason
                    FROM trades_live
                    ORDER BY opened_at DESC
                    LIMIT :lim
                    """
                ),
                {"lim": limit},
            ).mappings().all()
        return [dict(r) for r in rows]

    @app.get("/api/opportunities")
    def opportunities() -> list[dict]:
        if _LAST_TICK is None:
            return []
        return [
            {
                "market_id": o.market_id,
                "question": o.question,
                "p_model": o.p_model,
                "p_adj": o.p_adj,
                "market_price": o.market_price,
                "edge": o.edge,
                "action": o.action,
                "score": o.score,
                "confidence": o.confidence,
                "hedge": o.hedge_suggestion,
            }
            for o in _LAST_TICK.opportunities
        ]

    @app.post("/api/rescan")
    async def rescan() -> dict:
        global _LAST_TICK, _LAST_TICK_AT
        _LAST_TICK = await run_tick(execute=False)
        _LAST_TICK_AT = datetime.now(timezone.utc).isoformat()
        return {"opportunities": len(_LAST_TICK.opportunities)}

    @app.get("/", response_class=HTMLResponse)
    def home() -> str:
        return _render("home.html")

    @app.get("/portfolio", response_class=HTMLResponse)
    def portfolio_page() -> str:
        return _render("portfolio.html")

    @app.get("/history", response_class=HTMLResponse)
    def history_page() -> str:
        return _render("history.html")

    @app.get("/opportunities", response_class=HTMLResponse)
    def opportunities_page() -> str:
        return _render("opportunities.html")

    return app


def _render(name: str) -> str:
    path = TEMPLATE_DIR / name
    return path.read_text(encoding="utf-8")


def record_tick_result(result: TickResult) -> None:
    """Scheduler hands the latest tick to the dashboard."""
    global _LAST_TICK, _LAST_TICK_AT
    _LAST_TICK = result
    _LAST_TICK_AT = datetime.now(timezone.utc).isoformat()
