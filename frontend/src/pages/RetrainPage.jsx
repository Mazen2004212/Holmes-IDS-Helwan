import { useState, useEffect } from 'react';
import { api } from '../api/client';
import { useFlash } from '../components/FlashMessages';

export default function RetrainPage() {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [page, setPage] = useState(1);
    const [filters, setFilters] = useState({ label: '', labeled: '', source: '', date_from: '', date_to: '' });
    const flash = useFlash();

    const fetchData = (p = page) => {
        const params = new URLSearchParams({ page: p });
        Object.entries(filters).forEach(([k, v]) => { if (v) params.set(k, v); });
        api.get(`/api/retrain/dashboard?${params}`)
            .then(r => r.json())
            .then(d => { setData(d); setLoading(false); })
            .catch(() => setLoading(false));
    };

    useEffect(() => { fetchData(); }, [page]);

    const handleRetrain = async () => {
        const res = await api.post('/api/retrain/start');
        const d = await res.json();
        flash(d.message, d.success ? 'success' : 'danger');
        fetchData();
    };

    const handleLabel = async (sampleId, label) => {
        const res = await api.post('/api/retrain/label', { sample_id: sampleId, label });
        const d = await res.json();
        flash(d.message, d.success ? 'success' : 'danger');
        fetchData();
    };

    const handleFilter = (e) => {
        e.preventDefault();
        setPage(1);
        fetchData(1);
    };

    if (loading) return <div className="text-center mt-5"><div className="spinner-border text-light" /></div>;

    const stats = data?.stats || {};
    const samples = data?.samples || [];
    const history = data?.history || [];
    const retrain_status = data?.retrain_status || {};
    const label_classes = data?.label_classes || [];

    return (
        <div>
            <h2 className="mb-4"><i className="fa-solid fa-brain me-2" />Continual Learning</h2>

            {/* Stats + Retrain Button */}
            <div className="row mb-4">
                <div className="col-md-8">
                    <div className="card">
                        <div className="card-body">
                            <div className="row">
                                {Object.entries(stats).map(([k, v]) => (
                                    <div className="col-md-3 text-center mb-2" key={k}>
                                        <h4>{typeof v === 'number' ? v : String(v)}</h4>
                                        <small className="text-muted">{k.replace(/_/g, ' ')}</small>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                </div>
                <div className="col-md-4">
                    <div className="card">
                        <div className="card-body text-center">
                            <p className="mb-2">
                                Status: <span className={`badge ${retrain_status.running ? 'bg-warning' : 'bg-success'}`}>
                                    {retrain_status.running ? 'Running...' : 'Idle'}
                                </span>
                            </p>
                            <button className="btn btn-primary" onClick={handleRetrain} disabled={retrain_status.running}>
                                <i className="fas fa-play me-1" />Start Retraining
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            {/* Filters */}
            <div className="card mb-4">
                <div className="card-header"><h5 className="mb-0">Filters</h5></div>
                <div className="card-body">
                    <form onSubmit={handleFilter} className="row g-2">
                        <div className="col-md-2">
                            <select className="form-select form-select-sm" value={filters.label} onChange={e => setFilters({ ...filters, label: e.target.value })}>
                                <option value="">All Labels</option>
                                {label_classes.map(c => <option key={c} value={c}>{c}</option>)}
                            </select>
                        </div>
                        <div className="col-md-2">
                            <select className="form-select form-select-sm" value={filters.labeled} onChange={e => setFilters({ ...filters, labeled: e.target.value })}>
                                <option value="">All</option>
                                <option value="yes">Labeled</option>
                                <option value="no">Unlabeled</option>
                            </select>
                        </div>
                        <div className="col-md-2">
                            <input type="text" className="form-control form-control-sm" placeholder="Source" value={filters.source} onChange={e => setFilters({ ...filters, source: e.target.value })} />
                        </div>
                        <div className="col-md-2">
                            <input type="date" className="form-control form-control-sm" value={filters.date_from} onChange={e => setFilters({ ...filters, date_from: e.target.value })} />
                        </div>
                        <div className="col-md-2">
                            <input type="date" className="form-control form-control-sm" value={filters.date_to} onChange={e => setFilters({ ...filters, date_to: e.target.value })} />
                        </div>
                        <div className="col-md-2">
                            <button className="btn btn-sm btn-outline-primary w-100" type="submit"><i className="fas fa-filter me-1" />Filter</button>
                        </div>
                    </form>
                </div>
            </div>

            {/* Training Samples */}
            <div className="card mb-4">
                <div className="card-header d-flex justify-content-between">
                    <h5 className="mb-0">Training Samples</h5>
                    <div>
                        <button className="btn btn-sm btn-outline-secondary me-1" disabled={page <= 1} onClick={() => setPage(p => p - 1)}>← Prev</button>
                        <span className="badge bg-secondary">Page {page}</span>
                        <button className="btn btn-sm btn-outline-secondary ms-1" disabled={samples.length < (data?.per_page || 50)} onClick={() => setPage(p => p + 1)}>Next →</button>
                    </div>
                </div>
                <div className="card-body table-responsive">
                    <table className="table table-sm table-hover">
                        <thead>
                            <tr><th>#</th><th>Predicted</th><th>Human Label</th><th>Source</th><th>Date</th><th>Action</th></tr>
                        </thead>
                        <tbody>
                            {samples.map((s, i) => (
                                <tr key={s.id || i}>
                                    <td>{s.id}</td>
                                    <td><span className="badge bg-info">{s.predicted_label || '—'}</span></td>
                                    <td>{s.human_label || <span className="text-muted">—</span>}</td>
                                    <td>{s.source || '—'}</td>
                                    <td>{s.created_at || '—'}</td>
                                    <td>
                                        <select className="form-select form-select-sm" style={{ width: 'auto', display: 'inline' }}
                                            defaultValue="" onChange={e => { if (e.target.value) handleLabel(s.id, e.target.value); }}>
                                            <option value="" disabled>Label...</option>
                                            {label_classes.map(c => <option key={c} value={c}>{c}</option>)}
                                        </select>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Retrain History */}
            {history.length > 0 && (
                <div className="card mb-4">
                    <div className="card-header"><h5 className="mb-0">Retrain History</h5></div>
                    <div className="card-body table-responsive">
                        <table className="table table-sm">
                            <thead><tr><th>#</th><th>Started</th><th>Status</th><th>By</th><th>Details</th></tr></thead>
                            <tbody>
                                {history.map((h, i) => (
                                    <tr key={h.id || i}>
                                        <td>{h.id}</td>
                                        <td>{h.started_at}</td>
                                        <td><span className={`badge ${h.status === 'completed' ? 'bg-success' : h.status === 'failed' ? 'bg-danger' : 'bg-warning'}`}>{h.status}</span></td>
                                        <td>{h.started_by}</td>
                                        <td className="text-truncate" style={{ maxWidth: '300px' }}>{h.details || '—'}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}
        </div>
    );
}
