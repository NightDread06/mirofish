"""
Webcam service for Avoriaz / Portes du Soleil ski resort cameras.
Aggregates public webcam feeds and returns status + metadata.
No authentication required — all sources are publicly accessible.
"""

import os
import json
import logging
from datetime import datetime, timezone
from typing import Optional

try:
    import requests
except ImportError:
    requests = None  # type: ignore[assignment]

from .cache import webcam_cache

logger = logging.getLogger(__name__)

# Default public webcam sources (overridable via WEBCAM_SOURCES env var)
_DEFAULT_SOURCES = [
    {
        "name": "Avoriaz Official",
        "url": "https://www.avoriaz.com/en/webcams/",
        "type": "embed",
    },
    {
        "name": "Bergfex Avoriaz",
        "url": "https://www.bergfex.com/avoriaz/webcams/c35/",
        "type": "iframe",
    },
    {
        "name": "Portes du Soleil",
        "url": "https://www.portesdusoleil.com/en/webcams/",
        "type": "embed",
    },
    {
        "name": "Skiresort.info Avoriaz",
        "url": "https://www.skiresort.info/ski-resort/avoriaz-portes-du-soleil/webcams/",
        "type": "embed",
    },
]

# Timeout for HTTP HEAD checks
_CHECK_TIMEOUT = 6


def _load_sources() -> list[dict]:
    """Load webcam sources from WEBCAM_SOURCES env var or fall back to defaults."""
    raw = os.environ.get("WEBCAM_SOURCES", "")
    if raw:
        try:
            sources = json.loads(raw)
            if isinstance(sources, list):
                return sources
        except json.JSONDecodeError:
            logger.warning("WEBCAM_SOURCES env var is not valid JSON — using defaults")
    return _DEFAULT_SOURCES


def check_camera_status(url: str) -> tuple[str, Optional[int]]:
    """
    Probe *url* with a HEAD request.
    Returns (status, http_code) where status is 'online' or 'offline'.
    """
    if requests is None:
        return "unknown", None
    try:
        resp = requests.head(url, timeout=_CHECK_TIMEOUT, allow_redirects=True)
        if resp.status_code < 400:
            return "online", resp.status_code
        return "offline", resp.status_code
    except Exception as exc:
        logger.debug("Camera check failed for %s: %s", url, exc)
        return "offline", None


def get_camera_urls() -> list[dict]:
    """
    Return the list of webcam source definitions with direct embed/iframe URLs.
    Sources are read from WEBCAM_SOURCES env var or the built-in defaults.
    """
    return _load_sources()


def get_available_cameras(check_status: bool = False) -> list[dict]:
    """
    Return all configured cameras with metadata.

    If *check_status* is True (used by the background scheduler), each camera
    URL is probed to verify reachability.  In normal API calls the cached status
    is returned instead to keep response times fast.
    """
    cache_key = "webcam:cameras"
    if not check_status:
        cached = webcam_cache.get(cache_key)
        if cached is not None:
            return cached

    sources = _load_sources()
    cameras = []
    now = datetime.now(timezone.utc).isoformat()

    for src in sources:
        url = src.get("url", "")
        if check_status:
            status, code = check_camera_status(url)
        else:
            status, code = "unknown", None

        cameras.append({
            "name": src.get("name", "Unknown"),
            "url": url,
            "type": src.get("type", "embed"),
            "last_check": now,
            "status": status,
            "http_code": code,
        })

    webcam_cache.set(cache_key, cameras)
    return cameras


def refresh_camera_status() -> dict:
    """
    Re-probe all cameras and update the cache.
    Called by the background scheduler every 30 minutes.
    """
    webcam_cache.delete("webcam:cameras")
    cameras = get_available_cameras(check_status=True)
    online = sum(1 for c in cameras if c["status"] == "online")
    return {
        "refreshed_at": datetime.now(timezone.utc).isoformat(),
        "total": len(cameras),
        "online": online,
        "offline": len(cameras) - online,
    }
