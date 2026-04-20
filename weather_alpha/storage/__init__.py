"""Storage layer: SQLite (WAL) via SQLAlchemy Core."""

from .db import get_engine, init_db
from .dao import (
    Market,
    Snapshot,
    upsert_market,
    record_snapshot,
    record_forecast,
    record_paper_trade,
    list_active_markets,
    get_market,
    latest_snapshot,
    recent_snapshots,
    open_paper_positions,
    daily_realized_pnl,
    kill_switch_status,
    trip_kill_switch,
    reset_kill_switch,
)

__all__ = [
    "get_engine",
    "init_db",
    "Market",
    "Snapshot",
    "upsert_market",
    "record_snapshot",
    "record_forecast",
    "record_paper_trade",
    "list_active_markets",
    "get_market",
    "latest_snapshot",
    "recent_snapshots",
    "open_paper_positions",
    "daily_realized_pnl",
    "kill_switch_status",
    "trip_kill_switch",
    "reset_kill_switch",
]
