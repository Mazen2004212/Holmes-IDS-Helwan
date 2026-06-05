import { useState } from 'react';
import { api } from '../api/client';
import AlertsTable from '../components/AlertsTable';

export default function PcapUploadPage() {
    const [pcapFile, setPcapFile] = useState(null);
    const [keylogFile, setKeylogFile] = useState(null);
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState(null);
    const [error, setError] = useState('');

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!pcapFile) return;
        setLoading(true);
        setError('');
        setResult(null);

        const formData = new FormData();
        formData.append('pcap_file', pcapFile);
        if (keylogFile) formData.append('keylog_file', keylogFile);

        try {
            const res = await api.upload('/api/uploads/pcap', formData);
            const data = await res.json();
            if (data.success) {
                setResult(data);
            } else {
                setError(data.error || 'Upload failed.');
            }
        } catch (e) {
            setError('Connection error.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div>
            <h2 className="mb-4"><i className="fas fa-upload me-2" />PCAP Signature Detection</h2>

            <div className="card mb-4">
                <div className="card-body">
                    <form onSubmit={handleSubmit}>
                        <div className="mb-3">
                            <label className="form-label">PCAP File</label>
                            <input type="file" className="form-control" accept=".pcap,.pcapng,.cap" onChange={e => setPcapFile(e.target.files[0])} required />
                        </div>
                        <div className="mb-3">
                            <label className="form-label">TLS Keylog File (optional)</label>
                            <input type="file" className="form-control" onChange={e => setKeylogFile(e.target.files[0])} />
                        </div>
                        <button type="submit" className="btn btn-primary" disabled={loading}>
                            {loading ? <><span className="spinner-border spinner-border-sm me-2" />Scanning...</> : <><i className="fas fa-upload me-1" />Scan PCAP</>}
                        </button>
                    </form>
                </div>
            </div>

            {error && <div className="alert alert-danger">{error}</div>}

            {result && (
                <>
                    {result.messages && result.messages.map((m, i) => (
                        <div key={i} className="alert alert-info">{m}</div>
                    ))}
                    <AlertsTable alerts={result.alerts} title="PCAP Alerts" showMethod />

                    {result.tls_results && result.tls_results.results && (
                        <div className="card mb-4">
                            <div className="card-header"><h5 className="mb-0">TLS Decryption Results</h5></div>
                            <div className="card-body table-responsive">
                                <table className="table table-sm">
                                    <thead><tr><th>#</th><th>Detail</th></tr></thead>
                                    <tbody>
                                        {result.tls_results.results.map((r, i) => (
                                            <tr key={i}><td>{i + 1}</td><td><pre className="mb-0" style={{ fontSize: '0.8rem' }}>{JSON.stringify(r, null, 2)}</pre></td></tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    )}

                    {result.tls_metadata && result.tls_metadata.results && (
                        <div className="card mb-4">
                            <div className="card-header"><h5 className="mb-0">TLS Metadata</h5></div>
                            <div className="card-body table-responsive">
                                <table className="table table-sm">
                                    <thead><tr><th>#</th><th>Metadata</th></tr></thead>
                                    <tbody>
                                        {result.tls_metadata.results.map((r, i) => (
                                            <tr key={i}><td>{i + 1}</td><td><pre className="mb-0" style={{ fontSize: '0.8rem' }}>{JSON.stringify(r, null, 2)}</pre></td></tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    )}
                </>
            )}
        </div>
    );
}
