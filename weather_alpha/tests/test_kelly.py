from weather_alpha.risk.kelly import fractional_kelly


def test_kelly_no_edge_returns_zero():
    # Price exactly equals true probability -> no edge.
    assert fractional_kelly(p_true=0.5, price=0.5) == 0.0


def test_kelly_positive_edge_scales_with_fraction():
    full = fractional_kelly(p_true=0.7, price=0.5, fraction=1.0)
    third = fractional_kelly(p_true=0.7, price=0.5, fraction=0.33)
    assert 0 < third < full <= 1.0
    assert abs(third - full * 0.33) < 1e-9


def test_kelly_clamps_invalid_price():
    assert fractional_kelly(p_true=0.9, price=0.0) == 0.0
    assert fractional_kelly(p_true=0.9, price=1.0) == 0.0
