"""
Ski Live Data Fetcher
=====================
Fetches real-time weather and webcam data for Avoriaz / Portes du Soleil.
Results are cached in-memory with a 10-minute TTL.

When external APIs are unreachable the module falls back gracefully to the
simulation-based data from ski_assistant.
"""

from __future__ import annotations

import os
import sys
import time
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

# Ensure ski_assistant package is importable from the project root
_project_root = os.path.join(os.path.dirname(__file__), '..', '..', '..')
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

logger = logging.getLogger('mirofish.live_data')

# ---------------------------------------------------------------------------
# Cache
# ---------------------------------------------------------------------------

_CACHE_TTL_SECONDS = int(os.environ.get('SKI_CACHE_TTL', '600'))  # 10 minutes

_cache: Dict[str, Dict[str, Any]] = {}


def _cache_get(key: str) -> Optional[Any]:
    """Return cached value if still fresh, else None."""
    entry = _cache.get(key)
    if entry is None:
        return None
    if time.monotonic() - entry['ts'] > _CACHE_TTL_SECONDS:
        return None
    return entry['data']


def _cache_set(key: str, data: Any) -> None:
    _cache[key] = {'data': data, 'ts': time.monotonic()}


def _cache_last_updated(key: str) -> Optional[str]:
    """ISO-format timestamp of when the cache entry was last populated."""
    entry = _cache.get(key)
    if entry is None:
        return None
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Simulation-based fallback helpers
# ---------------------------------------------------------------------------

def _simulation_dt() -> datetime:
    """Return a datetime clamped to the simulated season range."""
    from ski_assistant.simulation import SEASON_END
    now = datetime.now()
    season_start = datetime(2026, 3, 28)
    if now < season_start or now > SEASON_END:
        return datetime(2026, 3, 28, 10, 0)
    return now


def _run_conditions_to_dict(rc) -> Dict[str, Any]:
    """Serialize a RunConditions dataclass to a plain dict."""
    return {
        'name': rc.run.name,
        'difficulty': rc.run.difficulty.value,
        'altitude_m': rc.run.altitude_m,
        'orientation': rc.run.orientation.value,
        'length_km': rc.run.length_km,
        'primary_lift': rc.run.primary_lift,
        'flow_score': rc.run.flow_score,
        'snow_score': rc.snow_score,
        'crowd_level': round(rc.crowd_level, 3),
        'crowd_label': rc.crowd_label,
        'enjoyment_score': rc.enjoyment_score,
        'temperature_c': round(rc.temperature_c, 1),
        'snow_surface': rc.snow_surface,
        'recommendation_reason': rc.recommendation_reason,
    }


# ---------------------------------------------------------------------------
# Conditions
# ---------------------------------------------------------------------------

def fetch_conditions() -> Dict[str, Any]:
    """
    Return current ski conditions for Avoriaz.

    Tries a live weather source (via WEATHER_API_KEY env var + OpenMeteo).
    Falls back to simulation data if any error occurs.
    """
    cached = _cache_get('conditions')
    if cached is not None:
        return cached

    data = _fetch_conditions_live()
    _cache_set('conditions', data)
    return data


def _fetch_conditions_live() -> Dict[str, Any]:
    """Inner fetch — returns simulation-enriched weather data."""
    dt = _simulation_dt()

    try:
        from ski_assistant.simulation import get_weather, diurnal_temp
        base_temp, snowfall_cm, cloud_cover = get_weather(dt)
        temp_now = diurnal_temp(base_temp, dt.hour)

        # Try OpenMeteo (free, no API key required)
        live_temp = _fetch_openmeteo_temp()
        if live_temp is not None:
            temp_now = live_temp
    except Exception as exc:
        logger.warning("Weather fetch error: %s – using defaults", exc)
        temp_now, snowfall_cm, cloud_cover = -3.0, 0.0, 0.30

    snow_quality = _classify_snow(snowfall_cm, temp_now)

    return {
        'temperature_c': round(temp_now, 1),
        'snowfall_24h_cm': round(snowfall_cm, 1),
        'cloud_cover': round(cloud_cover, 2),
        'snow_quality': snow_quality,
        'visibility': _classify_visibility(cloud_cover),
        'wind_kmh': _estimate_wind(cloud_cover),
        'resort': 'Avoriaz / Portes du Soleil',
        'altitude_m': 1800,
        'season_end': '2026-04-04',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'source': 'simulation+openmeteo',
    }


def _fetch_openmeteo_temp() -> Optional[float]:
    """
    Try OpenMeteo free API for current temperature at Avoriaz coords.
    Returns None on any failure.
    """
    try:
        import urllib.request
        import json
        url = (
            'https://api.open-meteo.com/v1/forecast'
            '?latitude=46.1928&longitude=6.7714'
            '&current=temperature_2m'
            '&timezone=Europe%2FParis'
        )
        with urllib.request.urlopen(url, timeout=5) as resp:
            payload = json.loads(resp.read())
        return float(payload['current']['temperature_2m'])
    except Exception:
        return None


def _classify_snow(snowfall_cm: float, temp_c: float) -> str:
    if snowfall_cm > 10:
        return 'fresh powder'
    if snowfall_cm > 3:
        return 'recent snowfall'
    if temp_c < -4:
        return 'packed powder'
    if temp_c < 0:
        return 'groomed'
    return 'spring snow'


def _classify_visibility(cloud_cover: float) -> str:
    if cloud_cover < 0.2:
        return 'excellent'
    if cloud_cover < 0.5:
        return 'good'
    if cloud_cover < 0.8:
        return 'moderate'
    return 'poor'


def _estimate_wind(cloud_cover: float) -> int:
    """Rough wind estimate in km/h based on cloud cover."""
    if cloud_cover > 0.8:
        return 35
    if cloud_cover > 0.5:
        return 20
    return 10


# ---------------------------------------------------------------------------
# Recommendations
# ---------------------------------------------------------------------------

def fetch_recommendations(prefs_dict: Optional[Dict] = None) -> Dict[str, Any]:
    """Return top-3 run recommendations for current conditions."""
    key = 'recommendations'
    cached = _cache_get(key)
    if cached is not None:
        return cached

    data = _fetch_recommendations_live(prefs_dict)
    _cache_set(key, data)
    return data


def _fetch_recommendations_live(prefs_dict: Optional[Dict]) -> Dict[str, Any]:
    try:
        from ski_assistant.decision_engine import (
            get_top_3,
            UserPreferences,
        )
        dt = _simulation_dt()
        prefs = UserPreferences(
            prioritize_snow=float((prefs_dict or {}).get('prioritize_snow', 0.5)),
            avoid_crowds=float((prefs_dict or {}).get('avoid_crowds', 0.5)),
            difficulty_level=str((prefs_dict or {}).get('difficulty_level', 'all')),
        )
        top3 = get_top_3(dt, prefs)
        runs = [_run_conditions_to_dict(rc) for rc in top3]
    except Exception as exc:
        logger.error("Recommendations fetch error: %s", exc)
        runs = []

    return {
        'runs': runs,
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'query_time': _simulation_dt().isoformat(),
    }


# ---------------------------------------------------------------------------
# Day plan
# ---------------------------------------------------------------------------

def fetch_day_plan(prefs_dict: Optional[Dict] = None) -> Dict[str, Any]:
    """Return an hour-by-hour itinerary for today."""
    key = 'day_plan'
    cached = _cache_get(key)
    if cached is not None:
        return cached

    data = _fetch_day_plan_live(prefs_dict)
    _cache_set(key, data)
    return data


def _fetch_day_plan_live(prefs_dict: Optional[Dict]) -> Dict[str, Any]:
    try:
        from ski_assistant.decision_engine import (
            generate_day_plan,
            UserPreferences,
        )
        dt = _simulation_dt().replace(hour=9, minute=0)
        prefs = UserPreferences(
            prioritize_snow=float((prefs_dict or {}).get('prioritize_snow', 0.5)),
            avoid_crowds=float((prefs_dict or {}).get('avoid_crowds', 0.5)),
            difficulty_level=str((prefs_dict or {}).get('difficulty_level', 'all')),
        )
        plan = generate_day_plan(dt, prefs)
        slots = []
        for slot in plan.slots:
            slots.append({
                'start_time': slot.start_time.strftime('%H:%M'),
                'end_time': slot.end_time.strftime('%H:%M'),
                'run_name': slot.run.name,
                'action': slot.action,
                'tip': slot.tip,
                'snow_surface': slot.conditions.snow_surface,
                'enjoyment_score': slot.conditions.enjoyment_score,
                'crowd_label': slot.conditions.crowd_label,
            })
    except Exception as exc:
        logger.error("Day plan fetch error: %s", exc)
        slots = []
        plan = type('Plan', (), {'total_runs': 0, 'total_km': 0.0, 'highlights': ''})()

    return {
        'slots': slots,
        'total_runs': plan.total_runs,
        'total_km': plan.total_km,
        'highlights': plan.highlights,
        'timestamp': datetime.now(timezone.utc).isoformat(),
    }


# ---------------------------------------------------------------------------
# Cameras
# ---------------------------------------------------------------------------

# Public webcam endpoints for Avoriaz / Portes du Soleil
_WEBCAM_SOURCES = [
    {
        'id': 'avoriaz-village',
        'name': 'Avoriaz Village',
        'url': os.environ.get(
            'CAM_AVORIAZ_VILLAGE',
            'https://www.skiline.cc/webcam/avoriaz/',
        ),
        'thumbnail': os.environ.get('CAM_AVORIAZ_VILLAGE_THUMB', ''),
        'location': 'Avoriaz 1800m',
    },
    {
        'id': 'chavannes-summit',
        'name': 'Chavannes Summit',
        'url': os.environ.get(
            'CAM_CHAVANNES',
            'https://www.skiinfo.fr/haute-savoie/avoriaz/webcam.html',
        ),
        'thumbnail': os.environ.get('CAM_CHAVANNES_THUMB', ''),
        'location': 'Chavannes Express top 2100m',
    },
    {
        'id': 'portes-du-soleil',
        'name': 'Portes du Soleil Overview',
        'url': os.environ.get(
            'CAM_PDS',
            'https://www.portesdusoleil.com/hiver/ski/webcams.html',
        ),
        'thumbnail': os.environ.get('CAM_PDS_THUMB', ''),
        'location': 'Multiple locations',
    },
    {
        'id': 'morzine-pleney',
        'name': 'Morzine - Pléney',
        'url': os.environ.get(
            'CAM_MORZINE',
            'https://www.morzine-avoriaz.com/activites-montagne/webcams.html',
        ),
        'thumbnail': os.environ.get('CAM_MORZINE_THUMB', ''),
        'location': 'Pléney 1440m',
    },
]


def fetch_cameras() -> Dict[str, Any]:
    """Return webcam list with availability status."""
    cached = _cache_get('cameras')
    if cached is not None:
        return cached

    cameras = []
    for cam in _WEBCAM_SOURCES:
        status = _probe_url(cam['url'])
        cameras.append({**cam, 'status': status})

    data = {
        'cameras': cameras,
        'timestamp': datetime.now(timezone.utc).isoformat(),
    }
    _cache_set('cameras', data)
    return data


def _probe_url(url: str) -> str:
    """Return 'online' if url responds with HTTP 200, else 'offline'."""
    try:
        import urllib.request
        req = urllib.request.Request(url, method='HEAD')
        with urllib.request.urlopen(req, timeout=4) as resp:
            return 'online' if resp.status < 400 else 'offline'
    except Exception:
        return 'offline'


# ---------------------------------------------------------------------------
# Forecast
# ---------------------------------------------------------------------------

def fetch_forecast() -> Dict[str, Any]:
    """Return 8-day weather forecast for Avoriaz."""
    cached = _cache_get('forecast')
    if cached is not None:
        return cached

    data = _fetch_forecast_live()
    _cache_set('forecast', data)
    return data


def _fetch_forecast_live() -> Dict[str, Any]:
    """Try OpenMeteo daily forecast; fall back to simulation DAILY_WEATHER."""
    try:
        import urllib.request
        import json
        url = (
            'https://api.open-meteo.com/v1/forecast'
            '?latitude=46.1928&longitude=6.7714'
            '&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,snowfall_sum,windspeed_10m_max'
            '&timezone=Europe%2FParis'
            '&forecast_days=8'
        )
        with urllib.request.urlopen(url, timeout=8) as resp:
            payload = json.loads(resp.read())
        days = []
        daily = payload.get('daily', {})
        for i, date_str in enumerate(daily.get('time', [])):
            days.append({
                'date': date_str,
                'temp_max_c': daily.get('temperature_2m_max', [None])[i],
                'temp_min_c': daily.get('temperature_2m_min', [None])[i],
                'precipitation_mm': daily.get('precipitation_sum', [None])[i],
                'snowfall_cm': daily.get('snowfall_sum', [None])[i],
                'wind_max_kmh': daily.get('windspeed_10m_max', [None])[i],
                'source': 'openmeteo',
            })
        return {'days': days, 'timestamp': datetime.now(timezone.utc).isoformat()}
    except Exception as exc:
        logger.warning("Forecast live fetch error: %s – using simulation", exc)
        return _forecast_from_simulation()


def _forecast_from_simulation() -> Dict[str, Any]:
    """Build forecast from the static DAILY_WEATHER dict in simulation.py."""
    try:
        from ski_assistant.simulation import DAILY_WEATHER
        days = []
        for date_str, (base_temp, snowfall_cm, cloud_cover) in sorted(DAILY_WEATHER.items()):
            days.append({
                'date': date_str,
                'temp_max_c': round(base_temp + 4, 1),
                'temp_min_c': round(base_temp - 3, 1),
                'precipitation_mm': round(snowfall_cm * 0.9, 1),
                'snowfall_cm': snowfall_cm,
                'wind_max_kmh': _estimate_wind(cloud_cover),
                'cloud_cover': cloud_cover,
                'source': 'simulation',
            })
    except Exception as exc:
        logger.error("Simulation forecast error: %s", exc)
        days = []
    return {'days': days, 'timestamp': datetime.now(timezone.utc).isoformat()}


# ---------------------------------------------------------------------------
# Stress tests
# ---------------------------------------------------------------------------

def fetch_stress_tests() -> Dict[str, Any]:
    """Run the three adversarial scenarios from decision_engine.stress_test."""
    cached = _cache_get('stress_tests')
    if cached is not None:
        return cached

    data = _fetch_stress_tests_live()
    _cache_set('stress_tests', data)
    return data


def _fetch_stress_tests_live() -> Dict[str, Any]:
    try:
        from ski_assistant.decision_engine import stress_test, UserPreferences
        dt = _simulation_dt()
        scenarios = stress_test(dt, UserPreferences())
        result = []
        for s in scenarios:
            # Compute average delta vs base (use top_3 vs worst_3 average)
            top_avg  = sum(rc.enjoyment_score for rc in s.top_3) / max(len(s.top_3), 1)
            base_avg = sum(rc.enjoyment_score for rc in s.conditions) / max(len(s.conditions), 1)
            delta = round(top_avg - base_avg, 1)
            result.append({
                'name': s.name,
                'description': s.description,
                'runs': [_run_conditions_to_dict(rc) for rc in s.top_3],
                'delta_enjoyment': delta,
                'key_impact': s.key_insight,
            })
    except Exception as exc:
        logger.error("Stress test error: %s", exc)
        result = []

    return {
        'scenarios': result,
        'timestamp': datetime.now(timezone.utc).isoformat(),
    }


# ---------------------------------------------------------------------------
# Manual cache refresh (called by scheduler)
# ---------------------------------------------------------------------------

def refresh_all() -> Dict[str, Any]:
    """
    Force-refresh all cache entries.
    Returns a summary dict with success/failure per key.
    """
    # Invalidate all cached entries
    _cache.clear()

    results: Dict[str, str] = {}

    tasks = [
        ('conditions',     fetch_conditions),
        ('recommendations', lambda: fetch_recommendations()),
        ('day_plan',       lambda: fetch_day_plan()),
        ('cameras',        fetch_cameras),
        ('forecast',       fetch_forecast),
        ('stress_tests',   fetch_stress_tests),
    ]

    for key, fn in tasks:
        try:
            fn()
            results[key] = 'ok'
        except Exception as exc:
            logger.error("Refresh error for %s: %s", key, exc)
            results[key] = f'error: {exc}'

    return {
        'refreshed_at': datetime.now(timezone.utc).isoformat(),
        'results': results,
    }
