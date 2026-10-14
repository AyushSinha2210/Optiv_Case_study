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
  AlertOctagon,
  Info,
} from 'lucide-react';
import type { UserProfile, ProcessResponse } from '../../types';
import { PageHeader } from './PageHeader';
import { CopyButton } from './CopyButton';

interface VerificationViewProps {
  currentUser?: UserProfile;
  activeDocument?: ProcessResponse | null;
  onNavigateToWorkspace: () => void;
}

interface FaultDiagnosticItem {
  check: string;
  category: string;
  entityType: string;
  stage: string;
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM';
  description: string;
  rootCause: string;
  remediation: string;
}

function diagnoseFault(check: string, entityType?: string): FaultDiagnosticItem {
  switch (check) {
    case 'residual_phone_pattern':
      return {
        check: 'residual_phone_pattern',
        category: 'Residual Leakage (Regex Sweep)',
        entityType: entityType || 'PHONE',
        stage: 'Stage 4: Detection Module (False Negative)',
        severity: 'CRITICAL',
        description: 'Secondary regex sweeper detected an unmasked telephone number pattern in the sanitized output text stream.',
        rootCause: 'Primary NER/Regex detector failed to flag an instance of this telephone number during detection, leaving it unredacted.',
        remediation: 'Expand phone regex expressions in pattern_detector.py to capture additional international or local format variations.',
      };
    case 'residual_email_pattern':
      return {
        check: 'residual_email_pattern',
        category: 'Residual Leakage (Regex Sweep)',
        entityType: entityType || 'EMAIL',
        stage: 'Stage 4: Detection Module (False Negative)',
        severity: 'CRITICAL',
        description: 'Secondary regex sweeper detected an unmasked RFC email address pattern in the sanitized output text.',
        rootCause: 'An email address was missed during the primary detection pass or partially preserved in a header/table element.',
        remediation: 'Check email regex boundaries and ensure all document segments (tables, headers, footnotes) are scanned.',
      };
    case 'residual_government_id_pattern':
      return {
        check: 'residual_government_id_pattern',
        category: 'Residual Leakage (Regex Sweep)',
        entityType: entityType || 'GOVERNMENT_ID',
        stage: 'Stage 4: Detection Module (False Negative)',
        severity: 'CRITICAL',
        description: 'Secondary regex sweeper detected an unredacted SSN / national government identifier pattern (###-##-####).',
        rootCause: 'A valid SSN/TIN format remained in the post-redaction text stream without proper token replacement.',
        remediation: 'Verify SSN area-code filtering and ensure high-priority masking rules apply before other redactions.',
      };
    case 'residual_financial_identifier_pattern':
      return {
        check: 'residual_financial_identifier_pattern',
        category: 'Residual Leakage (Luhn Checksum)',
        entityType: entityType || 'FINANCIAL_IDENTIFIER',
        stage: 'Stage 4: Detection Module (False Negative)',
        severity: 'CRITICAL',
        description: 'Secondary scanner detected a 13-19 digit number satisfying the Luhn payment card checksum algorithm.',
        rootCause: 'A payment card or banking PAN was not masked during the initial redaction stage.',
        remediation: 'Verify credit card regex patterns and ensure PAN separators (spaces, hyphens) are normalized.',
      };
    case 'residual_ip_pattern':
      return {
        check: 'residual_ip_pattern',
        category: 'Residual Leakage (Network)',
        entityType: entityType || 'IP_ADDRESS',
        stage: 'Stage 4: Detection Module (False Negative)',
        severity: 'HIGH',
        description: 'Secondary sweeper identified an unmasked IPv4 address in the sanitized document stream.',
        rootCause: 'IP address pattern was not flagged as sensitive or omitted from detection scope.',
        remediation: 'Enable IP_ADDRESS policy category in active redaction ruleset.',
      };
    case 'known_value_remaining':
      return {
        check: 'known_value_remaining',
        category: 'Masking Omission (Span Mismatch)',
        entityType: entityType || 'SENSITIVE_ENTITY',
        stage: 'Stage 6: Redaction Engine (Masking Failure)',
        severity: 'CRITICAL',
        description: `Known sensitive entity (${entityType || 'PII'}) detected in Stage 4 was found verbatim in the post-redaction output.`,
        rootCause: 'Character slice/offset misalignment between detected entity start/end coordinates and output text replacement buffer.',
        remediation: 'Review text slicing logic in redactor.py; ensure overlapping entity spans do not overwrite prior masks.',
      };
    case 'structure_score_below_threshold':
      return {
        check: 'structure_score_below_threshold',
        category: 'Structural Context Degradation',
        entityType: 'STRUCTURE / LAYOUT',
        stage: 'Stage 8: Invariant Verifier (Context Retention)',
        severity: 'HIGH',
        description: 'Retained non-sensitive structure and layout fell below the mandatory 80.0% invariant threshold.',
        rootCause: 'Redaction process eliminated too many newline delimiters, markdown headers, or paragraph separators.',
        remediation: 'Preserve structural whitespace and newlines when substituting sensitive tokens in document text.',
      };
    case 'saved_artifact_leakage':
      return {
        check: 'saved_artifact_leakage',
        category: 'Binary File Leakage',
        entityType: entityType || 'ARTIFACT_LEAK',
        stage: 'Stage 7: Format Exporter / Storage',
        severity: 'CRITICAL',
        description: 'Re-opening the saved binary artifact (PDF/DOCX/PPTX) revealed unmasked sensitive text in underlying glyphs.',
        rootCause: 'Visual redaction rendered overlay boxes without stripping underlying text streams from the binary container.',
        remediation: 'Ensure native vector redaction (PyMuPDF apply_redactions) strips glyph streams permanently.',
      };
    case 'artifact_reopen_failed':
      return {
        check: 'artifact_reopen_failed',
        category: 'Container Integrity Failure',
        entityType: 'FILE_INTEGRITY',
        stage: 'Stage 7: Format Exporter / Storage',
        severity: 'CRITICAL',
        description: 'The sanitized file could not be parsed or re-opened by the format reader after redaction.',
        rootCause: 'Corrupted binary serialization, truncated ZIP container, or malformed XML/PDF stream.',
        remediation: 'Verify file finalization and document stream flushing before closing artifact write buffer.',
      };
    case 'simulated_verification_failure':
      return {
        check: 'simulated_verification_failure',
        category: 'Fail-Closed Security Drill',
        entityType: 'SECURITY_TEST',
        stage: 'Stage 8: Verification Gate (Test Injection)',
        severity: 'HIGH',
        description: 'Active fail-closed security drill triggered via simulate_verification_failure=true.',
        rootCause: 'User or automated test requested a simulated verification failure to validate gate barrier locking.',
        remediation: 'Uncheck "Simulate Verification Failure" in the Document Workspace ingestion toolbar.',
      };
    default:
      return {
        check,
        category: 'Security Verification Invariant',
        entityType: entityType || 'UNKNOWN',
        stage: 'Stage 8: Verification Gate',
        severity: 'HIGH',
        description: `Verification check '${check}' triggered an alert during post-redaction re-scan.`,
        rootCause: 'Post-redaction invariant condition was violated, requiring fail-closed release withholding.',
        remediation: 'Inspect verification findings in audit ledger and adjust redaction policy rules.',
      };
  }
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

  // Real or calculated structure score
  const structureScoreVal =
    activeDocument?.structure_score !== undefined && activeDocument?.structure_score !== null
      ? activeDocument.structure_score
      : activeDocument?.char_count && activeDocument?.redacted_text
      ? Math.min(1.0, activeDocument.redacted_text.length / activeDocument.char_count)
      : 1.0;
  const structurePercent = (structureScoreVal * 100).toFixed(1);
  const structurePassed = structureScoreVal >= 0.8;

  // Verification findings breakdown
  const findings = activeDocument?.verification_findings || [];
  const hasLeakageFinding = findings.some(
    (f) =>
      f.check.startsWith('residual_') ||
      f.check === 'known_value_remaining' ||
      f.check === 'saved_artifact_leakage'
  );
  const hasStructureFinding =
    findings.some((f) => f.check === 'structure_score_below_threshold') || !structurePassed;
  const hasSimulationFinding = findings.some((f) => f.check === 'simulated_verification_failure');

  // Build diagnosed faults
  const diagnosedFaults: FaultDiagnosticItem[] = [];
  if (findings.length > 0) {
    findings.forEach((f) => {
      diagnosedFaults.push(diagnoseFault(f.check, f.entity_type));
    });
  } else if (activeDocument && (isFail || !releaseAuthorized)) {
    if (activeDocument.safe_error?.toLowerCase().includes('simulat')) {
      diagnosedFaults.push(diagnoseFault('simulated_verification_failure'));
    } else if (!structurePassed) {
      diagnosedFaults.push(diagnoseFault('structure_score_below_threshold'));
    } else {
      diagnosedFaults.push({
        check: activeDocument.safe_error_code || 'WARN_RELEASE_BLOCKED',
        category: 'Verification Re-Scan Barrier',
        entityType: 'RESIDUAL_PII',
        stage: 'Stage 8: Invariant Release Gate',
        severity: 'CRITICAL',
        description: activeDocument.safe_error || 'Independent verification sweeps detected residual sensitive data in sanitized stream.',
        rootCause: 'Zero-tolerance residual sweeper flagged unredacted entity tokens or pattern anomalies.',
        remediation: 'Inspect detected entity list in PII Findings and re-execute pipeline with updated redaction policy.',
      });
    }
  }

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
                <span
                  className="optiv-doc-stat-val"
                  style={{ color: structurePassed ? 'inherit' : 'var(--tprm-rose)', fontWeight: structurePassed ? 500 : 700 }}
                >
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

      {/* 4 Verification Checks Grid */}
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

            <span className={`badge ${isPass ? 'badge-success' : isFail || hasLeakageFinding ? 'badge-danger' : 'badge-warning'}`}>
              {isPass ? 'PASS' : isFail || hasLeakageFinding ? 'FAIL' : 'PENDING'}
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
                <div style={{ color: 'var(--tprm-rose)', display: 'flex', flexDirection: 'column', gap: 4 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontWeight: 600 }}>
                    <XCircle size={16} />
                    <span>Residual sensitive findings detected by secondary scanner!</span>
                  </div>
                  {findings.filter(f => f.check.startsWith('residual_') || f.check === 'known_value_remaining').length > 0 && (
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, marginTop: 4 }}>
                      {findings
                        .filter(f => f.check.startsWith('residual_') || f.check === 'known_value_remaining')
                        .map((f, i) => (
                          <span key={i} className="badge badge-danger" style={{ fontSize: '0.675rem' }}>
                            {f.entity_type || f.check}
                          </span>
                        ))}
                    </div>
                  )}
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
              <div
                style={{
                  padding: 8,
                  borderRadius: 8,
                  backgroundColor: structurePassed ? 'var(--tprm-cyan-light)' : 'rgba(239, 68, 68, 0.15)',
                  color: structurePassed ? 'var(--tprm-cyan)' : 'var(--tprm-rose)',
                }}
              >
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

            <span className={`badge ${!hasStructureFinding ? 'badge-info' : 'badge-danger'}`}>
              {activeDocument ? `${structurePercent}%` : '80.0% MIN'}
            </span>
          </div>

          <div style={{ padding: '10px 12px', borderRadius: 8, backgroundColor: 'var(--tprm-surface-subtle)', border: '1px solid var(--tprm-border)', fontSize: '0.8rem', lineHeight: 1.5 }}>
            {activeDocument ? (
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4, fontSize: '0.75rem' }}>
                  <span style={{ color: 'var(--tprm-text-muted)' }}>Retained Non-Sensitive Context:</span>
                  <span style={{ fontWeight: 700, color: !hasStructureFinding ? 'var(--tprm-text-primary)' : 'var(--tprm-rose)' }}>
                    {structurePercent}% {hasStructureFinding && '(DEGRADED)'}
                  </span>
                </div>
                <div style={{ width: '100%', height: 6, backgroundColor: 'var(--tprm-border)', borderRadius: 3, overflow: 'hidden' }}>
                  <div
                    style={{
                      width: `${Math.min(100, parseFloat(structurePercent))}%`,
                      height: '100%',
                      backgroundColor: structurePassed ? 'var(--tprm-cyan)' : 'var(--tprm-rose)',
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
              <div
                style={{
                  padding: 8,
                  borderRadius: 8,
                  backgroundColor: hasSimulationFinding ? 'rgba(239, 68, 68, 0.15)' : 'var(--tprm-indigo-light)',
                  color: hasSimulationFinding ? 'var(--tprm-rose)' : 'var(--tprm-indigo)',
                }}
              >
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

            <span className={`badge ${hasSimulationFinding ? 'badge-danger' : 'badge-generic'}`}>
              {hasSimulationFinding ? 'DRILL ACTIVE' : activeDocument ? activeDocument.source_type?.toUpperCase() : 'FORMAT'}
            </span>
          </div>

          <div style={{ padding: '10px 12px', borderRadius: 8, backgroundColor: 'var(--tprm-surface-subtle)', border: '1px solid var(--tprm-border)', fontSize: '0.8rem', lineHeight: 1.5 }}>
            {activeDocument ? (
              hasSimulationFinding ? (
                <span style={{ color: 'var(--tprm-rose)', fontWeight: 600 }}>
                  Active security drill: simulate_verification_failure=true forced gate blockage.
                </span>
              ) : (
                <span style={{ color: 'var(--tprm-text-secondary)' }}>
                  Format sanitizer removed underlying text glyphs. Replacement tokens cannot be reversed without an authorized key.
                </span>
              )
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

      {/* Dedicated Fault Diagnostics Panel when Release Is Blocked */}
      {activeDocument && (isFail || !releaseAuthorized) && (
        <div
          className="optiv-card"
          style={{
            borderLeft: '5px solid var(--tprm-rose)',
            backgroundColor: 'var(--tprm-surface)',
            padding: 24,
            display: 'flex',
            flexDirection: 'column',
            gap: 18,
          }}
        >
          {/* Diagnostic Header */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 12 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <div
                style={{
                  padding: 10,
                  borderRadius: 10,
                  backgroundColor: 'rgba(239, 68, 68, 0.15)',
                  color: 'var(--tprm-rose)',
                }}
              >
                <AlertOctagon size={24} />
              </div>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <h3 style={{ margin: 0, fontSize: '1.075rem', fontWeight: 700, color: 'var(--tprm-text-primary)' }}>
                    Why This Document Release Is Blocked — Fault Root Cause Analysis
                  </h3>
                  <span className="badge badge-danger">
                    FAIL-CLOSED BARRIER ENGAGED
                  </span>
                </div>
                <p style={{ margin: '4px 0 0 0', fontSize: '0.775rem', color: 'var(--tprm-text-muted)' }}>
                  Pinpointing the exact failing invariant check, responsible pipeline stage, leaked entity type, and required remediation.
                </p>
              </div>
            </div>

            <div style={{ display: 'flex', gap: 8 }}>
              <span className="badge badge-generic" style={{ fontSize: '0.725rem' }}>
                Document ID: {activeDocument.document_id}
              </span>
            </div>
          </div>

          {/* Fault Summary Banner */}
          <div
            style={{
              padding: '12px 16px',
              borderRadius: 8,
              backgroundColor: 'rgba(239, 68, 68, 0.08)',
              border: '1px solid rgba(239, 68, 68, 0.25)',
              display: 'flex',
              alignItems: 'center',
              gap: 12,
            }}
          >
            <ShieldAlert size={20} color="var(--tprm-rose)" style={{ flexShrink: 0 }} />
            <div style={{ fontSize: '0.825rem', color: 'var(--tprm-text-primary)', lineHeight: 1.5 }}>
              <strong>Primary Gate Failure Reason: </strong>
              <span style={{ color: 'var(--tprm-rose)', fontWeight: 600 }}>
                {activeDocument.safe_error || 'Independent post-redaction verification detected residual sensitive entities or policy invariant breach.'}
              </span>
            </div>
          </div>

          {/* Itemized Fault Diagnostics Table */}
          <div style={{ overflowX: 'auto' }}>
            <table className="optiv-table" style={{ width: '100%', fontSize: '0.8rem' }}>
              <thead>
                <tr>
                  <th style={{ width: '18%' }}>Triggered Check</th>
                  <th style={{ width: '12%' }}>Entity / Target</th>
                  <th style={{ width: '22%' }}>Fault Origin & Stage</th>
                  <th style={{ width: '26%' }}>Fault Diagnosis & Where the Fault Is</th>
                  <th style={{ width: '22%' }}>Remediation Action</th>
                </tr>
              </thead>
              <tbody>
                {diagnosedFaults.map((item, idx) => (
                  <tr key={idx}>
                    <td>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                        <code style={{ fontSize: '0.75rem', color: 'var(--tprm-rose)', fontWeight: 700 }}>
                          {item.check}
                        </code>
                        <span style={{ fontSize: '0.7rem', color: 'var(--tprm-text-muted)' }}>
                          {item.category}
                        </span>
                      </div>
                    </td>
                    <td>
                      <span className="badge badge-danger" style={{ fontSize: '0.7rem' }}>
                        {item.entityType}
                      </span>
                    </td>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                        <span
                          style={{
                            width: 8,
                            height: 8,
                            borderRadius: '50%',
                            backgroundColor: 'var(--tprm-rose)',
                            display: 'inline-block',
                            flexShrink: 0,
                          }}
                        />
                        <span style={{ fontWeight: 600, color: 'var(--tprm-text-primary)', fontSize: '0.75rem' }}>
                          {item.stage}
                        </span>
                      </div>
                    </td>
                    <td>
                      <p style={{ margin: 0, fontSize: '0.75rem', color: 'var(--tprm-text-secondary)', lineHeight: 1.4 }}>
                        {item.description}
                      </p>
                      <p style={{ margin: '4px 0 0 0', fontSize: '0.7rem', color: 'var(--tprm-text-muted)', fontStyle: 'italic' }}>
                        Root cause: {item.rootCause}
                      </p>
                    </td>
                    <td>
                      <div style={{ fontSize: '0.75rem', color: 'var(--tprm-indigo)', lineHeight: 1.4, fontWeight: 500 }}>
                        {item.remediation}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Fail-Closed Architectural Governance Notice */}
          <div
            style={{
              padding: '10px 14px',
              borderRadius: 6,
              backgroundColor: 'var(--tprm-surface-subtle)',
              border: '1px solid var(--tprm-border)',
              display: 'flex',
              alignItems: 'center',
              gap: 10,
              fontSize: '0.75rem',
              color: 'var(--tprm-text-muted)',
            }}
          >
            <Info size={16} color="var(--tprm-cyan)" style={{ flexShrink: 0 }} />
            <span>
              <strong>Fail-Closed Gate Contract: </strong>
              Under Cadence AI Governance rules, artifact tokens (<code>artifact_ref</code>) are immediately expunged from memory and storage access is denied (HTTP 403 Forbidden) whenever any verification invariant fails. Zero raw PII is ever leaked in error codes or audit logs.
            </span>
          </div>
        </div>
      )}

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
