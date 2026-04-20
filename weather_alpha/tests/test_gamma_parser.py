from weather_alpha.data.market.polymarket_gamma import _parse


def test_parse_extracts_city_and_threshold_f_to_c():
    raw = {
        "conditionId": "0x01",
        "slug": "nyc-high-above-90",
        "question": "Will NYC high temp be above 90F on Aug 5?",
        "endDate": "2026-08-05T23:59:59Z",
        "active": True,
        "closed": False,
        "clobTokenIds": ["111", "222"],
    }
    m = _parse(raw)
    assert m is not None
    assert m.city.lower() == "nyc"
    assert m.threshold_type == "temp_max_c"
    assert abs(m.threshold_value - (90 - 32) * 5 / 9) < 1e-6
    assert m.comparator == "gte"
    assert m.yes_token_id == "111" and m.no_token_id == "222"


def test_parse_handles_below_celsius():
    raw = {
        "conditionId": "0x02",
        "slug": "chi-low-under-5c",
        "question": "Will Chicago low be below -5C on Jan 3?",
        "endDate": "2026-01-03T23:59:59Z",
        "active": True,
        "closed": False,
        "clobTokenIds": ["a", "b"],
    }
    m = _parse(raw)
    assert m is not None
    assert m.comparator == "lte"
    assert m.threshold_type == "temp_max_c"  # heuristic; caller can override
    assert m.threshold_value == -5.0
