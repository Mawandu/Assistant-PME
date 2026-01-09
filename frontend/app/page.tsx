'use client';

import React, { useEffect, useState } from 'react';
import ChatWidget from '../src/components/ChatWidget';
import { LayoutDashboard, Package, Truck, Database, Activity, TrendingUp, Globe } from 'lucide-react';

// --- Translations ---
const translations = {
  en: {
    dashboardTitle: "Dashboard",
    welcome: "Welcome to StockPilot Analytics",
    totalProducts: "Total Products",
    totalSuppliers: "Active Suppliers",
    totalCategories: "Categories",
    connectedSources: "Data Sources",
    sourceListTitle: "Connected Data Sources",
    sourceName: "Name",
    sourceType: "Type",
    sourceStatus: "Status",
    lastUpdate: "Last Update",
    noSources: "No data sources connected.",
    quickActions: "Quick Actions",
    quickActionsSubtitle: "Ask the assistant to analyze data.",
    action1: "Price Histogram",
    action2: "Margin Analysis",
    action3: "Out of Stock Items",
    loading: "Loading Dashboard...",
  },
  fr: {
    dashboardTitle: "Tableau de Bord",
    welcome: "Bienvenue sur StockPilot Analytics",
    totalProducts: "Total Produits",
    totalSuppliers: "Fournisseurs Actifs",
    totalCategories: "Catégories",
    connectedSources: "Sources de Données",
    sourceListTitle: "Sources Connectées",
    sourceName: "Nom",
    sourceType: "Type",
    sourceStatus: "Statut",
    lastUpdate: "Dernière MàJ",
    noSources: "Aucune source connectée.",
    quickActions: "Actions Rapides",
    quickActionsSubtitle: "Demandez une analyse à l'assistant.",
    action1: "Histogramme des prix",
    action2: "Analyse des marges",
    action3: "Produits en rupture",
    loading: "Chargement...",
  }
};

type Language = 'en' | 'fr';

// Dashboard Components
const StatCard = ({ title, value, icon: Icon, color }: any) => (
  <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 flex items-center space-x-4 hover:shadow-md transition-shadow">
    <div className={`p-4 rounded-xl ${color} bg-opacity-10 text-opacity-100`}>
      <Icon className={`w-8 h-8 ${color.replace('bg-', 'text-')}`} />
    </div>
    <div>
      <p className="text-sm font-medium text-gray-500">{title}</p>
      <h3 className="text-2xl font-bold text-gray-900">{value}</h3>
    </div>
  </div>
);

const DataSourceList = ({ sources, t }: { sources: any[], t: any }) => (
  <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
    <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
      <Database className="w-5 h-5 mr-2 text-blue-600" />
      {t.sourceListTitle}
    </h3>
    <div className="overflow-x-auto">
      <table className="w-full text-left">
        <thead>
          <tr className="border-b border-gray-100 text-sm text-gray-500">
            <th className="pb-3 font-medium">{t.sourceName}</th>
            <th className="pb-3 font-medium">{t.sourceType}</th>
            <th className="pb-3 font-medium">{t.sourceStatus}</th>
            <th className="pb-3 font-medium text-right">{t.lastUpdate}</th>
          </tr>
        </thead>
        <tbody className="text-sm">
          {sources.length === 0 ? (
            <tr>
              <td colSpan={4} className="py-4 text-center text-gray-400">{t.noSources}</td>
            </tr>
          ) : (
            sources.map((source) => (
              <tr key={source.id} className="group hover:bg-gray-50 transition-colors">
                <td className="py-3 font-medium text-gray-800">{source.name}</td>
                <td className="py-3 text-gray-500">{source.type}</td>
                <td className="py-3">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium 
                    ${source.status === 'ACTIVE' ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'}`}>
                    {source.status}
                  </span>
                </td>
                <td className="py-3 text-right text-gray-400">
                  {new Date(source.updated_at).toLocaleDateString()}
                </td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  </div>
);

export default function Dashboard() {
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [lang, setLang] = useState<Language>('en'); // Default English
  const [clientId, setClientId] = useState<string>('');

  const t = translations[lang];

  useEffect(() => {
    // Initialize Session ID
    let id = localStorage.getItem('stockpilot_client_id');
    if (!id) {
      id = 'client_' + Math.random().toString(36).substr(2, 9) + '_' + Date.now();
      localStorage.setItem('stockpilot_client_id', id);
    }
    setClientId(id);
  }, []);

  // Fetch Dashboard Stats with Session Isolation
  const fetchStats = React.useCallback(async () => {
    if (!clientId) return;
    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';
      const res = await fetch(`${API_URL}/api/v1/dashboard/stats`, {
        headers: {
          'x-client-id': clientId // Pass session ID to isolate data
        }
      });
      if (res.ok) {
        const data = await res.json();
        setStats(data);
      }
    } catch (err) {
      console.error("Failed to load stats", err);
    } finally {
      setLoading(false);
    }
  }, [clientId]);

  useEffect(() => {
    if (clientId) {
      fetchStats();
    }
  }, [clientId, fetchStats]);

  const toggleLang = () => {
    setLang(prev => prev === 'en' ? 'fr' : 'en');
  };

  return (
    <div className="min-h-screen bg-slate-50 text-gray-800 font-sans">
      {/* Sidebar (Small Icon Only or hidden on mobile) */}
      <nav className="fixed top-0 left-0 h-full w-20 bg-white border-r border-gray-200 hidden md:flex flex-col items-center py-8 z-30">
        <div className="w-10 h-10 bg-blue-600 rounded-xl mb-8 flex items-center justify-center text-white font-bold">SP</div>
        <div className="space-y-6">
          <button className="p-3 bg-blue-50 text-blue-600 rounded-xl shadow-sm"><LayoutDashboard className="w-6 h-6" /></button>
          <button className="p-3 text-gray-400 hover:bg-gray-50 hover:text-gray-600 rounded-xl"><Package className="w-6 h-6" /></button>
          <button className="p-3 text-gray-400 hover:bg-gray-50 hover:text-gray-600 rounded-xl"><Activity className="w-6 h-6" /></button>
        </div>
      </nav>

      {/* Main Content */}
      <main className="md:ml-20 p-6 md:p-10 max-w-7xl mx-auto space-y-8">
        {/* Header with Language Toggle */}
        <header className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">{t.dashboardTitle}</h1>
            <p className="text-gray-500 mt-1">{t.welcome}</p>
          </div>
          <div className="flex items-center space-x-4">
            <button
              onClick={toggleLang}
              className="flex items-center space-x-2 px-4 py-2 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 transition shadow-sm text-sm font-medium"
            >
              <Globe className="w-4 h-4 text-blue-600" />
              <span>{lang === 'en' ? 'English' : 'Français'}</span>
            </button>
            <div className="hidden sm:block text-sm text-gray-400">
              {new Date().toLocaleDateString(lang === 'en' ? 'en-US' : 'fr-FR', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
            </div>
          </div>
        </header>

        {/* Loading State */}
        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 animate-pulse">
            {[1, 2, 3, 4].map(i => <div key={i} className="h-32 bg-gray-200 rounded-2xl"></div>)}
          </div>
        ) : (
          <>
            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <StatCard
                title={t.totalProducts}
                value={stats?.global_stats?.total_products || 0}
                icon={Package}
                color="bg-blue-600"
              />
              <StatCard
                title={t.totalSuppliers}
                value={stats?.global_stats?.total_suppliers || 0}
                icon={Truck}
                color="bg-purple-600"
              />
              <StatCard
                title={t.totalCategories}
                value={stats?.global_stats?.total_categories || 0}
                icon={LayoutDashboard}
                color="bg-indigo-600"
              />
              <StatCard
                title={t.connectedSources}
                value={stats?.global_stats?.connected_sources || 0}
                icon={Database}
                color="bg-emerald-600"
              />
            </div>

            {/* Main Content Area */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
              {/* Data Source List */}
              <div className="lg:col-span-2">
                <DataSourceList sources={stats?.data_sources || []} t={t} />
              </div>

              {/* Quick Activity / Tips */}
              <div className="bg-gradient-to-br from-blue-600 to-indigo-700 rounded-2xl p-6 text-white shadow-lg">
                <TrendingUp className="w-8 h-8 mb-4 text-blue-200" />
                <h3 className="text-xl font-bold mb-2">{t.quickActions}</h3>
                <p className="text-blue-100 mb-6">{t.quickActionsSubtitle}</p>
                <ul className="space-y-3 text-sm text-blue-50">
                  <li className="flex items-center">✨ "{t.action1}"</li>
                  <li className="flex items-center">✨ "{t.action2}"</li>
                  <li className="flex items-center">✨ "{t.action3}"</li>
                </ul>
              </div>
            </div>
          </>
        )}
      </main>

      {/* Floating Chat Widget */}
      {clientId && <ChatWidget clientId={clientId} onDataUpdate={fetchStats} />}
    </div>
  );
}