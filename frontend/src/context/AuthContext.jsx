import { createContext, useContext, useState, useEffect } from 'react';
import { api } from '../api/client';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    // Check session on mount
    useEffect(() => {
        api.get('/api/auth/me')
            .then(res => res.json())
            .then(data => {
                if (data.authenticated) {
                    setUser(data.user);
                }
            })
            .catch(() => { })
            .finally(() => setLoading(false));
    }, []);

    const login = async (username, password) => {
        const res = await api.post('/api/auth/login', { username, password });
        const data = await res.json();
        if (data.success) {
            setUser(data.user);
        }
        return data;
    };

    const logout = async () => {
        await api.post('/api/auth/logout');
        setUser(null);
    };

    return (
        <AuthContext.Provider value={{ user, loading, login, logout }}>
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    const ctx = useContext(AuthContext);
    if (!ctx) throw new Error('useAuth must be used within AuthProvider');
    return ctx;
}
