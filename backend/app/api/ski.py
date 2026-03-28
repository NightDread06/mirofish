"""
Ski API Routes
==============
Endpoints for the Avoriaz / Portes du Soleil live dashboard.
"""

from __future__ import annotations

import logging
from datetime import datetime

from flask import jsonify, request

from . import ski_bp
from ..live_data import (
    fetch_cameras,
    fetch_conditions,
    fetch_day_plan,
    fetch_forecast,
    fetch_recommendations,
    fetch_stress_tests,
    refresh_all,
)
from ..scheduler import get_scheduler_status

logger = logging.getLogger('mirofish.api.ski')


# ---------------------------------------------------------------------------
# GET /api/ski/conditions
# ---------------------------------------------------------------------------

@ski_bp.route('/conditions', methods=['GET'])
def get_conditions():
    """
    Current ski conditions: temperature, snow depth/quality,
    visibility, wind, crowd summary.
    """
    try:
        data = fetch_conditions()
        return jsonify({'success': True, 'data': data})
    except Exception as exc:
        logger.error("GET /conditions error: %s", exc)
        return jsonify({'success': False, 'error': str(exc)}), 500


# ---------------------------------------------------------------------------
# GET /api/ski/recommendations
# ---------------------------------------------------------------------------

@ski_bp.route('/recommendations', methods=['GET'])
def get_recommendations():
    """
    Top-3 recommended runs for the current moment.

    Optional query params:
      prioritize_snow   float 0–1  (default 0.5)
      avoid_crowds      float 0–1  (default 0.5)
      difficulty_level  str        (beginner|intermediate|advanced|all)
    """
    prefs = {
        'prioritize_snow':  float(request.args.get('prioritize_snow', 0.5)),
        'avoid_crowds':     float(request.args.get('avoid_crowds',    0.5)),
        'difficulty_level': request.args.get('difficulty_level', 'all'),
    }
    try:
        data = fetch_recommendations(prefs)
        return jsonify({'success': True, 'data': data})
    except Exception as exc:
        logger.error("GET /recommendations error: %s", exc)
        return jsonify({'success': False, 'error': str(exc)}), 500


# ---------------------------------------------------------------------------
# GET /api/ski/day-plan
# ---------------------------------------------------------------------------

@ski_bp.route('/day-plan', methods=['GET'])
def get_day_plan():
    """
    Hour-by-hour skiing itinerary for today.

    Accepts the same preference query params as /recommendations.
    """
    prefs = {
        'prioritize_snow':  float(request.args.get('prioritize_snow', 0.5)),
        'avoid_crowds':     float(request.args.get('avoid_crowds',    0.5)),
        'difficulty_level': request.args.get('difficulty_level', 'all'),
    }
    try:
        data = fetch_day_plan(prefs)
        return jsonify({'success': True, 'data': data})
    except Exception as exc:
        logger.error("GET /day-plan error: %s", exc)
        return jsonify({'success': False, 'error': str(exc)}), 500


# ---------------------------------------------------------------------------
# GET /api/ski/cameras
# ---------------------------------------------------------------------------

@ski_bp.route('/cameras', methods=['GET'])
def get_cameras():
    """Live webcam list with online/offline status."""
    try:
        data = fetch_cameras()
        return jsonify({'success': True, 'data': data})
    except Exception as exc:
        logger.error("GET /cameras error: %s", exc)
        return jsonify({'success': False, 'error': str(exc)}), 500


# ---------------------------------------------------------------------------
# GET /api/ski/forecast
# ---------------------------------------------------------------------------

@ski_bp.route('/forecast', methods=['GET'])
def get_forecast():
    """8-day weather forecast for Avoriaz."""
    try:
        data = fetch_forecast()
        return jsonify({'success': True, 'data': data})
    except Exception as exc:
        logger.error("GET /forecast error: %s", exc)
        return jsonify({'success': False, 'error': str(exc)}), 500


# ---------------------------------------------------------------------------
# GET /api/ski/stress-tests
# ---------------------------------------------------------------------------

@ski_bp.route('/stress-tests', methods=['GET'])
def get_stress_tests():
    """Scenario analysis: warm spell, peak crowds, storm day."""
    try:
        data = fetch_stress_tests()
        return jsonify({'success': True, 'data': data})
    except Exception as exc:
        logger.error("GET /stress-tests error: %s", exc)
        return jsonify({'success': False, 'error': str(exc)}), 500


# ---------------------------------------------------------------------------
# POST /api/ski/refresh
# ---------------------------------------------------------------------------

@ski_bp.route('/refresh', methods=['POST'])
def manual_refresh():
    """Force-refresh all cached ski data immediately."""
    try:
        summary = refresh_all()
        return jsonify({'success': True, 'data': summary})
    except Exception as exc:
        logger.error("POST /refresh error: %s", exc)
        return jsonify({'success': False, 'error': str(exc)}), 500


# ---------------------------------------------------------------------------
# GET /api/ski/status
# ---------------------------------------------------------------------------

@ski_bp.route('/status', methods=['GET'])
def get_status():
    """Scheduler and cache status."""
    return jsonify({
        'success': True,
        'data': {
            'scheduler': get_scheduler_status(),
            'server_time': datetime.utcnow().isoformat() + 'Z',
        },
    })
