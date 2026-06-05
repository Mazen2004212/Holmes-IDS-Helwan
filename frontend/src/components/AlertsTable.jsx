import { useState, useMemo } from 'react';
import { Link } from 'react-router-dom';

/**
 * Shared alerts table with sortable column headers.
 * Used by Signature, Anomaly, Live, and PCAP pages.
 */
export default function AlertsTable({
  alerts = [],
  title = 'Alerts',
  showMethod = true,
  showCheckbox = false,
  showExplain = false,
  onSelectionChange = null,
}) {
  const [sortKey, setSortKey] = useState(null);
  const [sortDir, setSortDir] = useState('asc');

  const handleSort = (key) => {
    if (sortKey === key) {
      setSortDir(d => (d === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortKey(key);
      setSortDir('asc');
    }
  };

  const sorted = useMemo(() => {
    if (!sortKey) return alerts;
    return [...alerts].sort((a, b) => {
      const va = a[sortKey] ?? '';
      const vb = b[sortKey] ?? '';
      if (typeof va === 'number' && typeof vb === 'number') {
        return sortDir === 'asc' ? va - vb : vb - va;
      }
      const sa = String(va).toLowerCase();
      const sb = String(vb).toLowerCase();
      if (sa < sb) return sortDir === 'asc' ? -1 : 1;
      if (sa > sb) return sortDir === 'asc' ? 1 : -1;
      return 0;
    });
  }, [alerts, sortKey, sortDir]);

  const SortIcon = ({ col }) => {
    if (sortKey !== col) return <i className="fas fa-sort ms-1 text-muted" style={{ fontSize: '0.7rem' }} />;
    return sortDir === 'asc'
      ? <i className="fas fa-sort-up ms-1" />
      : <i className="fas fa-sort-down ms-1" />;
  };

  const ThSort = ({ col, children }) => (
    <th role="button" onClick={() => handleSort(col)} style={{ cursor: 'pointer', userSelect: 'none' }}>
      {children}<SortIcon col={col} />
    </th>
  );

  if (!alerts.length) {
    return (
      <div className="card mb-4">
        <div className="card-header"><h5 className="mb-0">{title}</h5></div>
        <div className="card-body"><p className="text-muted mb-0">No alerts found.</p></div>
      </div>
    );
  }

  return (
    <div className="card mb-4">
      <div className="card-header d-flex justify-content-between align-items-center">
        <h5 className="mb-0">{title} ({alerts.length})</h5>
      </div>
      <div className="card-body table-responsive">
        <table className="table table-hover table-sm">
          <thead>
            <tr>
              {showCheckbox && <th><input type="checkbox" onChange={(e) => {
                const checked = e.target.checked;
                alerts.forEach(a => onSelectionChange?.(a.id, checked));
              }} /></th>}
              <ThSort col="id">#</ThSort>
              <ThSort col="timestamp">Timestamp</ThSort>
              <ThSort col="src_ip">Source IP</ThSort>
              <ThSort col="dst_ip">Dest IP</ThSort>
              <ThSort col="attack">Attack</ThSort>
              {showMethod && <ThSort col="method">Method</ThSort>}
              <ThSort col="message">Message</ThSort>
              {showExplain && <th>Actions</th>}
            </tr>
          </thead>
          <tbody>
            {sorted.map((a, i) => (
              <tr key={a.id || i}>
                {showCheckbox && <td><input type="checkbox" value={a.id} onChange={(e) => onSelectionChange?.(a.id, e.target.checked)} /></td>}
                <td>{a.id}</td>
                <td>{a.timestamp}</td>
                <td><span className="badge bg-info text-dark">{a.src_ip}</span></td>
                <td><span className="badge bg-warning text-dark">{a.dst_ip}</span></td>
                <td><span className="badge bg-danger">{a.attack}</span></td>
                {showMethod && <td><span className="badge bg-secondary">{a.method}</span></td>}
                <td className="text-truncate" style={{ maxWidth: '300px' }}>{a.message}</td>
                {showExplain && (
                  <td>
                    <Link
                      className="btn btn-sm btn-outline-info"
                      to={`/explain/${a.id}`}
                      title="Explain this alert with SHAP and LIME"
                    >
                      <i className="fa-solid fa-microscope me-1" />
                      Explain
                    </Link>
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
