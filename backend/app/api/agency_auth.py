"""
Agency authentication API endpoints.

POST /api/agency/auth/register   — Create a new client account
POST /api/agency/auth/login      — Authenticate and receive tokens
POST /api/agency/auth/refresh    — Exchange refresh cookie for new access token
POST /api/agency/auth/logout     — Clear refresh cookie
DELETE /api/agency/auth/account  — GDPR right-to-erasure: delete own account + data
POST /api/agency/auth/admin-setup — One-time admin account bootstrap
"""

from datetime import datetime, timedelta

from flask import Blueprint, request, jsonify, make_response
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity,
    get_jwt,
    set_refresh_cookies,
    unset_refresh_cookies,
)

from ..extensions import db, limiter
from ..middleware.auth import require_auth
from ..models.agency_auth import AgencyUser
from ..models.agency_client import AgencyClient
from ..services.agency_client_manager import AgencyClientManager
from ..utils.logger import get_logger

logger = get_logger('mirofish.agency.auth')
agency_auth_bp = Blueprint('agency_auth', __name__)


def _issue_tokens(user: AgencyUser):
    """Create access + refresh tokens for a user. Returns (access_token, refresh_token)."""
    claims = {'role': user.role}
    access = create_access_token(
        identity=str(user.id),
        additional_claims=claims,
        expires_delta=timedelta(hours=1),
    )
    refresh = create_refresh_token(
        identity=str(user.id),
        expires_delta=timedelta(days=7),
    )
    return access, refresh


# ── Register ──────────────────────────────────────────────────────────────────

@agency_auth_bp.route('/register', methods=['POST'])
@limiter.limit('10 per hour')
def register():
    """Create a new client account. Requires email + password (12+ chars)."""
    data = request.get_json(silent=True) or {}
    email    = str(data.get('email', '')).lower().strip()
    password = str(data.get('password', ''))

    if not email or '@' not in email:
        return jsonify({'success': False, 'error': 'Valid email required'}), 400
    if len(password) < 12:
        return jsonify({'success': False, 'error': 'Password must be at least 12 characters'}), 400
    if AgencyUser.query.filter_by(email=email).first():
        return jsonify({'success': False, 'error': 'Email already registered'}), 409

    user = AgencyUser(email=email, role='client')
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    access, refresh = _issue_tokens(user)
    resp = make_response(jsonify({
        'success': True,
        'data': {'access_token': access, 'user': user.to_dict()},
    }), 201)
    set_refresh_cookies(resp, refresh)
    return resp


# ── Login ─────────────────────────────────────────────────────────────────────

@agency_auth_bp.route('/login', methods=['POST'])
@limiter.limit('20 per hour')
def login():
    """Authenticate with email + password. Returns access token + sets refresh cookie."""
    data     = request.get_json(silent=True) or {}
    email    = str(data.get('email', '')).lower().strip()
    password = str(data.get('password', ''))

    user = AgencyUser.query.filter_by(email=email, is_active=True).first()
    if not user or not user.check_password(password):
        return jsonify({'success': False, 'error': 'Invalid credentials'}), 401

    user.last_login = datetime.utcnow()
    db.session.commit()

    access, refresh = _issue_tokens(user)
    resp = make_response(jsonify({
        'success': True,
        'data': {'access_token': access, 'user': user.to_dict()},
    }))
    set_refresh_cookies(resp, refresh)
    return resp


# ── Refresh ───────────────────────────────────────────────────────────────────

@agency_auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Exchange a valid refresh cookie for a new 1-hour access token."""
    identity = get_jwt_identity()
    claims   = get_jwt()
    access   = create_access_token(
        identity=identity,
        additional_claims={'role': claims.get('role', 'client')},
        expires_delta=timedelta(hours=1),
    )
    return jsonify({'success': True, 'data': {'access_token': access}})


# ── Logout ────────────────────────────────────────────────────────────────────

@agency_auth_bp.route('/logout', methods=['POST'])
def logout():
    """Clear the refresh cookie. Client should discard the access token."""
    resp = make_response(jsonify({'success': True}))
    unset_refresh_cookies(resp)
    return resp


# ── GDPR account deletion ─────────────────────────────────────────────────────

@agency_auth_bp.route('/account', methods=['DELETE'])
@require_auth
def delete_account():
    """
    GDPR right-to-erasure: permanently erase the caller's client data
    and deactivate their account. Irreversible.
    """
    user_id = int(get_jwt_identity())
    client  = AgencyClient.query.filter_by(user_id=user_id).first()
    if client:
        AgencyClientManager.process_gdpr_deletion(client.id)

    user = AgencyUser.query.get(user_id)
    if user:
        user.is_active = False
        db.session.commit()

    resp = make_response(jsonify({
        'success': True,
        'message': 'Account and all associated data have been erased.',
    }))
    unset_refresh_cookies(resp)
    return resp


# ── One-time admin bootstrap ──────────────────────────────────────────────────

@agency_auth_bp.route('/admin-setup', methods=['POST'])
@limiter.limit('3 per day')
def admin_setup():
    """
    Bootstrap the admin account from environment configuration.
    Idempotent: does nothing if an admin already exists.
    Secured by AGENCY_ADMIN_SETUP_TOKEN env var.
    """
    from ..config import Config
    import os

    setup_token = os.environ.get('AGENCY_ADMIN_SETUP_TOKEN', '')
    if not setup_token:
        return jsonify({'success': False, 'error': 'Admin setup is disabled'}), 403

    provided = str(request.get_json(silent=True) or {}).get('token', '')
    # Re-read from JSON
    data = request.get_json(silent=True) or {}
    if data.get('token', '') != setup_token:
        return jsonify({'success': False, 'error': 'Invalid setup token'}), 403

    admin_email    = Config.AGENCY_ADMIN_EMAIL
    admin_password = data.get('password', '')

    if not admin_email or not admin_password or len(admin_password) < 16:
        return jsonify({'success': False,
                        'error': 'admin_email in config + password (16+ chars) required'}), 400

    existing = AgencyUser.query.filter_by(email=admin_email).first()
    if existing:
        return jsonify({'success': True, 'message': 'Admin account already exists'}), 200

    admin = AgencyUser(email=admin_email, role='admin')
    admin.set_password(admin_password)
    db.session.add(admin)
    db.session.commit()

    logger.info(f'Admin account created: {admin_email}')
    return jsonify({'success': True, 'message': 'Admin account created'}), 201
