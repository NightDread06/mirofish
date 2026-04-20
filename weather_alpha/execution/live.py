"""Live order submission via py-clob-client.

Guarded three ways:
  1. `settings.live_trading` must be True (env `LIVE_TRADING=1`)
  2. `settings.assert_live_ready()` must have been called earlier
  3. py-clob-client must be installed (only present when [live] extra is installed)

The journal row is written FIRST (status=QUEUED) so a crash between journal
and submit is recoverable on the next scheduler tick.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import text

from weather_alpha.config import get_settings
from weather_alpha.storage import get_engine

from .router import Order, FillResult


def submit_live(order: Order) -> FillResult:
    settings = get_settings()
    settings.assert_live_ready()

    try:
        from py_clob_client.client import ClobClient  # type: ignore
        from py_clob_client.constants import POLYGON  # type: ignore
        from py_clob_client.order_builder.constants import BUY, SELL  # type: ignore
    except ImportError as e:
        raise RuntimeError(
            "py-clob-client not installed. Reinstall with the [live] extra."
        ) from e

    engine = get_engine()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    with engine.begin() as conn:
        trade_id = int(
            conn.execute(
                text(
                    """
                    INSERT INTO trades_live
                        (market_id, side, size_usd, price, status, opened_at, reason)
                    VALUES
                        (:mid, :side, :size, :price, 'QUEUED', :ts, :reason)
                    RETURNING id
                    """
                ),
                {
                    "mid": order.market_id,
                    "side": order.side,
                    "size": order.size_usd,
                    "price": order.limit_price,
                    "ts": now,
                    "reason": order.reason,
                },
            ).scalar_one()
        )

    client = ClobClient(
        host=settings.polymarket_clob_url,
        key=settings.polymarket_private_key,
        chain_id=POLYGON,
        funder=settings.polymarket_funder_address,
        signature_type=1,
    )
    client.set_api_creds(client.create_or_derive_api_creds())

    clob_side = BUY if order.side.startswith("BUY") else SELL
    size = order.size_usd / max(order.limit_price, 1e-4)

    try:
        resp = client.create_and_post_order(
            {
                "token_id": order.token_id,
                "price": order.limit_price,
                "size": size,
                "side": clob_side,
            }
        )
    except Exception as e:
        with engine.begin() as conn:
            conn.execute(
                text("UPDATE trades_live SET status='CANCELLED', closed_at=:ts, reason=:r WHERE id=:id"),
                {"ts": now, "r": f"submit-failed: {e}", "id": trade_id},
            )
        return FillResult(ok=False, mode="live", trade_id=trade_id, fill_price=None,
                          message=f"submit-failed: {e}")

    broker_id = resp.get("orderID") if isinstance(resp, dict) else None
    with engine.begin() as conn:
        conn.execute(
            text(
                "UPDATE trades_live SET status='FILLED', broker_order_id=:bid WHERE id=:id"
            ),
            {"bid": broker_id, "id": trade_id},
        )
    return FillResult(ok=True, mode="live", trade_id=trade_id, fill_price=order.limit_price,
                      message=f"live-submitted broker_id={broker_id}")
