from weather_alpha.storage import dao
from weather_alpha.storage.dao import Market, Snapshot


def test_upsert_and_list_market():
    m = Market(
        id="0xabc", slug="chi-high-30", question="Chicago high >=30C?",
        city="Chicago", country="US", lat=41.88, lon=-87.63,
        threshold_type="temp_max_c", threshold_value=30.0, comparator="gte",
        resolves_at="2026-04-21T23:59:59Z", yes_token_id="y", no_token_id="n",
        active=True,
    )
    dao.upsert_market(m)
    rows = dao.list_active_markets()
    assert len(rows) == 1
    assert rows[0].question == "Chicago high >=30C?"


def test_paper_trade_roundtrip():
    m = Market(id="0xabc", slug=None, question="q", city="Chicago", country=None,
               lat=41.88, lon=-87.63, threshold_type="temp_max_c",
               threshold_value=30.0, comparator="gte",
               resolves_at=None, yes_token_id="y", no_token_id="n", active=True)
    dao.upsert_market(m)
    tid = dao.record_paper_trade(
        market_id="0xabc", side="BUY_YES", size_usd=25.0,
        price=0.42, reason="test",
    )
    assert tid > 0
    pos = dao.open_paper_positions()
    assert len(pos) == 1 and pos[0]["side"] == "BUY_YES"


def test_snapshot_roundtrip():
    m = Market(id="0xabc", slug=None, question="q", city="Chicago", country=None,
               lat=41.88, lon=-87.63, threshold_type="temp_max_c",
               threshold_value=30.0, comparator="gte",
               resolves_at=None, yes_token_id="y", no_token_id="n", active=True)
    dao.upsert_market(m)
    s = Snapshot(market_id="0xabc", ts="2026-04-20T12:00:00.000Z",
                 yes_bid=0.48, yes_ask=0.52, yes_mid=0.50,
                 spread_pct=0.08, last_trade=0.50, volume_24h=1000.0,
                 bid_depth_1pct=300.0, ask_depth_1pct=250.0)
    dao.record_snapshot(s)
    latest = dao.latest_snapshot("0xabc")
    assert latest is not None and latest.yes_mid == 0.50
