"""Typed DAO helpers. One function per query — keep SQL inline and obvious."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Iterable

from sqlalchemy import text
from sqlalchemy.engine import Engine

from .db import get_engine


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


@dataclass(slots=True)
class Market:
    id: str
    slug: str | None
    question: str
    city: str | None
    country: str | None
    lat: float | None
    lon: float | None
    threshold_type: str | None
    threshold_value: float | None
    comparator: str | None
    resolves_at: str | None
    yes_token_id: str | None
    no_token_id: str | None
    active: bool


@dataclass(slots=True)
class Snapshot:
    market_id: str
    ts: str
    yes_bid: float | None
    yes_ask: float | None
    yes_mid: float | None
    spread_pct: float | None
    last_trade: float | None
    volume_24h: float | None
    bid_depth_1pct: float | None
    ask_depth_1pct: float | None


def upsert_market(m: Market, engine: Engine | None = None) -> None:
    engine = engine or get_engine()
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO markets
                    (id, slug, question, city, country, lat, lon,
                     threshold_type, threshold_value, comparator, resolves_at,
                     yes_token_id, no_token_id, active, updated_at)
                VALUES
                    (:id, :slug, :question, :city, :country, :lat, :lon,
                     :threshold_type, :threshold_value, :comparator, :resolves_at,
                     :yes_token_id, :no_token_id, :active, :updated_at)
                ON CONFLICT(id) DO UPDATE SET
                    slug=excluded.slug,
                    question=excluded.question,
                    city=excluded.city,
                    country=excluded.country,
                    lat=excluded.lat,
                    lon=excluded.lon,
                    threshold_type=excluded.threshold_type,
                    threshold_value=excluded.threshold_value,
                    comparator=excluded.comparator,
                    resolves_at=excluded.resolves_at,
                    yes_token_id=excluded.yes_token_id,
                    no_token_id=excluded.no_token_id,
                    active=excluded.active,
                    updated_at=excluded.updated_at
                """
            ),
            {
                "id": m.id,
                "slug": m.slug,
                "question": m.question,
                "city": m.city,
                "country": m.country,
                "lat": m.lat,
                "lon": m.lon,
                "threshold_type": m.threshold_type,
                "threshold_value": m.threshold_value,
                "comparator": m.comparator,
                "resolves_at": m.resolves_at,
                "yes_token_id": m.yes_token_id,
                "no_token_id": m.no_token_id,
                "active": 1 if m.active else 0,
                "updated_at": _now_iso(),
            },
        )


_MARKET_FIELDS = (
    "id", "slug", "question", "city", "country", "lat", "lon",
    "threshold_type", "threshold_value", "comparator", "resolves_at",
    "yes_token_id", "no_token_id",
)


def _row_to_market(r: dict[str, Any]) -> Market:
    return Market(
        **{k: r.get(k) for k in _MARKET_FIELDS},
        active=bool(r["active"]),
    )


def list_active_markets(engine: Engine | None = None) -> list[Market]:
    engine = engine or get_engine()
    with engine.connect() as conn:
        rows = conn.execute(
            text("SELECT * FROM markets WHERE active = 1 ORDER BY resolves_at ASC")
        ).mappings().all()
    return [_row_to_market(dict(r)) for r in rows]


def get_market(market_id: str, engine: Engine | None = None) -> Market | None:
    engine = engine or get_engine()
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT * FROM markets WHERE id = :mid"),
            {"mid": market_id},
        ).mappings().first()
    return _row_to_market(dict(row)) if row else None


def record_snapshot(s: Snapshot, engine: Engine | None = None) -> None:
    engine = engine or get_engine()
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO market_snapshots
                    (market_id, ts, yes_bid, yes_ask, yes_mid,
                     no_bid, no_ask, spread_pct, last_trade, volume_24h,
                     bid_depth_1pct, ask_depth_1pct)
                VALUES
                    (:market_id, :ts, :yes_bid, :yes_ask, :yes_mid,
                     :no_bid, :no_ask, :spread_pct, :last_trade, :volume_24h,
                     :bid_depth_1pct, :ask_depth_1pct)
                """
            ),
            {
                "market_id": s.market_id,
                "ts": s.ts,
                "yes_bid": s.yes_bid,
                "yes_ask": s.yes_ask,
                "yes_mid": s.yes_mid,
                "no_bid": None if s.yes_ask is None else 1.0 - s.yes_ask,
                "no_ask": None if s.yes_bid is None else 1.0 - s.yes_bid,
                "spread_pct": s.spread_pct,
                "last_trade": s.last_trade,
                "volume_24h": s.volume_24h,
                "bid_depth_1pct": s.bid_depth_1pct,
                "ask_depth_1pct": s.ask_depth_1pct,
            },
        )


def latest_snapshot(market_id: str, engine: Engine | None = None) -> Snapshot | None:
    engine = engine or get_engine()
    with engine.connect() as conn:
        row = conn.execute(
            text(
                """
                SELECT market_id, ts, yes_bid, yes_ask, yes_mid, spread_pct,
                       last_trade, volume_24h, bid_depth_1pct, ask_depth_1pct
                FROM market_snapshots
                WHERE market_id = :mid
                ORDER BY ts DESC
                LIMIT 1
                """
            ),
            {"mid": market_id},
        ).mappings().first()
    return Snapshot(**row) if row else None


def recent_snapshots(
    market_id: str, minutes: int = 60, engine: Engine | None = None
) -> list[Snapshot]:
    engine = engine or get_engine()
    cutoff = (datetime.now(timezone.utc) - timedelta(minutes=minutes)).strftime(
        "%Y-%m-%dT%H:%M:%S.%fZ"
    )
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                """
                SELECT market_id, ts, yes_bid, yes_ask, yes_mid, spread_pct,
                       last_trade, volume_24h, bid_depth_1pct, ask_depth_1pct
                FROM market_snapshots
                WHERE market_id = :mid AND ts >= :cutoff
                ORDER BY ts ASC
                """
            ),
            {"mid": market_id, "cutoff": cutoff},
        ).mappings().all()
    return [Snapshot(**r) for r in rows]


def record_forecast(
    lat: float,
    lon: float,
    issued_at: str,
    valid_date: str,
    variable: str,
    member: int,
    value: float,
    engine: Engine | None = None,
) -> None:
    engine = engine or get_engine()
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO weather_forecasts
                    (lat, lon, issued_at, valid_date, variable, member, value)
                VALUES
                    (:lat, :lon, :issued_at, :valid_date, :variable, :member, :value)
                """
            ),
            {
                "lat": lat,
                "lon": lon,
                "issued_at": issued_at,
                "valid_date": valid_date,
                "variable": variable,
                "member": member,
                "value": value,
            },
        )


def record_paper_trade(
    *,
    market_id: str,
    side: str,
    size_usd: float,
    price: float,
    reason: str,
    engine: Engine | None = None,
) -> int:
    engine = engine or get_engine()
    with engine.begin() as conn:
        result = conn.execute(
            text(
                """
                INSERT INTO trades_paper
                    (market_id, side, size_usd, price, status, opened_at, reason)
                VALUES
                    (:market_id, :side, :size_usd, :price, 'FILLED', :opened_at, :reason)
                RETURNING id
                """
            ),
            {
                "market_id": market_id,
                "side": side,
                "size_usd": size_usd,
                "price": price,
                "opened_at": _now_iso(),
                "reason": reason,
            },
        )
        return int(result.scalar_one())


def open_paper_positions(engine: Engine | None = None) -> list[dict[str, Any]]:
    engine = engine or get_engine()
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                """
                SELECT market_id, side, SUM(size_usd) AS size_usd,
                       AVG(price) AS avg_price, MIN(opened_at) AS opened_at
                FROM trades_paper
                WHERE status IN ('FILLED','QUEUED')
                GROUP BY market_id, side
                """
            )
        ).mappings().all()
    return [dict(r) for r in rows]


def daily_realized_pnl(engine: Engine | None = None) -> float:
    engine = engine or get_engine()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    with engine.connect() as conn:
        val = conn.execute(
            text(
                """
                SELECT COALESCE(SUM(pnl_usd), 0.0)
                FROM trades_paper
                WHERE status = 'SETTLED'
                  AND substr(closed_at, 1, 10) = :today
                """
            ),
            {"today": today},
        ).scalar_one()
    return float(val or 0.0)


def kill_switch_status(engine: Engine | None = None) -> tuple[bool, str | None]:
    engine = engine or get_engine()
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT tripped, reason FROM kill_switch WHERE id = 1")
        ).mappings().first()
    if not row:
        return (False, None)
    return (bool(row["tripped"]), row["reason"])


def trip_kill_switch(reason: str, engine: Engine | None = None) -> None:
    engine = engine or get_engine()
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                UPDATE kill_switch
                SET tripped = 1, tripped_at = :ts, reason = :reason
                WHERE id = 1
                """
            ),
            {"ts": _now_iso(), "reason": reason},
        )


def reset_kill_switch(engine: Engine | None = None) -> None:
    engine = engine or get_engine()
    with engine.begin() as conn:
        conn.execute(
            text("UPDATE kill_switch SET tripped = 0, tripped_at = NULL, reason = NULL WHERE id = 1")
        )
