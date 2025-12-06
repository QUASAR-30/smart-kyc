import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import axios from 'axios';
import {
    LayoutDashboard,
    FileText,
    LogOut,
    TrendingUp,
    Users,
    DollarSign,
    AlertCircle,
    Share2,
    CheckCircle,
    Shield
} from 'lucide-react';
import TrustScoreGauge from '../components/TrustScoreGauge';

// Types
interface Metrics {
    documents: {
        score: number;
        verified_count?: number;
        total_verified?: number;
        total_count: number;
        details?: Record<string, { verified: boolean; score: number }>;
    };
    historique: { score: number };
    comportement: { score: number };
    financiers: { score: number };
}

interface TrustScoreData {
    trustscore: number;
    badge: string;
    calculation_mode: string;
    metrics: Metrics;
    valid_until: string;
}

const Dashboard: React.FC = () => {
    const [searchParams] = useSearchParams();
    const navigate = useNavigate();
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [data, setData] = useState<TrustScoreData | null>(null);
    const [merchantName, setMerchantName] = useState("Merchant");

    // Helper to get verified count safely
    const getVerifiedCount = (metrics: Metrics['documents']) => {
        if (metrics.details) {
            return Object.values(metrics.details).filter((doc: any) => doc.verified === true).length;
        }
        return metrics.verified_count || metrics.total_verified || 0;
    };

    useEffect(() => {
        const initDashboard = async () => {
            try {
                // 1. Handle Auth Token
                let token = searchParams.get('token');
                if (token) {
                    localStorage.setItem('smartkyc_token', token);
                    window.history.replaceState({}, document.title, "/dashboard");
                } else {
                    token = localStorage.getItem('smartkyc_token');
                }

                if (!token) {
                    navigate('/');
                    return;
                }

                // Configure Axios
                const api = axios.create({
                    baseURL: 'http://localhost:8000',
                    headers: { Authorization: `Bearer ${token}` }
                });

                // 2. Fetch Merchant Info
                try {
                    const meRes = await api.get('/auth/me');
                    setMerchantName(meRes.data.business_name);
                } catch (e) {
                    console.error("Failed to fetch merchant info", e);
                }

                // 3. Fetch or Calculate TrustScore
                try {
                    const scoreRes = await api.get('/api/trustscores/latest');
                    setData(scoreRes.data);
                } catch (e: any) {
                    if (e.response && e.response.status === 404) {
                        console.log("No score found, calculating...");
                        const calcRes = await api.post('/api/trustscores/calculate');
                        setData(calcRes.data);
                    } else {
                        throw e;
                    }
                }

            } catch (err: any) {
                console.error("Dashboard Error:", err);
                setError(err.message || "An error occurred");
                if (err.response && err.response.status === 401) {
                    localStorage.removeItem('smartkyc_token');
                    navigate('/');
                }
            } finally {
                setLoading(false);
            }
        };

        initDashboard();
    }, [navigate, searchParams]);

    const handleLogout = () => {
        localStorage.removeItem('smartkyc_token');
        navigate('/');
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-slate-50 flex items-center justify-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="min-h-screen bg-slate-50 flex items-center justify-center">
                <div className="text-center">
                    <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-slate-900">Error</h3>
                    <p className="text-slate-500 mb-4">{error}</p>
                    <button onClick={() => window.location.reload()} className="text-indigo-600 hover:text-indigo-800">
                        Retry
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-slate-50 font-sans">
            {/* Sidebar */}
            <div className="fixed inset-y-0 left-0 w-64 bg-white border-r border-slate-200 hidden md:block z-20">
                <div className="flex items-center justify-center h-20 border-b border-slate-100 bg-gradient-to-r from-indigo-600 to-violet-600">
                    <div className="flex items-center text-white">
                        <Shield className="h-6 w-6 mr-2" />
                        <span className="text-xl font-bold">SmartKYC</span>
                    </div>
                </div>
                <nav className="mt-8 px-4 space-y-3">
                    <a href="#" className="flex items-center px-4 py-3 text-sm font-medium text-indigo-700 bg-indigo-50 rounded-xl shadow-sm transition-all">
                        <LayoutDashboard className="mr-3 h-5 w-5" />
                        Dashboard
                    </a>
                    <a href="/upload" className="flex items-center px-4 py-3 text-sm font-medium text-slate-600 hover:bg-slate-50 hover:text-indigo-600 rounded-xl transition-all" onClick={(e) => { e.preventDefault(); navigate('/upload'); }}>
                        <FileText className="mr-3 h-5 w-5" />
                        Documents
                    </a>
                </nav>
                <div className="absolute bottom-0 w-full p-4 border-t border-slate-100 bg-slate-50">
                    <button onClick={handleLogout} className="flex items-center w-full px-4 py-2 text-sm font-medium text-red-600 hover:bg-red-50 rounded-lg transition-colors">
                        <LogOut className="mr-3 h-5 w-5" />
                        Déconnexion
                    </button>
                </div>
            </div>

            {/* Main Content */}
            <div className="md:ml-64 p-8">
                {/* Header */}
                <div className="mb-8 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                    <div>
                        <h1 className="text-3xl font-bold text-slate-900 tracking-tight">Bonjour, {merchantName}</h1>
                        <p className="text-slate-500 mt-1">Voici l'état de votre crédibilité financière en temps réel.</p>
                    </div>
                    <button
                        onClick={async () => {
                            try {
                                const token = localStorage.getItem('smartkyc_token');
                                if (!token) return;

                                const api = axios.create({
                                    baseURL: 'http://localhost:8000',
                                    headers: { Authorization: `Bearer ${token}` }
                                });

                                // Generate badge if needed
                                await api.post('/api/badges/generate');
                                // Get share info
                                const shareRes = await api.get('/api/badges/share');
                                // Open share link in new tab or copy to clipboard
                                window.open(shareRes.data.verification_url, '_blank');
                            } catch (e) {
                                console.error("Share error", e);
                                alert("Erreur lors du partage. Veuillez d'abord calculer votre score.");
                            }
                        }}
                        className="flex items-center px-6 py-3 bg-indigo-600 text-white rounded-xl shadow-lg shadow-indigo-200 hover:bg-indigo-700 transition-all transform hover:-translate-y-0.5"
                    >
                        <Share2 className="mr-2 h-5 w-5" />
                        Partager mon Badge
                    </button>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                    {/* Left Column: TrustScore */}
                    <div className="lg:col-span-1">
                        <div className="bg-white rounded-2xl shadow-sm border border-slate-100 p-8 flex flex-col items-center h-full relative overflow-hidden">
                            <div className="absolute top-0 left-0 w-full h-2 bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500"></div>
                            <h2 className="text-xl font-bold text-slate-900 mb-8">Votre TrustScore</h2>

                            <div className="transform scale-110 mb-4">
                                {data && <TrustScoreGauge score={data.trustscore} badge={data.badge} />}
                            </div>

                            <div className="mt-auto w-full space-y-4">
                                <div className="flex justify-between items-center p-3 bg-slate-50 rounded-lg">
                                    <span className="text-sm text-slate-500">Mode de calcul</span>
                                    <span className={`text-sm font-semibold px-2 py-1 rounded-md ${data?.calculation_mode === 'NORMAL' ? 'bg-green-100 text-green-700' : 'bg-orange-100 text-orange-700'}`}>
                                        {data?.calculation_mode === 'NORMAL' ? 'Complet' : 'Cold Start'}
                                    </span>
                                </div>
                                <div className="flex justify-between items-center p-3 bg-slate-50 rounded-lg">
                                    <span className="text-sm text-slate-500">Validité</span>
                                    <span className="text-sm font-semibold text-slate-900">
                                        {data ? new Date(data.valid_until).toLocaleDateString() : '-'}
                                    </span>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Right Column: Metrics */}
                    <div className="lg:col-span-2 space-y-6">
                        {/* Main Metrics Card */}
                        <div className="bg-white rounded-2xl shadow-sm border border-slate-100 p-8">
                            <h2 className="text-xl font-bold text-slate-900 mb-6">Détails du Score</h2>

                            <div className="space-y-8">
                                {/* Documents */}
                                <div>
                                    <div className="flex justify-between items-center mb-3">
                                        <div className="flex items-center">
                                            <div className="p-2 bg-indigo-50 rounded-lg mr-3">
                                                <FileText className="h-5 w-5 text-indigo-600" />
                                            </div>
                                            <div>
                                                <span className="font-semibold text-slate-900 block">Documents Vérifiés</span>
                                                <p className="text-xs text-slate-500 mt-1">
                                                    {data ? getVerifiedCount(data.metrics.documents) : 0}/{data?.metrics.documents.total_count || 5} validés
                                                </p>
                                            </div>
                                        </div>
                                        <span className="text-lg font-bold text-indigo-600">{Math.round(data?.metrics.documents.score || 0)}/100</span>
                                    </div>
                                    <div className="w-full bg-slate-100 rounded-full h-3">
                                        <div
                                            className="bg-gradient-to-r from-indigo-500 to-violet-500 h-3 rounded-full transition-all duration-1000 ease-out"
                                            style={{ width: `${data?.metrics.documents.score || 0}%` }}
                                        ></div>
                                    </div>
                                </div>

                                {/* Grid for other metrics */}
                                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-4">
                                    {/* Historique */}
                                    <div className="bg-slate-50 rounded-xl p-4 border border-slate-100">
                                        <div className="flex items-center mb-3">
                                            <TrendingUp className="h-5 w-5 text-emerald-500 mr-2" />
                                            <span className="font-medium text-slate-700">Historique</span>
                                        </div>
                                        <div className="text-2xl font-bold text-slate-900 mb-2">{Math.round(data?.metrics.historique.score || 0)}<span className="text-sm text-slate-400 font-normal">/100</span></div>
                                        <div className="w-full bg-slate-200 rounded-full h-1.5">
                                            <div className="bg-emerald-500 h-1.5 rounded-full" style={{ width: `${data?.metrics.historique.score || 0}%` }}></div>
                                        </div>
                                    </div>

                                    {/* Comportement */}
                                    <div className="bg-slate-50 rounded-xl p-4 border border-slate-100">
                                        <div className="flex items-center mb-3">
                                            <Users className="h-5 w-5 text-blue-500 mr-2" />
                                            <span className="font-medium text-slate-700">Comportement</span>
                                        </div>
                                        <div className="text-2xl font-bold text-slate-900 mb-2">{Math.round(data?.metrics.comportement.score || 0)}<span className="text-sm text-slate-400 font-normal">/100</span></div>
                                        <div className="w-full bg-slate-200 rounded-full h-1.5">
                                            <div className="bg-blue-500 h-1.5 rounded-full" style={{ width: `${data?.metrics.comportement.score || 0}%` }}></div>
                                        </div>
                                    </div>

                                    {/* Financiers */}
                                    <div className="bg-slate-50 rounded-xl p-4 border border-slate-100">
                                        <div className="flex items-center mb-3">
                                            <DollarSign className="h-5 w-5 text-amber-500 mr-2" />
                                            <span className="font-medium text-slate-700">Financier</span>
                                        </div>
                                        <div className="text-2xl font-bold text-slate-900 mb-2">{Math.round(data?.metrics.financiers.score || 0)}<span className="text-sm text-slate-400 font-normal">/100</span></div>
                                        <div className="w-full bg-slate-200 rounded-full h-1.5">
                                            <div className="bg-amber-500 h-1.5 rounded-full" style={{ width: `${data?.metrics.financiers.score || 0}%` }}></div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {data?.calculation_mode === 'COLD_START' && (
                            <div className="bg-gradient-to-r from-orange-50 to-amber-50 rounded-2xl border border-orange-100 p-6 flex items-start">
                                <div className="p-3 bg-orange-100 rounded-full mr-4 flex-shrink-0">
                                    <AlertCircle className="h-6 w-6 text-orange-600" />
                                </div>
                                <div>
                                    <h4 className="text-lg font-bold text-orange-900 mb-1">Mode Cold Start Actif</h4>
                                    <p className="text-orange-800 mb-3">
                                        Votre historique Genuka est insuffisant pour un score complet.
                                        Téléchargez vos documents légaux pour débloquer votre potentiel de crédit.
                                    </p>
                                    <button
                                        onClick={() => navigate('/upload')}
                                        className="text-sm font-semibold text-white bg-orange-500 px-4 py-2 rounded-lg hover:bg-orange-600 transition-colors shadow-sm"
                                    >
                                        Uploader mes documents &rarr;
                                    </button>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Dashboard;
