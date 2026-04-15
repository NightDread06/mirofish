"""
Agency client management API.

GET  /api/agency/clients            — Admin: list all clients
POST /api/agency/clients/onboarding — Submit client intake form
GET  /api/agency/clients/me         — Get own client profile
GET  /api/agency/clients/<id>       — Admin: get client details
PATCH /api/agency/clients/<id>      — Admin: update client status/plan
GET  /api/agency/clients/<id>/export — GDPR data export
DELETE /api/agency/clients/<id>/gdpr-delete — GDPR erasure (admin or own)
GET  /api/agency/dashboard          — Admin: metrics dashboard
"""

import re
from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity, get_jwt

from ..extensions import db, limiter
from ..middleware.auth import require_auth, require_admin
from ..middleware.sanitize import sanitize_dict
from ..models.agency_auth import AgencyUser
from ..models.agency_client import AgencyClient
from ..services.agency_client_manager import AgencyClientManager
from ..utils.logger import get_logger

logger = get_logger('mirofish.agency.clients')
agency_clients_bp = Blueprint('agency_clients', __name__)

_ONBOARDING_FIELDS = [
    'business_name', 'business_type', 'city', 'country', 'email',
    'tone', 'target_audience', 'competitors', 'brand_keywords',
    'linkedin_url', 'instagram_handle', 'facebook_page',
]

_VALID_BUSINESS_TYPES = {'gym', 'salon', 'restaurant', 'clinic', 'real_estate', 'other'}
_VALID_TONES          = {'professional', 'friendly', 'bold', 'calm', 'playful'}
_EMAIL_RE             = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')


def _validate_onboarding(data: dict) -> list:
    errors = []
    if not data.get('business_name', '').strip():
        errors.append('business_name is required')
    if len(data.get('business_name', '')) > 255:
        errors.append('business_name must be ≤ 255 characters')
    if data.get('business_type') and data['business_type'] not in _VALID_BUSINESS_TYPES:
        errors.append(f"business_type must be one of: {', '.join(_VALID_BUSINESS_TYPES)}")
    if data.get('tone') and data['tone'] not in _VALID_TONES:
        errors.append(f"tone must be one of: {', '.join(_VALID_TONES)}")
    if not data.get('email', '').strip():
        errors.append('email is required')
    elif not _EMAIL_RE.match(data.get('email', '')):
        errors.append('email is not valid')
    if not data.get('gdpr_consent'):
        errors.append('gdpr_consent is required')
    return errors


# ── Admin: list all clients ────────────────────────────────────────────────────

@agency_clients_bp.route('', methods=['GET'])
@require_admin
def list_clients():
    status = request.args.get('status')
    limit  = min(request.args.get('limit', 100, type=int), 500)
    clients = AgencyClientManager.list_clients(status=status, limit=limit)
    return jsonify({
        'success': True,
        'data': [c.to_dict(include_sensitive=True) for c in clients],
        'count': len(clients),
    })


# ── Client onboarding intake ───────────────────────────────────────────────────

@agency_clients_bp.route('/onboarding', methods=['POST'])
@require_auth
@limiter.limit('5 per hour')
def submit_onboarding():
    """Submit the 3-step onboarding form. Creates or updates the client profile."""
    data    = request.get_json(silent=True) or {}
    user_id = int(get_jwt_identity())

    # Sanitize all text fields before DB storage
    clean = sanitize_dict(data, _ONBOARDING_FIELDS)

    errors = _validate_onboarding(clean)
    if errors:
        return jsonify({'success': False, 'error': '; '.join(errors)}), 400

    # Check if user already has a client profile
    existing = AgencyClient.query.filter_by(user_id=user_id).first()
    if existing:
        # Update existing profile
        for field in _ONBOARDING_FIELDS:
            if field in clean:
                setattr(existing, field, clean[field])
        existing.gdpr_consent = bool(clean.get('gdpr_consent', existing.gdpr_consent))
        if clean.get('gdpr_consent') and not existing.gdpr_consent_at:
            from datetime import datetime
            existing.gdpr_consent_at = datetime.utcnow()
        existing.status = 'active'
        db.session.commit()
        return jsonify({'success': True, 'data': existing.to_dict(include_sensitive=True)})

    client = AgencyClientManager.create_client(clean, user_id=user_id)
    client.status = 'active'
    db.session.commit()
    return jsonify({'success': True, 'data': client.to_dict(include_sensitive=True)}), 201


# ── Own profile ────────────────────────────────────────────────────────────────

@agency_clients_bp.route('/me', methods=['GET'])
@require_auth
def get_my_profile():
    user_id = int(get_jwt_identity())
    client  = AgencyClient.query.filter_by(user_id=user_id).first()
    if not client:
        return jsonify({'success': False, 'error': 'No client profile found. Complete onboarding first.'}), 404
    return jsonify({'success': True, 'data': client.to_dict(include_sensitive=True)})


# ── Admin: get / update single client ─────────────────────────────────────────

@agency_clients_bp.route('/<client_id>', methods=['GET'])
@require_admin
def get_client(client_id: str):
    client = AgencyClientManager.get_client(client_id)
    if not client:
        return jsonify({'success': False, 'error': 'Client not found'}), 404
    return jsonify({'success': True, 'data': client.to_dict(include_sensitive=True)})


@agency_clients_bp.route('/<client_id>', methods=['PATCH'])
@require_admin
def update_client(client_id: str):
    data   = request.get_json(silent=True) or {}
    client = AgencyClientManager.get_client(client_id)
    if not client:
        return jsonify({'success': False, 'error': 'Client not found'}), 404

    if 'status' in data and data['status'] in ('onboarding', 'active', 'paused', 'churned'):
        client.status = data['status']
    if 'plan' in data and data['plan'] in ('pilot', 'retainer'):
        client.plan = data['plan']
    db.session.commit()
    return jsonify({'success': True, 'data': client.to_dict()})


# ── GDPR data export ───────────────────────────────────────────────────────────

@agency_clients_bp.route('/<client_id>/export', methods=['GET'])
@require_auth
def export_data(client_id: str):
    user_id = int(get_jwt_identity())
    claims  = get_jwt()

    if claims.get('role') != 'admin':
        client = AgencyClient.query.filter_by(id=client_id, user_id=user_id).first()
        if not client:
            return jsonify({'success': False, 'error': 'Access denied'}), 403

    data = AgencyClientManager.export_client_data(client_id)
    if not data:
        return jsonify({'success': False, 'error': 'Client not found'}), 404
    return jsonify({'success': True, 'data': data})


# ── GDPR erasure ──────────────────────────────────────────────────────────────

@agency_clients_bp.route('/<client_id>/gdpr-delete', methods=['DELETE'])
@require_auth
def gdpr_delete(client_id: str):
    user_id = int(get_jwt_identity())
    claims  = get_jwt()

    if claims.get('role') != 'admin':
        client = AgencyClient.query.filter_by(id=client_id, user_id=user_id).first()
        if not client:
            return jsonify({'success': False, 'error': 'Access denied'}), 403

    success = AgencyClientManager.process_gdpr_deletion(client_id)
    if not success:
        return jsonify({'success': False, 'error': 'Client not found'}), 404
    return jsonify({'success': True, 'message': 'Client data erased in compliance with GDPR Article 17.'})


# ── Admin dashboard metrics ────────────────────────────────────────────────────

@agency_clients_bp.route('/dashboard/metrics', methods=['GET'])
@require_admin
def dashboard():
    metrics = AgencyClientManager.get_dashboard_metrics()
    return jsonify({'success': True, 'data': metrics})
