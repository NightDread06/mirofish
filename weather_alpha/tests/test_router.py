import os

from weather_alpha import config as cfg
from weather_alpha.execution.router import Order, place_order
from weather_alpha.storage import dao
from weather_alpha.storage.dao import Market


def _seed_market() -> None:
    dao.upsert_market(Market(
        id="0xabc", slug=None, question="q", city="Chicago", country=None,
        lat=41.88, lon=-87.63, threshold_type="temp_max_c",
        threshold_value=30.0, comparator="gte", resolves_at=None,
        yes_token_id="y", no_token_id="n", active=True,
    ))


def test_paper_order_fills_and_journals():
    _seed_market()
    res = place_order(Order(market_id="0xabc", side="BUY_YES",
                            size_usd=10.0, limit_price=0.5, reason="test"))
    assert res.ok and res.mode == "paper" and res.trade_id is not None
    assert len(dao.open_paper_positions()) == 1


def test_rejects_when_kill_switch_tripped():
    _seed_market()
    dao.trip_kill_switch("manual-test")
    res = place_order(Order(market_id="0xabc", side="BUY_YES",
                            size_usd=10.0, limit_price=0.5, reason="test"))
    assert not res.ok and res.mode == "rejected"
    dao.reset_kill_switch()


def test_live_without_key_raises():
    os.environ["LIVE_TRADING"] = "1"
    os.environ.pop("POLYMARKET_PRIVATE_KEY", None)
    os.environ.pop("POLYMARKET_FUNDER_ADDRESS", None)
    cfg.get_settings.cache_clear()
    try:
        raised = False
        try:
            place_order(Order(market_id="0xabc", side="BUY_YES",
                              size_usd=10.0, limit_price=0.5, reason="test"))
        except RuntimeError as e:
            raised = True
            assert "LIVE_TRADING" in str(e)
        assert raised, "live mode must refuse without credentials"
    finally:
        os.environ["LIVE_TRADING"] = "0"
        cfg.get_settings.cache_clear()
