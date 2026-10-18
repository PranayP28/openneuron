"use client";
import React, { useState } from 'react';

export default function ChatPage() {
  const [file, setFile] = useState<File | null>(null);
  const [docId, setDocId] = useState<string | null>(null);
  const [messages, setMessages] = useState<{role: string, text: string}[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  const handleUpload = async () => {
    if (!file) return;
    setLoading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch('http://127.0.0.1:8000/upload', {
        method: 'POST',
        body: formData,
      });
      const data = await res.json();
      if (data.doc_id) {
        setDocId(data.doc_id);
        setMessages([{ role: 'ai', text: `Document ${data.filename} uploaded. How can I help you analyze it?` }]);
      } else {
        alert(data.error || 'Upload failed');
      }
    } catch (e) {
      alert('Error uploading file');
    } finally {
      setLoading(false);
    }
  };

  const handleSend = async () => {
    if (!input || !docId) return;
    const userMsg = { role: 'user', text: input };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    const formData = new FormData();
    formData.append('doc_id', docId);
    formData.append('query', input);

    try {
      const res = await fetch('http://127.0.0.1:8000/chat', {
        method: 'POST',
        body: formData,
      });
      const data = await res.json();
      setMessages(prev => [...prev, { role: 'ai', text: data.response }]);
    } catch (e) {
      setMessages(prev => [...prev, { role: 'ai', text: 'Error connecting to backend.' }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-screen bg-gray-100 font-sans">
      <header className="p-4 bg-white border-b flex justify-between items-center">
        <h1 className="text-xl font-bold text-gray-800">ZeroDay PS2 Legal Triage</h1>
        <div className="flex gap-2">
          <input type="file" onChange={(e) => setFile(e.target.files?.[0] || null)} className="text-sm" />
          <button
            onClick={handleUpload}
            disabled={!file || loading}
            className="px-4 py-2 bg-blue-600 text-white rounded disabled:bg-gray-400"
          >
            {loading ? '...' : 'Upload'}
          </button>
        </div>
      </header>

      <main className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((m, i) => (
          <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-2xl p-3 rounded-lg ${m.role === 'user' ? 'bg-blue-500 text-white' : 'bg-white text-gray-800 border'}`}>
              {m.text}
            </div>
          </div>
        ))}
      </main>

      <footer className="p-4 bg-white border-t">
        <div className="flex gap-2 max-w-4xl mx-auto">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            placeholder={docId ? "Ask a question about the document..." : "Upload a document first"}
            disabled={!docId || loading}
            className="flex-1 p-2 border rounded outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            onClick={handleSend}
            disabled={!docId || loading}
            className="px-4 py-2 bg-blue-600 text-white rounded disabled:bg-gray-400"
          >
            Send
          </button>
        </div>
      </footer>
    </div>
  );
}
