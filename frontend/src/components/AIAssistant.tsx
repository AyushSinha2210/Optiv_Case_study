import React, { useState } from 'react';
import type { AssistantChatResponse } from '../types';
import { Bot, Send, Sparkles, BookOpen, ShieldCheck, Scale, Cpu } from 'lucide-react';

interface AIAssistantProps {
  documentId: string;
}

export const AIAssistant: React.FC<AIAssistantProps> = ({ documentId }) => {
  const [query, setQuery] = useState('');
  const [messages, setMessages] = useState<AssistantChatResponse[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchExplanation = async (topic: string, customQuery?: string) => {
    if (!documentId) return;
    setLoading(true);
    try {
      const res = await fetch('/api/assistant/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          document_id: documentId,
          topic,
          query: customQuery || topic,
        }),
      });
      if (res.ok) {
        const data: AssistantChatResponse = await res.json();
        setMessages((prev) => [...prev, data]);
      }
    } catch (err) {
      console.error('AI Assistant request failed', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSend = (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    const q = query;
    setQuery('');
    fetchExplanation('custom', q);
  };

  return (
    <div className="glass-panel" style={{ padding: 24, display: 'flex', flexDirection: 'column', gap: 20 }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--border-color)', paddingBottom: 14 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{ background: 'linear-gradient(135deg, #8b5cf6 0%, #3b82f6 100%)', padding: 8, borderRadius: 8 }}>
            <Bot size={22} color="#ffffff" />
          </div>
          <div>
            <h3 style={{ fontSize: '1.1rem', margin: 0 }}>AI Security & Governance Assistant</h3>
            <p style={{ fontSize: '0.8rem', color: '#94a3b8', margin: 0 }}>
              Explains real-time processing telemetry, release barriers, and technical invariants
            </p>
          </div>
        </div>
        <span className="badge badge-emp" style={{ fontSize: '0.75rem' }}>
          <Sparkles size={12} /> CADENCE AI COPILOT
        </span>
      </div>

      {/* Suggested Quick Prompt Chips */}
      <div>
        <div style={{ fontSize: '0.8rem', color: '#94a3b8', marginBottom: 10, fontWeight: 500 }}>
          Quick Invariant Inquiries:
        </div>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          <button
            onClick={() => fetchExplanation('decision', 'Why was this document release decision reached?')}
            disabled={loading}
            className="btn-secondary"
            style={{ fontSize: '0.8rem', padding: '6px 12px' }}
          >
            <Scale size={14} color="#06b6d4" />
            Explain Release Decision
          </button>
          <button
            onClick={() => fetchExplanation('taxonomy', 'Explain PII classification and overlap resolution rules')}
            disabled={loading}
            className="btn-secondary"
            style={{ fontSize: '0.8rem', padding: '6px 12px' }}
          >
            <Cpu size={14} color="#3b82f6" />
            Explain Classification Rules
          </button>
          <button
            onClick={() => fetchExplanation('leakage', 'Explain independent verification residual re-scan')}
            disabled={loading}
            className="btn-secondary"
            style={{ fontSize: '0.8rem', padding: '6px 12px' }}
          >
            <ShieldCheck size={14} color="#10b981" />
            Explain Residual Verification
          </button>
          <button
            onClick={() => fetchExplanation('policy', 'Explain Zero-Leakage audit policy')}
            disabled={loading}
            className="btn-secondary"
            style={{ fontSize: '0.8rem', padding: '6px 12px' }}
          >
            <BookOpen size={14} color="#f59e0b" />
            Explain Zero-Leakage Audit
          </button>
        </div>
      </div>

      {/* Chat Messages Log */}
      <div
        style={{
          minHeight: '280px',
          maxHeight: '450px',
          overflowY: 'auto',
          background: 'rgba(10, 15, 29, 0.7)',
          padding: 16,
          borderRadius: 10,
          border: '1px solid rgba(51, 65, 85, 0.4)',
          display: 'flex',
          flexDirection: 'column',
          gap: 16,
        }}
      >
        {messages.length === 0 ? (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '240px', color: '#64748b', textAlign: 'center', gap: 8 }}>
            <Bot size={36} color="#475569" />
            <p style={{ maxWidth: 360, fontSize: '0.85rem' }}>
              Select an invariant query above or ask a question below to analyze the security outcome and backend state transitions for document <code>{documentId}</code>.
            </p>
          </div>
        ) : (
          messages.map((msg, i) => (
            <div
              key={i}
              style={{
                background: 'rgba(30, 41, 59, 0.5)',
                border: '1px solid rgba(51, 65, 85, 0.6)',
                borderRadius: 8,
                padding: '14px 18px',
              }}
            >
              {msg.query && (
                <div style={{ fontSize: '0.85rem', fontWeight: 600, color: '#38bdf8', marginBottom: 8, display: 'flex', alignItems: 'center', gap: 6 }}>
                  <span>Q:</span> {msg.query}
                </div>
              )}
              <div
                style={{
                  fontSize: '0.875rem',
                  lineHeight: '1.6',
                  color: '#e2e8f0',
                  whiteSpace: 'pre-wrap',
                }}
              >
                {msg.explanation}
              </div>

              {msg.citations && msg.citations.length > 0 && (
                <div style={{ marginTop: 12, paddingTop: 10, borderTop: '1px solid rgba(51, 65, 85, 0.4)', display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                  <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Authoritative Code References:</span>
                  {msg.citations.map((c, idx) => (
                    <span key={idx} className="badge badge-generic font-mono" style={{ fontSize: '0.7rem' }}>
                      {c}
                    </span>
                  ))}
                </div>
              )}
            </div>
          ))
        )}

        {loading && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, color: '#06b6d4', fontSize: '0.85rem', padding: 10 }}>
            <div className="animate-pulse-glow" style={{ width: 10, height: 10, borderRadius: '50%', background: '#06b6d4' }} />
            <span>Analyzing document telemetry and evaluating governance rules...</span>
          </div>
        )}
      </div>

      {/* Input Box */}
      <form onSubmit={handleSend} style={{ display: 'flex', gap: 10 }}>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ask why entities were masked, how the release gate functioned, or verify compliance..."
          disabled={loading}
          style={{
            flex: 1,
            background: 'rgba(15, 23, 42, 0.8)',
            border: '1px solid var(--border-color)',
            borderRadius: 8,
            padding: '10px 14px',
            color: '#f8fafc',
            fontSize: '0.875rem',
            outline: 'none',
          }}
        />
        <button type="submit" disabled={loading || !query.trim()} className="btn-primary" style={{ padding: '10px 18px' }}>
          <Send size={16} />
          <span>Ask Copilot</span>
        </button>
      </form>
    </div>
  );
};
