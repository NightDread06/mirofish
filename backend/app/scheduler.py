"""
Background Scheduler
====================
APScheduler-based task runner that refreshes ski live-data every 10 minutes.

Usage (called from create_app):
    from .scheduler import start_scheduler, stop_scheduler
    start_scheduler()          # at app startup
    stop_scheduler()           # at app shutdown (optional – atexit handles it)
"""

from __future__ import annotations

import atexit
import logging
from datetime import datetime, timezone

logger = logging.getLogger('mirofish.scheduler')

_scheduler = None


def start_scheduler() -> None:
    """Start the background scheduler (idempotent)."""
    global _scheduler

    if _scheduler is not None and _scheduler.running:
        logger.info("Scheduler already running – skipping start")
        return

    try:
        from apscheduler.schedulers.background import BackgroundScheduler
    except ImportError:
        logger.warning(
            "APScheduler not installed – background refresh disabled. "
            "Install with: pip install apscheduler"
        )
        return

    import os
    interval_minutes = int(os.environ.get('SKI_REFRESH_INTERVAL', '10'))

    _scheduler = BackgroundScheduler(daemon=True)
    _scheduler.add_job(
        _refresh_job,
        trigger='interval',
        minutes=interval_minutes,
        id='ski_refresh',
        name='Ski live-data refresh',
        max_instances=1,
        coalesce=True,
    )

    _scheduler.start()
    atexit.register(stop_scheduler)

    logger.info(
        "Ski data scheduler started – refreshing every %d minutes", interval_minutes
    )

    # Perform an immediate first refresh so data is warm right away
    try:
        _refresh_job()
    except Exception as exc:
        logger.warning("Initial ski data refresh failed: %s", exc)


def stop_scheduler() -> None:
    """Gracefully stop the scheduler."""
    global _scheduler
    if _scheduler is not None and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("Ski data scheduler stopped")
    _scheduler = None


def _refresh_job() -> None:
    """The actual refresh task executed by the scheduler."""
    from .live_data import refresh_all

    started = datetime.now(timezone.utc)
    logger.info("Ski data refresh starting at %s", started.isoformat())
    try:
        summary = refresh_all()
        ok_keys = [k for k, v in summary['results'].items() if v == 'ok']
        err_keys = [k for k, v in summary['results'].items() if v != 'ok']
        logger.info(
            "Ski data refresh complete – ok=%s errors=%s",
            ok_keys, err_keys,
        )
        if err_keys:
            for key in err_keys:
                logger.warning("  [%s]: %s", key, summary['results'][key])
    except Exception as exc:
        logger.error("Ski data refresh failed: %s", exc)


def get_scheduler_status() -> dict:
    """Return scheduler status info for health-check / API."""
    if _scheduler is None:
        return {'running': False, 'jobs': []}
    jobs = []
    for job in _scheduler.get_jobs():
        jobs.append({
            'id': job.id,
            'name': job.name,
            'next_run': job.next_run_time.isoformat() if job.next_run_time else None,
        })
    return {
        'running': _scheduler.running,
        'jobs': jobs,
    }
