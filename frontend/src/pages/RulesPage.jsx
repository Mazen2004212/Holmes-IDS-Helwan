import { useState, useEffect } from 'react';
import { api } from '../api/client';

export default function RulesPage() {
  const [rules, setRules] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    api.get('/api/rules')
      .then(async r => {
        if (!r.ok) {
          const body = await r.json().catch(() => ({}));
          throw new Error(body.error || `Server error (${r.status})`);
        }
        return r.json();
      })
      .then(d => { setRules(d.rules || []); setLoading(false); })
      .catch(e => { setError(e.message || 'Failed to load rules'); setLoading(false); });
  }, []);

  if (loading) return <div className="text-center mt-5"><div className="spinner-border text-light" /></div>;
  if (error) return <div className="alert alert-danger mt-4"><i className="fas fa-exclamation-triangle me-2" />{error}</div>;

  return (
    <div>
      <h2 className="mb-4"><i className="fa-solid fa-gavel me-2" />Rules Dashboard</h2>
      <div className="card">
        <div className="card-header"><h5 className="mb-0">Loaded Rules ({rules.length})</h5></div>
        <div className="card-body table-responsive">
          {rules.length === 0 ? (
            <p className="text-muted">No rules loaded.</p>
          ) : (
            <table className="table table-sm table-hover">
              <thead>
                <tr><th>#</th><th>Action</th><th>Protocol</th><th>Source IP</th><th>Src Port</th><th>Direction</th><th>Dest IP</th><th>Dst Port</th><th>Options</th></tr>
              </thead>
              <tbody>
                {rules.map((r, i) => (
                  <tr key={r.id || i}>
                    <td>{r.id}</td>
                    <td><span className={`badge ${r.action === 'alert' ? 'bg-danger' : 'bg-secondary'}`}>{r.action}</span></td>
                    <td>{r.protocol}</td>
                    <td>{r.src_ip}</td>
                    <td>{r.src_port}</td>
                    <td>{r.direction}</td>
                    <td>{r.dst_ip}</td>
                    <td>{r.dst_port}</td>
                    <td className="text-truncate" style={{ maxWidth: '250px' }}>{r.options}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}
