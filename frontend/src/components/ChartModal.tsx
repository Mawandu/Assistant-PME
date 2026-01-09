'use client';

import React from 'react';
import dynamic from 'next/dynamic';

// Import dynamique de Plotly
const Plot = dynamic(() => import('react-plotly.js'), { ssr: false });

interface ChartModalProps {
    isOpen: boolean;
    onClose: () => void;
    chartData: any;
}

const ChartModal: React.FC<ChartModalProps> = ({ isOpen, onClose, chartData }) => {
    if (!isOpen || !chartData) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
            <div className="bg-white rounded-2xl shadow-2xl w-full max-w-5xl h-[80vh] flex flex-col overflow-hidden animate-in fade-in zoom-in duration-200">
                {/* Header */}
                <div className="flex justify-between items-center p-4 border-b border-gray-100">
                    <h3 className="text-lg font-semibold text-gray-800">Visualisation</h3>
                    <button
                        onClick={onClose}
                        className="p-2 hover:bg-gray-100 rounded-full transition-colors text-gray-500 hover:text-gray-700"
                    >
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-6 h-6">
                            <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                        </svg>
                    </button>
                </div>

                {/* Content */}
                <div className="flex-1 p-4 bg-gray-50 relative">
                    <div className="absolute inset-4 bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
                        <Plot
                            data={chartData.data}
                            layout={{
                                ...chartData.layout,
                                autosize: true,
                                margin: { l: 50, r: 20, t: 50, b: 50 },
                                font: { family: 'Inter, sans-serif' }
                            }}
                            config={{
                                responsive: true,
                                displayModeBar: true,
                                displaylogo: false,
                                modeBarButtonsToRemove: ['lasso2d', 'select2d']
                            }}
                            style={{ width: '100%', height: '100%' }}
                            useResizeHandler={true}
                        />
                    </div>
                </div>

                {/* Footer (Optional controls) */}
                <div className="p-4 border-t border-gray-100 bg-white flex justify-end space-x-2">
                    <button
                        onClick={onClose}
                        className="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg transition-colors font-medium"
                    >
                        Fermer
                    </button>
                </div>
            </div>
        </div>
    );
};

export default ChartModal;
