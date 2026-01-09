'use client';

import React, { useState, useEffect, useRef, useCallback } from 'react';
import ChartModal from './ChartModal';
import DataSourceModal from './DataSourceModal';
import ReactMarkdown from 'react-markdown';

const SendIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-5 h-5">
    <path d="M3.478 2.404a.75.75 0 0 0-.926.941l2.432 7.905H13.5a.75.75 0 0 1 0 1.5H4.984l-2.432 7.905a.75.75 0 0 0 .926.94 60.519 60.519 0 0 0 18.445-8.986.75.75 0 0 0 0-1.218A60.517 60.517 0 0 0 3.478 2.404Z" />
  </svg>
);

const DatabaseIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5">
    <path strokeLinecap="round" strokeLinejoin="round" d="M20.25 6.375c0 2.278-3.694 4.125-8.25 4.125S3.75 8.653 3.75 6.375m16.5 0c0-2.278-3.694-4.125-8.25-4.125S3.75 4.097 3.75 6.375m16.5 0v11.25c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125V6.375m16.5 0v3.75m-16.5-3.75v3.75m16.5 0v3.75C20.25 16.153 16.556 18 12 18s-8.25-1.847-8.25-4.125v-3.75m16.5 0c0 2.278-3.694 4.125-8.25 4.125s-8.25-1.847-8.25-4.125" />
  </svg>
);

const ChartIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5">
    <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 3v11.25A2.25 2.25 0 0 0 6 16.5h2.25M3.75 3h-1.5m1.5 0h16.5m0 0h1.5m-1.5 0v11.25A2.25 2.25 0 0 1 18 16.5h-2.25m-7.5 0h7.5m-7.5 0-1 3m8.5-3 1 3m0 0 .5 1.5m-.5-1.5h-9.5m0 0-.5 1.5m.75-9 3-3 2.148 2.148A12.061 12.061 0 0 1 16.5 7.605" />
  </svg>
);

interface Message {
  id: number | string;
  sender: 'user' | 'ai';
  text?: string;
  chartData?: any;
}

const ChatInterface = ({ clientId, onDataUpdate }: { clientId: string, onDataUpdate?: () => void }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [currentMessage, setCurrentMessage] = useState('');
  const [isConnected, setIsConnected] = useState(false);

  // Modals state
  const [isChartModalOpen, setIsChartModalOpen] = useState(false);
  const [currentChartData, setCurrentChartData] = useState<any>(null);
  const [isDataSourceModalOpen, setIsDataSourceModalOpen] = useState(false);

  const ws = useRef<WebSocket | null>(null);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const shouldReconnect = useRef(true);

  const addMessage = useCallback((sender: 'user' | 'ai', text?: string, chartData?: any) => {
    setMessages((prevMessages) => [
      ...prevMessages,
      { id: Date.now() + Math.random(), sender, text, chartData },
    ]);
  }, []);

  const openChart = useCallback((data: any) => {
    setCurrentChartData(data);
    setIsChartModalOpen(true);
  }, []);

  const handleUploadSuccess = useCallback(() => {
    addMessage('ai', "Merci d'avoir ajouter vos fichiers d'analyse j'ai pris sa en consideration et je suis pret maintenant à repondre à votre question selon votre source ajoutée .");
    if (onDataUpdate) {
      onDataUpdate();
    }
  }, [addMessage, onDataUpdate]);

  const connect = useCallback(() => {
    if (ws.current?.readyState === WebSocket.OPEN) return;

    // Use persisted clientId from prop
    if (!clientId) return; // Wait for prop

    // Derive WS URL from API URL
    const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';
    const isSecure = API_URL.startsWith('https');
    const wsProtocol = isSecure ? 'wss' : 'ws';
    const wsHost = API_URL.replace(/^https?:\/\//, '');
    const wsUrl = `${wsProtocol}://${wsHost}/api/v1/chat/ws/${clientId}`;

    console.log('Connecting WebSocket with ID:', clientId);
    ws.current = new WebSocket(wsUrl);

    ws.current.onopen = () => {
      console.log('WebSocket Connected');
      setIsConnected(true);
    };

    ws.current.onclose = () => {
      console.log('WebSocket Disconnected');
      setIsConnected(false);
      // Auto reconnect after 3s only if not intentionally closed
      if (shouldReconnect.current) {
        setTimeout(connect, 3000);
      }
    };

    ws.current.onerror = (error) => {
      console.error('WebSocket Error:', error);
      // Optionally, also try to reconnect on error
      // setTimeout(connect, 3000); // This would cause a double reconnect attempt if onclose also fires
    };

    ws.current.onmessage = (event) => {
      console.log('Message received from server:', event.data);
      const msg = event.data;
      if (msg.startsWith('{')) {
        try {
          const data = JSON.parse(msg);
          if (data.type === 'chart') {
            setMessages(prev => [...prev, { id: Date.now(), sender: 'ai', chartData: data.data }]);
            openChart(data.data); // Open chart directly when received
          } else {
            setMessages(prev => [...prev, { id: Date.now(), sender: 'ai', text: msg }]);
          }
        } catch (e) {
          // Not JSON, treat as plain text
          setMessages(prev => [...prev, { id: Date.now(), sender: 'ai', text: msg }]);
        }
      } else {
        setMessages(prev => [...prev, { id: Date.now(), sender: 'ai', text: msg }]);
      }
    };
  }, [clientId, openChart]); // Depend on clientId and openChart

  useEffect(() => {
    shouldReconnect.current = true;
    if (clientId) {
      connect();
    }
    return () => {
      console.log('Closing WebSocket...');
      shouldReconnect.current = false; // Prevent auto-reconnect
      if (ws.current) {
        ws.current.onclose = null;
        ws.current.onerror = null;
        ws.current.onmessage = null;
        ws.current.close();
        ws.current = null;
      }
    };
  }, [connect, clientId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);


  const handleSendMessage = (e: React.FormEvent) => {
    e.preventDefault();
    if (currentMessage.trim() === '' || !ws.current || !isConnected) return;

    const messageToSend = currentMessage;
    addMessage('user', messageToSend);

    console.log('Sending message to server:', messageToSend);
    ws.current.send(messageToSend);

    setCurrentMessage('');
  };

  return (
    <div className="flex flex-col h-[85vh] max-w-5xl mx-auto border rounded-2xl shadow-2xl bg-white overflow-hidden font-sans ring-1 ring-gray-100">
      {/* Header */}
      <div className="bg-white p-4 border-b border-gray-100 flex justify-between items-center">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 bg-blue-600 rounded-xl flex items-center justify-center text-white shadow-blue-200 shadow-lg">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-6 h-6">
              <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 21v-7.5a.75.75 0 0 1 .75-.75h3a.75.75 0 0 1 .75.75V21m-4.5 0H2.36m11.14 0H18m0 0h3.64m-1.39 0V9.349m-16.5 11.65V9.35m0 0a3.001 3.001 0 0 0 3.75-.615A2.993 2.993 0 0 0 9.75 9.75c.896 0 1.7-.393 2.25-1.016a2.993 2.993 0 0 0 2.25 1.016c.896 0 1.7-.393 2.25-1.016a3.001 3.001 0 0 0 3.75.614m-16.5 0a3.004 3.004 0 0 1-.621-4.72l1.189-1.19A1.5 1.5 0 0 1 5.378 3h13.243a1.5 1.5 0 0 1 1.06.44l1.19 1.189a3 3 0 0 1-.621 4.72m-13.5 8.65h3.75a.75.75 0 0 0 .75-.75V13.5a.75.75 0 0 0-.75-.75H6.75a.75.75 0 0 0-.75.75v3.75c0 .415.336.75.75.75Z" />
            </svg>
          </div>
          <div>
            <h1 className="font-bold text-gray-900 text-lg leading-tight">StockPilot</h1>
            <div className="flex items-center space-x-2">
              <span className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}></span>
              <span className="text-xs text-gray-500 font-medium">
                {isConnected ? 'En ligne' : 'Hors ligne'}
              </span>
            </div>
          </div>
        </div>

        <button
          onClick={() => setIsDataSourceModalOpen(true)}
          className="flex items-center space-x-2 px-4 py-2 bg-gray-50 hover:bg-gray-100 text-gray-700 rounded-lg transition-colors text-sm font-medium border border-gray-200"
        >
          <DatabaseIcon />
          <span>Sources de données</span>
        </button>
      </div>

      {/* Zone d'affichage des messages */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6 bg-gray-50/50">
        {messages.length === 0 && isConnected && (
          <div className="flex flex-col items-center justify-center h-full text-gray-400 space-y-2">
            <p>En attente du message de bienvenue...</p>
          </div>
        )}

        {messages.map((msg, index) => (
          <div
            key={`${msg.id}-${index}`}
            className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[85%] lg:max-w-[70%] px-5 py-3 rounded-2xl shadow-sm animate-in slide-in-from-bottom-2 duration-200 ${msg.sender === 'user'
                ? 'bg-blue-600 text-white rounded-br-sm'
                : 'bg-white text-gray-800 border border-gray-100 rounded-bl-sm'
                }`}
            >
              {msg.text && (
                <div className="text-[15px] prose prose-sm max-w-none prose-p:leading-relaxed prose-pre:bg-gray-100 prose-pre:p-2 prose-pre:rounded-lg">
                  <ReactMarkdown>{msg.text.replace(/^AI:\s*/, '')}</ReactMarkdown>
                </div>
              )}

              {msg.chartData && (
                <div className="mt-2">
                  <button
                    onClick={() => openChart(msg.chartData)}
                    className="flex items-center space-x-2 bg-blue-50 hover:bg-blue-100 text-blue-700 px-4 py-3 rounded-xl transition-colors w-full border border-blue-100 group"
                  >
                    <div className="bg-white p-2 rounded-lg shadow-sm group-hover:scale-110 transition-transform">
                      <ChartIcon />
                    </div>
                    <span className="font-medium">Ouvrir la visualisation</span>
                  </button>
                </div>
              )}
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Zone de saisie */}
      <div className="p-4 bg-white border-t border-gray-100">
        <form onSubmit={handleSendMessage} className="flex items-center space-x-3 relative">
          <input
            type="text"
            value={currentMessage}
            onChange={(e) => setCurrentMessage(e.target.value)}
            placeholder={isConnected ? "Posez votre question à StockPilot..." : "Connexion en cours..."}
            className="flex-1 bg-gray-50 border border-gray-200 rounded-xl px-5 py-3.5 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all text-gray-800 placeholder-gray-400"
            disabled={!isConnected}
          />
          <button
            type="submit"
            className="bg-blue-600 text-white p-3.5 rounded-xl hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg shadow-blue-200 active:scale-95"
            disabled={currentMessage.trim() === '' || !isConnected}
          >
            <SendIcon />
          </button>
        </form>
      </div>

      {/* Modals */}
      <ChartModal
        isOpen={isChartModalOpen}
        onClose={() => setIsChartModalOpen(false)}
        chartData={currentChartData}
      />

      <DataSourceModal
        isOpen={isDataSourceModalOpen}
        onClose={() => setIsDataSourceModalOpen(false)}
        onUploadSuccess={handleUploadSuccess}
        clientId={clientId}
      />
    </div>
  );
};

export default ChatInterface;