"""
Weather service using Open-Meteo API (free, no API key required).
Provides current conditions and forecasts for Avoriaz ski resort.
"""

import os
import logging
import time
from datetime import datetime, timezone
from typing import Any, Optional

try:
    import requests
except ImportError:
    requests = None  # type: ignore[assignment]

from .cache import weather_cache

logger = logging.getLogger(__name__)

# Avoriaz coordinates (default, overridable via env)
LAT = float(os.environ.get("AVORIAZ_LAT", "46.3627"))
LON = float(os.environ.get("AVORIAZ_LON", "6.6330"))

OPEN_METEO_BASE = "https://api.open-meteo.com/v1/forecast"

HOURLY_VARS = ",".join([
    "temperature_2m",
    "precipitation_probability",
    "precipitation",
    "snowfall",
    "snow_depth",
    "windspeed_10m",
    "visibility",
    "relative_humidity_2m",
    "weathercode",
])

DAILY_VARS = ",".join([
    "snow_depth_sum",
    "precipitation_sum",
    "temperature_2m_max",
    "temperature_2m_min",
    "weathercode",
])

# WMO weather interpretation codes → readable strings
WMO_CODES: dict[int, str] = {
    0: "Clear sky",
    1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Depositing rime fog",
    51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
    61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
    71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
    77: "Snow grains",
    80: "Slight showers", 81: "Moderate showers", 82: "Violent showers",
    85: "Slight snow showers", 86: "Heavy snow showers",
    95: "Thunderstorm", 96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


def parse_weather_code(code: Optional[int]) -> str:
    """Convert a WMO weather code to a human-readable string."""
    if code is None:
        return "Unknown"
    return WMO_CODES.get(int(code), f"Code {code}")


def _fetch_open_meteo(params: dict) -> Optional[dict]:
    """Make a GET request to Open-Meteo and return JSON, or None on error."""
    if requests is None:
        logger.error("requests library is not installed")
        return None
    try:
        resp = requests.get(OPEN_METEO_BASE, params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        logger.warning("Open-Meteo request failed: %s", exc)
        return None


def _simulated_current() -> dict:
    """Return plausible fallback data when the API is unavailable."""
    return {
        "temperature": -2.0,
        "condition": "Partly cloudy",
        "snowfall": 0.0,
        "snow_depth": 1.2,
        "wind_speed": 15.0,
        "humidity": 75,
        "visibility": 10000,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": "simulated",
    }


def get_current_conditions() -> dict:
    """Return current weather conditions at Avoriaz."""
    cache_key = "weather:current"
    cached = weather_cache.get(cache_key)
    if cached is not None:
        return cached

    data = _fetch_open_meteo({
        "latitude": LAT,
        "longitude": LON,
        "hourly": HOURLY_VARS,
        "timezone": "Europe/Paris",
        "forecast_days": 1,
    })

    if data is None:
        result = _simulated_current()
        weather_cache.set(cache_key, result, ttl=120)
        return result

    hourly = data.get("hourly", {})
    times = hourly.get("time", [])
    now_str = datetime.now().strftime("%Y-%m-%dT%H:00")
    idx = 0
    for i, t in enumerate(times):
        if t >= now_str:
            idx = i
            break

    def _val(key: str) -> Any:
        arr = hourly.get(key, [])
        return arr[idx] if idx < len(arr) else None

    result = {
        "temperature": _val("temperature_2m"),
        "condition": parse_weather_code(_val("weathercode")),
        "snowfall": _val("snowfall"),
        "snow_depth": _val("snow_depth"),
        "wind_speed": _val("windspeed_10m"),
        "humidity": _val("relative_humidity_2m"),
        "visibility": _val("visibility"),
        "precipitation_probability": _val("precipitation_probability"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": "open-meteo",
    }
    weather_cache.set(cache_key, result)
    return result


def get_hourly_forecast(hours: int = 24) -> list[dict]:
    """Return hourly forecast data for the next *hours* hours."""
    cache_key = f"weather:hourly:{hours}"
    cached = weather_cache.get(cache_key)
    if cached is not None:
        return cached

    data = _fetch_open_meteo({
        "latitude": LAT,
        "longitude": LON,
        "hourly": HOURLY_VARS,
        "timezone": "Europe/Paris",
        "forecast_days": max(1, hours // 24 + 1),
    })

    if data is None:
        fallback = [_simulated_current() | {"time": f"hour_{i}"} for i in range(hours)]
        weather_cache.set(cache_key, fallback, ttl=120)
        return fallback

    hourly = data.get("hourly", {})
    times = hourly.get("time", [])
    now_str = datetime.now().strftime("%Y-%m-%dT%H:00")

    start_idx = 0
    for i, t in enumerate(times):
        if t >= now_str:
            start_idx = i
            break

    result = []
    for i in range(start_idx, min(start_idx + hours, len(times))):
        def _v(key: str) -> Any:
            arr = hourly.get(key, [])
            return arr[i] if i < len(arr) else None

        result.append({
            "time": times[i],
            "temperature": _v("temperature_2m"),
            "condition": parse_weather_code(_v("weathercode")),
            "snowfall": _v("snowfall"),
            "snow_depth": _v("snow_depth"),
            "wind_speed": _v("windspeed_10m"),
            "humidity": _v("relative_humidity_2m"),
            "visibility": _v("visibility"),
            "precipitation_probability": _v("precipitation_probability"),
        })

    weather_cache.set(cache_key, result)
    return result


def get_daily_forecast(days: int = 8) -> list[dict]:
    """Return daily forecast data for the next *days* days."""
    cache_key = f"weather:daily:{days}"
    cached = weather_cache.get(cache_key)
    if cached is not None:
        return cached

    data = _fetch_open_meteo({
        "latitude": LAT,
        "longitude": LON,
        "daily": DAILY_VARS,
        "timezone": "Europe/Paris",
        "forecast_days": min(days, 16),
    })

    if data is None:
        fallback = [{"date": f"day_{i}", "temp_max": 2, "temp_min": -5} for i in range(days)]
        weather_cache.set(cache_key, fallback, ttl=120)
        return fallback

    daily = data.get("daily", {})
    dates = daily.get("time", [])

    result = []
    for i, date in enumerate(dates[:days]):
        def _v(key: str) -> Any:
            arr = daily.get(key, [])
            return arr[i] if i < len(arr) else None

        result.append({
            "date": date,
            "temp_max": _v("temperature_2m_max"),
            "temp_min": _v("temperature_2m_min"),
            "condition": parse_weather_code(_v("weathercode")),
            "precipitation_sum": _v("precipitation_sum"),
            "snow_depth_sum": _v("snow_depth_sum"),
        })

    weather_cache.set(cache_key, result)
    return result


def refresh_weather_cache() -> dict:
    """Force-refresh all weather cache entries. Used by the scheduler."""
    weather_cache.delete("weather:current")
    for h in [24, 48]:
        weather_cache.delete(f"weather:hourly:{h}")
    for d in [7, 8]:
        weather_cache.delete(f"weather:daily:{d}")

    current = get_current_conditions()
    hourly = get_hourly_forecast(24)
    daily = get_daily_forecast(8)

    return {
        "refreshed_at": datetime.now(timezone.utc).isoformat(),
        "current": current,
        "hourly_count": len(hourly),
        "daily_count": len(daily),
    }
