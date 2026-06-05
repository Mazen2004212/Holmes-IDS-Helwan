import { useState } from 'react';
import { useNavigate, Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function LoginPage() {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const { login, user } = useAuth();
    const navigate = useNavigate();

    // If already authenticated, redirect
    if (user) {
        return <Navigate to="/" replace />;
    }

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        try {
            const data = await login(username, password);
            if (data.success) {
                navigate(data.default_route || '/', { replace: true });
            } else {
                setError(data.error || 'Invalid username or password.');
            }
        } catch (err) {
            setError('Connection error. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="row justify-content-center mt-5">
            <div className="col-md-5">
                <div className="card shadow-lg">
                    <div className="card-body p-5">
                        <div className="text-center mb-4">
                            <img src="/static/IMG/w1.png" alt="Logo" style={{ width: '80px' }} />
                            <h3 className="fw-bold mt-2">HOLMES IDS</h3>
                            <p className="text-muted">Sign in to your account</p>
                        </div>

                        {error && (
                            <div className="alert alert-danger alert-dismissible fade show" role="alert">
                                {error}
                                <button
                                    type="button"
                                    className="btn-close"
                                    onClick={() => setError('')}
                                />
                            </div>
                        )}

                        <form onSubmit={handleSubmit}>
                            <div className="mb-3">
                                <label htmlFor="username" className="form-label">
                                    <i className="fa-solid fa-user me-1" />Username
                                </label>
                                <input
                                    type="text"
                                    className="form-control form-control-lg"
                                    id="username"
                                    placeholder="Enter username"
                                    required
                                    autoFocus
                                    value={username}
                                    onChange={(e) => setUsername(e.target.value)}
                                />
                            </div>
                            <div className="mb-4">
                                <label htmlFor="password" className="form-label">
                                    <i className="fa-solid fa-lock me-1" />Password
                                </label>
                                <input
                                    type="password"
                                    className="form-control form-control-lg"
                                    id="password"
                                    placeholder="Enter password"
                                    required
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                />
                            </div>
                            <button
                                type="submit"
                                className="btn btn-primary btn-lg w-100"
                                disabled={loading}
                            >
                                {loading ? (
                                    <>
                                        <span className="spinner-border spinner-border-sm me-2" role="status" />
                                        Signing in...
                                    </>
                                ) : (
                                    <>
                                        <i className="fa-solid fa-right-to-bracket me-1" /> Sign In
                                    </>
                                )}
                            </button>
                        </form>
                    </div>
                </div>
            </div>
        </div>
    );
}
