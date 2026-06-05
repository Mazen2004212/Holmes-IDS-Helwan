import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { api } from '../api/client';

export default function ExplainPage() {
    const { alertId } = useParams();
    const navigate = useNavigate();
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        api.get(`/api/explain/${alertId}`)
            .then(r => r.json())
            .then(d => {
                if (d.error) setError(d.error);
                else setData(d);
                setLoading(false);
            })
            .catch(e => { setError(e.message); setLoading(false); });
    }, [alertId]);

    if (loading) return <div className="text-center mt-5"><div className="spinner-border text-light" /></div>;
    if (error) return (
        <div>
            <div className="alert alert-warning">{error}</div>
            <button className="btn btn-secondary" onClick={() => navigate(-1)}>Go Back</button>
        </div>
    );

    const shapFeatures = data.shap_result?.top_features
        || data.shap_result?.feature_contributions?.map(([feature, importance]) => ({ feature, importance }))
        || [];
    const limeFeatures = data.lime_result?.top_features
        || data.lime_result?.feature_contributions?.map(([feature, weight]) => ({ feature, weight }))
        || [];
    const describeFeature = (feature) => {
        const entry = data.glossary?.[feature];
        if (!entry) return '';
        return typeof entry === 'string' ? entry : entry.description || entry.name || '';
    };

    return (
        <div>
            <div className="d-flex justify-content-between align-items-center mb-4">
                <h2><i className="fa-solid fa-microscope me-2" />Explain Alert #{alertId}</h2>
                <button className="btn btn-outline-secondary" onClick={() => navigate(-1)}>
                    <i className="fas fa-arrow-left me-1" />Back
                </button>
            </div>

            {/* Prediction Info */}
            <div className="row mb-4">
                <div className="col-md-6">
                    <div className="card">
                        <div className="card-body">
                            <h5>Predicted Label: <span className="badge bg-danger">{data.predicted_label}</span></h5>
                        </div>
                    </div>
                </div>
            </div>

            {/* SHAP Results */}
            {data.shap_result && (
                <div className="card mb-4">
                    <div className="card-header"><h5 className="mb-0">SHAP Feature Importance</h5></div>
                    <div className="card-body">
                        {data.shap_result.error && (
                            <div className="alert alert-warning">{data.shap_result.error}</div>
                        )}
                        {data.shap_result.chart_base64 && (
                            <img
                                className="img-fluid mb-3"
                                src={`data:image/png;base64,${data.shap_result.chart_base64}`}
                                alt="SHAP feature importance chart"
                            />
                        )}
                        {shapFeatures.length > 0 && (
                            <table className="table table-sm">
                                <thead><tr><th>Feature</th><th>SHAP Value</th><th>Description</th></tr></thead>
                                <tbody>
                                    {shapFeatures.map((f, i) => (
                                        <tr key={i}>
                                            <td><code>{f.feature}</code></td>
                                            <td>
                                                <span className={`badge ${f.importance > 0 ? 'bg-danger' : 'bg-success'}`}>
                                                    {f.importance.toFixed(4)}
                                                </span>
                                            </td>
                                            <td className="text-muted small">{describeFeature(f.feature)}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        )}
                    </div>
                </div>
            )}

            {/* LIME Results */}
            {data.lime_result && (
                <div className="card mb-4">
                    <div className="card-header"><h5 className="mb-0">LIME Explanation</h5></div>
                    <div className="card-body">
                        {data.lime_result.error && (
                            <div className="alert alert-warning">{data.lime_result.error}</div>
                        )}
                        {data.lime_result.chart_base64 && (
                            <img
                                className="img-fluid mb-3"
                                src={`data:image/png;base64,${data.lime_result.chart_base64}`}
                                alt="LIME feature contribution chart"
                            />
                        )}
                        {limeFeatures.length > 0 && (
                            <table className="table table-sm">
                                <thead><tr><th>Feature</th><th>Weight</th></tr></thead>
                                <tbody>
                                    {limeFeatures.map((f, i) => (
                                        <tr key={i}>
                                            <td><code>{f.feature}</code></td>
                                            <td><span className={`badge ${f.weight > 0 ? 'bg-danger' : 'bg-success'}`}>{f.weight.toFixed(4)}</span></td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        )}
                    </div>
                </div>
            )}

            {/* Raw Features */}
            <div className="card mb-4">
                <div className="card-header"><h5 className="mb-0">Alert Features</h5></div>
                <div className="card-body table-responsive">
                    <table className="table table-sm">
                        <thead><tr><th>Feature</th><th>Value</th><th>Description</th></tr></thead>
                        <tbody>
                            {data.features && Object.entries(data.features).map(([k, v]) => (
                                <tr key={k}>
                                    <td><code>{k}</code></td>
                                    <td>{typeof v === 'number' ? v.toFixed(4) : String(v)}</td>
                                    <td className="text-muted small">{describeFeature(k)}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}
