import { NavLink } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

// Helper: check if role has access to a given route name
// Mirrors auth.py ROLES logic
const ROLES = {
    admin: { allowed: '__all__' },
    signature_analyst: {
        allowed: ['signature_dashboard', 'upload_pcap', 'rules_dashboard',
            'analytics_dashboard', 'analytics_query'],
    },
    anomaly_analyst: {
        allowed: ['anomaly_dashboard', 'upload_csv', 'explain_alert',
            'analytics_dashboard', 'analytics_query'],
    },
    live_operator: {
        allowed: ['live_dashboard', 'live_start', 'live_stop',
            'live_clear_alerts', 'live_delete_alerts'],
    },
};

function hasAccess(role, routeName) {
    const roleInfo = ROLES[role];
    if (!roleInfo) return false;
    if (roleInfo.allowed === '__all__') return true;
    return roleInfo.allowed.includes(routeName);
}

export default function Navbar() {
    const { user, logout } = useAuth();

    if (!user) return null;

    return (
        <nav className="navbar navbar-expand-lg navbar-dark sticky-top">
            <div className="container-fluid">
                <NavLink className="navbar-brand d-flex align-items-center" to="/">
                    <img className="flying-logo" src="/static/IMG/w1.png" alt="Logo" />
                    <span className="fw-bold fs-4">HOLMES IDS</span>
                </NavLink>
                <button
                    className="navbar-toggler" type="button"
                    data-bs-toggle="collapse" data-bs-target="#navMenu"
                >
                    <span className="navbar-toggler-icon" />
                </button>
                <div className="collapse navbar-collapse justify-content-end" id="navMenu">
                    <ul className="navbar-nav mb-2 mb-lg-0">

                        {hasAccess(user.role, 'signature_dashboard') && (
                            <li className="nav-item">
                                <NavLink className="nav-link" to="/">
                                    <i className="fa-solid fa-file-signature" /> Signature IDS
                                </NavLink>
                            </li>
                        )}

                        {hasAccess(user.role, 'anomaly_dashboard') && (
                            <li className="nav-item">
                                <NavLink className="nav-link" to="/anomaly">
                                    <i className="fa-solid fa-brain" /> Anomaly IDS
                                </NavLink>
                            </li>
                        )}

                        {hasAccess(user.role, 'upload_csv') && (
                            <li className="nav-item">
                                <NavLink className="nav-link" to="/csv">
                                    <i className="fas fa-upload me-1" />Upload CSV
                                </NavLink>
                            </li>
                        )}

                        {hasAccess(user.role, 'upload_pcap') && (
                            <li className="nav-item">
                                <NavLink className="nav-link" to="/upload_pcap">
                                    <i className="fas fa-upload me-1" />Upload PCAP
                                </NavLink>
                            </li>
                        )}

                        {hasAccess(user.role, 'live_dashboard') && (
                            <li className="nav-item">
                                <NavLink className="nav-link" to="/live">
                                    <i className="fa-solid fa-satellite-dish me-1" />Live Capture
                                </NavLink>
                            </li>
                        )}

                        {hasAccess(user.role, 'rules_dashboard') && (
                            <li className="nav-item">
                                <NavLink className="nav-link" to="/rules">
                                    <i className="fa-solid fa-gavel me-1" />Rules
                                </NavLink>
                            </li>
                        )}

                        {hasAccess(user.role, 'analytics_dashboard') && (
                            <li className="nav-item">
                                <NavLink className="nav-link" to="/analytics">
                                    <i className="fa-solid fa-magnifying-glass-chart me-1" />Analytics
                                </NavLink>
                            </li>
                        )}

                        {user.role === 'admin' && (
                            <>
                                <li className="nav-item">
                                    <NavLink className="nav-link" to="/admin">
                                        <i className="fa-solid fa-users-gear me-1" />Admin
                                    </NavLink>
                                </li>
                                <li className="nav-item">
                                    <NavLink className="nav-link" to="/retrain">
                                        <i className="fa-solid fa-brain me-1" />Retrain
                                    </NavLink>
                                </li>
                            </>
                        )}

                        {/* User dropdown */}
                        <li className="nav-item dropdown">
                            <a className="nav-link dropdown-toggle" href="#" role="button" data-bs-toggle="dropdown">
                                <i className="fa-solid fa-circle-user me-1" />{user.username}
                            </a>
                            <ul className="dropdown-menu dropdown-menu-end">
                                <li>
                                    <span className="dropdown-item-text text-muted">
                                        <small>Role: {user.role_label}</small>
                                    </span>
                                </li>
                                <li><hr className="dropdown-divider" /></li>
                                <li>
                                    <button className="dropdown-item" onClick={logout}>
                                        <i className="fa-solid fa-right-from-bracket me-1" />Logout
                                    </button>
                                </li>
                            </ul>
                        </li>

                    </ul>
                </div>
            </div>
        </nav>
    );
}
