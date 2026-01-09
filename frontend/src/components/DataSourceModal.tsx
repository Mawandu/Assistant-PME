'use client';

import React, { useState } from 'react';

interface DataSourceModalProps {
    isOpen: boolean;
    onClose: () => void;
    onUploadSuccess?: () => void;
    clientId: string;
}

const DataSourceModal: React.FC<DataSourceModalProps> = ({ isOpen, onClose, onUploadSuccess, clientId }) => {
    const [activeTab, setActiveTab] = useState<'upload' | 'database'>('upload');
    const [uploadStatus, setUploadStatus] = useState<'idle' | 'uploading' | 'success' | 'error'>('idle');
    const [message, setMessage] = useState('');

    const [dataSources, setDataSources] = useState<any[]>([]);

    const fetchDataSources = async () => {
        try {
            const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';
            const response = await fetch(`${API_URL}/api/v1/datasources/`, {
                headers: {
                    'X-Client-ID': clientId
                }
            });
            if (response.ok) {
                const data = await response.json();
                setDataSources(data);
            }
        } catch (error) {
            console.error('Error fetching data sources:', error);
        }
    };

    React.useEffect(() => {
        if (isOpen) {
            fetchDataSources();
        }
    }, [isOpen]);

    const handleDelete = async (id: string) => {
        if (!confirm("Êtes-vous sûr de vouloir supprimer cette source ?")) return;
        try {
            const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';
            const response = await fetch(`${API_URL}/api/v1/datasources/${id}`, {
                method: 'DELETE',
                headers: {
                    'X-Client-ID': clientId
                }
            });
            if (response.ok) {
                // Refresh list
                fetchDataSources();
            } else {
                alert("Erreur lors de la suppression");
            }
        } catch (error) {
            console.error('Error deletion:', error);
        }
    };


    const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (!file) return;

        setUploadStatus('uploading');
        setMessage('Upload en cours...');

        const formData = new FormData();
        formData.append('file', file);

        try {
            // Note: In a real app, you might need to handle auth token here
            // For MVP/Dev with no auth on this endpoint or cookie-based, this might work
            // If Bearer token is needed, we need to get it from context/storage
            const token = localStorage.getItem('token'); // Example if we had auth

            const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';
            const response = await fetch(`${API_URL}/api/v1/datasources/upload`, {
                method: 'POST',
                headers: {
                    // 'Authorization': `Bearer ${token}`, // Uncomment if auth is active and token stored
                    'X-Client-ID': clientId
                },
                body: formData,
            });

            const data = await response.json();

            if (response.ok) {
                setUploadStatus('success');
                setMessage(data.message || 'Fichier importé avec succès !');
                if (onUploadSuccess) {
                    onUploadSuccess();
                }
                fetchDataSources(); // Refresh list immediately
                setTimeout(() => {
                    setUploadStatus('idle');
                    setMessage('');
                }, 2000);
            } else {
                setUploadStatus('error');
                setMessage(data.detail || "Erreur lors de l'import.");
            }
        } catch (error) {
            setUploadStatus('error');
            setMessage("Erreur de connexion au serveur.");
            console.error(error);
        }
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
            <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl overflow-hidden animate-in fade-in zoom-in duration-200 flex flex-col max-h-[90vh]">
                {/* Header */}
                <div className="flex justify-between items-center p-6 border-b border-gray-100 shrink-0">
                    <div>
                        <h3 className="text-xl font-bold text-gray-800">Sources de données</h3>
                        <p className="text-sm text-gray-500 mt-1">Gérez vos fichiers et connexions</p>
                    </div>
                    <button
                        onClick={onClose}
                        className="p-2 hover:bg-gray-100 rounded-full transition-colors text-gray-500 hover:text-gray-700"
                    >
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-6 h-6">
                            <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                        </svg>
                    </button>
                </div>

                {/* Tabs */}
                <div className="flex border-b border-gray-100 shrink-0">
                    <button
                        onClick={() => setActiveTab('upload')}
                        className={`flex-1 py-3 text-sm font-medium transition-colors ${activeTab === 'upload'
                            ? 'text-blue-600 border-b-2 border-blue-600'
                            : 'text-gray-500 hover:text-gray-700'
                            }`}
                    >
                        Nouvelle Source
                    </button>
                    <button
                        onClick={() => setActiveTab('database')} // Using 'database' tab as 'Manage' for now or keep separate? 
                        // Let's rename 'database' to 'manage' or just show list below upload?
                        // For simplicity, let's keep 'upload' for new and add a list at the bottom of upload or separate section.
                        className={`flex-1 py-3 text-sm font-medium transition-colors ${activeTab === 'database'
                            ? 'text-blue-600 border-b-2 border-blue-600'
                            : 'text-gray-500 hover:text-gray-700'
                            }`}
                    >
                        Base de données
                    </button>
                </div>

                {/* Content */}
                <div className="p-6 overflow-y-auto">
                    {activeTab === 'upload' && (
                        <div className="space-y-8">
                            {/* Upload Section */}
                            <div className="space-y-4">
                                <h4 className="font-medium text-gray-900 border-b pb-2">Importer un fichier</h4>
                                <label className={`border-2 border-dashed border-gray-300 rounded-xl p-8 text-center hover:border-blue-500 hover:bg-blue-50 transition-colors cursor-pointer group block relative ${uploadStatus === 'uploading' ? 'opacity-50 pointer-events-none' : ''}`}>
                                    <input
                                        type="file"
                                        accept=".csv, .xlsx, .xls"
                                        className="hidden"
                                        onChange={handleFileUpload}
                                    />
                                    <div className="w-12 h-12 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center mx-auto mb-4 group-hover:scale-110 transition-transform">
                                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-6 h-6">
                                            <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5m-13.5-9L12 3m0 0 4.5 4.5M12 3v13.5" />
                                        </svg>
                                    </div>
                                    <h4 className="text-lg font-medium text-gray-900">Glissez-déposez vos fichiers ici</h4>
                                    <p className="text-sm text-gray-500 mt-2">ou cliquez pour parcourir (Excel, CSV)</p>
                                </label>

                                {uploadStatus !== 'idle' && (
                                    <div className={`p-4 rounded-lg text-sm font-medium ${uploadStatus === 'success' ? 'bg-green-50 text-green-700' :
                                        uploadStatus === 'error' ? 'bg-red-50 text-red-700' :
                                            'bg-blue-50 text-blue-700'
                                        }`}>
                                        {message}
                                    </div>
                                )}
                            </div>

                            {/* Existing Data Sources List */}
                            <div className="space-y-4">
                                <h4 className="font-medium text-gray-900 border-b pb-2">Mes Fichiers / Sources</h4>
                                {dataSources.length === 0 ? (
                                    <p className="text-sm text-gray-500 italic">Aucune source connectée.</p>
                                ) : (
                                    <div className="space-y-2">
                                        {dataSources.map((ds) => (
                                            <div key={ds.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg border border-gray-100 hover:bg-white hover:shadow-sm transition-all">
                                                <div className="flex items-center space-x-3">
                                                    <div className="bg-blue-100 p-2 rounded-lg text-blue-600">
                                                        {ds.type === 'FILE_UPLOAD' ? (
                                                            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-5 h-5">
                                                                <path d="M3 3.5A1.5 1.5 0 0 1 4.5 2h6.879a.75.75 0 0 1 .53.22l4.372 4.371A.75.75 0 0 1 16.5 7.12V16.5a1.5 1.5 0 0 1-1.5 1.5h-10.5A1.5 1.5 0 0 1 3 16.5v-13Z" />
                                                            </svg>
                                                        ) : (
                                                            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-5 h-5">
                                                                <path fillRule="evenodd" d="M10 1c3.866 0 7 1.79 7 4s-3.134 4-7 4-7-1.79-7-4 3.134-4 7-4Zm5.694 8.13c.464-.264.91-.583 1.306-.951v3.957a17.221 17.221 0 0 1-4.004 1.594A5.992 5.992 0 0 1 10 14.5c-1.397 0-2.677-.386-3.79-.817A17.227 17.227 0 0 1 3 12.136V8.179c.396.368.842.687 1.306.951.78.441 1.708.775 2.766 1.01a17.25 17.25 0 0 1 2.502.26 15.116 15.116 0 0 1 .426.046 5.8 5.8 0 0 1 1.066.012 11.232 11.232 0 0 0 3.24 0c.34-.029.69-.033 1.066-.012l.426-.046c.86-.176 1.693-.263 2.502-.26 1.058-.235 1.986-.57 2.766-1.01ZM17 12.136c-.464.264-.91.583-1.306.952-.78.44-1.708.774-2.766 1.01a17.25 17.25 0 0 1-2.502.26 15.12 15.12 0 0 1-.426.045 5.86 5.86 0 0 1-1.066.012 11.229 11.229 0 0 0-3.24 0c-.34.03-.69.034-1.066.012l-.426.045c-.86.177-1.693.264-2.502.26-1.058-.236-1.986-.57-2.766-1.01A17.222 17.222 0 0 1 3 12.088v3.958c2.827 1.609 8.243 1.83 11.394.49 1.096-.464 2.035-1.129 2.606-1.996v-3.356Z" clipRule="evenodd" />
                                                            </svg>
                                                        )}
                                                    </div>
                                                    <div>
                                                        <p className="text-sm font-medium text-gray-900">{ds.name}</p>
                                                        <p className="text-xs text-gray-500 uppercase">{ds.type} • {new Date(ds.created_at).toLocaleDateString()}</p>
                                                    </div>
                                                </div>
                                                <button
                                                    onClick={() => handleDelete(ds.id)}
                                                    className="p-2 text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                                                    title="Supprimer / Déconnecter"
                                                >
                                                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-5 h-5">
                                                        <path fillRule="evenodd" d="M8.75 1A2.75 2.75 0 0 0 6 3.75v.443c-.795.077-1.584.176-2.365.298a.75.75 0 1 0 .23 1.482l.149-.022.841 10.518A2.75 2.75 0 0 0 7.596 19h4.807a2.75 2.75 0 0 0 2.742-2.53l.841-10.52.149.023a.75.75 0 0 0 .23-1.482A41.03 41.03 0 0 0 14 4.193V3.75A2.75 2.75 0 0 0 11.25 1h-2.5ZM10 4c.84 0 1.673.025 2.5.075V3.75c0-.69-.56-1.25-1.25-1.25h-2.5c-.69 0-1.25.56-1.25 1.25v.325C8.327 4.025 9.16 4 10 4ZM8.58 7.72a.75.75 0 0 0-1.5.06l.3 7.5a.75.75 0 1 0 1.5-.06l-.3-7.5Zm4.34.06a.75.75 0 1 0-1.5-.06l-.3 7.5a.75.75 0 0 0 1.5.06l.3-7.5Z" clipRule="evenodd" />
                                                    </svg>
                                                </button>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        </div>
                    )}

                    {activeTab === 'database' && (
                        <div className="space-y-4">
                            <p className="text-sm text-gray-600 mb-4">Connectez-vous directement à votre base de données existante.</p>
                            <div className="grid grid-cols-1 gap-4">
                                <input type="text" placeholder="Hôte (ex: localhost)" className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none" />
                                <input type="text" placeholder="Port (ex: 5432)" className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none" />
                                <input type="text" placeholder="Nom de la base" className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none" />
                                <div className="grid grid-cols-2 gap-4">
                                    <input type="text" placeholder="Utilisateur" className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none" />
                                    <input type="password" placeholder="Mot de passe" className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none" />
                                </div>
                            </div>
                            <button className="w-full bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 transition-colors font-medium mt-2">
                                Tester la connexion
                            </button>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default DataSourceModal;
