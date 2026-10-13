import React, { useState, useEffect } from 'react';
import { Download, FileText, Lock, FileSpreadsheet, ScrollText, RefreshCw, CheckCircle2 } from 'lucide-react';
import type { UserProfile } from '../../types';

interface ReportsDownloadsViewProps {
  currentUser: UserProfile;
}

export const ReportsDownloadsView: React.FC<ReportsDownloadsViewProps> = ({ currentUser }) => {
  const [runs, setRuns] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [selectedDocId, setSelectedDocId] = useState<string>('');

  const fetchRuns = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/runs?limit=50', {
        headers: { 'X-User-Email': currentUser.email },
      });
      if (res.ok) {
        const data = await res.json();
        const runList = data.runs || [];
        setRuns(runList);
        if (runList.length > 0 && !selectedDocId) {
          setSelectedDocId(runList[0].document_id);
        }
      }
    } catch (err) {
      console.warn('Failed to fetch runs for downloads', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRuns();
  }, [currentUser.email]);

  const activeRun = runs.find((r) => r.document_id === selectedDocId);

  const downloadOriginal = () => {
    if (!selectedDocId) return;
    window.open(`/api/original/${selectedDocId}`, '_blank');
  };

  const downloadSanitized = () => {
    if (!selectedDocId) return;
    window.open(`/api/artifact/${selectedDocId}`, '_blank');
  };

  const downloadReport = (format: 'json' | 'csv' | 'summary') => {
    if (!selectedDocId) return;
    window.open(`/api/report/${selectedDocId}?format=${format}`, '_blank');
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      {/* Header */}
      <div className="optiv-card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 700, margin: 0, color: 'var(--tprm-text-primary)' }}>
            Authorized Artifacts & Audit Export Hub
          </h2>
          <p style={{ fontSize: '0.8rem', color: 'var(--tprm-text-muted)', margin: '4px 0 0' }}>
            Download format-native sanitized artifacts, original evidence, and Contract D compliance reports.
          </p>
        </div>

        <button onClick={fetchRuns} className="btn-secondary" style={{ padding: '6px 12px', fontSize: '0.8rem' }}>
          <RefreshCw size={13} className={loading ? 'animate-spin' : ''} />
          <span>Refresh Records</span>
        </button>
      </div>

      {/* Select Document Run */}
      <div className="optiv-card">
        <label style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--tprm-text-secondary)', display: 'block', marginBottom: 6 }}>
          Select Processed Document Run:
        </label>
        <select
          value={selectedDocId}
          onChange={(e) => setSelectedDocId(e.target.value)}
          style={{
            padding: '8px 12px',
            borderRadius: 6,
            border: '1px solid var(--tprm-border)',
            backgroundColor: 'var(--tprm-surface)',
            color: 'var(--tprm-text-primary)',
            fontSize: '0.85rem',
            width: '100%',
          }}
        >
          {runs.map((r) => (
            <option key={r.document_id} value={r.document_id}>
              {r.original_filename || 'document.txt'} ({r.document_id}) • {r.release_allowed ? 'RELEASE AUTHORIZED' : 'WITHHELD'}
            </option>
          ))}
        </select>
      </div>

      {/* Artifact Download Grid */}
      {activeRun ? (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: 16 }}>
          {/* Card 1: Sanitized Output Artifact */}
          <div className="optiv-card" style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <div style={{ padding: 8, borderRadius: 8, backgroundColor: 'var(--tprm-emerald-light)' }}>
                <CheckCircle2 size={20} color="var(--tprm-emerald)" />
              </div>
              <div>
                <h4 style={{ margin: 0, fontSize: '0.95rem', color: 'var(--tprm-text-primary)' }}>
                  Sanitized Output Artifact
                </h4>
                <span style={{ fontSize: '0.7rem', color: 'var(--tprm-text-muted)' }}>
                  Format: {activeRun.file_type?.toUpperCase() || 'DOCUMENT'}
                </span>
              </div>
            </div>

            <p style={{ fontSize: '0.75rem', color: 'var(--tprm-text-muted)', lineHeight: 1.5, margin: 0 }}>
              The newly generated sanitized copy in which all verified sensitive entities were permanently stripped.
            </p>

            {activeRun.release_allowed ? (
              <button onClick={downloadSanitized} className="btn-primary" style={{ marginTop: 'auto', justifyContent: 'center' }}>
                <Download size={14} />
                <span>Download Sanitized ({activeRun.file_type?.toUpperCase() || 'FILE'})</span>
              </button>
            ) : (
              <button disabled className="btn-secondary" style={{ marginTop: 'auto', justifyContent: 'center', opacity: 0.6, cursor: 'not-allowed' }}>
                <Lock size={14} color="var(--tprm-rose)" />
                <span>Download Blocked (Verification Gate)</span>
              </button>
            )}
          </div>

          {/* Card 2: Original Input Document */}
          <div className="optiv-card" style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <div style={{ padding: 8, borderRadius: 8, backgroundColor: 'var(--tprm-indigo-light)' }}>
                <FileText size={20} color="var(--tprm-indigo)" />
              </div>
              <div>
                <h4 style={{ margin: 0, fontSize: '0.95rem', color: 'var(--tprm-text-primary)' }}>
                  Original Evidence Document
                </h4>
                <span style={{ fontSize: '0.7rem', color: 'var(--tprm-text-muted)' }}>
                  Immutable Source • Permission Governed
                </span>
              </div>
            </div>

            <p style={{ fontSize: '0.75rem', color: 'var(--tprm-text-muted)', lineHeight: 1.5, margin: 0 }}>
              The exact unmodified file uploaded by the user. Kept in isolated storage with separate integrity hashes.
            </p>

            <button onClick={downloadOriginal} className="btn-secondary" style={{ marginTop: 'auto', justifyContent: 'center' }}>
              <Download size={14} />
              <span>Download Original Input</span>
            </button>
          </div>

          {/* Card 3: Contract D JSON Audit Report */}
          <div className="optiv-card" style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <div style={{ padding: 8, borderRadius: 8, backgroundColor: 'var(--tprm-cyan-light)' }}>
                <ScrollText size={20} color="var(--tprm-cyan)" />
              </div>
              <div>
                <h4 style={{ margin: 0, fontSize: '0.95rem', color: 'var(--tprm-text-primary)' }}>
                  Contract D Compliance Report (JSON)
                </h4>
                <span style={{ fontSize: '0.7rem', color: 'var(--tprm-text-muted)' }}>
                  Structured Audit Telemetry • Metadata-Only
                </span>
              </div>
            </div>

            <p style={{ fontSize: '0.75rem', color: 'var(--tprm-text-muted)', lineHeight: 1.5, margin: 0 }}>
              Structured machine-readable report containing stage timings, category counts, rule IDs, and release decisions.
            </p>

            <button onClick={() => downloadReport('json')} className="btn-secondary" style={{ marginTop: 'auto', justifyContent: 'center' }}>
              <Download size={14} />
              <span>Download Audit Report (JSON)</span>
            </button>
          </div>

          {/* Card 4: CSV Findings Matrix */}
          <div className="optiv-card" style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <div style={{ padding: 8, borderRadius: 8, backgroundColor: 'rgba(245, 158, 11, 0.15)' }}>
                <FileSpreadsheet size={20} color="#f59e0b" />
              </div>
              <div>
                <h4 style={{ margin: 0, fontSize: '0.95rem', color: 'var(--tprm-text-primary)' }}>
                  Entity Findings Matrix (CSV)
                </h4>
                <span style={{ fontSize: '0.7rem', color: 'var(--tprm-text-muted)' }}>
                  Spreadsheet Format
                </span>
              </div>
            </div>

            <p style={{ fontSize: '0.75rem', color: 'var(--tprm-text-muted)', lineHeight: 1.5, margin: 0 }}>
              Tabular spreadsheet containing all detected entity types, character offsets, detector confidences, and masking tokens.
            </p>

            <button onClick={() => downloadReport('csv')} className="btn-secondary" style={{ marginTop: 'auto', justifyContent: 'center' }}>
              <Download size={14} />
              <span>Download CSV Matrix</span>
            </button>
          </div>
        </div>
      ) : (
        <div className="optiv-card" style={{ textAlign: 'center', padding: 40, color: 'var(--tprm-text-muted)' }}>
          No document processing runs available for download.
        </div>
      )}
    </div>
  );
};
