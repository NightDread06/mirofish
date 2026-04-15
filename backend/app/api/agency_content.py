"""
Agency content generation and delivery API.

POST /api/agency/content/generate             — Trigger async 30-day content generation
GET  /api/agency/content/<id>                 — Get package status + posts (when complete)
GET  /api/agency/content/client/<client_id>   — List all packages for a client
PATCH /api/agency/content/<pkg_id>/posts/<post_id> — Request revision on a post
GET  /api/agency/content/<id>/download        — Download package as JSON
"""

import uuid
from datetime import date

from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity, get_jwt

from ..extensions import db, limiter
from ..middleware.auth import require_auth, require_admin
from ..middleware.sanitize import sanitize_dict
from ..models.agency_client import AgencyClient
from ..models.agency_content import ContentPackage, ContentPost
from ..models.task import TaskManager, TaskStatus
from ..services.agency_content_generator import AgencyContentGenerator
from ..utils.logger import get_logger

logger = get_logger('mirofish.agency.content')
agency_content_bp = Blueprint('agency_content', __name__)

_CONTENT_FIELDS = ['business_name', 'business_type', 'city', 'country',
                   'tone', 'target_audience', 'competitors', 'brand_keywords']
_VALID_PLATFORMS = {'linkedin', 'instagram', 'facebook', 'twitter'}


def _get_authorized_client(client_id: str, user_id: int, is_admin: bool):
    if is_admin:
        return AgencyClient.query.filter_by(id=client_id).first()
    return AgencyClient.query.filter_by(id=client_id, user_id=user_id).first()


# ── Trigger generation ────────────────────────────────────────────────────────

@agency_content_bp.route('/generate', methods=['POST'])
@require_auth
@limiter.limit('5 per hour')
def generate_content():
    """
    Start async 30-day content generation for a client.
    Returns immediately with task_id and package_id.
    Poll GET /api/agency/content/<package_id> to check status.

    Pattern mirrors /api/report/generate from report.py.
    """
    from flask import current_app

    data    = request.get_json(silent=True) or {}
    user_id = int(get_jwt_identity())
    claims  = get_jwt()
    is_admin = claims.get('role') == 'admin'

    client_id = data.get('client_id')
    if not client_id:
        return jsonify({'success': False, 'error': 'client_id required'}), 400

    client = _get_authorized_client(client_id, user_id, is_admin)
    if not client:
        return jsonify({'success': False, 'error': 'Client not found or access denied'}), 404

    # Validate platforms
    platforms_raw = data.get('platforms', ['linkedin', 'instagram', 'facebook'])
    platforms = [p for p in platforms_raw if p in _VALID_PLATFORMS]
    if not platforms:
        platforms = ['linkedin', 'instagram', 'facebook']

    # Parse start date
    start_str = data.get('start_date', '')
    try:
        start_date = date.fromisoformat(start_str) if start_str else date.today()
    except ValueError:
        return jsonify({'success': False, 'error': 'Invalid start_date; use YYYY-MM-DD'}), 400

    use_premium = data.get('use_premium', False) or client.plan == 'retainer'

    # Create task + package records
    task_manager = TaskManager()
    task_id      = task_manager.create_task(
        task_type='agency_content_generate',
        metadata={'client_id': client_id},
    )
    package_id = str(uuid.uuid4())
    package = ContentPackage(
        id=package_id,
        client_id=client_id,
        task_id=task_id,
        status='pending',
        month_label=start_date.strftime('%Y-%m'),
        platforms=platforms,
        model_used=('claude-sonnet-4-6' if use_premium else 'claude-haiku-4-5-20251001'),
    )
    db.session.add(package)
    db.session.commit()

    # Build sanitized client data dict for the generator
    client_data = sanitize_dict({
        'business_name':   client.business_name,
        'business_type':   client.business_type,
        'city':            client.city,
        'country':         client.country,
        'tone':            client.tone,
        'target_audience': client.target_audience,
        'competitors':     client.competitors,
        'brand_keywords':  client.brand_keywords,
    }, keys=_CONTENT_FIELDS)

    # Launch background generation — passes flask app for app context in thread
    generator = AgencyContentGenerator(use_premium=use_premium)
    flask_app  = current_app._get_current_object()
    generator.generate_async(
        client_data=client_data,
        package_id=package_id,
        task_id=task_id,
        platforms=platforms,
        start_date=start_date,
        flask_app=flask_app,
    )

    return jsonify({
        'success': True,
        'data': {
            'package_id': package_id,
            'task_id': task_id,
            'status': 'pending',
            'message': 'Content generation started. Poll GET /api/agency/content/{package_id}.',
        },
    }), 202


# ── Get package (with status sync) ────────────────────────────────────────────

@agency_content_bp.route('/<package_id>', methods=['GET'])
@require_auth
def get_content_package(package_id: str):
    """Return package status. Includes all posts once status == 'completed'."""
    user_id  = int(get_jwt_identity())
    claims   = get_jwt()
    is_admin = claims.get('role') == 'admin'

    package = ContentPackage.query.filter_by(id=package_id).first()
    if not package:
        return jsonify({'success': False, 'error': 'Package not found'}), 404

    # Auth: clients can only see their own packages
    if not is_admin:
        client = AgencyClient.query.filter_by(id=package.client_id, user_id=user_id).first()
        if not client:
            return jsonify({'success': False, 'error': 'Access denied'}), 403

    # Sync task status into package if still in-flight
    if package.status in ('pending', 'generating') and package.task_id:
        task_manager = TaskManager()
        task = task_manager.get_task(package.task_id)
        if task:
            if task.status == TaskStatus.FAILED:
                package.status = 'failed'
                package.error  = task.error
                db.session.commit()
            elif task.status == TaskStatus.PROCESSING and package.status == 'pending':
                package.status = 'generating'
                db.session.commit()

    include_posts = (package.status == 'completed')
    data = package.to_dict(include_posts=include_posts)

    # Include progress if still generating
    if package.status in ('pending', 'generating') and package.task_id:
        task_manager = TaskManager()
        task = task_manager.get_task(package.task_id)
        if task:
            data['progress'] = task.progress
            data['progress_message'] = task.message

    return jsonify({'success': True, 'data': data})


# ── List packages for a client ────────────────────────────────────────────────

@agency_content_bp.route('/client/<client_id>', methods=['GET'])
@require_auth
def list_client_packages(client_id: str):
    user_id  = int(get_jwt_identity())
    claims   = get_jwt()
    is_admin = claims.get('role') == 'admin'

    client = _get_authorized_client(client_id, user_id, is_admin)
    if not client:
        return jsonify({'success': False, 'error': 'Client not found or access denied'}), 404

    packages = (ContentPackage.query
                .filter_by(client_id=client_id)
                .order_by(ContentPackage.created_at.desc())
                .all())
    return jsonify({
        'success': True,
        'data': [p.to_dict() for p in packages],
        'count': len(packages),
    })


# ── Revision request on a single post ─────────────────────────────────────────

@agency_content_bp.route('/<package_id>/posts/<post_id>', methods=['PATCH'])
@require_auth
def update_post(package_id: str, post_id: str):
    user_id  = int(get_jwt_identity())
    claims   = get_jwt()
    is_admin = claims.get('role') == 'admin'

    package = ContentPackage.query.filter_by(id=package_id).first()
    if not package:
        return jsonify({'success': False, 'error': 'Package not found'}), 404

    if not is_admin:
        client = AgencyClient.query.filter_by(id=package.client_id, user_id=user_id).first()
        if not client:
            return jsonify({'success': False, 'error': 'Access denied'}), 403

    post = ContentPost.query.filter_by(id=post_id, package_id=package_id).first()
    if not post:
        return jsonify({'success': False, 'error': 'Post not found'}), 404

    data = request.get_json(silent=True) or {}
    if 'revision_note' in data:
        from ..middleware.sanitize import sanitize_text
        post.revision_note = sanitize_text(str(data['revision_note']))[:1000]
        post.is_approved   = False
    if 'is_approved' in data and is_admin:
        post.is_approved = bool(data['is_approved'])
    db.session.commit()
    return jsonify({'success': True, 'data': post.to_dict()})


# ── Download package as JSON ──────────────────────────────────────────────────

@agency_content_bp.route('/<package_id>/download', methods=['GET'])
@require_auth
def download_package(package_id: str):
    user_id  = int(get_jwt_identity())
    claims   = get_jwt()
    is_admin = claims.get('role') == 'admin'

    package = ContentPackage.query.filter_by(id=package_id).first()
    if not package:
        return jsonify({'success': False, 'error': 'Package not found'}), 404

    if not is_admin:
        client = AgencyClient.query.filter_by(id=package.client_id, user_id=user_id).first()
        if not client:
            return jsonify({'success': False, 'error': 'Access denied'}), 403

    if package.status != 'completed':
        return jsonify({'success': False, 'error': 'Package not yet completed'}), 400

    return jsonify(package.to_dict(include_posts=True))
