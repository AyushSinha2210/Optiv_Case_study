import React, { useState, useEffect } from 'react';
import {
  Download,
  FileText,
  Lock,
  FileSpreadsheet,
  ScrollText,
  RefreshCw,
  CheckCircle2,
  FolderOpen,
} from 'lucide-react';
import type { UserProfile } from '../../types';
import { PageHeader } from './PageHeader';
import { CopyButton } from './CopyButton';

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
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      {/* Unified Page Header */}
      <PageHeader
        title="Authorized Artifacts & Compliance Export Hub"
        description="Retrieve format-native sanitized outputs, original evidence documents, metadata-only Contract D compliance reports, and entity findings matrices."
        actions={
          <button
            onClick={fetchRuns}
            className="btn-secondary"
            disabled={loading}
            title="Refresh available artifact records"
          >
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
            <span>Refresh Records</span>
          </button>
        }
      />

      {/* Document Selection Control */}
      <div className="optiv-card" style={{ padding: '16px 20px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 14 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, flex: 1, minWidth: 280 }}>
            <FolderOpen size={18} color="var(--tprm-text-muted)" />
            <div style={{ flex: 1 }}>
              <label style={{ fontSize: '0.775rem', fontWeight: 600, color: 'var(--tprm-text-muted)', display: 'block', marginBottom: 4 }}>
                Target Processed Document:
              </label>
              <select
                value={selectedDocId}
                onChange={(e) => setSelectedDocId(e.target.value)}
                className="optiv-select"
                style={{ width: '100%', height: 38 }}
                aria-label="Select processed document"
              >
                {runs.map((r) => (
                  <option key={r.document_id} value={r.document_id}>
                    {r.original_filename || 'document.txt'} ({r.document_id.slice(0, 18)}...) &bull; {r.release_allowed ? 'RELEASE: PASS' : 'RELEASE: BLOCKED'}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {activeRun && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <div className="optiv-doc-id-cell">
                <span className="optiv-doc-id-text" title={activeRun.document_id}>
                  {activeRun.document_id}
                </span>
                <CopyButton text={activeRun.document_id} />
              </div>
              <span className={`badge ${activeRun.release_allowed ? 'badge-success' : 'badge-danger'}`}>
                {activeRun.release_allowed ? 'GATE: AUTHORIZED' : 'GATE: BLOCKED'}
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Two-Column Grid (2 Rows of 2 Cards on Desktop, 1 Col on Mobile) */}
      {activeRun ? (
        <div className="optiv-two-col-grid">
          {/* Card 1: Sanitized Output Artifact */}
          <div className="optiv-card" style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <div style={{ padding: 10, borderRadius: 10, backgroundColor: activeRun.release_allowed ? 'var(--tprm-emerald-light)' : 'rgba(239, 68, 68, 0.15)', color: activeRun.release_allowed ? 'var(--tprm-emerald)' : 'var(--tprm-rose)' }}>
                {activeRun.release_allowed ? <CheckCircle2 size={22} /> : <Lock size={22} />}
              </div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <h3 style={{ margin: 0, fontSize: '1rem', color: 'var(--tprm-text-primary)', fontWeight: 700 }}>
                  1. Sanitized Output Artifact
                </h3>
                <span style={{ fontSize: '0.725rem', color: 'var(--tprm-text-muted)' }}>
                  Format: {activeRun.source_type?.toUpperCase() || activeRun.file_type?.toUpperCase() || 'DOCUMENT'} &bull; Non-Reversible
                </span>
              </div>
              <span className={`badge ${activeRun.release_allowed ? 'badge-success' : 'badge-danger'}`}>
                {activeRun.release_allowed ? 'AVAILABLE' : 'WITHHELD'}
              </span>
            </div>

            <p style={{ fontSize: '0.8125rem', color: 'var(--tprm-text-muted)', lineHeight: 1.5, margin: 0 }}>
              The newly generated sanitized copy in which all verified sensitive entities were permanently stripped. Safe for downstream LLM analysis when release is authorized.
            </p>

            <div style={{ marginTop: 'auto', paddingTop: 8 }}>
              {activeRun.release_allowed ? (
                <button
                  onClick={downloadSanitized}
                  className="btn-primary"
                  style={{ width: '100%', justifyContent: 'center' }}
                  title="Download verified sanitized document"
                >
                  <Download size={15} />
                  <span>Download Sanitized ({activeRun.source_type?.toUpperCase() || activeRun.file_type?.toUpperCase() || 'DOCUMENT'})</span>
                </button>
              ) : (
                <button
                  disabled
                  className="btn-secondary"
                  style={{ width: '100%', justifyContent: 'center', opacity: 0.65, cursor: 'not-allowed', color: 'var(--tprm-rose)' }}
                  title="Release withheld by verification gate"
                >
                  <Lock size={15} />
                  <span>Download Blocked (Verification Gate)</span>
                </button>
              )}
            </div>
          </div>

          {/* Card 2: Original Evidence Document */}
          <div className="optiv-card" style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <div style={{ padding: 10, borderRadius: 10, backgroundColor: 'var(--tprm-indigo-light)', color: 'var(--tprm-indigo)' }}>
                <FileText size={22} />
              </div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <h3 style={{ margin: 0, fontSize: '1rem', color: 'var(--tprm-text-primary)', fontWeight: 700 }}>
                  2. Original Evidence Document
                </h3>
                <span style={{ fontSize: '0.725rem', color: 'var(--tprm-text-muted)' }}>
                  Immutable Source &bull; Permission Governed
                </span>
              </div>
              <span className="badge badge-generic">AUDIT VAULT</span>
            </div>

            <p style={{ fontSize: '0.8125rem', color: 'var(--tprm-text-muted)', lineHeight: 1.5, margin: 0 }}>
              The unmodified original file uploaded to the gateway. Kept in isolated storage with cryptographic integrity hashes for regulatory examination.
            </p>

            <div style={{ marginTop: 'auto', paddingTop: 8 }}>
              <button
                onClick={downloadOriginal}
                className="btn-secondary"
                style={{ width: '100%', justifyContent: 'center' }}
                title="Download immutable source file"
              >
                <Download size={15} />
                <span>Download Original Source</span>
              </button>
            </div>
          </div>

          {/* Card 3: Contract D JSON Compliance Report */}
          <div className="optiv-card" style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <div style={{ padding: 10, borderRadius: 10, backgroundColor: 'var(--tprm-cyan-light)', color: 'var(--tprm-cyan)' }}>
                <ScrollText size={22} />
              </div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <h3 style={{ margin: 0, fontSize: '1rem', color: 'var(--tprm-text-primary)', fontWeight: 700 }}>
                  3. Contract D Compliance Report
                </h3>
                <span style={{ fontSize: '0.725rem', color: 'var(--tprm-text-muted)' }}>
                  JSON Format &bull; Metadata-Only Projection
                </span>
              </div>
              <span className="badge badge-info">JSON REPORT</span>
            </div>

            <p style={{ fontSize: '0.8125rem', color: 'var(--tprm-text-muted)', lineHeight: 1.5, margin: 0 }}>
              Machine-readable structured audit telemetry detailing stage transitions, processing durations, applied rule IDs, and release authorization verdicts. Zero raw PII retained.
            </p>

            <div style={{ marginTop: 'auto', paddingTop: 8 }}>
              <button
                onClick={() => downloadReport('json')}
                className="btn-secondary"
                style={{ width: '100%', justifyContent: 'center' }}
                title="Download structured JSON compliance report"
              >
                <Download size={15} />
                <span>Download Audit Report (JSON)</span>
              </button>
            </div>
          </div>

          {/* Card 4: Tabular Findings Matrix */}
          <div className="optiv-card" style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <div style={{ padding: 10, borderRadius: 10, backgroundColor: 'rgba(245, 158, 11, 0.15)', color: '#f59e0b' }}>
                <FileSpreadsheet size={22} />
              </div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <h3 style={{ margin: 0, fontSize: '1rem', color: 'var(--tprm-text-primary)', fontWeight: 700 }}>
                  4. Entity Findings Matrix
                </h3>
                <span style={{ fontSize: '0.725rem', color: 'var(--tprm-text-muted)' }}>
                  CSV Spreadsheet &bull; Redaction Ledger
                </span>
              </div>
              <span className="badge badge-warning">CSV MATRIX</span>
            </div>

            <p style={{ fontSize: '0.8125rem', color: 'var(--tprm-text-muted)', lineHeight: 1.5, margin: 0 }}>
              Tabular spreadsheet listing all classified PII categories, character offset spans, detector confidences, and replacement masking tokens for compliance logging.
            </p>

            <div style={{ marginTop: 'auto', paddingTop: 8 }}>
              <button
                onClick={() => downloadReport('csv')}
                className="btn-secondary"
                style={{ width: '100%', justifyContent: 'center' }}
                title="Download CSV entity findings matrix"
              >
                <Download size={15} />
                <span>Download Findings Matrix (CSV)</span>
              </button>
            </div>
          </div>
        </div>
      ) : (
        <div className="optiv-card" style={{ textAlign: 'center', padding: 48, color: 'var(--tprm-text-muted)' }}>
          No document processing runs available for artifact download.
        </div>
      )}
    </div>
  );
};
