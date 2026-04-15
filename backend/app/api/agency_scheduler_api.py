"""
Scheduler admin API.

GET  /api/agency/scheduler/status         — Running state + job list
POST /api/agency/scheduler/jobs/<id>/run  — Trigger a specific job immediately
POST /api/agency/scheduler/pause          — Pause all jobs
POST /api/agency/scheduler/resume         — Resume all jobs
"""

from flask import Blueprint, jsonify, current_app

from ..extensions import scheduler
from ..middleware.auth import require_admin
from ..utils.logger import get_logger

logger = get_logger('mirofish.agency.scheduler_api')
agency_scheduler_bp = Blueprint('agency_scheduler', __name__)

_RUNNABLE_JOBS = {'daily_scout', 'check_replies', 'follow_ups', 'publish_posts'}


# ── Status ────────────────────────────────────────────────────────────────────

@agency_scheduler_bp.route('/status', methods=['GET'])
@require_admin
def get_status():
    """Return scheduler running state and all registered jobs with next run times."""
    jobs = []
    for job in scheduler.get_jobs():
        jobs.append({
            'id':            job.id,
            'name':          job.name,
            'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None,
            'trigger':       str(job.trigger),
        })
    return jsonify({
        'success': True,
        'data': {
            'running': scheduler.running,
            'jobs':    jobs,
        },
    })


# ── Manual trigger ────────────────────────────────────────────────────────────

@agency_scheduler_bp.route('/jobs/<job_id>/run', methods=['POST'])
@require_admin
def run_job(job_id: str):
    """Immediately execute a specific scheduler job (for testing/manual trigger)."""
    if job_id not in _RUNNABLE_JOBS:
        return jsonify({
            'success': False,
            'error':   f'Unknown job_id. Valid: {sorted(_RUNNABLE_JOBS)}',
        }), 400

    flask_app = current_app._get_current_object()

    from ..services.agency_scheduler import (
        run_daily_scout, check_email_replies,
        send_scheduled_follow_ups, publish_approved_posts,
    )

    job_map = {
        'daily_scout':   run_daily_scout,
        'check_replies': check_email_replies,
        'follow_ups':    send_scheduled_follow_ups,
        'publish_posts': publish_approved_posts,
    }

    import threading
    t = threading.Thread(
        target=job_map[job_id],
        args=[flask_app],
        daemon=True,
        name=f'manual_{job_id}',
    )
    t.start()
    logger.info(f'Manual trigger: {job_id}')
    return jsonify({'success': True, 'message': f'Job {job_id} triggered in background'})


# ── Pause / Resume ────────────────────────────────────────────────────────────

@agency_scheduler_bp.route('/pause', methods=['POST'])
@require_admin
def pause_scheduler():
    if scheduler.running:
        scheduler.pause()
    return jsonify({'success': True, 'message': 'Scheduler paused'})


@agency_scheduler_bp.route('/resume', methods=['POST'])
@require_admin
def resume_scheduler():
    if scheduler.running:
        scheduler.resume()
    return jsonify({'success': True, 'message': 'Scheduler resumed'})
