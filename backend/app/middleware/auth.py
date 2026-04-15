"""
JWT authentication decorators for agency API routes.

Usage:
    @require_auth     — valid JWT access token required
    @require_admin    — valid JWT + role == 'admin' required
"""

from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt


def require_auth(f):
    """Require a valid JWT access token in the Authorization header."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request()
        except Exception:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return wrapper


def require_admin(f):
    """Require a valid JWT access token with role='admin' in the claims."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request()
            claims = get_jwt()
            if claims.get('role') != 'admin':
                return jsonify({'success': False, 'error': 'Admin access required'}), 403
        except Exception:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return wrapper
