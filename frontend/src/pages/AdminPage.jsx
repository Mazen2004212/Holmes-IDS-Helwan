import { useState, useEffect } from 'react';
import { api } from '../api/client';
import { useFlash } from '../components/FlashMessages';

export default function AdminPage() {
    const [users, setUsers] = useState([]);
    const [roles, setRoles] = useState({});
    const [loading, setLoading] = useState(true);
    const [newUser, setNewUser] = useState({ username: '', password: '', role: 'live_operator' });
    const flash = useFlash();

    const fetchUsers = () => {
        api.get('/api/admin/users')
            .then(async r => {
                if (!r.ok) throw new Error(`Server error (${r.status})`);
                return r.json();
            })
            .then(d => { setUsers(d.users || []); setRoles(d.roles || {}); setLoading(false); })
            .catch(() => setLoading(false));
    };

    useEffect(() => { fetchUsers(); }, []);

    const handleCreate = async (e) => {
        e.preventDefault();
        const res = await api.post('/api/admin/users', newUser);
        const d = await res.json();
        flash(d.message, d.success ? 'success' : 'danger');
        if (d.success) { setNewUser({ username: '', password: '', role: 'live_operator' }); fetchUsers(); }
    };

    const handleDelete = async (id) => {
        if (!confirm('Delete this user?')) return;
        const res = await api.delete(`/api/admin/users/${id}`);
        const d = await res.json();
        flash(d.message, d.success ? 'success' : 'danger');
        fetchUsers();
    };

    const handleRoleChange = async (id, role) => {
        const res = await api.put(`/api/admin/users/${id}/role`, { role });
        const d = await res.json();
        flash(d.message, d.success ? 'success' : 'danger');
        fetchUsers();
    };

    if (loading) return <div className="text-center mt-5"><div className="spinner-border text-light" /></div>;

    return (
        <div>
            <h2 className="mb-4"><i className="fa-solid fa-users-gear me-2" />Admin — User Management</h2>

            {/* Create User */}
            <div className="card mb-4">
                <div className="card-header"><h5 className="mb-0">Create User</h5></div>
                <div className="card-body">
                    <form onSubmit={handleCreate} className="row g-3">
                        <div className="col-md-3">
                            <input className="form-control" placeholder="Username" value={newUser.username}
                                onChange={e => setNewUser({ ...newUser, username: e.target.value })} required />
                        </div>
                        <div className="col-md-3">
                            <input className="form-control" type="password" placeholder="Password" value={newUser.password}
                                onChange={e => setNewUser({ ...newUser, password: e.target.value })} required />
                        </div>
                        <div className="col-md-3">
                            <select className="form-select" value={newUser.role}
                                onChange={e => setNewUser({ ...newUser, role: e.target.value })}>
                                {Object.entries(roles).map(([k, v]) => <option key={k} value={k}>{v.label}</option>)}
                            </select>
                        </div>
                        <div className="col-md-3">
                            <button type="submit" className="btn btn-success w-100"><i className="fas fa-plus me-1" />Create</button>
                        </div>
                    </form>
                </div>
            </div>

            {/* Users Table */}
            <div className="card">
                <div className="card-header"><h5 className="mb-0">Users ({users.length})</h5></div>
                <div className="card-body table-responsive">
                    <table className="table table-hover">
                        <thead><tr><th>ID</th><th>Username</th><th>Role</th><th>Actions</th></tr></thead>
                        <tbody>
                            {users.map(u => (
                                <tr key={u.id}>
                                    <td>{u.id}</td>
                                    <td>{u.username}</td>
                                    <td>
                                        <select className="form-select form-select-sm" value={u.role}
                                            onChange={e => handleRoleChange(u.id, e.target.value)} style={{ width: 'auto', display: 'inline' }}>
                                            {Object.entries(roles).map(([k, v]) => <option key={k} value={k}>{v.label}</option>)}
                                        </select>
                                    </td>
                                    <td>
                                        <button className="btn btn-sm btn-outline-danger" onClick={() => handleDelete(u.id)}
                                            disabled={u.username === 'admin'}><i className="fas fa-trash" /></button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}
