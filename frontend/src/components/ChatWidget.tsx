import React, { useState } from 'react';
import { MessageSquare, X, Minimize2, Maximize2 } from 'lucide-react';
import ChatInterface from './ChatInterface';

const ChatWidget = ({ clientId, onDataUpdate }: { clientId: string, onDataUpdate?: () => void }) => {
    const [isOpen, setIsOpen] = useState(false);
    const [isExpanded, setIsExpanded] = useState(false);

    const toggleOpen = () => setIsOpen(!isOpen);
    const toggleExpand = () => setIsExpanded(!isExpanded);

    if (!isOpen) {
        return (
            <button
                onClick={toggleOpen}
                className="fixed bottom-6 right-6 w-14 h-14 bg-blue-600 hover:bg-blue-700 text-white rounded-full shadow-lg flex items-center justify-center transition-all duration-300 hover:scale-110 z-50"
            >
                <MessageSquare className="w-6 h-6" />
            </button>
        );
    }

    return (
        <div
            className={`fixed bottom-6 right-6 bg-white rounded-2xl shadow-2xl overflow-hidden flex flex-col transition-all duration-300 z-50 border border-gray-100
        ${isExpanded ? 'w-[90vw] h-[90vh] md:w-[800px] md:h-[800px]' : 'w-[380px] h-[600px]'}`}
        >
            {/* Widget Header */}
            <div className="bg-blue-600 p-4 flex items-center justify-between text-white shrink-0">
                <div className="flex items-center space-x-2">
                    <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
                    <h3 className="font-semibold text-sm">StockPilot Assistant</h3>
                </div>
                <div className="flex items-center space-x-1">
                    <button onClick={toggleExpand} className="p-1 hover:bg-blue-500 rounded transition">
                        {isExpanded ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
                    </button>
                    <button onClick={toggleOpen} className="p-1 hover:bg-blue-500 rounded transition">
                        <X className="w-5 h-5" />
                    </button>
                </div>
            </div>

            {/* Chat Content */}
            <div className="flex-1 overflow-hidden relative bg-gray-50/50">
                <ChatInterface clientId={clientId} onDataUpdate={onDataUpdate} />
            </div>
        </div>
    );
};

export default ChatWidget;
