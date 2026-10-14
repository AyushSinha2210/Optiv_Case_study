import React, { useState, useEffect, useRef } from 'react';
import {
  Send,
  X,
  Scale,
  Cpu,
  ShieldCheck,
  ScrollText,
  HelpCircle,
  RefreshCw,
  AlertOctagon,
  FileText,
} from 'lucide-react';
import type { AssistantChatResponse } from '../../types';
import { MarkdownRenderer } from './MarkdownRenderer';

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
  const [activeTopic, setActiveTopic] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Focus input and handle Escape key
  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 100);
      const handleKeyDown = (e: KeyboardEvent) => {
        if (e.key === 'Escape') onClose();
      };
      window.addEventListener('keydown', handleKeyDown);
      return () => window.removeEventListener('keydown', handleKeyDown);
    }
  }, [isOpen, onClose]);

  // Scroll to bottom on new messages
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, loading]);

  if (!isOpen) return null;

  const fetchExplanation = async (topic: string, customQuery?: string) => {
    if (!documentId) return;
    setLoading(true);
    setActiveTopic(topic);
    setErrorMessage(null);

    const questionText = customQuery || topic;

    try {
      const res = await fetch('/api/assistant/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          document_id: documentId,
          topic,
          query: questionText,
        }),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || `Request failed with status ${res.status}`);
      }

      const data: AssistantChatResponse = await res.json();
      setMessages((prev) => [...prev, data]);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to retrieve grounded explanation');
    } finally {
      setLoading(false);
      setActiveTopic(null);
    }
  };

  const handleSend = (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim() || loading) return;
    const q = query;
    setQuery('');
    fetchExplanation('custom', q);
  };

  return (
    <div
      className="ai-drawer-overlay"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-label="AI Privacy Copilot Explanation Drawer"
    >
      <div className="ai-drawer" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div
          style={{
            padding: '16px 20px',
            borderBottom: '1px solid var(--tprm-border)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <div
              style={{
                padding: 8,
                borderRadius: 8,
                backgroundColor: 'var(--tprm-indigo-light)',
                color: 'var(--tprm-indigo)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <FileText size={18} />
            </div>
            <div>
              <h3 style={{ fontSize: '0.95rem', fontWeight: 700, margin: 0, color: 'var(--tprm-text-primary)' }}>
                AI Privacy Copilot
              </h3>
              <p style={{ fontSize: '0.725rem', color: 'var(--tprm-text-muted)', margin: 0 }}>
                Grounded Explanation Engine • Document: {documentId || 'Active Run'}
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="optiv-btn-header icon-only"
            aria-label="Close Copilot Drawer"
          >
            <X size={16} />
          </button>
        </div>

        {/* Quick Inquiries Section */}
        <div
          style={{
            padding: '12px 16px',
            borderBottom: '1px solid var(--tprm-border)',
            backgroundColor: 'var(--tprm-surface-subtle)',
          }}
        >
          <div style={{ fontSize: '0.725rem', fontWeight: 600, color: 'var(--tprm-text-secondary)', marginBottom: 8 }}>
            Quick Document Inquiries:
          </div>
          <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
            <button
              onClick={() => fetchExplanation('decision', 'Why was this document release decision reached?')}
              disabled={loading}
              className={`optiv-btn-header ${activeTopic === 'decision' ? 'active' : ''}`}
              style={{ fontSize: '0.725rem', height: 28 }}
            >
              <Scale size={12} color="var(--tprm-cyan)" />
              <span>Release Decision</span>
            </button>
            <button
              onClick={() => fetchExplanation('taxonomy', 'Explain PII classification rules')}
              disabled={loading}
              className={`optiv-btn-header ${activeTopic === 'taxonomy' ? 'active' : ''}`}
              style={{ fontSize: '0.725rem', height: 28 }}
            >
              <Cpu size={12} color="var(--tprm-indigo)" />
              <span>Classification Rules</span>
            </button>
            <button
              onClick={() => fetchExplanation('leakage', 'Explain residual verification re-scan')}
              disabled={loading}
              className={`optiv-btn-header ${activeTopic === 'leakage' ? 'active' : ''}`}
              style={{ fontSize: '0.725rem', height: 28 }}
            >
              <ShieldCheck size={12} color="var(--tprm-emerald)" />
              <span>Residual Re-scan</span>
            </button>
            <button
              onClick={() => fetchExplanation('policy', 'Explain Zero-Leakage audit policy')}
              disabled={loading}
              className={`optiv-btn-header ${activeTopic === 'policy' ? 'active' : ''}`}
              style={{ fontSize: '0.725rem', height: 28 }}
            >
              <ScrollText size={12} color="#f59e0b" />
              <span>Audit Policy</span>
            </button>
          </div>
        </div>

        {/* Chat / Response Scroll Area */}
        <div
          ref={scrollRef}
          style={{
            flex: 1,
            padding: 16,
            overflowY: 'auto',
            display: 'flex',
            flexDirection: 'column',
            gap: 14,
          }}
        >
          {messages.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '40px 16px', color: 'var(--tprm-text-muted)' }}>
              <div
                style={{
                  width: 44,
                  height: 44,
                  borderRadius: '50%',
                  backgroundColor: 'var(--tprm-surface-subtle)',
                  border: '1px solid var(--tprm-border)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  margin: '0 auto 12px',
                  color: 'var(--tprm-indigo)',
                }}
              >
                <HelpCircle size={22} />
              </div>
              <h4 style={{ fontSize: '0.9rem', color: 'var(--tprm-text-primary)', margin: '0 0 6px', fontWeight: 600 }}>
                Grounded Pipeline Intelligence
              </h4>
              <p style={{ fontSize: '0.775rem', lineHeight: 1.5, margin: '0 auto', maxWidth: 320 }}>
                Submit questions regarding entity detection, release decisions, structure retention, or residual scan metrics for document {documentId}.
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
                  <div
                    style={{
                      fontWeight: 600,
                      color: 'var(--tprm-indigo)',
                      marginBottom: 10,
                      display: 'flex',
                      alignItems: 'center',
                      gap: 6,
                      fontSize: '0.8rem',
                      borderBottom: '1px solid var(--tprm-border)',
                      paddingBottom: 6,
                    }}
                  >
                    <span>Inquiry: {m.query}</span>
                  </div>
                )}

                {/* Render Formatted Markdown */}
                <div style={{ color: 'var(--tprm-text-primary)' }}>
                  <MarkdownRenderer content={m.explanation} />
                </div>

                {m.citations && m.citations.length > 0 && (
                  <div
                    style={{
                      marginTop: 12,
                      paddingTop: 8,
                      borderTop: '1px solid var(--tprm-border)',
                      display: 'flex',
                      alignItems: 'center',
                      gap: 6,
                      flexWrap: 'wrap',
                    }}
                  >
                    <span style={{ fontSize: '0.7rem', color: 'var(--tprm-text-muted)', fontWeight: 600 }}>
                      Evidence Citations:
                    </span>
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

          {/* Loading Indicator */}
          {loading && (
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 10,
                color: 'var(--tprm-text-muted)',
                fontSize: '0.8rem',
                padding: '10px 14px',
                borderRadius: 8,
                backgroundColor: 'var(--tprm-surface-subtle)',
                border: '1px solid var(--tprm-border)',
              }}
            >
              <RefreshCw size={14} className="animate-spin text-cyan" />
              <span>Analyzing telemetry and synthesizing grounded explanation...</span>
            </div>
          )}

          {/* Error Message */}
          {errorMessage && (
            <div
              style={{
                padding: '10px 14px',
                borderRadius: 8,
                backgroundColor: 'rgba(239, 68, 68, 0.08)',
                border: '1px solid rgba(239, 68, 68, 0.3)',
                color: 'var(--tprm-rose)',
                fontSize: '0.8rem',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <AlertOctagon size={16} />
                <span>{errorMessage}</span>
              </div>
              <button
                onClick={() => fetchExplanation('decision', 'Explain release decision')}
                className="optiv-btn-header"
                style={{ height: 26, fontSize: '0.7rem' }}
              >
                Retry
              </button>
            </div>
          )}
        </div>

        {/* Input Form */}
        <form
          onSubmit={handleSend}
          style={{
            padding: 12,
            borderTop: '1px solid var(--tprm-border)',
            display: 'flex',
            gap: 8,
            backgroundColor: 'var(--tprm-surface)',
          }}
        >
          <input
            ref={inputRef}
            type="text"
            placeholder="Ask question about this document run..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            disabled={loading}
            aria-label="Ask question about document run"
            style={{
              flex: 1,
              padding: '8px 12px',
              borderRadius: 6,
              border: '1px solid var(--tprm-border)',
              backgroundColor: 'var(--tprm-surface-subtle)',
              color: 'var(--tprm-text-primary)',
              fontSize: '0.8rem',
              outline: 'none',
            }}
          />
          <button
            type="submit"
            disabled={loading || !query.trim()}
            className="btn-primary"
            style={{ padding: '8px 14px', display: 'flex', alignItems: 'center', gap: 6 }}
            aria-label="Send question"
          >
            <Send size={14} />
          </button>
        </form>
      </div>
    </div>
  );
};
