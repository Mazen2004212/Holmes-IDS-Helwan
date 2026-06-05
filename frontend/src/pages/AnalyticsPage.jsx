import { useState } from 'react';
import { api } from '../api/client';

export default function AnalyticsPage() {
    const [query, setQuery] = useState({
        table: 'alerts',
        columns: ['*'],
        conditions: [],
        order_by: '',
        order_dir: 'DESC',
        limit: 100,
    });
    const [result, setResult] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const tables = ['alerts', 'logs', 'rules', 'users', 'training_data'];
    const commonColumns = {
        alerts: ['id', 'timestamp', 'src_ip', 'dst_ip', 'message', 'attack', 'method'],
        logs: ['id', 'timestamp', 'event_type', 'src_ip', 'dst_ip', 'message', 'attack', 'method'],
        rules: ['id', 'action', 'protocol', 'src_ip', 'src_port', 'direction', 'dst_ip', 'dst_port', 'options'],
        users: ['id', 'username', 'role'],
        training_data: ['id', 'predicted_label', 'human_label', 'source', 'created_at'],
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');
        setResult(null);

        try {
            const res = await api.post('/api/analytics/query', query);
            const data = await res.json();
            if (data.success === false) {
                setError(data.error || 'Query failed.');
            } else {
                setResult(data);
            }
        } catch (e) {
            setError('Connection error.');
        } finally {
            setLoading(false);
        }
    };

    const addCondition = () => {
        setQuery(q => ({
            ...q,
            conditions: [...q.conditions, { column: '', operator: '=', value: '' }],
        }));
    };

    const removeCondition = (i) => {
        setQuery(q => ({
            ...q,
            conditions: q.conditions.filter((_, idx) => idx !== i),
        }));
    };

    const updateCondition = (i, field, value) => {
        setQuery(q => ({
            ...q,
            conditions: q.conditions.map((c, idx) => idx === i ? { ...c, [field]: value } : c),
        }));
    };

    return (
        <div>
            <h2 className="mb-4"><i className="fa-solid fa-magnifying-glass-chart me-2" />Analytics Query Builder</h2>

            <div className="card mb-4">
                <div className="card-body">
                    <form onSubmit={handleSubmit}>
                        <div className="row g-3 mb-3">
                            <div className="col-md-3">
                                <label className="form-label">Table</label>
                                <select className="form-select" value={query.table} onChange={e => setQuery({ ...query, table: e.target.value })}>
                                    {tables.map(t => <option key={t} value={t}>{t}</option>)}
                                </select>
                            </div>
                            <div className="col-md-3">
                                <label className="form-label">Order By</label>
                                <select className="form-select" value={query.order_by} onChange={e => setQuery({ ...query, order_by: e.target.value })}>
                                    <option value="">Default</option>
                                    {(commonColumns[query.table] || []).map(c => <option key={c} value={c}>{c}</option>)}
                                </select>
                            </div>
                            <div className="col-md-2">
                                <label className="form-label">Direction</label>
                                <select className="form-select" value={query.order_dir} onChange={e => setQuery({ ...query, order_dir: e.target.value })}>
                                    <option value="DESC">DESC</option>
                                    <option value="ASC">ASC</option>
                                </select>
                            </div>
                            <div className="col-md-2">
                                <label className="form-label">Limit</label>
                                <input type="number" className="form-control" value={query.limit} onChange={e => setQuery({ ...query, limit: parseInt(e.target.value) || 100 })} />
                            </div>
                            <div className="col-md-2 d-flex align-items-end">
                                <button type="submit" className="btn btn-primary w-100" disabled={loading}>
                                    {loading ? <span className="spinner-border spinner-border-sm" /> : <><i className="fas fa-search me-1" />Query</>}
                                </button>
                            </div>
                        </div>

                        {/* Conditions */}
                        <div className="mb-2">
                            <label className="form-label">Conditions</label>
                            <button type="button" className="btn btn-sm btn-outline-secondary ms-2" onClick={addCondition}>
                                <i className="fas fa-plus me-1" />Add
                            </button>
                        </div>
                        {query.conditions.map((c, i) => (
                            <div className="row g-2 mb-2" key={i}>
                                <div className="col-md-3">
                                    <select className="form-select form-select-sm" value={c.column} onChange={e => updateCondition(i, 'column', e.target.value)}>
                                        <option value="">Column...</option>
                                        {(commonColumns[query.table] || []).map(col => <option key={col} value={col}>{col}</option>)}
                                    </select>
                                </div>
                                <div className="col-md-2">
                                    <select className="form-select form-select-sm" value={c.operator} onChange={e => updateCondition(i, 'operator', e.target.value)}>
                                        {['=', '!=', '>', '<', '>=', '<=', 'LIKE', 'IN'].map(op => <option key={op} value={op}>{op}</option>)}
                                    </select>
                                </div>
                                <div className="col-md-5">
                                    <input className="form-control form-control-sm" value={c.value} onChange={e => updateCondition(i, 'value', e.target.value)} placeholder="Value" />
                                </div>
                                <div className="col-md-2">
                                    <button type="button" className="btn btn-sm btn-outline-danger" onClick={() => removeCondition(i)}><i className="fas fa-times" /></button>
                                </div>
                            </div>
                        ))}
                    </form>
                </div>
            </div>

            {error && <div className="alert alert-danger">{error}</div>}

            {result && (
                <div className="card">
                    <div className="card-header">
                        <h5 className="mb-0">Results {result.rows ? `(${result.rows.length} rows)` : ''}</h5>
                    </div>
                    <div className="card-body table-responsive">
                        {result.rows && result.rows.length > 0 ? (
                            <table className="table table-sm table-hover">
                                <thead>
                                    <tr>{(result.columns || Object.keys(result.rows[0])).map(c => <th key={c}>{c}</th>)}</tr>
                                </thead>
                                <tbody>
                                    {result.rows.map((row, i) => (
                                        <tr key={i}>
                                            {(result.columns || Object.keys(row)).map(c => <td key={c}>{String(row[c] ?? '')}</td>)}
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        ) : (
                            <p className="text-muted">No results found.</p>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
}
