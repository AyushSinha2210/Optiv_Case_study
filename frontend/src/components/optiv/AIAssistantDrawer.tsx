import React, { useState } from 'react';
import {
  Bot,
  Send,
  X,
  Sparkles,
  Scale,
  Cpu,
  ShieldCheck,
  ScrollText,
} from 'lucide-react';
import type { AssistantChatResponse } from '../../types';

interface AIAssistantDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  documentId: string;
}

export const AIAssistantDrawer: React.FC<AIAssistantDrawerProps> = ({
  isOpen,
  onClose,
  documentId,
}) => {
  const [query, setQuery] = useState('');
  const [messages, setMessages] = useState<AssistantChatResponse[]>([]);
  const [loading, setLoading] = useState(false);

  if (!isOpen) return null;

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
    <div className="ai-drawer-overlay" onClick={onClose}>
      <div className="ai-drawer" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--tprm-border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <div style={{ padding: 8, borderRadius: 8, background: 'linear-gradient(135deg, #6366f1 0%, #0ea5e9 100%)' }}>
              <Bot size={20} color="#ffffff" />
            </div>
            <div>
              <h3 style={{ fontSize: '0.95rem', fontWeight: 700, margin: 0, color: 'var(--tprm-text-primary)' }}>
                AI Privacy Copilot
              </h3>
              <p style={{ fontSize: '0.725rem', color: 'var(--tprm-text-muted)', margin: 0 }}>
                Grounded explanations • Doc: {documentId || 'active'}
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--tprm-text-muted)' }}
          >
            <X size={18} />
          </button>
        </div>

        {/* Suggested Quick Prompt Chips */}
        <div style={{ padding: '12px 16px', borderBottom: '1px solid var(--tprm-border)', backgroundColor: 'var(--tprm-surface-subtle)' }}>
          <div style={{ fontSize: '0.725rem', fontWeight: 600, color: 'var(--tprm-text-secondary)', marginBottom: 8 }}>
            Quick Inquiries:
          </div>
          <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
            <button
              onClick={() => fetchExplanation('decision', 'Why was this document release decision reached?')}
              disabled={loading}
              className="btn-secondary"
              style={{ fontSize: '0.725rem', padding: '4px 8px', display: 'flex', alignItems: 'center', gap: 4 }}
            >
              <Scale size={12} color="var(--tprm-cyan)" />
              <span>Release Decision</span>
            </button>
            <button
              onClick={() => fetchExplanation('taxonomy', 'Explain PII classification rules')}
              disabled={loading}
              className="btn-secondary"
              style={{ fontSize: '0.725rem', padding: '4px 8px', display: 'flex', alignItems: 'center', gap: 4 }}
            >
              <Cpu size={12} color="var(--tprm-indigo)" />
              <span>Classification Rules</span>
            </button>
            <button
              onClick={() => fetchExplanation('leakage', 'Explain residual verification re-scan')}
              disabled={loading}
              className="btn-secondary"
              style={{ fontSize: '0.725rem', padding: '4px 8px', display: 'flex', alignItems: 'center', gap: 4 }}
            >
              <ShieldCheck size={12} color="var(--tprm-emerald)" />
              <span>Residual Re-scan</span>
            </button>
            <button
              onClick={() => fetchExplanation('policy', 'Explain Zero-Leakage audit policy')}
              disabled={loading}
              className="btn-secondary"
              style={{ fontSize: '0.725rem', padding: '4px 8px', display: 'flex', alignItems: 'center', gap: 4 }}
            >
              <ScrollText size={12} color="#f59e0b" />
              <span>Audit Policy</span>
            </button>
          </div>
        </div>

        {/* Chat / Response Scroll Area */}
        <div style={{ flex: 1, padding: 16, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 14 }}>
          {messages.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '32px 16px', color: 'var(--tprm-text-muted)' }}>
              <div style={{ marginBottom: 10 }}>
                <Sparkles size={28} color="var(--tprm-indigo)" />
              </div>
              <h4 style={{ fontSize: '0.9rem', color: 'var(--tprm-text-primary)', margin: '0 0 6px' }}>
                Ask me about this document run
              </h4>
              <p style={{ fontSize: '0.75rem', lineHeight: 1.5, margin: 0 }}>
                Every explanation is grounded in actual pipeline stage telemetry, verification re-scans, and documented invariants.
              </p>
            </div>
          ) : (
            messages.map((m, idx) => (
              <div
                key={idx}
                style={{
                  padding: 14,
                  borderRadius: 8,
                  backgroundColor: 'var(--tprm-surface-subtle)',
                  border: '1px solid var(--tprm-border)',
                  fontSize: '0.8rem',
                  lineHeight: 1.5,
                }}
              >
                {m.query && (
                  <div style={{ fontWeight: 700, color: 'var(--tprm-indigo)', marginBottom: 8, display: 'flex', alignItems: 'center', gap: 6 }}>
                    <span>Q: {m.query}</span>
                  </div>
                )}
                <div style={{ color: 'var(--tprm-text-primary)', whiteSpace: 'pre-wrap' }}>
                  {m.explanation}
                </div>

                {m.citations && m.citations.length > 0 && (
                  <div style={{ marginTop: 10, paddingTop: 8, borderTop: '1px solid var(--tprm-border)', display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
                    <span style={{ fontSize: '0.7rem', color: 'var(--tprm-text-muted)' }}>Citations:</span>
                    {m.citations.map((c, i) => (
                      <span key={i} className="badge badge-generic" style={{ fontSize: '0.65rem' }}>
                        {c}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))
          )}

          {loading && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'var(--tprm-text-muted)', fontSize: '0.8rem' }}>
              <span className="pulsing-dot" />
              <span>Analyzing telemetry and generating grounded explanation...</span>
            </div>
          )}
        </div>

        {/* Input Form */}
        <form onSubmit={handleSend} style={{ padding: 12, borderTop: '1px solid var(--tprm-border)', display: 'flex', gap: 8 }}>
          <input
            type="text"
            placeholder="Ask question about this document run..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            style={{
              flex: 1,
              padding: '8px 12px',
              borderRadius: 6,
              border: '1px solid var(--tprm-border)',
              backgroundColor: 'var(--tprm-surface)',
              color: 'var(--tprm-text-primary)',
              fontSize: '0.8rem',
              outline: 'none',
            }}
          />
          <button
            type="submit"
            disabled={loading || !query.trim()}
            className="btn-primary"
            style={{ padding: '8px 12px' }}
          >
            <Send size={14} />
          </button>
        </form>
      </div>
    </div>
  );
};
