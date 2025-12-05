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
    Share2
} from 'lucide-react';
import TrustScoreGauge from '../components/TrustScoreGauge';

// Types
interface Metrics {
    documents: { score: number; verified_count: number; total_count: number };
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

    useEffect(() => {
        const initDashboard = async () => {
            try {
                // 1. Handle Auth Token
                let token = searchParams.get('token');
                if (token) {
                    localStorage.setItem('smartkyc_token', token);
                    // Remove token from URL for cleaner look
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
                    // Try to get latest score
                    const scoreRes = await api.get('/api/trustscores/latest');
                    setData(scoreRes.data);
                } catch (e: any) {
                    if (e.response && e.response.status === 404) {
                        // If not found, calculate it (first time)
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
        <div className="min-h-screen bg-slate-50">
            {/* Sidebar */}
            <div className="fixed inset-y-0 left-0 w-64 bg-white border-r border-slate-200 hidden md:block">
                <div className="flex items-center justify-center h-16 border-b border-slate-200">
                    <span className="text-xl font-bold text-indigo-600">SmartKYC</span>
                </div>
                <nav className="mt-6 px-4 space-y-2">
                    <a href="#" className="flex items-center px-4 py-2 text-sm font-medium text-indigo-600 bg-indigo-50 rounded-md">
                        <LayoutDashboard className="mr-3 h-5 w-5" />
                        Dashboard
                    </a>
                    <a href="/upload" className="flex items-center px-4 py-2 text-sm font-medium text-slate-600 hover:bg-slate-50 rounded-md" onClick={(e) => { e.preventDefault(); navigate('/upload'); }}>
                        <FileText className="mr-3 h-5 w-5" />
                        Documents
                    </a>
                </nav>
                <div className="absolute bottom-0 w-full p-4 border-t border-slate-200">
                    <button onClick={handleLogout} className="flex items-center w-full px-4 py-2 text-sm font-medium text-red-600 hover:bg-red-50 rounded-md">
                        <LogOut className="mr-3 h-5 w-5" />
                        Déconnexion
                    </button>
                </div>
            </div>

            {/* Main Content */}
            <div className="md:ml-64 p-8">
                <div className="mb-8 flex justify-between items-center">
                    <div>
                        <h1 className="text-2xl font-bold text-slate-900">Bonjour, {merchantName}</h1>
                        <p className="text-slate-500">Voici l'état de votre crédibilité financière.</p>
                    </div>
                    <button className="flex items-center px-4 py-2 bg-white border border-slate-300 rounded-md shadow-sm text-sm font-medium text-slate-700 hover:bg-slate-50">
                        <Share2 className="mr-2 h-4 w-4" />
                        Partager mon Badge
                    </button>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                    {/* Left Column: TrustScore */}
                    <div className="lg:col-span-1">
                        <div className="bg-white rounded-xl shadow-sm p-6 border border-slate-100 flex flex-col items-center">
                            <h2 className="text-lg font-semibold text-slate-900 mb-6">Votre TrustScore</h2>
                            {data && <TrustScoreGauge score={data.trustscore} badge={data.badge} />}

                            <div className="mt-8 w-full">
                                <div className="flex justify-between items-center text-sm mb-2">
                                    <span className="text-slate-500">Mode de calcul</span>
                                    <span className={`font-medium ${data?.calculation_mode === 'NORMAL' ? 'text-green-600' : 'text-orange-600'}`}>
                                        {data?.calculation_mode === 'NORMAL' ? 'Complet (Normal)' : 'Dégradé (Cold Start)'}
                                    </span>
                                </div>
                                <div className="flex justify-between items-center text-sm">
                                    <span className="text-slate-500">Validité</span>
                                    <span className="font-medium text-slate-900">
                                        {data ? new Date(data.valid_until).toLocaleDateString() : '-'}
                                    </span>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Right Column: Metrics */}
                    <div className="lg:col-span-2">
                        <div className="bg-white rounded-xl shadow-sm p-6 border border-slate-100 h-full">
                            <h2 className="text-lg font-semibold text-slate-900 mb-6">Détails du Score</h2>

                            <div className="space-y-6">
                                {/* Documents */}
                                <div>
                                    <div className="flex justify-between items-center mb-2">
                                        <div className="flex items-center">
                                            <FileText className="h-5 w-5 text-indigo-500 mr-2" />
                                            <span className="font-medium text-slate-700">Documents Vérifiés</span>
                                        </div>
                                        <span className="text-sm font-bold text-slate-900">{Math.round(data?.metrics.documents.score || 0)}/100</span>
                                    </div>
                                    <div className="w-full bg-slate-100 rounded-full h-2.5">
                                        <div className="bg-indigo-500 h-2.5 rounded-full" style={{ width: `${data?.metrics.documents.score || 0}%` }}></div>
                                    </div>
                                    <p className="text-xs text-slate-500 mt-1">
                                        {data?.metrics.documents.verified_count}/{data?.metrics.documents.total_count} documents validés
                                    </p>
                                </div>

                                {/* Historique */}
                                <div>
                                    <div className="flex justify-between items-center mb-2">
                                        <div className="flex items-center">
                                            <TrendingUp className="h-5 w-5 text-emerald-500 mr-2" />
                                            <span className="font-medium text-slate-700">Historique Business</span>
                                        </div>
                                        <span className="text-sm font-bold text-slate-900">{Math.round(data?.metrics.historique.score || 0)}/100</span>
                                    </div>
                                    <div className="w-full bg-slate-100 rounded-full h-2.5">
                                        <div className="bg-emerald-500 h-2.5 rounded-full" style={{ width: `${data?.metrics.historique.score || 0}%` }}></div>
                                    </div>
                                </div>

                                {/* Comportement */}
                                <div>
                                    <div className="flex justify-between items-center mb-2">
                                        <div className="flex items-center">
                                            <Users className="h-5 w-5 text-blue-500 mr-2" />
                                            <span className="font-medium text-slate-700">Comportement Client</span>
                                        </div>
                                        <span className="text-sm font-bold text-slate-900">{Math.round(data?.metrics.comportement.score || 0)}/100</span>
                                    </div>
                                    <div className="w-full bg-slate-100 rounded-full h-2.5">
                                        <div className="bg-blue-500 h-2.5 rounded-full" style={{ width: `${data?.metrics.comportement.score || 0}%` }}></div>
                                    </div>
                                </div>

                                {/* Financiers */}
                                <div>
                                    <div className="flex justify-between items-center mb-2">
                                        <div className="flex items-center">
                                            <DollarSign className="h-5 w-5 text-amber-500 mr-2" />
                                            <span className="font-medium text-slate-700">Santé Financière</span>
                                        </div>
                                        <span className="text-sm font-bold text-slate-900">{Math.round(data?.metrics.financiers.score || 0)}/100</span>
                                    </div>
                                    <div className="w-full bg-slate-100 rounded-full h-2.5">
                                        <div className="bg-amber-500 h-2.5 rounded-full" style={{ width: `${data?.metrics.financiers.score || 0}%` }}></div>
                                    </div>
                                </div>
                            </div>

                            {data?.calculation_mode === 'COLD_START' && (
                                <div className="mt-8 p-4 bg-orange-50 rounded-lg border border-orange-100">
                                    <div className="flex">
                                        <AlertCircle className="h-5 w-5 text-orange-400 mr-3" />
                                        <div>
                                            <h4 className="text-sm font-medium text-orange-800">Mode Cold Start Actif</h4>
                                            <p className="text-sm text-orange-700 mt-1">
                                                Votre historique Genuka est insuffisant pour un score complet.
                                                Téléchargez plus de documents pour augmenter votre score jusqu'à 500 points.
                                            </p>
                                            <button
                                                onClick={() => navigate('/upload')}
                                                className="mt-2 text-sm font-medium text-orange-900 underline hover:text-orange-800"
                                            >
                                                Uploader des documents &rarr;
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Dashboard;
