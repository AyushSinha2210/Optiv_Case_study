import React from 'react';
import { CheckCircle2, ShieldAlert, AlertTriangle, FileCheck, Lock } from 'lucide-react';
import type { UserProfile } from '../../types';

interface VerificationViewProps {
  currentUser?: UserProfile;
  onNavigateToWorkspace: () => void;
}

export const VerificationView: React.FC<VerificationViewProps> = ({
  onNavigateToWorkspace,
}) => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      {/* Header */}
      <div className="optiv-card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 700, margin: 0, color: 'var(--tprm-text-primary)' }}>
            Stage 7: Independent Post-Redaction Verification Plane
          </h2>
          <p style={{ fontSize: '0.8rem', color: 'var(--tprm-text-muted)', margin: '4px 0 0' }}>
            Autonomous secondary scanner verifying that saved artifacts satisfy zero-leakage and layout integrity.
          </p>
        </div>

        <button
          onClick={onNavigateToWorkspace}
          className="btn-primary"
          style={{ fontSize: '0.8rem', padding: '6px 14px' }}
        >
          Test in Workspace
        </button>
      </div>

      {/* 3 Pillars of Independent Verification */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: 16 }}>
        {/* Pillar 1: Residual Leakage Re-Scan */}
        <div className="optiv-card" style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <div style={{ padding: 8, borderRadius: 8, backgroundColor: 'var(--tprm-emerald-light)' }}>
              <ShieldAlert size={20} color="var(--tprm-emerald)" />
            </div>
            <div>
              <h4 style={{ margin: 0, fontSize: '0.95rem', color: 'var(--tprm-text-primary)' }}>
                1. Zero Residual Leakage Re-Scan
              </h4>
              <span style={{ fontSize: '0.7rem', color: 'var(--tprm-text-muted)' }}>Mandatory Check • Fail-Closed</span>
            </div>
          </div>

          <p style={{ fontSize: '0.75rem', color: 'var(--tprm-text-muted)', lineHeight: 1.5, margin: 0 }}>
            The verification engine reopens the actual saved artifact from sandbox storage and executes an autonomous secondary scan completely decoupled from the original detector:
          </p>

          <ul style={{ fontSize: '0.75rem', color: 'var(--tprm-text-secondary)', paddingLeft: 16, margin: 0, lineHeight: 1.6 }}>
            <li><strong>Known Value Search:</strong> Verifies that every sensitive value detected in Stage 4 is absent from the output text.</li>
            <li><strong>Independent Pattern Scanner:</strong> Executes fresh regex checks for SSNs, phone numbers, credit cards, emails, and IP addresses.</li>
            <li><strong>Outcome:</strong> If a single residual leak is found, status evaluates to <code>FAIL</code> and release is immediately blocked.</li>
          </ul>
        </div>

        {/* Pillar 2: 80% Structure Retention Scoring */}
        <div className="optiv-card" style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <div style={{ padding: 8, borderRadius: 8, backgroundColor: 'var(--tprm-cyan-light)' }}>
              <FileCheck size={20} color="var(--tprm-cyan)" />
            </div>
            <div>
              <h4 style={{ margin: 0, fontSize: '0.95rem', color: 'var(--tprm-text-primary)' }}>
                2. Structure Retention Scoring (&gt;= 80%)
              </h4>
              <span style={{ fontSize: '0.7rem', color: 'var(--tprm-text-muted)' }}>Case Study Invariant • Context Preservation</span>
            </div>
          </div>

          <p style={{ fontSize: '0.75rem', color: 'var(--tprm-text-muted)', lineHeight: 1.5, margin: 0 }}>
            Under the Optiv Case Study specification, redacted text must retain no less than 80% of its original layout structure:
          </p>

          <ul style={{ fontSize: '0.75rem', color: 'var(--tprm-text-secondary)', paddingLeft: 16, margin: 0, lineHeight: 1.6 }}>
            <li><strong>Paragraph & Heading Retention:</strong> Line feeds, section titles, and markdown structure are verified.</li>
            <li><strong>Preceding Context:</strong> Surrounding sentences and explanatory clauses remain intact so AI models can review business evidence.</li>
            <li><strong>Threshold Enforcement:</strong> Score below 0.80 flags <code>FAIL</code> on layout verification.</li>
          </ul>
        </div>

        {/* Pillar 3: Format Non-Reversibility */}
        <div className="optiv-card" style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <div style={{ padding: 8, borderRadius: 8, backgroundColor: 'var(--tprm-indigo-light)' }}>
              <Lock size={20} color="var(--tprm-indigo)" />
            </div>
            <div>
              <h4 style={{ margin: 0, fontSize: '0.95rem', color: 'var(--tprm-text-primary)' }}>
                3. Non-Reversibility & Content Stream Scrub
              </h4>
              <span style={{ fontSize: '0.7rem', color: 'var(--tprm-text-muted)' }}>Cryptographic & Document Security</span>
            </div>
          </div>

          <p style={{ fontSize: '0.75rem', color: 'var(--tprm-text-muted)', lineHeight: 1.5, margin: 0 }}>
            Verifies that sensitive data cannot be recovered by inspecting underlying content streams:
          </p>

          <ul style={{ fontSize: '0.75rem', color: 'var(--tprm-text-secondary)', paddingLeft: 16, margin: 0, lineHeight: 1.6 }}>
            <li><strong>PDF Vector Redaction:</strong> Drawing a black visual box is prohibited; underlying text glyphs must be removed from the PDF stream.</li>
            <li><strong>Metadata Scrubbing:</strong> Author, creation date, and hidden comment fields are inspected and sanitized.</li>
            <li><strong>JSON Schema Integrity:</strong> Redacted JSON outputs must remain valid, well-formed JSON documents.</li>
          </ul>
        </div>
      </div>

      {/* Dual-Key Release Barrier Diagram */}
      <div className="optiv-card">
        <h3 style={{ fontSize: '1rem', fontWeight: 700, margin: '0 0 12px', color: 'var(--tprm-text-primary)' }}>
          Dual-Key Release Barrier Decision Logic
        </h3>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 16 }}>
          <div style={{ padding: 14, borderRadius: 8, backgroundColor: 'rgba(16, 185, 129, 0.08)', border: '1px solid var(--tprm-emerald)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
              <CheckCircle2 size={18} color="var(--tprm-emerald)" />
              <span style={{ fontWeight: 700, fontSize: '0.85rem', color: 'var(--tprm-text-primary)' }}>
                Release Authorized (PASS)
              </span>
            </div>
            <p style={{ fontSize: '0.75rem', color: 'var(--tprm-text-muted)', margin: 0, lineHeight: 1.4 }}>
              Requires: (1) <code>verification_status == 'PASS'</code> AND (2) <code>release_allowed == true</code>. The opaque artifact reference token is validated and client download is unlocked.
            </p>
          </div>

          <div style={{ padding: 14, borderRadius: 8, backgroundColor: 'rgba(239, 68, 68, 0.08)', border: '1px solid var(--tprm-rose)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
              <AlertTriangle size={18} color="var(--tprm-rose)" />
              <span style={{ fontWeight: 700, fontSize: '0.85rem', color: 'var(--tprm-text-primary)' }}>
                Release Blocked (FAIL / INCOMPLETE)
              </span>
            </div>
            <p style={{ fontSize: '0.75rem', color: 'var(--tprm-text-muted)', margin: 0, lineHeight: 1.4 }}>
              If residual PII is detected, extraction failed, or verification checks were interrupted, the artifact reference token is invalidated. Download attempts return HTTP 403 Forbidden.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
