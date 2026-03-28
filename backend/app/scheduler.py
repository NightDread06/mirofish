"""
Background scheduler for the ski dashboard.
Uses APScheduler to refresh weather and webcam data on a configurable interval.
"""

import logging
import os
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

_scheduler = None


def _job_refresh_weather() -> None:
    """Scheduled job: refresh weather cache."""
    try:
        from .weather_service import refresh_weather_cache
        result = refresh_weather_cache()
        logger.info("Weather cache refreshed at %s", result.get("refreshed_at"))
    except Exception as exc:
        logger.error("Weather refresh job failed: %s", exc, exc_info=True)


def _job_refresh_cameras() -> None:
    """Scheduled job: probe all webcam URLs and update cache."""
    try:
        from .webcam_service import refresh_camera_status
        result = refresh_camera_status()
        logger.info(
            "Camera status refreshed at %s — %d online / %d total",
            result.get("refreshed_at"),
            result.get("online", 0),
            result.get("total", 0),
        )
    except Exception as exc:
        logger.error("Camera refresh job failed: %s", exc, exc_info=True)


def _job_cleanup_cache() -> None:
    """Scheduled job: evict expired cache entries."""
    try:
        from .cache import weather_cache, webcam_cache
        removed = weather_cache.clear_expired() + webcam_cache.clear_expired()
        logger.debug("Cache cleanup: removed %d expired entries", removed)
    except Exception as exc:
        logger.error("Cache cleanup job failed: %s", exc, exc_info=True)


def start_scheduler() -> None:
    """
    Start the APScheduler background scheduler.
    Safe to call multiple times — will not start a second instance.
    """
    global _scheduler
    if _scheduler is not None and _scheduler.running:
        logger.debug("Scheduler already running — skipping start")
        return

    try:
        from apscheduler.schedulers.background import BackgroundScheduler
    except ImportError:
        logger.warning(
            "APScheduler is not installed — background refresh is disabled. "
            "Install it with: pip install apscheduler"
        )
        return

    interval_minutes = int(os.environ.get("REFRESH_INTERVAL_MINUTES", "10"))
    cache_ttl = int(os.environ.get("CACHE_TTL_SECONDS", "600"))

    _scheduler = BackgroundScheduler(timezone="UTC")

    # Refresh weather every REFRESH_INTERVAL_MINUTES
    _scheduler.add_job(
        _job_refresh_weather,
        "interval",
        minutes=interval_minutes,
        id="refresh_weather",
        replace_existing=True,
    )

    # Refresh camera status every 30 minutes
    _scheduler.add_job(
        _job_refresh_cameras,
        "interval",
        minutes=30,
        id="refresh_cameras",
        replace_existing=True,
    )

    # Clean up expired cache entries every hour
    _scheduler.add_job(
        _job_cleanup_cache,
        "interval",
        hours=1,
        id="cleanup_cache",
        replace_existing=True,
    )

    _scheduler.start()
    logger.info(
        "Ski dashboard scheduler started — weather refresh every %d min, "
        "camera refresh every 30 min, cache cleanup every 60 min",
        interval_minutes,
    )


def stop_scheduler() -> None:
    """Gracefully shut down the scheduler (called on app teardown)."""
    global _scheduler
    if _scheduler is not None and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("Ski dashboard scheduler stopped")
    _scheduler = None


def get_scheduler_status() -> dict:
    """Return current scheduler state for the health endpoint."""
    if _scheduler is None:
        return {"running": False, "jobs": []}

    jobs = []
    for job in _scheduler.get_jobs():
        next_run = job.next_run_time
        jobs.append({
            "id": job.id,
            "next_run": next_run.isoformat() if next_run else None,
        })

    return {
        "running": _scheduler.running,
        "jobs": jobs,
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }
