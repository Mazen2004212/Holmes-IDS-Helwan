import { useState, useEffect, useCallback } from 'react';
import { api } from '../api/client';
import AlertsTable from '../components/AlertsTable';
import { useFlash } from '../components/FlashMessages';

export default function LiveCapturePage() {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [selectedAlerts, setSelectedAlerts] = useState(new Set());
    const flash = useFlash();

    const fetchStatus = useCallback(() => {
        api.get('/api/live/status')
            .then(async r => {
                if (!r.ok) throw new Error(`Server error (${r.status})`);
                return r.json();
            })
            .then(d => { setData(d); setLoading(false); })
            .catch(() => setLoading(false));
    }, []);

    useEffect(() => {
        fetchStatus();
        const interval = setInterval(fetchStatus, 5000); // Poll every 5s
        return () => clearInterval(interval);
    }, [fetchStatus]);

    const handleStart = async (iface) => {
        const res = await api.post('/api/live/start', { interface: iface });
        const d = await res.json();
        flash(d.message, d.success ? 'success' : 'danger');
        fetchStatus();
    };

    const handleStop = async () => {
        const res = await api.post('/api/live/stop');
        const d = await res.json();
        flash(d.message, d.success ? 'success' : 'danger');
        fetchStatus();
    };

    const handleClear = async () => {
        const res = await api.post('/api/live/clear');
        const d = await res.json();
        flash(d.message, d.success ? 'success' : 'danger');
        fetchStatus();
    };

    const handleDelete = async () => {
        if (selectedAlerts.size === 0) return;
        const res = await api.post('/api/live/delete', { alert_ids: [...selectedAlerts] });
        const d = await res.json();
        flash(d.message, d.success ? 'success' : 'danger');
        setSelectedAlerts(new Set());
        fetchStatus();
    };

    const handleSelectionChange = (id, checked) => {
        setSelectedAlerts(prev => {
            const next = new Set(prev);
            if (checked) next.add(id); else next.delete(id);
            return next;
        });
    };

    if (loading) return <div className="text-center mt-5"><div className="spinner-border text-light" /></div>;

    const status = data?.status || {};
    const alerts = data?.alerts || [];
    const interfaces = data?.interfaces || [];

    return (
        <div>
            <h2 className="mb-4"><i className="fa-solid fa-satellite-dish me-2" />Live Capture</h2>

            {/* Status Card */}
            <div className="card mb-4">
                <div className="card-header d-flex justify-content-between align-items-center">
                    <h5 className="mb-0">Capture Status</h5>
                    <span className={`badge ${status.running ? 'bg-success' : 'bg-secondary'}`}>
                        {status.running ? 'Running' : 'Stopped'}
                    </span>
                </div>
                <div className="card-body">
                    <div className="row mb-3">
                        <div className="col-md-3"><strong>Interface:</strong> {status.interface_name || 'None'}</div>
                        <div className="col-md-3"><strong>Packets:</strong> {status.packets_captured}</div>
                        <div className="col-md-3"><strong>Alerts:</strong> {status.alerts_generated}</div>
                        <div className="col-md-3"><strong>Description:</strong> {status.interface_desc || '—'}</div>
                    </div>

                    {status.last_error && (
                        <div className="alert alert-danger py-2">
                            <strong>Capture error:</strong> {status.last_error}
                        </div>
                    )}

                    <div className="d-flex gap-2 flex-wrap">
                        {!status.running ? (
                            <>
                                <select className="form-select" style={{ width: 'auto' }} id="ifaceSelect">
                                    {interfaces.map(iface => (
                                        <option key={iface.id} value={iface.id}>{iface.name} — {iface.description}</option>
                                    ))}
                                </select>
                                <button className="btn btn-success" onClick={() => {
                                    const sel = document.getElementById('ifaceSelect');
                                    handleStart(sel?.value);
                                }}><i className="fas fa-play me-1" />Start</button>
                            </>
                        ) : (
                            <button className="btn btn-danger" onClick={handleStop}><i className="fas fa-stop me-1" />Stop</button>
                        )}
                        <button className="btn btn-warning" onClick={handleClear}><i className="fas fa-trash me-1" />Clear All</button>
                        <button className="btn btn-outline-danger" onClick={handleDelete} disabled={selectedAlerts.size === 0}>
                            <i className="fas fa-times me-1" />Delete Selected ({selectedAlerts.size})
                        </button>
                    </div>
                </div>
            </div>

            <AlertsTable alerts={alerts} title="Live Alerts" showMethod showCheckbox onSelectionChange={handleSelectionChange} />
        </div>
    );
}
