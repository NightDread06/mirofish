from weather_alpha.data.weather.open_meteo import EnsembleForecast, MemberTrack
from weather_alpha.edge.adjusted_probability import adjusted_probability
from weather_alpha.edge.opportunity_score import decide_action, opportunity_score
from weather_alpha.edge.weather_model import probability_over_threshold


def _forecast(members: dict[int, float], date: str = "2026-04-21") -> EnsembleForecast:
    tracks = [
        MemberTrack(member=m, variable="temp_max_c", values={date: v})
        for m, v in members.items()
    ]
    return EnsembleForecast(lat=0, lon=0, issued_at="now", tracks=tracks)


def test_probability_from_ensemble_members():
    # 10 members, 7 above 30C -> P(>=30) = 0.7
    members = {i: (31.0 if i <= 7 else 28.0) for i in range(1, 11)}
    fc = _forecast(members)
    p = probability_over_threshold(
        fc, variable="temp_max_c", valid_date="2026-04-21",
        threshold=30.0, comparator="gte",
    )
    assert abs(p - 0.7) < 1e-9


def test_probability_gaussian_fallback_from_deterministic():
    # Single deterministic member => Gaussian around mu with fallback sigma.
    fc = _forecast({0: 30.0})
    p_eq = probability_over_threshold(
        fc, variable="temp_max_c", valid_date="2026-04-21",
        threshold=30.0, comparator="gte",
    )
    assert abs(p_eq - 0.5) < 1e-6


def test_adjusted_probability_sums_and_clamps():
    adj = adjusted_probability(0.58, 0.09, 0.04, 0.0)
    assert abs(adj.p_adj - 0.71) < 1e-6
    over = adjusted_probability(0.9, 0.2, 0.0, 0.0)
    assert over.p_adj == 1.0
    under = adjusted_probability(0.1, -0.5, 0.0, 0.0)
    assert under.p_adj == 0.0


def test_decide_action():
    assert decide_action(0.05, 0.03) == "BUY_YES"
    assert decide_action(-0.05, 0.03) == "BUY_NO"
    assert decide_action(0.02, 0.03) == "SPREAD"
    assert decide_action(0.005, 0.03) == "WAIT"


def test_opportunity_score_weights():
    s = opportunity_score(
        edge=0.1, historical_error=0.1, liquidity=1.0,
        freshness=1.0, convexity=1.0, hedgeability=1.0,
    )
    # 30*0.1 + 25*0.1 + 15*1 + 15*1 + 10*1 + 5*1 = 3 + 2.5 + 15 + 15 + 10 + 5
    assert abs(s - 50.5) < 1e-9
