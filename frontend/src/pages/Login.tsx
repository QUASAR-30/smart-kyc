import React from 'react';
import { ShieldCheck, ArrowRight } from 'lucide-react';

const Login: React.FC = () => {
    const handleLogin = () => {
        // Genuka OAuth Configuration
        // Genuka OAuth Configuration
        // Use staging.genuka.com for the interactive login page
        const GENUKA_AUTH_URL = "https://staging.genuka.com/oauth/authorize";
        const CLIENT_ID = "019aeb8b-cfbe-72a3-bb28-b54c537d7d4a"; // From CLAUDE.md
        const REDIRECT_URI = "http://localhost:8000/auth/callback"; // Backend callback
        const SCOPE = "company.read orders.read customers.read";

        const authUrl = `${GENUKA_AUTH_URL}?client_id=${CLIENT_ID}&redirect_uri=${encodeURIComponent(REDIRECT_URI)}&response_type=code&scope=${encodeURIComponent(SCOPE)}`;

        window.location.href = authUrl;
    };

    return (
        <div className="min-h-screen bg-slate-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
            <div className="sm:mx-auto sm:w-full sm:max-w-md">
                <div className="flex justify-center">
                    <div className="h-12 w-12 bg-indigo-600 rounded-xl flex items-center justify-center shadow-lg">
                        <ShieldCheck className="h-8 w-8 text-white" />
                    </div>
                </div>
                <h2 className="mt-6 text-center text-3xl font-extrabold text-slate-900">
                    SmartKYC
                </h2>
                <p className="mt-2 text-center text-sm text-slate-600">
                    Le Badge de Confiance du B2B Africain
                </p>
            </div>

            <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
                <div className="bg-white py-8 px-4 shadow-xl sm:rounded-lg sm:px-10 border border-slate-100">
                    <div className="space-y-6">
                        <div>
                            <h3 className="text-lg font-medium text-slate-900 text-center mb-4">
                                Connexion Marchand
                            </h3>
                            <p className="text-sm text-slate-500 text-center mb-6">
                                Connectez votre compte Genuka pour générer votre TrustScore instantanément.
                            </p>

                            <button
                                onClick={handleLogin}
                                className="w-full flex justify-center items-center py-3 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-[#F37021] hover:bg-[#d65a10] focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-[#F37021] transition-colors duration-200"
                            >
                                <span className="mr-2">Se connecter avec Genuka</span>
                                <ArrowRight className="h-4 w-4" />
                            </button>
                        </div>

                        <div className="mt-6">
                            <div className="relative">
                                <div className="absolute inset-0 flex items-center">
                                    <div className="w-full border-t border-slate-300" />
                                </div>
                                <div className="relative flex justify-center text-sm">
                                    <span className="px-2 bg-white text-slate-500">
                                        Pourquoi SmartKYC ?
                                    </span>
                                </div>
                            </div>

                            <div className="mt-6 grid grid-cols-3 gap-3 text-center">
                                <div className="p-2">
                                    <div className="text-xs font-semibold text-slate-900">TrustScore</div>
                                    <div className="text-[10px] text-slate-500">Crédibilité</div>
                                </div>
                                <div className="p-2">
                                    <div className="text-xs font-semibold text-slate-900">Badge</div>
                                    <div className="text-[10px] text-slate-500">Confiance</div>
                                </div>
                                <div className="p-2">
                                    <div className="text-xs font-semibold text-slate-900">Crédit</div>
                                    <div className="text-[10px] text-slate-500">Accès</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Login;
