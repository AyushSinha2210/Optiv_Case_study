import React, { useState, useEffect } from 'react';
import type { AuditEvent } from '../types';
import { FileDown, ScrollText, ShieldCheck, Download, Lock } from 'lucide-react';

interface AuditLedgerProps {
  documentId: string;
  releaseAllowed: boolean;
  sourceType?: string | null;
}

export const AuditLedger: React.FC<AuditLedgerProps> = ({
  documentId,
  releaseAllowed,
}) => {
  const [events, setEvents] = useState<AuditEvent[]>([]);
  const [reportSummary, setReportSummary] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    if (!documentId) return;
    setLoading(true);

    // Fetch audit events
    fetch(`/api/audit/${documentId}`)
      .then((res) => res.json())
      .then((data) => setEvents(data.events || []))
      .catch((err) => console.error('Error fetching audit log', err));

    // Fetch executive report summary text
    fetch(`/api/report/${documentId}?format=summary`)
      .then((res) => res.text())
      .then((txt) => setReportSummary(txt))
      .catch((err) => console.error('Error fetching report summary', err))
      .finally(() => setLoading(false));
  }, [documentId]);

  const handleDownloadArtifact = () => {
    if (!releaseAllowed) return;
    window.open(`/api/artifact/${documentId}`, '_blank');
  };

  const handleDownloadJSON = () => {
    window.open(`/api/report/${documentId}?format=json`, '_blank');
  };

  const handleDownloadCSV = () => {
    window.open(`/api/report/${documentId}?format=csv`, '_blank');
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      {/* Export & Download Action Bar */}
      <div className="glass-panel" style={{ padding: 20, display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 14 }}>
        <div>
          <h4 style={{ margin: 0, fontSize: '1rem', color: '#f8fafc' }}>Authorized Artifact & Audit Exports</h4>
          <p style={{ margin: 0, fontSize: '0.8rem', color: '#94a3b8' }}>
            Downstream LLM egress requires verified PASS clearance. Audit files are metadata-only.
          </p>
        </div>

        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
          <button onClick={handleDownloadJSON} className="btn-secondary">
            <FileDown size={16} color="#06b6d4" />
            <span>Audit Report (JSON)</span>
          </button>

          <button onClick={handleDownloadCSV} className="btn-secondary">
            <FileDown size={16} color="#3b82f6" />
            <span>Ledger Matrix (CSV)</span>
          </button>

          {releaseAllowed ? (
            <button onClick={handleDownloadArtifact} className="btn-primary glow-emerald">
              <Download size={16} />
              <span>Download Approved Redacted Document</span>
            </button>
          ) : (
            <button disabled className="btn-primary" style={{ opacity: 0.5, cursor: 'not-allowed', background: '#334155' }}>
              <Lock size={16} />
              <span>Download Blocked (Verification Gate)</span>
            </button>
          )}
        </div>
      </div>

      {/* Contract D Executive Summary */}
      <div className="glass-panel" style={{ padding: 24 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <ScrollText size={18} color="#f59e0b" />
            <h4 style={{ margin: 0, fontSize: '1rem' }}>Contract D Executive Compliance Summary</h4>
          </div>
          <span className="badge badge-card">Allowlist Serialized</span>
        </div>

        <div style={{ background: 'rgba(10, 15, 29, 0.7)', padding: 16, borderRadius: 8, border: '1px solid rgba(51, 65, 85, 0.4)' }}>
          <pre style={{ whiteSpace: 'pre-wrap', fontFamily: 'var(--font-mono)', fontSize: '0.85rem', color: '#cbd5e1', lineHeight: '1.6' }}>
            {loading ? 'Loading executive compliance summary...' : (reportSummary || 'No summary available.')}
          </pre>
        </div>
      </div>

      {/* Immutable Sanitized Audit Trail */}
      <div className="glass-panel" style={{ padding: 24 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <ShieldCheck size={18} color="#10b981" />
            <h4 style={{ margin: 0, fontSize: '1rem' }}>Immutable Audit Event Log (Zero-Leakage Guarantee)</h4>
          </div>
          <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Document ID: {documentId}</span>
        </div>

        {events.length === 0 ? (
          <p style={{ color: '#94a3b8', fontSize: '0.85rem' }}>No audit events logged.</p>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.85rem' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border-color)', color: '#94a3b8' }}>
                  <th style={{ padding: '8px 12px' }}>Event ID</th>
                  <th style={{ padding: '8px 12px' }}>Timestamp (UTC)</th>
                  <th style={{ padding: '8px 12px' }}>Pipeline Stage</th>
                  <th style={{ padding: '8px 12px' }}>Event Type</th>
                  <th style={{ padding: '8px 12px' }}>Status</th>
                  <th style={{ padding: '8px 12px' }}>Metadata Details</th>
                </tr>
              </thead>
              <tbody>
                {events.map((ev, i) => (
                  <tr key={ev.event_id || i} style={{ borderBottom: '1px solid rgba(51, 65, 85, 0.3)' }}>
                    <td style={{ padding: '8px 12px', fontFamily: 'var(--font-mono)', color: '#94a3b8', fontSize: '0.75rem' }}>
                      {ev.event_id?.slice(0, 12)}...
                    </td>
                    <td style={{ padding: '8px 12px', fontFamily: 'var(--font-mono)', color: '#cbd5e1' }}>
                      {new Date(ev.timestamp).toLocaleTimeString([], { hour12: false })}.{new Date(ev.timestamp).getMilliseconds().toString().padStart(3, '0')}
                    </td>
                    <td style={{ padding: '8px 12px' }}>
                      <span className="badge badge-generic">{ev.stage}</span>
                    </td>
                    <td style={{ padding: '8px 12px', fontWeight: 600, color: '#38bdf8' }}>
                      {ev.event_type}
                    </td>
                    <td style={{ padding: '8px 12px' }}>
                      <span className={`badge ${ev.status === 'success' ? 'badge-phone' : 'badge-gov'}`}>
                        {ev.status}
                      </span>
                    </td>
                    <td style={{ padding: '8px 12px', fontSize: '0.75rem', color: '#94a3b8' }}>
                      {ev.duration_sec !== undefined && `Duration: ${ev.duration_sec.toFixed(4)}s | `}
                      {ev.entity_count !== undefined && `Entities: ${ev.entity_count} | `}
                      {ev.verification_status && `Verification: ${ev.verification_status}`}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
