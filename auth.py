"""Authentication and Role-Based Access Control for HOLMES IDS."""
import sqlite3
from functools import wraps
from flask import redirect, url_for, flash
from flask_login import UserMixin, current_user
from werkzeug.security import generate_password_hash, check_password_hash


# ========== Role Definitions ========== #

ROLES = {
    "admin": {
        "label": "Administrator",
        "description": "Full access to all features and user management",
        "allowed_routes": "__all__",
        "default_route": "signature_dashboard"
    },
    "signature_analyst": {
        "label": "Signature Analyst",
        "description": "Access to Signature IDS, PCAP upload, and Rules",
        "allowed_routes": [
            "signature_dashboard", "upload_pcap", "rules_dashboard",
            "analytics_dashboard", "analytics_query",
            "logout"
        ],
        "default_route": "signature_dashboard"
    },
    "anomaly_analyst": {
        "label": "Anomaly Analyst",
        "description": "Access to Anomaly IDS and CSV upload",
        "allowed_routes": [
            "anomaly_dashboard", "upload_csv", "explain_alert",
            "analytics_dashboard", "analytics_query",
            "logout"
        ],
        "default_route": "anomaly_dashboard"
    },
    "live_operator": {
        "label": "Live Operator",
        "description": "Access to Live Capture only",
        "allowed_routes": [
            "live_dashboard", "live_start", "live_stop",
            "live_clear_alerts", "live_delete_alerts", "logout"
        ],
        "default_route": "live_dashboard"
    }
}


def get_default_route(role):
    """Return the default landing route for a given role."""
    role_info = ROLES.get(role, {})
    return role_info.get("default_route", "live_dashboard")


# ========== User Model ========== #

class User(UserMixin):
    def __init__(self, id, username, password_hash, role):
        self.id = id
        self.username = username
        self.password_hash = password_hash
        self.role = role

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def has_access(self, route_name):
        """Check if user's role allows access to a given route."""
        role_info = ROLES.get(self.role, {})
        allowed = role_info.get("allowed_routes", [])
        if allowed == "__all__":
            return True
        return route_name in allowed

    @property
    def role_label(self):
        return ROLES.get(self.role, {}).get("label", self.role)

    @staticmethod
    def get_by_id(conn, user_id):
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, password_hash, role FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        if row:
            return User(id=row[0], username=row[1], password_hash=row[2], role=row[3])
        return None

    @staticmethod
    def get_by_username(conn, username):
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, password_hash, role FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        if row:
            return User(id=row[0], username=row[1], password_hash=row[2], role=row[3])
        return None

    @staticmethod
    def get_all(conn):
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, password_hash, role FROM users ORDER BY id")
        rows = cursor.fetchall()
        return [User(id=r[0], username=r[1], password_hash=r[2], role=r[3]) for r in rows]

    @staticmethod
    def create(conn, username, password, role):
        password_hash = generate_password_hash(password)
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                (username, password_hash, role)
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    @staticmethod
    def delete(conn, user_id):
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        return cursor.rowcount > 0

    @staticmethod
    def update_role(conn, user_id, new_role):
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET role = ? WHERE id = ?", (new_role, user_id))
        conn.commit()
        return cursor.rowcount > 0

    @staticmethod
    def ensure_default_admin(conn):
        """Create default admin user if no users exist."""
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        count = cursor.fetchone()[0]
        if count == 0:
            User.create(conn, "admin", "admin", "admin")
            print("[AUTH] Default admin user created (username: admin, password: admin)")


# ========== Access Control Decorator ========== #

def role_required(*allowed_roles):
    """Decorator to restrict route access by role.
    Usage: @role_required('admin', 'signature_analyst')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('login'))
            if current_user.role not in allowed_roles and current_user.role != 'admin':
                flash("You do not have permission to access this page.")
                # Redirect to user's default page, NOT login (avoids redirect loops)
                default = get_default_route(current_user.role)
                return redirect(url_for(default))
            return f(*args, **kwargs)
        return decorated_function
    return decorator
