"""
Lightweight standalone server for the Avoriaz Ski Assistant.
Serves the ski API + Vue SPA without the heavy CAMEL-OASIS/torch backend.
"""

import os
import sys

# Ensure ski_assistant package is importable
_here = os.path.dirname(os.path.abspath(__file__))
if _here not in sys.path:
    sys.path.insert(0, _here)

from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

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

app = Flask(__name__)
app.json.ensure_ascii = False
CORS(app, resources={r"/api/*": {"origins": "*"}})


# ── helpers ────────────────────────────────────────────────────────────────

def _parse_params():
    time_str = request.args.get('time')
    dt = datetime(2026, 3, 28, 10, 0)
    if time_str:
        for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M", "%Y-%m-%d"):
            try:
                dt = datetime.strptime(time_str, fmt)
                break
            except ValueError:
                continue
    prefs = UserPreferences(
        prioritize_snow=float(request.args.get('prioritize_snow', 0.5)),
        avoid_crowds=float(request.args.get('avoid_crowds', 0.5)),
        difficulty_level=request.args.get('difficulty', 'all'),
    )
    tourists = float(request.args.get('tourists', 1.0))
    seed = int(request.args.get('seed', 42))
    return dt, prefs, tourists, seed


def _rc_to_dict(rc):
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


# ── API endpoints ──────────────────────────────────────────────────────────

@app.route('/health')
def health():
    return {"status": "ok", "service": "ski-assistant"}


@app.route('/api/ski/dashboard')
def dashboard():
    dt, prefs, tourists, seed = _parse_params()
    top3 = get_top_3(dt, prefs, tourists, seed)
    return jsonify({"timestamp": dt.isoformat(), "top_3": [_rc_to_dict(rc) for rc in top3]})


@app.route('/api/ski/strategy')
def strategy():
    dt, prefs, tourists, seed = _parse_params()
    result = []
    for s in get_time_strategy(dt, prefs, tourists, seed):
        result.append({
            "slot": s.slot, "time_range": s.time_range, "rationale": s.rationale,
            "top_runs": [_rc_to_dict(rc) for rc in s.top_runs],
            "avoid_runs": [_rc_to_dict(rc) for rc in s.avoid_runs],
        })
    return jsonify({"strategies": result})


@app.route('/api/ski/itinerary')
def itinerary():
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
        "date": plan.date.isoformat(), "slots": slots,
        "total_runs": plan.total_runs, "total_km": plan.total_km,
        "highlights": plan.highlights,
    })


@app.route('/api/ski/gems')
def gems():
    dt, prefs, tourists, seed = _parse_params()
    result = []
    for g in get_hidden_gems(dt, prefs, tourists, seed):
        result.append({
            "run": _rc_to_dict(g.conditions)["run"],
            "conditions": _rc_to_dict(g.conditions),
            "why_hidden": g.why_hidden,
            "why_excellent": g.why_excellent,
            "alpha_score": g.alpha_score,
        })
    return jsonify({"gems": result})


@app.route('/api/ski/sensitivity')
def sensitivity():
    dt, _, tourists, seed = _parse_params()
    data = []
    for r in sensitivity_analysis(dt, tourists, seed):
        data.append({
            "variable": r.variable, "base_avg": r.base_avg,
            "shocked_avg": r.shocked_avg, "delta": r.delta,
            "pct_change": r.pct_change, "interpretation": r.interpretation,
        })
    return jsonify({"sensitivity": data})


@app.route('/api/ski/stress')
def stress():
    dt, prefs, _, seed = _parse_params()
    result = []
    for s in stress_test(dt, prefs, seed):
        result.append({
            "name": s.name, "description": s.description,
            "top_3": [_rc_to_dict(rc) for rc in s.top_3],
            "worst_3": [_rc_to_dict(rc) for rc in s.worst_3],
            "key_insight": s.key_insight,
        })
    return jsonify({"scenarios": result})


@app.route('/api/ski/rules')
def rules():
    dt, _, _, _ = _parse_params()
    result = [{"condition": r.condition, "action": r.action, "rationale": r.rationale}
              for r in decision_rules(dt)]
    return jsonify({"rules": result})


# ── SPA static file serving ────────────────────────────────────────────────

DIST_DIR = os.path.join(_here, "frontend", "dist")

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def spa(path):
    if path and os.path.exists(os.path.join(DIST_DIR, path)):
        return send_from_directory(DIST_DIR, path)
    return send_from_directory(DIST_DIR, 'index.html')


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    print(f"\n  Ski Assistant running → http://0.0.0.0:{port}\n")
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
