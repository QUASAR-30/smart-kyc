import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Upload, CheckCircle, XCircle, FileText, ArrowLeft, Loader } from 'lucide-react';

interface Document {
    id: string;
    document_type: string;
    filename: string;
    verification_status: string;
    verification_reason?: string;
    uploaded_at: string;
}

const DocumentUpload: React.FC = () => {
    const navigate = useNavigate();
    const [documents, setDocuments] = useState<Document[]>([]);
    const [loading, setLoading] = useState(true);
    const [uploading, setUploading] = useState(false);
    const [selectedType, setSelectedType] = useState('RCCM');
    const [file, setFile] = useState<File | null>(null);
    const [message, setMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null);

    const token = localStorage.getItem('smartkyc_token');

    const api = axios.create({
        baseURL: 'http://localhost:8000',
        headers: { Authorization: `Bearer ${token}` }
    });

    useEffect(() => {
        if (!token) {
            navigate('/');
            return;
        }
        fetchDocuments();
    }, [navigate, token]);

    const fetchDocuments = async () => {
        try {
            const res = await api.get('/api/documents/list');
            setDocuments(res.data.documents);
        } catch (error) {
            console.error("Failed to fetch documents", error);
        } finally {
            setLoading(false);
        }
    };

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            setFile(e.target.files[0]);
        }
    };

    const handleUpload = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!file) return;

        setUploading(true);
        setMessage(null);

        const formData = new FormData();
        formData.append('file', file);
        formData.append('document_type', selectedType);

        try {
            const res = await api.post('/api/documents/upload', formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });

            setMessage({
                type: 'success',
                text: `Document uploaded! Status: ${res.data.verification_status}`
            });

            setFile(null);
            // Reset file input
            const fileInput = document.getElementById('file-upload') as HTMLInputElement;
            if (fileInput) fileInput.value = '';

            fetchDocuments();
        } catch (error: any) {
            console.error("Upload failed", error);
            setMessage({
                type: 'error',
                text: error.response?.data?.detail || "Upload failed"
            });
        } finally {
            setUploading(false);
        }
    };

    const docTypes = [
        { value: 'RCCM', label: 'Registre de Commerce (RCCM)' },
        { value: 'CNI', label: "Carte Nationale d'Identité (CNI)" },
        { value: 'NIF', label: "Numéro d'Identification Fiscale (NIF)" },
        { value: 'BANK_STATEMENT', label: 'Relevé Bancaire' },
        { value: 'ADDRESS_PROOF', label: 'Preuve d\'Adresse' },
    ];

    return (
        <div className="min-h-screen bg-slate-50 p-8">
            <div className="max-w-4xl mx-auto">
                <button
                    onClick={() => navigate('/dashboard')}
                    className="flex items-center text-slate-600 hover:text-slate-900 mb-6"
                >
                    <ArrowLeft className="h-4 w-4 mr-2" />
                    Retour au Dashboard
                </button>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                    {/* Upload Form */}
                    <div className="bg-white rounded-xl shadow-sm p-6 border border-slate-100">
                        <h2 className="text-lg font-semibold text-slate-900 mb-6">Ajouter un Document</h2>

                        <form onSubmit={handleUpload} className="space-y-6">
                            <div>
                                <label className="block text-sm font-medium text-slate-700 mb-2">
                                    Type de Document
                                </label>
                                <select
                                    value={selectedType}
                                    onChange={(e) => setSelectedType(e.target.value)}
                                    className="block w-full rounded-md border-slate-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm p-2 border"
                                >
                                    {docTypes.map(type => (
                                        <option key={type.value} value={type.value}>{type.label}</option>
                                    ))}
                                </select>
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-slate-700 mb-2">
                                    Fichier (Image ou PDF)
                                </label>
                                <div className="mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-slate-300 border-dashed rounded-md hover:border-indigo-500 transition-colors">
                                    <div className="space-y-1 text-center">
                                        <Upload className="mx-auto h-12 w-12 text-slate-400" />
                                        <div className="flex text-sm text-slate-600">
                                            <label htmlFor="file-upload" className="relative cursor-pointer bg-white rounded-md font-medium text-indigo-600 hover:text-indigo-500 focus-within:outline-none focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-indigo-500">
                                                <span>Téléverser un fichier</span>
                                                <input id="file-upload" name="file-upload" type="file" className="sr-only" onChange={handleFileChange} accept=".jpg,.jpeg,.png,.pdf" />
                                            </label>
                                        </div>
                                        <p className="text-xs text-slate-500">PNG, JPG, PDF jusqu'à 5MB</p>
                                        {file && (
                                            <p className="text-sm text-indigo-600 font-medium mt-2">
                                                Sélectionné: {file.name}
                                            </p>
                                        )}
                                    </div>
                                </div>
                            </div>

                            {message && (
                                <div className={`p-4 rounded-md ${message.type === 'success' ? 'bg-green-50 text-green-800' : 'bg-red-50 text-red-800'}`}>
                                    {message.text}
                                </div>
                            )}

                            <button
                                type="submit"
                                disabled={!file || uploading}
                                className={`w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white ${!file || uploading ? 'bg-slate-400 cursor-not-allowed' : 'bg-indigo-600 hover:bg-indigo-700'
                                    }`}
                            >
                                {uploading ? (
                                    <>
                                        <Loader className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" />
                                        Vérification en cours...
                                    </>
                                ) : (
                                    'Envoyer et Vérifier'
                                )}
                            </button>
                        </form>
                    </div>

                    {/* Document List */}
                    <div className="bg-white rounded-xl shadow-sm p-6 border border-slate-100">
                        <h2 className="text-lg font-semibold text-slate-900 mb-6">Vos Documents</h2>

                        {loading ? (
                            <div className="flex justify-center py-8">
                                <Loader className="animate-spin h-8 w-8 text-indigo-600" />
                            </div>
                        ) : documents.length === 0 ? (
                            <div className="text-center py-8 text-slate-500">
                                Aucun document téléversé
                            </div>
                        ) : (
                            <div className="space-y-4">
                                {documents.map((doc) => (
                                    <div key={doc.id} className="flex items-start p-4 border border-slate-200 rounded-lg">
                                        <div className="flex-shrink-0">
                                            <FileText className="h-6 w-6 text-slate-400" />
                                        </div>
                                        <div className="ml-3 flex-1">
                                            <div className="flex items-center justify-between">
                                                <p className="text-sm font-medium text-slate-900">
                                                    {docTypes.find(t => t.value === doc.document_type)?.label || doc.document_type}
                                                </p>
                                                {doc.verification_status === 'VERIFIED' ? (
                                                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                                                        <CheckCircle className="h-3 w-3 mr-1" />
                                                        Vérifié
                                                    </span>
                                                ) : doc.verification_status === 'REJECTED' ? (
                                                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                                                        <XCircle className="h-3 w-3 mr-1" />
                                                        Rejeté
                                                    </span>
                                                ) : (
                                                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                                                        En attente
                                                    </span>
                                                )}
                                            </div>
                                            <p className="text-xs text-slate-500 mt-1 truncate">{doc.filename}</p>
                                            <p className="text-xs text-slate-400 mt-1">
                                                {new Date(doc.uploaded_at).toLocaleDateString()}
                                            </p>
                                            {doc.verification_reason && (
                                                <p className="text-xs text-slate-600 mt-2 bg-slate-50 p-2 rounded">
                                                    {doc.verification_reason}
                                                </p>
                                            )}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default DocumentUpload;
