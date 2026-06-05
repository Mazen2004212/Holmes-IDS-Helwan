import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { FlashProvider } from './components/FlashMessages';
import Layout from './components/Layout';
import ProtectedRoute from './components/ProtectedRoute';

// Pages
import LoginPage from './pages/LoginPage';
import SignaturePage from './pages/SignaturePage';
import AnomalyPage from './pages/AnomalyPage';
import CsvUploadPage from './pages/CsvUploadPage';
import PcapUploadPage from './pages/PcapUploadPage';
import RulesPage from './pages/RulesPage';
import LiveCapturePage from './pages/LiveCapturePage';
import AdminPage from './pages/AdminPage';
import ExplainPage from './pages/ExplainPage';
import RetrainPage from './pages/RetrainPage';
import AnalyticsPage from './pages/AnalyticsPage';

export default function App() {
    return (
        <BrowserRouter>
            <AuthProvider>
                <FlashProvider>
                    <Routes>
                        {/* Public */}
                        <Route path="/login" element={<LoginPage />} />

                        {/* Protected — wrapped in Layout (Navbar + Footer) */}
                        <Route element={<Layout />}>
                            <Route
                                path="/"
                                element={
                                    <ProtectedRoute roles={['admin', 'signature_analyst']}>
                                        <SignaturePage />
                                    </ProtectedRoute>
                                }
                            />
                            <Route
                                path="/anomaly"
                                element={
                                    <ProtectedRoute roles={['admin', 'anomaly_analyst']}>
                                        <AnomalyPage />
                                    </ProtectedRoute>
                                }
                            />
                            <Route
                                path="/csv"
                                element={
                                    <ProtectedRoute roles={['admin', 'anomaly_analyst']}>
                                        <CsvUploadPage />
                                    </ProtectedRoute>
                                }
                            />
                            <Route
                                path="/upload_pcap"
                                element={
                                    <ProtectedRoute roles={['admin', 'signature_analyst']}>
                                        <PcapUploadPage />
                                    </ProtectedRoute>
                                }
                            />
                            <Route
                                path="/rules"
                                element={
                                    <ProtectedRoute roles={['admin', 'signature_analyst']}>
                                        <RulesPage />
                                    </ProtectedRoute>
                                }
                            />
                            <Route
                                path="/live"
                                element={
                                    <ProtectedRoute roles={['admin', 'signature_analyst', 'anomaly_analyst', 'live_operator']}>
                                        <LiveCapturePage />
                                    </ProtectedRoute>
                                }
                            />
                            <Route
                                path="/admin"
                                element={
                                    <ProtectedRoute roles={['admin']}>
                                        <AdminPage />
                                    </ProtectedRoute>
                                }
                            />
                            <Route
                                path="/explain/:alertId"
                                element={
                                    <ProtectedRoute roles={['admin', 'anomaly_analyst']}>
                                        <ExplainPage />
                                    </ProtectedRoute>
                                }
                            />
                            <Route
                                path="/retrain"
                                element={
                                    <ProtectedRoute roles={['admin']}>
                                        <RetrainPage />
                                    </ProtectedRoute>
                                }
                            />
                            <Route
                                path="/analytics"
                                element={
                                    <ProtectedRoute roles={['admin', 'signature_analyst', 'anomaly_analyst']}>
                                        <AnalyticsPage />
                                    </ProtectedRoute>
                                }
                            />
                        </Route>
                    </Routes>
                </FlashProvider>
            </AuthProvider>
        </BrowserRouter>
    );
}
