"""
Flask JSON API endpoints for authentication.
Wraps existing auth.py logic — does NOT modify auth.py itself.
Uses cookie-session (Flask-Login) + CSRF token.
"""
import secrets
from flask import Blueprint, request, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from DB import Database
from auth import User, ROLES, get_default_route
import app_state

api_auth = Blueprint('api_auth', __name__, url_prefix='/api/auth')


# ========== CSRF Token ========== #

@api_auth.route('/csrf', methods=['GET'])
def get_csrf_token():
    """Return a CSRF token stored in the session."""
    if 'csrf_token' not in session:
        session['csrf_token'] = secrets.token_hex(32)
    return jsonify({'csrf_token': session['csrf_token']})


def _check_csrf():
    """Validate CSRF token on mutating requests. Returns error response or None."""
    token = request.headers.get('X-CSRFToken', '')
    if not token or token != session.get('csrf_token'):
        return jsonify({'success': False, 'error': 'Invalid CSRF token.'}), 403
    return None


# ========== Auth Endpoints ========== #

@api_auth.route('/me', methods=['GET'])
def get_current_user():
    """Check current session — returns user info or unauthenticated."""
    if current_user.is_authenticated:
        return jsonify({
            'authenticated': True,
            'user': {
                'id': current_user.id,
                'username': current_user.username,
                'role': current_user.role,
                'role_label': current_user.role_label,
            }
        })
    return jsonify({'authenticated': False, 'user': None})


@api_auth.route('/login', methods=['POST'])
def api_login():
    """Authenticate user via JSON body. Sets session cookie."""
    data = request.get_json(silent=True) or {}
    username = data.get('username', '').strip()
    password = data.get('password', '')

    if not username or not password:
        return jsonify({'success': False, 'error': 'Username and password are required.'}), 400

    db = Database(app_state.DB_PATH)
    conn = db.connect()
    if not conn:
        return jsonify({'success': False, 'error': 'Database connection error.'}), 500

    user = User.get_by_username(conn, username)
    conn.close()

    if user and user.check_password(password):
        login_user(user)
        # Generate CSRF token for the new session
        session['csrf_token'] = secrets.token_hex(32)
        return jsonify({
            'success': True,
            'user': {
                'id': user.id,
                'username': user.username,
                'role': user.role,
                'role_label': user.role_label,
            },
            'default_route': _role_to_spa_path(user.role),
        })

    return jsonify({'success': False, 'error': 'Invalid username or password.'}), 401


@api_auth.route('/logout', methods=['POST'])
@login_required
def api_logout():
    """Log out current user."""
    csrf_error = _check_csrf()
    if csrf_error:
        return csrf_error
    logout_user()
    return jsonify({'success': True})


# ========== Helpers ========== #

# Map backend route names to SPA paths for default redirect
_ROUTE_TO_PATH = {
    'signature_dashboard': '/',
    'anomaly_dashboard': '/anomaly',
    'live_dashboard': '/live',
}

def _role_to_spa_path(role):
    """Return the SPA path for a role's default landing page."""
    route_name = get_default_route(role)
    return _ROUTE_TO_PATH.get(route_name, '/')
