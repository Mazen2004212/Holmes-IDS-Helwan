import { useState, useEffect } from 'react';
import { api } from '../api/client';
import AlertsTable from '../components/AlertsTable';

export default function SignaturePage() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    api.get('/api/signature/dashboard')
      .then(async r => {
        if (!r.ok) {
          const body = await r.json().catch(() => ({}));
          throw new Error(body.error || `Server error (${r.status})`);
        }
        return r.json();
      })
      .then(d => { setData(d); setLoading(false); })
      .catch(e => { setError(e.message || 'Failed to load dashboard'); setLoading(false); });
  }, []);

  if (loading) return <div className="text-center mt-5"><div className="spinner-border text-light" /></div>;
  if (error) return <div className="alert alert-danger mt-4"><i className="fas fa-exclamation-triangle me-2" />{error}</div>;
  if (!data) return <div className="alert alert-warning mt-4">No data available.</div>;

  return (
    <div>
      <h2 className="mb-4"><i className="fa-solid fa-file-signature me-2" />Signature IDS Dashboard</h2>

      {/* Stats Cards */}
      <div className="row mb-4">
        <div className="col-md-4">
          <div className="card text-center">
            <div className="card-body">
              <h3 className="text-danger">{data.num_alerts}</h3>
              <p className="text-muted mb-0">Total Alerts</p>
            </div>
          </div>
        </div>
        <div className="col-md-4">
          <div className="card text-center">
            <div className="card-body">
              <h3 className="text-info">{data.top_src_ip}</h3>
              <p className="text-muted mb-0">Top Source IP</p>
            </div>
          </div>
        </div>
        <div className="col-md-4">
          <div className="card text-center">
            <div className="card-body">
              <h3 className="text-warning">{data.top_dst_ip}</h3>
              <p className="text-muted mb-0">Top Destination IP</p>
            </div>
          </div>
        </div>
      </div>

      <AlertsTable alerts={data.alerts} title="Signature Alerts" />

      {/* Rules Table */}
      <div className="card mb-4">
        <div className="card-header"><h5 className="mb-0">Loaded Rules ({data.rules.length})</h5></div>
        <div className="card-body table-responsive">
          <table className="table table-sm table-hover">
            <thead>
              <tr><th>Action</th><th>Protocol</th><th>Source</th><th>Direction</th><th>Destination</th><th>Options</th></tr>
            </thead>
            <tbody>
              {data.rules.map((r, i) => (
                <tr key={r.id || i}>
                  <td><span className={`badge ${r.action === 'alert' ? 'bg-danger' : 'bg-secondary'}`}>{r.action}</span></td>
                  <td>{r.protocol}</td>
                  <td>{r.src_ip}:{r.src_port}</td>
                  <td>{r.direction}</td>
                  <td>{r.dst_ip}:{r.dst_port}</td>
                  <td className="text-truncate" style={{ maxWidth: '200px' }}>{r.options}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
