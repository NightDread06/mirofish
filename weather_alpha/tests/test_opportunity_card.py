from weather_alpha.edge.opportunity_score import Opportunity
from weather_alpha.reports.opportunity_card import render_card


def test_card_matches_spec_shape():
    o = Opportunity(
        market_id="0xabc",
        question="Chicago high temp above 30C on 2026-04-21?",
        p_model=0.58,
        p_adj=0.71,
        market_price=0.50,
        edge=0.21,
        action="BUY_YES",
        score=35.2,
        liquidity=0.8,
        freshness=0.9,
        convexity=0.5,
        hedgeability=1.0,
        historical_error=0.09,
        hedge_suggestion="Chicago high >32C @ 0xdef",
        confidence=7.1,
    )
    card = render_card(o, size_pct_bankroll=0.04)
    assert "MARKET: Chicago high temp above 30C on 2026-04-21?" in card
    assert "Model Probability: 58%" in card
    assert "Adjusted Probability: 71%" in card
    assert "Market Price: 50%" in card
    assert "Edge: +21.0%" in card
    assert "Action: BUY_YES" in card
    assert "Size: 4.00% bankroll" in card
    assert "Confidence: 7.1/10" in card
    assert "Historical Error Bias: Underpriced YES" in card
