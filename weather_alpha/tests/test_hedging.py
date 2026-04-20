from weather_alpha.hedging import cross_city_hedge, cross_threshold_hedge, time_hedge
from weather_alpha.storage.dao import Market


def _m(**kw) -> Market:
    base = dict(
        id="x", slug=None, question="q", city="Chicago", country=None,
        lat=41.88, lon=-87.63, threshold_type="temp_max_c", threshold_value=30.0,
        comparator="gte", resolves_at="2026-04-21T23:59:59Z", yes_token_id="y",
        no_token_id="n", active=True,
    )
    base.update(kw)
    return Market(**base)


def test_cross_threshold_picks_next_step_up():
    primary = _m(id="a", threshold_value=30.0)
    t32 = _m(id="b", threshold_value=32.0)
    t35 = _m(id="c", threshold_value=35.0)
    unrelated = _m(id="d", city="NYC", threshold_value=32.0)
    pick = cross_threshold_hedge(primary, [primary, t32, t35, unrelated])
    assert pick is not None and pick.id == "b"


def test_cross_city_picks_closest_same_variable():
    chi = _m(id="chi")
    det = _m(id="det", city="Detroit", lat=42.33, lon=-83.05)
    phx = _m(id="phx", city="Phoenix", lat=33.44, lon=-112.07)
    pick = cross_city_hedge(chi, [chi, det, phx])
    assert pick is not None and pick.id == "det"


def test_time_hedge_picks_other_date_same_market():
    today = _m(id="t1", resolves_at="2026-04-21T23:59:59Z")
    tomorrow = _m(id="t2", resolves_at="2026-04-22T23:59:59Z")
    pick = time_hedge(today, [today, tomorrow])
    assert pick is not None and pick.id == "t2"
