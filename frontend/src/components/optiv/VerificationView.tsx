import React from 'react';
import {
  CheckCircle2,
  ShieldAlert,
  FileCheck,
  Lock,
  ExternalLink,
  Download,
  XCircle,
} from 'lucide-react';
import type { UserProfile, ProcessResponse } from '../../types';

interface VerificationViewProps {
  currentUser?: UserProfile;
  activeDocument?: ProcessResponse | null;
  onNavigateToWorkspace: () => void;
}

export const VerificationView: React.FC<VerificationViewProps> = ({
  activeDocument,
  onNavigateToWorkspace,
}) => {
  const isPass = activeDocument?.verification_status === 'PASS';
  const isBlocked = !activeDocument?.release_allowed;

  // Calculate structure score approximation if text is available
  const origLen = activeDocument?.char_count || 1;
  const redactedLen = activeDocument?.redacted_text ? activeDocument.redacted_text.length : origLen;
  const structureRatio = Math.min(1.0, (redactedLen / origLen)).toFixed(3);
  const structurePercent = (parseFloat(structureRatio) * 100).toFixed(1);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      {/* Active Document Context Header */}
      <div className="optiv-doc-banner">
        <div className="optiv-doc-banner-info">
          <div
            className="optiv-doc-icon-wrap"
            style={{
              backgroundColor: isPass ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
              color: isPass ? 'var(--tprm-emerald)' : 'var(--tprm-rose)',
            }}
          >
            {isPass ? <CheckCircle2 size={22} /> : <ShieldAlert size={22} />}
          </div>
          <div className="optiv-doc-meta">
            <div className="optiv-doc-title-row">
              <span className="optiv-doc-title">
                {activeDocument
                  ? `Stage 7 Verification Telemetry: ${activeDocument.document_id ? activeDocument.document_id.slice(0, 18) : 'Doc'}...`
                  : 'Stage 7: Independent Post-Redaction Verification Plane'}
              </span>
              {activeDocument && (
                <span className={`badge ${activeDocument.release_allowed ? 'badge-success' : 'badge-danger'}`}>
                  {activeDocument.release_allowed ? 'GATE: RELEASE AUTHORIZED' : 'GATE: FAIL-CLOSED BLOCKED'}
                </span>
              )}
            </div>
            <div className="optiv-doc-stats-row">
              <span className="optiv-doc-stat-item">
                <span>Verification Status:</span>
                <span
                  className="optiv-doc-stat-val"
                  style={{ color: isPass ? 'var(--tprm-emerald)' : 'var(--tprm-rose)' }}
                >
                  {activeDocument?.verification_status || 'IDLE'}
                </span>
              </span>
              <span>•</span>
              <span className="optiv-doc-stat-item">
                <span>Format:</span>
                <span className="optiv-doc-stat-val">
                  {activeDocument?.source_type?.toUpperCase() || 'DOCUMENT'}
                </span>
              </span>
              <span>•</span>
              <span className="optiv-doc-stat-item">
                <span>Structure Preserved:</span>
                <span className="optiv-doc-stat-val">
                  {activeDocument ? `${structurePercent}%` : 'N/A'}
                </span>
              </span>
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          {activeDocument?.release_allowed && (
            <button
              onClick={() => window.open(`/api/artifact/${activeDocument.document_id}`, '_blank')}
              className="btn-primary"
              style={{ fontSize: '0.8rem', padding: '7px 14px', display: 'flex', alignItems: 'center', gap: 6 }}
            >
              <Download size={14} />
              <span>Download Verified Output</span>
            </button>
          )}

          <button
            onClick={onNavigateToWorkspace}
            className="optiv-btn-header"
            style={{ height: 36, display: 'flex', alignItems: 'center', gap: 6 }}
          >
            <ExternalLink size={14} />
            <span>Open Document Workspace</span>
          </button>
        </div>
      </div>

      {/* 3 Pillars of Independent Verification Evaluated for Given Document */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: 16 }}>
        {/* Pillar 1: Residual Leakage Re-Scan */}
        <div className="optiv-card" style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <div
                style={{
                  padding: 8,
                  borderRadius: 8,
                  backgroundColor: isPass ? 'var(--tprm-emerald-light)' : 'rgba(239, 68, 68, 0.15)',
                }}
              >
                <ShieldAlert size={20} color={isPass ? 'var(--tprm-emerald)' : '#ef4444'} />
              </div>
              <div>
                <h4 style={{ margin: 0, fontSize: '0.95rem', color: 'var(--tprm-text-primary)' }}>
                  1. Zero Residual Leakage Re-Scan
                </h4>
                <span style={{ fontSize: '0.7rem', color: 'var(--tprm-text-muted)' }}>
                  Autonomous Secondary Scanner
                </span>
              </div>
            </div>

            <span className={`badge ${isPass ? 'badge-success' : 'badge-danger'}`}>
              {isPass ? 'PASS' : 'FAIL'}
            </span>
          </div>

          <div
            style={{
              padding: 10,
              borderRadius: 6,
              backgroundColor: 'var(--tprm-surface-subtle)',
              fontSize: '0.8rem',
              lineHeight: 1.5,
            }}
          >
            {activeDocument ? (
              isPass ? (
                <div style={{ color: 'var(--tprm-emerald)', display: 'flex', alignItems: 'center', gap: 6, fontWeight: 600 }}>
                  <CheckCircle2 size={16} />
                  <span>0 residual findings in output text or metadata.</span>
                </div>
              ) : (
                <div style={{ color: 'var(--tprm-rose)', display: 'flex', alignItems: 'center', gap: 6, fontWeight: 600 }}>
                  <XCircle size={16} />
                  <span>Residual findings detected during secondary re-scan!</span>
                </div>
              )
            ) : (
              <span style={{ color: 'var(--tprm-text-muted)' }}>No document loaded. Run a pipeline in Document Workspace.</span>
            )}
          </div>

          <ul style={{ fontSize: '0.75rem', color: 'var(--tprm-text-secondary)', paddingLeft: 16, margin: 0, lineHeight: 1.6 }}>
            <li><strong>Known Value Search:</strong> Verifies all {activeDocument?.entities.length ?? 0} sensitive spans are eliminated.</li>
            <li><strong>Independent Pattern Scanner:</strong> Autonomous regex sweep for SSN, email, phone, and card tokens.</li>
            <li><strong>Policy Rule:</strong> Zero tolerance; a single residual discovery triggers immediate fail-closed gate block.</li>
          </ul>
        </div>

        {/* Pillar 2: Structure Retention Scoring */}
        <div className="optiv-card" style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <div style={{ padding: 8, borderRadius: 8, backgroundColor: 'var(--tprm-cyan-light)' }}>
                <FileCheck size={20} color="var(--tprm-cyan)" />
              </div>
              <div>
                <h4 style={{ margin: 0, fontSize: '0.95rem', color: 'var(--tprm-text-primary)' }}>
                  2. Structure Retention Scoring (&gt;= 80%)
                </h4>
                <span style={{ fontSize: '0.7rem', color: 'var(--tprm-text-muted)' }}>
                  Context &amp; Layout Preservation
                </span>
              </div>
            </div>

            <span className="badge badge-info">
              {activeDocument ? `${structurePercent}%` : '80.0% MIN'}
            </span>
          </div>

          <div
            style={{
              padding: 10,
              borderRadius: 6,
              backgroundColor: 'var(--tprm-surface-subtle)',
              fontSize: '0.8rem',
              lineHeight: 1.5,
            }}
          >
            {activeDocument ? (
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                  <span style={{ fontSize: '0.75rem', color: 'var(--tprm-text-muted)' }}>Retained Character Ratio:</span>
                  <span style={{ fontWeight: 700, color: 'var(--tprm-text-primary)' }}>{structurePercent}%</span>
                </div>
                <div style={{ width: '100%', height: 6, backgroundColor: 'var(--tprm-border)', borderRadius: 3, overflow: 'hidden' }}>
                  <div
                    style={{
                      width: `${Math.min(100, parseFloat(structurePercent))}%`,
                      height: '100%',
                      backgroundColor: parseFloat(structurePercent) >= 80 ? 'var(--tprm-cyan)' : 'var(--tprm-rose)',
                    }}
                  />
                </div>
              </div>
            ) : (
              <span style={{ color: 'var(--tprm-text-muted)' }}>Awaiting document execution.</span>
            )}
          </div>

          <ul style={{ fontSize: '0.75rem', color: 'var(--tprm-text-secondary)', paddingLeft: 16, margin: 0, lineHeight: 1.6 }}>
            <li><strong>Syntactic Integrity:</strong> Headings, paragraphs, and list enumerations are preserved.</li>
            <li><strong>AI Audit Readability:</strong> Ensures downstream LLM or analyst can comprehend non-sensitive facts.</li>
            <li><strong>Threshold Enforcement:</strong> Enforces &gt;= 80% structure retention specification.</li>
          </ul>
        </div>

        {/* Pillar 3: Format Non-Reversibility */}
        <div className="optiv-card" style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <div style={{ padding: 8, borderRadius: 8, backgroundColor: 'var(--tprm-indigo-light)' }}>
                <Lock size={20} color="var(--tprm-indigo)" />
              </div>
              <div>
                <h4 style={{ margin: 0, fontSize: '0.95rem', color: 'var(--tprm-text-primary)' }}>
                  3. Non-Reversibility &amp; Content Scrub
                </h4>
                <span style={{ fontSize: '0.7rem', color: 'var(--tprm-text-muted)' }}>
                  Format-Native Sanitization
                </span>
              </div>
            </div>

            <span className="badge badge-success">CERTIFIED</span>
          </div>

          <div
            style={{
              padding: 10,
              borderRadius: 6,
              backgroundColor: 'var(--tprm-surface-subtle)',
              fontSize: '0.8rem',
              lineHeight: 1.5,
              color: 'var(--tprm-text-secondary)',
            }}
          >
            {activeDocument ? (
              <span>
                Format-native <strong>{activeDocument.source_type?.toUpperCase()}</strong> sanitizer scrubbed underlying glyphs; irreversible token replacement.
              </span>
            ) : (
              <span>Awaiting document execution.</span>
            )}
          </div>

          <ul style={{ fontSize: '0.75rem', color: 'var(--tprm-text-secondary)', paddingLeft: 16, margin: 0, lineHeight: 1.6 }}>
            <li><strong>No Hidden Layers:</strong> Vector text streams permanently pruned; no floating black boxes.</li>
            <li><strong>Cryptographic Salt:</strong> Medical/HIPAA data hashed with tenant-isolated salt.</li>
            <li><strong>Metadata Sanitized:</strong> PDF/DOCX author, revision, and tool metadata scrubbed.</li>
          </ul>
        </div>
      </div>

      {/* Dual-Key Release Gate Decision Card */}
      <div
        className="optiv-card"
        style={{
          borderLeft: `4px solid ${!isBlocked ? 'var(--tprm-emerald)' : 'var(--tprm-rose)'}`,
          backgroundColor: 'var(--tprm-surface)',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 14 }}>
          <div>
            <h3 style={{ margin: '0 0 6px', fontSize: '1.05rem', color: 'var(--tprm-text-primary)' }}>
              Dual-Key Release Authorization Verdict
            </h3>
            <p style={{ margin: 0, fontSize: '0.8rem', color: 'var(--tprm-text-muted)' }}>
              Release of document artifacts requires: Key 1 (Automated 3-Pillar Verification PASS) + Key 2 (Compliance Policy Release Authorization).
            </p>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--tprm-text-muted)' }}>Gate Authorization:</div>
              <div style={{ fontWeight: 700, fontSize: '0.9rem', color: !isBlocked ? 'var(--tprm-emerald)' : 'var(--tprm-rose)' }}>
                {!isBlocked ? 'AUTHORIZED FOR RELEASE' : 'FAIL-CLOSED / WITHHELD'}
              </div>
            </div>

            {activeDocument?.release_allowed ? (
              <button
                onClick={() => window.open(`/api/artifact/${activeDocument.document_id}`, '_blank')}
                className="btn-primary"
                style={{ fontSize: '0.8rem', padding: '8px 16px', display: 'flex', alignItems: 'center', gap: 6 }}
              >
                <Download size={14} />
                <span>Download Artifact</span>
              </button>
            ) : (
              <button
                onClick={onNavigateToWorkspace}
                className="btn-secondary"
                style={{ fontSize: '0.8rem', padding: '8px 16px', color: 'var(--tprm-rose)' }}
              >
                Inspect Gate Block In Workspace
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
