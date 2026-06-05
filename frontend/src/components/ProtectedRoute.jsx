import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

/**
 * Protects routes by role.
 * Usage: <ProtectedRoute roles={['admin','signature_analyst']}>...</ProtectedRoute>
 */
export default function ProtectedRoute({ children, roles = [] }) {
    const { user, loading } = useAuth();

    if (loading) {
        return (
            <div className="d-flex justify-content-center align-items-center" style={{ minHeight: '60vh' }}>
                <div className="spinner-border text-light" role="status">
                    <span className="visually-hidden">Loading...</span>
                </div>
            </div>
        );
    }

    if (!user) {
        return <Navigate to="/login" replace />;
    }

    // Admin has access to everything
    if (user.role === 'admin') {
        return children;
    }

    // Check if user's role is in the allowed list
    if (roles.length > 0 && !roles.includes(user.role)) {
        return <Navigate to="/" replace />;
    }

    return children;
}
