"""
Ski Assistant API endpoints
Exposes the Avoriaz ski decision engine over HTTP.
"""

import os
import sys
from datetime import datetime
from flask import request, jsonify

# Add project root to path so ski_assistant module can be imported
_backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_project_root = os.path.dirname(_backend_dir)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from . import ski_bp
from ski_assistant.decision_engine import (
    UserPreferences,
    get_top_3,
    get_time_strategy,
    generate_day_plan,
    get_hidden_gems,
    sensitivity_analysis,
    stress_test,
    decision_rules,
)


# ──────────────────────────────────────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────────────────────────────────────

def _parse_params():
    """Parse common query parameters from the request."""
    time_str = request.args.get('time')
    if time_str:
        for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M", "%Y-%m-%d"):
            try:
                dt = datetime.strptime(time_str, fmt)
                break
            except ValueError:
                continue
        else:
            dt = datetime(2026, 3, 28, 10, 0)
    else:
        dt = datetime(2026, 3, 28, 10, 0)

    prefs = UserPreferences(
        prioritize_snow=float(request.args.get('prioritize_snow', 0.5)),
        avoid_crowds=float(request.args.get('avoid_crowds', 0.5)),
        difficulty_level=request.args.get('difficulty', 'all'),
    )
    tourists = float(request.args.get('tourists', 1.0))
    seed = int(request.args.get('seed', 42))
    return dt, prefs, tourists, seed


def _rc_to_dict(rc):
    """Serialize a RunConditions object to a plain dict."""
    return {
        "run": {
            "name": rc.run.name,
            "difficulty": rc.run.difficulty.value,
            "altitude_m": rc.run.altitude_m,
            "orientation": rc.run.orientation.value,
            "length_km": rc.run.length_km,
            "primary_lift": rc.run.primary_lift,
            "popularity": rc.run.popularity,
            "flow_score": rc.run.flow_score,
            "notes": rc.run.notes,
        },
        "snow_score": rc.snow_score,
        "crowd_level": rc.crowd_level,
        "crowd_label": rc.crowd_label,
        "enjoyment_score": rc.enjoyment_score,
        "temperature_c": rc.temperature_c,
        "snow_surface": rc.snow_surface,
        "timestamp": rc.timestamp.isoformat(),
        "recommendation_reason": rc.recommendation_reason,
    }


# ──────────────────────────────────────────────────────────────────────────────
# ENDPOINTS
# ──────────────────────────────────────────────────────────────────────────────

@ski_bp.route('/dashboard')
def dashboard():
    """Top-3 run recommendations for the given time and preferences."""
    dt, prefs, tourists, seed = _parse_params()
    top3 = get_top_3(dt, prefs, tourists, seed)
    return jsonify({
        "timestamp": dt.isoformat(),
        "top_3": [_rc_to_dict(rc) for rc in top3],
    })


@ski_bp.route('/strategy')
def strategy():
    """Morning / Midday / Afternoon strategy breakdown."""
    dt, prefs, tourists, seed = _parse_params()
    strategies = get_time_strategy(dt, prefs, tourists, seed)
    result = []
    for s in strategies:
        result.append({
            "slot": s.slot,
            "time_range": s.time_range,
            "rationale": s.rationale,
            "top_runs": [_rc_to_dict(rc) for rc in s.top_runs],
            "avoid_runs": [_rc_to_dict(rc) for rc in s.avoid_runs],
        })
    return jsonify({"strategies": result})


@ski_bp.route('/itinerary')
def itinerary():
    """Hour-by-hour day plan from start_time to ~16:30."""
    dt, prefs, tourists, seed = _parse_params()
    plan = generate_day_plan(dt, prefs, tourists, seed=seed)
    slots = []
    for slot in plan.slots:
        slots.append({
            "start_time": slot.start_time.isoformat(),
            "end_time": slot.end_time.isoformat(),
            "run_name": slot.run.name,
            "run_difficulty": slot.run.difficulty.value,
            "action": slot.action,
            "tip": slot.tip,
            "enjoyment_score": slot.conditions.enjoyment_score,
            "snow_surface": slot.conditions.snow_surface,
            "crowd_label": slot.conditions.crowd_label,
        })
    return jsonify({
        "date": plan.date.isoformat(),
        "slots": slots,
        "total_runs": plan.total_runs,
        "total_km": plan.total_km,
        "highlights": plan.highlights,
    })


@ski_bp.route('/gems')
def gems():
    """Hidden gem runs — high enjoyment, low popularity."""
    dt, prefs, tourists, seed = _parse_params()
    gem_list = get_hidden_gems(dt, prefs, tourists, seed)
    result = []
    for g in gem_list:
        result.append({
            "run": _rc_to_dict(g.conditions)["run"],
            "conditions": _rc_to_dict(g.conditions),
            "why_hidden": g.why_hidden,
            "why_excellent": g.why_excellent,
            "alpha_score": g.alpha_score,
        })
    return jsonify({"gems": result})


@ski_bp.route('/sensitivity')
def sensitivity():
    """Sensitivity analysis: how each variable impacts resort enjoyment."""
    dt, _, tourists, seed = _parse_params()
    results = sensitivity_analysis(dt, tourists, seed)
    data = []
    for r in results:
        data.append({
            "variable": r.variable,
            "base_avg": r.base_avg,
            "shocked_avg": r.shocked_avg,
            "delta": r.delta,
            "pct_change": r.pct_change,
            "interpretation": r.interpretation,
        })
    return jsonify({"sensitivity": data})


@ski_bp.route('/stress')
def stress():
    """Stress test scenarios: warm spell, peak influx, snow drought."""
    dt, prefs, _, seed = _parse_params()
    scenarios = stress_test(dt, prefs, seed)
    result = []
    for s in scenarios:
        result.append({
            "name": s.name,
            "description": s.description,
            "top_3": [_rc_to_dict(rc) for rc in s.top_3],
            "worst_3": [_rc_to_dict(rc) for rc in s.worst_3],
            "key_insight": s.key_insight,
        })
    return jsonify({"scenarios": result})


@ski_bp.route('/rules')
def rules():
    """Plain-English field-ready decision rules."""
    dt, _, _, _ = _parse_params()
    rule_list = decision_rules(dt)
    result = []
    for r in rule_list:
        result.append({
            "condition": r.condition,
            "action": r.action,
            "rationale": r.rationale,
        })
    return jsonify({"rules": result})
