"""
Ski dashboard API endpoints.
Provides weather, webcam, conditions, recommendations, and scheduler status.
"""

import logging
import sys
import os
from datetime import datetime
from flask import Blueprint, jsonify, request

logger = logging.getLogger(__name__)

ski_bp = Blueprint("ski", __name__)


def _get_dt() -> datetime:
    """Parse an optional ?time= query parameter, or use now."""
    time_str = request.args.get("time")
    if time_str:
        try:
            return datetime.fromisoformat(time_str)
        except ValueError:
            pass
    return datetime.now()


# ---------------------------------------------------------------------------
# Weather endpoints
# ---------------------------------------------------------------------------

@ski_bp.route("/weather/current")
def weather_current():
    """Current weather conditions at Avoriaz."""
    try:
        from app.weather_service import get_current_conditions
        return jsonify(get_current_conditions())
    except Exception as exc:
        logger.error("Weather current error: %s", exc, exc_info=True)
        return jsonify({"error": str(exc)}), 500


@ski_bp.route("/weather/hourly")
def weather_hourly():
    """Hourly forecast. Query param: hours (default 24)."""
    try:
        from app.weather_service import get_hourly_forecast
        hours = min(int(request.args.get("hours", 24)), 48)
        return jsonify(get_hourly_forecast(hours))
    except Exception as exc:
        logger.error("Weather hourly error: %s", exc, exc_info=True)
        return jsonify({"error": str(exc)}), 500


@ski_bp.route("/weather/daily")
def weather_daily():
    """Daily forecast. Query param: days (default 8)."""
    try:
        from app.weather_service import get_daily_forecast
        days = min(int(request.args.get("days", 8)), 16)
        return jsonify(get_daily_forecast(days))
    except Exception as exc:
        logger.error("Weather daily error: %s", exc, exc_info=True)
        return jsonify({"error": str(exc)}), 500


# ---------------------------------------------------------------------------
# Webcam endpoints
# ---------------------------------------------------------------------------

@ski_bp.route("/cameras")
def cameras():
    """List all configured webcam sources."""
    try:
        from app.webcam_service import get_available_cameras
        return jsonify(get_available_cameras())
    except Exception as exc:
        logger.error("Cameras error: %s", exc, exc_info=True)
        return jsonify({"error": str(exc)}), 500


# ---------------------------------------------------------------------------
# Ski conditions & recommendations
# ---------------------------------------------------------------------------

@ski_bp.route("/conditions")
def conditions():
    """
    Current ski conditions for all runs.
    Combines simulation data with live weather.
    """
    try:
        # Add ski_assistant to path if needed
        project_root = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        if project_root not in sys.path:
            sys.path.insert(0, project_root)

        from ski_assistant.simulation import get_all_conditions
        dt = _get_dt()
        all_conds = get_all_conditions(dt)
        return jsonify([
            {
                "name": rc.run.name,
                "difficulty": rc.run.difficulty.value,
                "snow_score": round(rc.snow_score, 3),
                "crowd_level": round(rc.crowd_level, 3),
                "crowd_label": rc.crowd_label,
                "snow_surface": rc.snow_surface,
                "enjoyment": round(rc.enjoyment, 3),
            }
            for rc in all_conds
        ])
    except Exception as exc:
        logger.error("Conditions error: %s", exc, exc_info=True)
        return jsonify({"error": str(exc)}), 500


@ski_bp.route("/recommendations")
def recommendations():
    """
    Top 3 recommended runs.
    Query params: difficulty (beginner/intermediate/advanced/all),
                  prioritize_snow (0-1), avoid_crowds (0-1), time (ISO datetime)
    """
    try:
        project_root = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        if project_root not in sys.path:
            sys.path.insert(0, project_root)

        from ski_assistant.decision_engine import UserPreferences, get_top_3

        prefs = UserPreferences(
            prioritize_snow=float(request.args.get("prioritize_snow", 0.5)),
            avoid_crowds=float(request.args.get("avoid_crowds", 0.5)),
            difficulty_level=request.args.get("difficulty", "all"),
        )
        dt = _get_dt()
        top3 = get_top_3(dt, prefs)

        result = []
        for rank, (rc, reason) in enumerate(top3, start=1):
            result.append({
                "rank": rank,
                "name": rc.run.name,
                "difficulty": rc.run.difficulty.value,
                "reason": reason,
                "snow_score": round(rc.snow_score, 3),
                "crowd_level": round(rc.crowd_level, 3),
                "enjoyment": round(rc.enjoyment, 3),
            })
        return jsonify(result)
    except Exception as exc:
        logger.error("Recommendations error: %s", exc, exc_info=True)
        return jsonify({"error": str(exc)}), 500


@ski_bp.route("/day-plan")
def day_plan():
    """
    Hour-by-hour day plan.
    Query params: same as /recommendations plus start_hour (0-23).
    """
    try:
        project_root = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        if project_root not in sys.path:
            sys.path.insert(0, project_root)

        from ski_assistant.decision_engine import UserPreferences, generate_day_plan

        prefs = UserPreferences(
            prioritize_snow=float(request.args.get("prioritize_snow", 0.5)),
            avoid_crowds=float(request.args.get("avoid_crowds", 0.5)),
            difficulty_level=request.args.get("difficulty", "all"),
        )
        dt = _get_dt()
        plan = generate_day_plan(dt, prefs)
        return jsonify(plan)
    except Exception as exc:
        logger.error("Day plan error: %s", exc, exc_info=True)
        return jsonify({"error": str(exc)}), 500


@ski_bp.route("/hidden-gems")
def hidden_gems():
    """Off-the-beaten-path run suggestions."""
    try:
        project_root = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        if project_root not in sys.path:
            sys.path.insert(0, project_root)

        from ski_assistant.decision_engine import get_hidden_gems
        dt = _get_dt()
        gems = get_hidden_gems(dt)
        return jsonify(gems)
    except Exception as exc:
        logger.error("Hidden gems error: %s", exc, exc_info=True)
        return jsonify({"error": str(exc)}), 500


@ski_bp.route("/stress-test")
def stress_test():
    """Adversarial scenario analysis."""
    try:
        project_root = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        if project_root not in sys.path:
            sys.path.insert(0, project_root)

        from ski_assistant.decision_engine import stress_test as _stress_test
        dt = _get_dt()
        return jsonify(_stress_test(dt))
    except Exception as exc:
        logger.error("Stress test error: %s", exc, exc_info=True)
        return jsonify({"error": str(exc)}), 500


@ski_bp.route("/forecast")
def forecast():
    """Combined weather forecast summary (current + hourly + daily)."""
    try:
        from app.weather_service import (
            get_current_conditions,
            get_hourly_forecast,
            get_daily_forecast,
        )
        return jsonify({
            "current": get_current_conditions(),
            "hourly": get_hourly_forecast(24),
            "daily": get_daily_forecast(7),
        })
    except Exception as exc:
        logger.error("Forecast error: %s", exc, exc_info=True)
        return jsonify({"error": str(exc)}), 500


# ---------------------------------------------------------------------------
# Scheduler / health
# ---------------------------------------------------------------------------

@ski_bp.route("/scheduler/status")
def scheduler_status():
    """Return background scheduler state."""
    try:
        from app.scheduler import get_scheduler_status
        return jsonify(get_scheduler_status())
    except Exception as exc:
        logger.error("Scheduler status error: %s", exc, exc_info=True)
        return jsonify({"error": str(exc)}), 500


@ski_bp.route("/scheduler/refresh")
def scheduler_refresh():
    """Manually trigger an immediate weather + camera refresh."""
    try:
        from app.weather_service import refresh_weather_cache
        from app.webcam_service import refresh_camera_status
        weather = refresh_weather_cache()
        cameras = refresh_camera_status()
        return jsonify({"weather": weather, "cameras": cameras})
    except Exception as exc:
        logger.error("Manual refresh error: %s", exc, exc_info=True)
        return jsonify({"error": str(exc)}), 500
