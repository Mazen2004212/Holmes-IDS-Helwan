import { useState } from 'react';
import { api } from '../api/client';

export default function CsvUploadPage() {
    const [file, setFile] = useState(null);
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState(null);
    const [error, setError] = useState('');

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!file) return;
        setLoading(true);
        setError('');
        setResult(null);

        const formData = new FormData();
        formData.append('csv_file', file);

        try {
            const res = await api.upload('/api/uploads/csv', formData);
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
            <h2 className="mb-4"><i className="fas fa-upload me-2" />CSV Anomaly Detection</h2>

            <div className="card mb-4">
                <div className="card-body">
                    <form onSubmit={handleSubmit}>
                        <div className="mb-3">
                            <label className="form-label">Upload CSV File</label>
                            <input type="file" className="form-control" accept=".csv" onChange={e => setFile(e.target.files[0])} required />
                        </div>
                        <button type="submit" className="btn btn-primary" disabled={loading}>
                            {loading ? <><span className="spinner-border spinner-border-sm me-2" />Processing...</> : <><i className="fas fa-upload me-1" />Analyze CSV</>}
                        </button>
                    </form>
                </div>
            </div>

            {error && <div className="alert alert-danger">{error}</div>}

            {result && (
                <>
                    {/* Stats */}
                    {result.stats && (
                        <div className="row mb-4">
                            {Object.entries(result.stats).map(([key, val]) => (
                                <div className="col-md-3 mb-2" key={key}>
                                    <div className="card text-center">
                                        <div className="card-body py-2">
                                            <h5 className="mb-0">{typeof val === 'number' ? val : String(val)}</h5>
                                            <small className="text-muted">{key.replace(/_/g, ' ')}</small>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}

                    {/* Predictions Table */}
                    {result.predictions && result.predictions.length > 0 && (
                        <div className="card">
                            <div className="card-header">
                                <h5 className="mb-0">
                                    Predictions ({result.total_rows || result.predictions.length} total)
                                    {result.truncated && <small className="text-muted ms-2">— showing first {result.predictions.length}</small>}
                                </h5>
                            </div>
                            <div className="card-body table-responsive">
                                <table className="table table-sm table-hover">
                                    <thead>
                                        <tr>
                                            <th>#</th>
                                            <th>Prediction</th>
                                            <th>Method</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {result.predictions.map((pred, i) => {
                                            const label = typeof pred === 'object' ? JSON.stringify(pred) : String(pred);
                                            const isBenign = label === 'BENIGN';
                                            return (
                                                <tr key={i}>
                                                    <td>{i + 1}</td>
                                                    <td><span className={`badge ${isBenign ? 'bg-success' : 'bg-danger'}`}>{label}</span></td>
                                                    <td><span className="badge bg-secondary">anomaly</span></td>
                                                </tr>
                                            );
                                        })}
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
