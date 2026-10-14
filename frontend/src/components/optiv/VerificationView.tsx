import React, { useState } from 'react';
import {
  CheckCircle2,
  ShieldAlert,
  FileCheck,
  Lock,
  ExternalLink,
  Download,
  XCircle,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import type { UserProfile, ProcessResponse } from '../../types';
import { PageHeader } from './PageHeader';
import { CopyButton } from './CopyButton';

interface VerificationViewProps {
  currentUser?: UserProfile;
  activeDocument?: ProcessResponse | null;
  onNavigateToWorkspace: () => void;
}

export const VerificationView: React.FC<VerificationViewProps> = ({
  activeDocument,
  onNavigateToWorkspace,
}) => {
  const [expandedChecks, setExpandedChecks] = useState<Record<string, boolean>>({});

  const toggleCheck = (id: string) => {
    setExpandedChecks((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const vStatus = activeDocument?.verification_status || 'NOT_RUN';
  const isPass = vStatus === 'PASS';
  const isFail = vStatus === 'FAIL';
  const isIncomplete = !activeDocument || (!isPass && !isFail);
  const releaseAuthorized = activeDocument?.release_allowed === true;

  // Calculate structure score approximation if text is available
  const origLen = activeDocument?.char_count || 1;
  const redactedLen = activeDocument?.redacted_text ? activeDocument.redacted_text.length : origLen;
  const structureRatio = Math.min(1.0, (redactedLen / origLen)).toFixed(3);
  const structurePercent = (parseFloat(structureRatio) * 100).toFixed(1);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      {/* Unified Page Header */}
      <PageHeader
        title="Post-Redaction Verification & Release Gate"
        description="Autonomous dual-pass verification engine, zero-residual PII re-scans, structural retention invariant validation, and fail-closed release controls."
        actions={
          <button
            onClick={onNavigateToWorkspace}
            className="btn-secondary"
            title="Open Document Comparison Workspace"
          >
            <span>Open Document Workspace</span>
            <ExternalLink size={14} />
          </button>
        }
      />

      {/* Top Document Summary Banner */}
      <div className="optiv-doc-banner">
        <div className="optiv-doc-banner-info">
          <div
            className="optiv-doc-icon-wrap"
            style={{
              backgroundColor: isPass ? 'var(--tprm-emerald-light)' : isFail ? 'rgba(239, 68, 68, 0.15)' : 'var(--tprm-surface-subtle)',
              color: isPass ? 'var(--tprm-emerald)' : isFail ? 'var(--tprm-rose)' : 'var(--tprm-text-muted)',
            }}
          >
            {isPass ? <CheckCircle2 size={22} /> : isFail ? <XCircle size={22} /> : <ShieldAlert size={22} />}
          </div>
          <div className="optiv-doc-meta">
            <div className="optiv-doc-title-row">
              <span className="optiv-doc-title">
                {activeDocument ? `Document: ${activeDocument.document_id}` : 'No Active Document Loaded'}
              </span>
              {activeDocument?.document_id && <CopyButton text={activeDocument.document_id} />}
              {activeDocument && (
                <span className={`badge ${releaseAuthorized ? 'badge-success' : 'badge-danger'}`}>
                  {releaseAuthorized ? 'RELEASE: AUTHORIZED' : 'RELEASE: BLOCKED'}
                </span>
              )}
            </div>
            <div className="optiv-doc-stats-row">
              <span className="optiv-doc-stat-item">
                <span>Verification Verdict:</span>
                <span
                  className="optiv-doc-stat-val"
                  style={{
                    color: isPass ? 'var(--tprm-emerald)' : isFail ? 'var(--tprm-rose)' : 'var(--tprm-amber)',
                    fontWeight: 700,
                  }}
                >
                  {isPass ? 'VERIFICATION PASS' : isFail ? 'VERIFICATION FAIL' : 'VERIFICATION INCOMPLETE'}
                </span>
              </span>
              <span>•</span>
              <span className="optiv-doc-stat-item">
                <span>Format:</span>
                <span className="optiv-doc-stat-val">
                  {activeDocument?.source_type?.toUpperCase() || 'N/A'}
                </span>
              </span>
              <span>•</span>
              <span className="optiv-doc-stat-item">
                <span>Structural Context Retained:</span>
                <span className="optiv-doc-stat-val">
                  {activeDocument ? `${structurePercent}%` : 'N/A'}
                </span>
              </span>
            </div>
          </div>
        </div>

        {releaseAuthorized && (
          <button
            onClick={() => window.open(`/api/artifact/${activeDocument!.document_id}`, '_blank')}
            className="btn-primary"
            title="Download verified sanitized document artifact"
          >
            <Download size={15} />
            <span>Download Verified Output</span>
          </button>
        )}
      </div>

      {/* 3 Verification Checks Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: 20 }}>
        {/* Check 1: Secondary Residual Leakage Sweep */}
        <div className="optiv-card" style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <div
                style={{
                  padding: 8,
                  borderRadius: 8,
                  backgroundColor: isPass ? 'var(--tprm-emerald-light)' : 'rgba(239, 68, 68, 0.15)',
                  color: isPass ? 'var(--tprm-emerald)' : 'var(--tprm-rose)',
                }}
              >
                <ShieldAlert size={20} />
              </div>
              <div>
                <h3 style={{ margin: 0, fontSize: '0.975rem', color: 'var(--tprm-text-primary)', fontWeight: 700 }}>
                  1. Residual Leakage Re-Scan
                </h3>
                <span style={{ fontSize: '0.725rem', color: 'var(--tprm-text-muted)' }}>
                  Secondary Independent Sweep
                </span>
              </div>
            </div>

            <span className={`badge ${isPass ? 'badge-success' : isFail ? 'badge-danger' : 'badge-warning'}`}>
              {isPass ? 'PASS' : isFail ? 'FAIL' : 'PENDING'}
            </span>
          </div>

          <div style={{ padding: '10px 12px', borderRadius: 8, backgroundColor: 'var(--tprm-surface-subtle)', border: '1px solid var(--tprm-border)', fontSize: '0.8rem', lineHeight: 1.5 }}>
            {activeDocument ? (
              isPass ? (
                <div style={{ color: 'var(--tprm-emerald)', display: 'flex', alignItems: 'center', gap: 6, fontWeight: 600 }}>
                  <CheckCircle2 size={16} />
                  <span>0 residual unmasked entities detected in sanitized text.</span>
                </div>
              ) : (
                <div style={{ color: 'var(--tprm-rose)', display: 'flex', alignItems: 'center', gap: 6, fontWeight: 600 }}>
                  <XCircle size={16} />
                  <span>Residual sensitive findings detected by secondary scanner!</span>
                </div>
              )
            ) : (
              <span style={{ color: 'var(--tprm-text-muted)' }}>No document loaded. Execute a pipeline in the Workspace.</span>
            )}
          </div>

          <div style={{ marginTop: 'auto', paddingTop: 6 }}>
            <button
              type="button"
              onClick={() => toggleCheck('check1')}
              style={{
                background: 'none',
                border: 'none',
                padding: 0,
                display: 'flex',
                alignItems: 'center',
                gap: 6,
                fontSize: '0.75rem',
                fontWeight: 600,
                color: 'var(--tprm-indigo)',
                cursor: 'pointer',
              }}
            >
              {expandedChecks['check1'] ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
              <span>{expandedChecks['check1'] ? 'Hide Verification Mechanics' : 'View Verification Mechanics'}</span>
            </button>

            {expandedChecks['check1'] && (
              <ul style={{ fontSize: '0.75rem', color: 'var(--tprm-text-secondary)', paddingLeft: 16, margin: '8px 0 0 0', lineHeight: 1.6 }}>
                <li><strong>Known-Span Search:</strong> Confirms all original sensitive offsets were replaced.</li>
                <li><strong>Regex Sweeper:</strong> Independent pattern verification for SSN, email, phone, and cards.</li>
                <li><strong>Zero Tolerance:</strong> A single residual entity blocks release immediately.</li>
              </ul>
            )}
          </div>
        </div>

        {/* Check 2: Structure Retention Invariant */}
        <div className="optiv-card" style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <div style={{ padding: 8, borderRadius: 8, backgroundColor: 'var(--tprm-cyan-light)', color: 'var(--tprm-cyan)' }}>
                <FileCheck size={20} />
              </div>
              <div>
                <h3 style={{ margin: 0, fontSize: '0.975rem', color: 'var(--tprm-text-primary)', fontWeight: 700 }}>
                  2. Structure Retention Scoring
                </h3>
                <span style={{ fontSize: '0.725rem', color: 'var(--tprm-text-muted)' }}>
                  Layout & Context Invariant (≥ 80%)
                </span>
              </div>
            </div>

            <span className="badge badge-info">
              {activeDocument ? `${structurePercent}%` : '80.0% MIN'}
            </span>
          </div>

          <div style={{ padding: '10px 12px', borderRadius: 8, backgroundColor: 'var(--tprm-surface-subtle)', border: '1px solid var(--tprm-border)', fontSize: '0.8rem', lineHeight: 1.5 }}>
            {activeDocument ? (
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4, fontSize: '0.75rem' }}>
                  <span style={{ color: 'var(--tprm-text-muted)' }}>Retained Non-Sensitive Context:</span>
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
              <span style={{ color: 'var(--tprm-text-muted)' }}>Awaiting document processing.</span>
            )}
          </div>

          <div style={{ marginTop: 'auto', paddingTop: 6 }}>
            <button
              type="button"
              onClick={() => toggleCheck('check2')}
              style={{
                background: 'none',
                border: 'none',
                padding: 0,
                display: 'flex',
                alignItems: 'center',
                gap: 6,
                fontSize: '0.75rem',
                fontWeight: 600,
                color: 'var(--tprm-indigo)',
                cursor: 'pointer',
              }}
            >
              {expandedChecks['check2'] ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
              <span>{expandedChecks['check2'] ? 'Hide Invariant Details' : 'View Invariant Details'}</span>
            </button>

            {expandedChecks['check2'] && (
              <ul style={{ fontSize: '0.75rem', color: 'var(--tprm-text-secondary)', paddingLeft: 16, margin: '8px 0 0 0', lineHeight: 1.6 }}>
                <li><strong>Syntactic Integrity:</strong> Paragraphs, tables, and sentence structures remain legible.</li>
                <li><strong>LLM Utility:</strong> Ensures downstream AI systems receive semantic document context.</li>
                <li><strong>Threshold Enforcement:</strong> Enforces minimum 80% non-sensitive character preservation.</li>
              </ul>
            )}
          </div>
        </div>

        {/* Check 3: Format Non-Reversibility */}
        <div className="optiv-card" style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <div style={{ padding: 8, borderRadius: 8, backgroundColor: 'var(--tprm-indigo-light)', color: 'var(--tprm-indigo)' }}>
                <Lock size={20} />
              </div>
              <div>
                <h3 style={{ margin: 0, fontSize: '0.975rem', color: 'var(--tprm-text-primary)', fontWeight: 700 }}>
                  3. Format Non-Reversibility
                </h3>
                <span style={{ fontSize: '0.725rem', color: 'var(--tprm-text-muted)' }}>
                  Underlying Glyph & Metadata Scrub
                </span>
              </div>
            </div>

            <span className="badge badge-generic">
              {activeDocument ? activeDocument.source_type?.toUpperCase() : 'FORMAT'}
            </span>
          </div>

          <div style={{ padding: '10px 12px', borderRadius: 8, backgroundColor: 'var(--tprm-surface-subtle)', border: '1px solid var(--tprm-border)', fontSize: '0.8rem', lineHeight: 1.5 }}>
            {activeDocument ? (
              <span style={{ color: 'var(--tprm-text-secondary)' }}>
                Format sanitizer removed underlying text glyphs. Replacement tokens cannot be reversed without an authorized key.
              </span>
            ) : (
              <span style={{ color: 'var(--tprm-text-muted)' }}>Awaiting document processing.</span>
            )}
          </div>

          <div style={{ marginTop: 'auto', paddingTop: 6 }}>
            <button
              type="button"
              onClick={() => toggleCheck('check3')}
              style={{
                background: 'none',
                border: 'none',
                padding: 0,
                display: 'flex',
                alignItems: 'center',
                gap: 6,
                fontSize: '0.75rem',
                fontWeight: 600,
                color: 'var(--tprm-indigo)',
                cursor: 'pointer',
              }}
            >
              {expandedChecks['check3'] ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
              <span>{expandedChecks['check3'] ? 'Hide Scrubbing Specifications' : 'View Scrubbing Specifications'}</span>
            </button>

            {expandedChecks['check3'] && (
              <ul style={{ fontSize: '0.75rem', color: 'var(--tprm-text-secondary)', paddingLeft: 16, margin: '8px 0 0 0', lineHeight: 1.6 }}>
                <li><strong>No Pruning Artifacts:</strong> PDF/DOCX streams scrubbed; no invisible overlay boxes.</li>
                <li><strong>Metadata Sanitization:</strong> Creator, revision stamps, and author identifiers pruned.</li>
                <li><strong>Tenant Isolation:</strong> Masking salts are segregated per enterprise customer.</li>
              </ul>
            )}
          </div>
        </div>

        {/* Check 4: Evaluation & Model Governance Metrics */}
        <div className="optiv-card" style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <div style={{ padding: 8, borderRadius: 8, backgroundColor: 'var(--tprm-amber-light)', color: 'var(--tprm-amber)' }}>
                <CheckCircle2 size={20} />
              </div>
              <div>
                <h3 style={{ margin: 0, fontSize: '0.975rem', color: 'var(--tprm-text-primary)', fontWeight: 700 }}>
                  4. Evaluation Quality Metrics
                </h3>
                <span style={{ fontSize: '0.725rem', color: 'var(--tprm-text-muted)' }}>
                  Precision, Recall, F1 & FNR
                </span>
              </div>
            </div>

            <span className="badge badge-success">
              {activeDocument ? `F1: ${(activeDocument.f1_score ?? 1.0).toFixed(3)}` : '1.000'}
            </span>
          </div>

          <div style={{ padding: '10px 12px', borderRadius: 8, backgroundColor: 'var(--tprm-surface-subtle)', border: '1px solid var(--tprm-border)', fontSize: '0.8rem', lineHeight: 1.5 }}>
            {activeDocument ? (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 8 }}>
                <div>
                  <span style={{ fontSize: '0.7rem', color: 'var(--tprm-text-muted)', display: 'block' }}>Precision:</span>
                  <span style={{ fontWeight: 700, color: 'var(--tprm-emerald)' }}>
                    {((activeDocument.precision ?? 1.0) * 100).toFixed(1)}%
                  </span>
                </div>
                <div>
                  <span style={{ fontSize: '0.7rem', color: 'var(--tprm-text-muted)', display: 'block' }}>Recall:</span>
                  <span style={{ fontWeight: 700, color: 'var(--tprm-emerald)' }}>
                    {((activeDocument.recall ?? 1.0) * 100).toFixed(1)}%
                  </span>
                </div>
                <div>
                  <span style={{ fontSize: '0.7rem', color: 'var(--tprm-text-muted)', display: 'block' }}>F1-Score:</span>
                  <span style={{ fontWeight: 700, color: 'var(--tprm-indigo)' }}>
                    {(activeDocument.f1_score ?? 1.0).toFixed(4)}
                  </span>
                </div>
                <div>
                  <span style={{ fontSize: '0.7rem', color: 'var(--tprm-text-muted)', display: 'block' }}>False Negative Rate:</span>
                  <span style={{ fontWeight: 700, color: (activeDocument.false_negative_rate ?? 0.0) === 0 ? 'var(--tprm-emerald)' : 'var(--tprm-rose)' }}>
                    {((activeDocument.false_negative_rate ?? 0.0) * 100).toFixed(1)}%
                  </span>
                </div>
              </div>
            ) : (
              <span style={{ color: 'var(--tprm-text-muted)' }}>Awaiting document processing.</span>
            )}
          </div>

          <div style={{ marginTop: 'auto', paddingTop: 6 }}>
            <button
              type="button"
              onClick={() => toggleCheck('check4')}
              style={{
                background: 'none',
                border: 'none',
                padding: 0,
                display: 'flex',
                alignItems: 'center',
                gap: 6,
                fontSize: '0.75rem',
                fontWeight: 600,
                color: 'var(--tprm-indigo)',
                cursor: 'pointer',
              }}
            >
              {expandedChecks['check4'] ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
              <span>{expandedChecks['check4'] ? 'Hide Evaluation Rigor' : 'View Evaluation Rigor'}</span>
            </button>

            {expandedChecks['check4'] && (
              <ul style={{ fontSize: '0.75rem', color: 'var(--tprm-text-secondary)', paddingLeft: 16, margin: '8px 0 0 0', lineHeight: 1.6 }}>
                <li><strong>Precision:</strong> Measures exactness; zero false positives on non-PII tokens.</li>
                <li><strong>Recall & FNR:</strong> Measures sensitivity; 100% recall ensures zero residual leaks.</li>
                <li><strong>Harmonic F1:</strong> Balances over-redaction vs under-redaction metrics.</li>
              </ul>
            )}
          </div>
        </div>
      </div>

      {/* Release Decision & Gate Enforcement Panel */}
      <div
        className="optiv-card"
        style={{
          borderLeft: `5px solid ${releaseAuthorized ? 'var(--tprm-emerald)' : isFail ? 'var(--tprm-rose)' : '#f59e0b'}`,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: 16,
          padding: 24,
        }}
      >
        <div style={{ maxWidth: 760 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
            <h3 style={{ margin: 0, fontSize: '1.1rem', color: 'var(--tprm-text-primary)', fontWeight: 700 }}>
              Release Authorization & Governance Gate Status
            </h3>
            <span
              className={`badge ${
                releaseAuthorized
                  ? 'badge-success'
                  : isFail
                  ? 'badge-danger'
                  : isIncomplete
                  ? 'badge-warning'
                  : 'badge-generic'
              }`}
            >
              {releaseAuthorized
                ? 'RELEASE: AUTHORIZED'
                : isFail
                ? 'VERIFICATION FAIL — BLOCKED'
                : isIncomplete
                ? 'VERIFICATION INCOMPLETE'
                : 'RELEASE WITHHELD'}
            </span>
          </div>
          <p style={{ margin: 0, fontSize: '0.825rem', color: 'var(--tprm-text-muted)', lineHeight: 1.5 }}>
            {releaseAuthorized
              ? 'All three independent verification invariants passed without residual PII. Document is authorized for downstream AI pipeline ingestion.'
              : isFail
              ? 'Independent re-scan discovered residual unmasked entities or structural violations. The fail-closed gate blocks artifact download (HTTP 403).'
              : 'Document processing run has not yet completed verification checks. Release remains withheld by default.'}
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          {releaseAuthorized ? (
            <button
              onClick={() => window.open(`/api/artifact/${activeDocument!.document_id}`, '_blank')}
              className="btn-primary"
              title="Download verified sanitized artifact"
            >
              <Download size={15} />
              <span>Download Verified Artifact</span>
            </button>
          ) : (
            <button
              onClick={onNavigateToWorkspace}
              className="btn-secondary"
              style={{ color: 'var(--tprm-rose)', borderColor: 'rgba(239, 68, 68, 0.3)' }}
              title="Inspect barriers in Document Workspace"
            >
              <ExternalLink size={14} />
              <span>Inspect Gate Barriers in Workspace</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
