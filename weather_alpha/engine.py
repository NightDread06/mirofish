"""One-shot pipeline: fetch markets + forecasts + books -> score -> optionally trade.

Used by both the CLI (`scan`) and the scheduler. Splitting it out keeps the
scheduler file small and makes the whole pipeline unit-testable end-to-end.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone

import httpx

from weather_alpha.config import get_settings
from weather_alpha.data.market.polymarket_clob import fetch_book
from weather_alpha.data.market.polymarket_gamma import list_weather_markets, GammaMarket
from weather_alpha.data.weather.open_meteo import fetch_ensemble
from weather_alpha.edge.adjusted_probability import adjusted_probability
from weather_alpha.edge.crowd_bias import crowd_overreaction_score
from weather_alpha.edge.historical_bias import city_threshold_bias
from weather_alpha.edge.liquidity import liquidity_distortion
from weather_alpha.edge.opportunity_score import (
    Opportunity,
    confidence_from,
    decide_action,
    opportunity_score,
)
from weather_alpha.edge.weather_model import probability_over_threshold
from weather_alpha.execution.router import Order, place_order
from weather_alpha.hedging import cross_city_hedge, cross_threshold_hedge, time_hedge
from weather_alpha.risk.bankroll import clip_size
from weather_alpha.risk.kelly import fractional_kelly
from weather_alpha.risk.portfolio import portfolio_cap
from weather_alpha.storage import dao
from weather_alpha.storage.dao import Market, Snapshot


@dataclass(slots=True)
class TickResult:
    opportunities: list[Opportunity]
    orders_placed: list[dict]


async def _snapshot_book(g: GammaMarket, client: httpx.AsyncClient) -> Snapshot | None:
    if not g.yes_token_id:
        return None
    try:
        book = await fetch_book(g.yes_token_id, client=client)
    except Exception:
        return None
    bid_depth, ask_depth = book.depth_within(0.01)
    s = Snapshot(
        market_id=g.id,
        ts=book.ts,
        yes_bid=book.best_bid,
        yes_ask=book.best_ask,
        yes_mid=book.mid,
        spread_pct=book.spread_pct,
        last_trade=None,
        volume_24h=None,
        bid_depth_1pct=bid_depth,
        ask_depth_1pct=ask_depth,
    )
    dao.record_snapshot(s)
    return s


def _g_to_market(g: GammaMarket) -> Market:
    return Market(
        id=g.id, slug=g.slug, question=g.question, city=g.city, country=g.country,
        lat=g.lat, lon=g.lon, threshold_type=g.threshold_type,
        threshold_value=g.threshold_value, comparator=g.comparator,
        resolves_at=g.resolves_at, yes_token_id=g.yes_token_id,
        no_token_id=g.no_token_id, active=g.active,
    )


def _valid_date(resolves_at: str | None) -> str:
    if not resolves_at:
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return resolves_at[:10]


def _lead_hours(resolves_at: str | None) -> float:
    if not resolves_at:
        return 0.0
    try:
        end = datetime.fromisoformat(resolves_at.replace("Z", "+00:00"))
        return max(0.0, (end - datetime.now(timezone.utc)).total_seconds() / 3600.0)
    except ValueError:
        return 0.0


async def run_tick(*, execute: bool = False) -> TickResult:
    settings = get_settings()
    opportunities: list[Opportunity] = []
    orders_placed: list[dict] = []

    async with httpx.AsyncClient(timeout=30.0) as client:
        gamma_markets = await list_weather_markets(client=client)
        tradeable = [
            g for g in gamma_markets
            if g.active and g.lat is not None and g.lon is not None
            and g.threshold_type and g.threshold_value is not None
            and g.yes_token_id
        ]

        # Upsert catalog first.
        for g in tradeable:
            dao.upsert_market(_g_to_market(g))

        # Snapshot books in parallel.
        snapshots = await asyncio.gather(*[_snapshot_book(g, client) for g in tradeable])

        # Group by (lat, lon) to minimize forecast API calls.
        forecasts: dict[tuple[float, float], object] = {}
        for g in tradeable:
            key = (round(g.lat, 2), round(g.lon, 2))
            if key not in forecasts:
                try:
                    forecasts[key] = await fetch_ensemble(g.lat, g.lon, client=client)
                except Exception:
                    forecasts[key] = None

    all_markets = [_g_to_market(g) for g in tradeable]

    for g, snap in zip(tradeable, snapshots):
        if snap is None or snap.yes_ask is None:
            continue
        key = (round(g.lat, 2), round(g.lon, 2))
        fc = forecasts.get(key)
        if fc is None:
            continue

        p_model = probability_over_threshold(
            fc,
            variable=g.threshold_type,
            valid_date=_valid_date(g.resolves_at),
            threshold=g.threshold_value,
            comparator=g.comparator or "gte",
        )
        b_hist = city_threshold_bias(
            city=g.city, threshold_type=g.threshold_type,
            lead_time_hours=_lead_hours(g.resolves_at),
        )
        recent = dao.recent_snapshots(g.id, minutes=180)
        b_crowd = crowd_overreaction_score(recent)
        b_liq, liq_score = liquidity_distortion_proxy(snap)
        adj = adjusted_probability(p_model, b_hist, b_crowd, b_liq)

        market_price = snap.yes_ask  # cost to BUY_YES
        edge = adj.p_adj - market_price
        action = decide_action(edge, settings.min_edge_pct)

        primary_market = _g_to_market(g)
        hedge = (
            cross_threshold_hedge(primary_market, all_markets)
            or cross_city_hedge(primary_market, all_markets)
            or time_hedge(primary_market, all_markets)
        )
        hedge_desc = f"{hedge.question} @ {hedge.id[:10]}" if hedge else None

        freshness = min(1.0, max(0.0, 1.0 - _lead_hours(g.resolves_at) / 72.0))
        convexity = 1.0 if min(market_price, 1 - market_price) < 0.15 else 0.5
        hedgeability = 1.0 if hedge else 0.0

        score = opportunity_score(
            edge=edge, historical_error=b_hist, liquidity=liq_score,
            freshness=freshness, convexity=convexity, hedgeability=hedgeability,
        )

        opp = Opportunity(
            market_id=g.id, question=g.question,
            p_model=p_model, p_adj=adj.p_adj,
            market_price=market_price, edge=edge, action=action, score=score,
            liquidity=liq_score, freshness=freshness, convexity=convexity,
            hedgeability=hedgeability, historical_error=b_hist,
            hedge_suggestion=hedge_desc,
            confidence=confidence_from(score),
        )
        opportunities.append(opp)

        if execute and action in ("BUY_YES", "BUY_NO") and score >= 20.0:
            if action == "BUY_YES":
                p_true, price, side = adj.p_adj, snap.yes_ask, "BUY_YES"
                token = g.yes_token_id
            else:
                p_true, price, side = 1 - adj.p_adj, 1 - (snap.yes_bid or snap.yes_ask), "BUY_NO"
                token = g.no_token_id

            raw_f = fractional_kelly(
                p_true=p_true, price=price, fraction=settings.kelly_fraction,
            )
            f = clip_size(raw_f)
            raw_usd = f * settings.bankroll_usd
            usd = portfolio_cap(market_city=g.city, proposed_size_usd=raw_usd)
            if usd > 0.5:  # ignore sub-$0.50 noise
                fill = place_order(
                    Order(
                        market_id=g.id, side=side, size_usd=usd,
                        limit_price=price, reason=f"score={score:.1f} edge={edge:+.2%}",
                        token_id=token,
                    )
                )
                orders_placed.append(
                    {"market_id": g.id, "side": side, "size_usd": usd,
                     "price": price, "ok": fill.ok, "mode": fill.mode,
                     "msg": fill.message}
                )

    opportunities.sort(key=lambda o: o.score, reverse=True)
    return TickResult(opportunities=opportunities, orders_placed=orders_placed)


def liquidity_distortion_proxy(snap: Snapshot) -> tuple[float, float]:
    """Approximate liquidity_distortion() directly from a stored Snapshot."""
    spread = snap.spread_pct
    total_depth = (snap.bid_depth_1pct or 0.0) + (snap.ask_depth_1pct or 0.0)
    liquidity_score = min(1.0, total_depth / 1000.0)
    return (0.0, liquidity_score)
