import React, { useState, useMemo } from 'react';
import {
  CheckCircle2,
  ExternalLink,
  Filter,
  Sparkles,
  Layers,
} from 'lucide-react';
import type { UserProfile, ProcessResponse } from '../../types';

interface RedactionReviewViewProps {
  currentUser?: UserProfile;
  activeDocument?: ProcessResponse | null;
  onNavigateToWorkspace: () => void;
}

export const RedactionReviewView: React.FC<RedactionReviewViewProps> = ({
  activeDocument,
  onNavigateToWorkspace,
}) => {
  const [filterMode, setFilterMode] = useState<'ALL' | 'TRIGGERED' | 'CRITICAL'>('ALL');

  const basePolicies = [
    {
      category: 'GOVERNMENT_ID',
      label: 'Government-Issued Identifiers (SSN, Aadhaar, PAN)',
      technique: 'Deterministic Token Replacement',
      mask: '[REDACTED_GOVERNMENT_ID]',
      rationale: 'Zero tolerance under GLBA / Privacy Act; glyphs eliminated permanently.',
      risk: 'CRITICAL',
      regulatoryMandate: 'GLBA §501(b) / Privacy Act 1974',
    },
    {
      category: 'FINANCIAL_IDENTIFIER',
      label: 'Financial & Card Accounts (Credit Cards, Bank Accounts)',
      technique: 'Luhn-Validated Token Substitution',
      mask: '[REDACTED_FINANCIAL_IDENTIFIER]',
      rationale: 'PCI-DSS DSS 3.4 mandate; no partial card numbers permitted in LLM context.',
      risk: 'CRITICAL',
      regulatoryMandate: 'PCI-DSS Req 3.4 / FTC Safeguards',
    },
    {
      category: 'EMAIL',
      label: 'Email Addresses (Corporate & Personal)',
      technique: 'Contextual Semantic Token',
      mask: '[REDACTED_EMAIL]',
      rationale: 'Prevents direct phishing or contact harvesting by downstream models.',
      risk: 'HIGH',
      regulatoryMandate: 'CAN-SPAM / GDPR Art. 6',
    },
    {
      category: 'PHONE',
      label: 'Telephone Numbers (National & International E.164)',
      technique: 'Contextual Semantic Token',
      mask: '[REDACTED_PHONE]',
      rationale: 'Protects customer and employee direct dial numbers from prompt leakage.',
      risk: 'HIGH',
      regulatoryMandate: 'TCPA / GDPR Art. 5',
    },
    {
      category: 'PERSON',
      label: 'Personal Names (Customer, Executive, Officer)',
      technique: 'Entity Replacement Token',
      mask: '[REDACTED_PERSON]',
      rationale: 'Mitigates privacy exposure in case summaries and credit memos.',
      risk: 'MEDIUM',
      regulatoryMandate: 'CCPA / CPRA §1798.140',
    },
    {
      category: 'IP_ADDRESS',
      label: 'IP Addresses (IPv4 & IPv6)',
      technique: 'Network Token Masking',
      mask: '[REDACTED_IP_ADDRESS]',
      rationale: 'Prevents internal network topology disclosure to external LLMs.',
      risk: 'MEDIUM',
      regulatoryMandate: 'NIST SP 800-53 SC-7',
    },
    {
      category: 'EMPLOYEE_ID',
      label: 'Employee Corporate Identifiers',
      technique: 'Internal Identifier Masking',
      mask: '[REDACTED_EMPLOYEE_ID]',
      rationale: 'Eliminates internal badge and staff correlation tokens.',
      risk: 'MEDIUM',
      regulatoryMandate: 'Cadence Enterprise Security Policy',
    },
  ];

  // Map active document findings to policies
  const policyEvaluations = useMemo(() => {
    const entities = activeDocument?.entities || [];

    return basePolicies.map((p) => {
      const matches = entities.filter(
        (e) => (e.type || '').toUpperCase() === p.category
      );
      return {
        ...p,
        matches,
        isTriggered: matches.length > 0,
        count: matches.length,
      };
    });
  }, [activeDocument]);

  const triggeredCount = policyEvaluations.filter((p) => p.isTriggered).length;

  const displayedPolicies = useMemo(() => {
    if (filterMode === 'TRIGGERED') {
      return policyEvaluations.filter((p) => p.isTriggered);
    }
    if (filterMode === 'CRITICAL') {
      return policyEvaluations.filter((p) => p.risk === 'CRITICAL');
    }
    return policyEvaluations;
  }, [policyEvaluations, filterMode]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      {/* Active Document Context Header */}
      <div className="optiv-doc-banner">
        <div className="optiv-doc-banner-info">
          <div className="optiv-doc-icon-wrap" style={{ backgroundColor: 'rgba(99, 102, 241, 0.15)', color: 'var(--tprm-indigo)' }}>
            <Layers size={22} />
          </div>
          <div className="optiv-doc-meta">
            <div className="optiv-doc-title-row">
              <span className="optiv-doc-title">
                {activeDocument
                  ? `Policy Evaluation for: ${activeDocument.document_id ? activeDocument.document_id.slice(0, 18) : 'Doc'}... (${activeDocument.source_type?.toUpperCase() || 'DOCUMENT'})`
                  : 'Enterprise Policy & Masking Taxonomy'}
              </span>
              {activeDocument && (
                <span className={`badge ${activeDocument.release_allowed ? 'badge-success' : 'badge-danger'}`}>
                  {activeDocument.release_allowed ? 'Zero-Leakage PASS' : 'Gate BLOCKED'}
                </span>
              )}
            </div>
            <div className="optiv-doc-stats-row">
              <span className="optiv-doc-stat-item">
                <span>Policies Evaluated:</span>
                <span className="optiv-doc-stat-val">7 Mandates</span>
              </span>
              <span>•</span>
              <span className="optiv-doc-stat-item">
                <span>Triggered in Document:</span>
                <span className="optiv-doc-stat-val" style={{ color: triggeredCount > 0 ? 'var(--tprm-cyan)' : 'inherit' }}>
                  {triggeredCount} Categories
                </span>
              </span>
              <span>•</span>
              <span className="optiv-doc-stat-item">
                <span>Total Redactions Applied:</span>
                <span className="optiv-doc-stat-val">
                  {activeDocument?.redactions_applied ?? 0}
                </span>
              </span>
            </div>
          </div>
        </div>

        <button
          onClick={onNavigateToWorkspace}
          className="btn-primary"
          style={{ fontSize: '0.8rem', padding: '7px 14px', display: 'flex', alignItems: 'center', gap: 6 }}
        >
          <ExternalLink size={14} />
          <span>Open Document Workspace</span>
        </button>
      </div>

      {/* Filter Tabs */}
      <div className="optiv-card" style={{ padding: '12px 18px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 10 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <Filter size={15} color="var(--tprm-text-muted)" />
          <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--tprm-text-muted)' }}>Filter Policies:</span>
          
          <button
            onClick={() => setFilterMode('ALL')}
            className={`optiv-btn-header ${filterMode === 'ALL' ? 'active' : ''}`}
            style={{
              backgroundColor: filterMode === 'ALL' ? 'var(--tprm-indigo-light)' : 'transparent',
              color: filterMode === 'ALL' ? 'var(--tprm-indigo)' : 'var(--tprm-text-primary)',
              borderColor: filterMode === 'ALL' ? 'rgba(99, 102, 241, 0.4)' : 'var(--tprm-border)',
            }}
          >
            All Policies (7)
          </button>
          
          <button
            onClick={() => setFilterMode('TRIGGERED')}
            className={`optiv-btn-header ${filterMode === 'TRIGGERED' ? 'active' : ''}`}
            style={{
              backgroundColor: filterMode === 'TRIGGERED' ? 'rgba(16, 185, 129, 0.15)' : 'transparent',
              color: filterMode === 'TRIGGERED' ? 'var(--tprm-emerald)' : 'var(--tprm-text-primary)',
              borderColor: filterMode === 'TRIGGERED' ? 'rgba(16, 185, 129, 0.4)' : 'var(--tprm-border)',
            }}
          >
            Triggered in Given Document ({triggeredCount})
          </button>

          <button
            onClick={() => setFilterMode('CRITICAL')}
            className={`optiv-btn-header ${filterMode === 'CRITICAL' ? 'active' : ''}`}
            style={{
              backgroundColor: filterMode === 'CRITICAL' ? 'rgba(239, 68, 68, 0.15)' : 'transparent',
              color: filterMode === 'CRITICAL' ? 'var(--tprm-rose)' : 'var(--tprm-text-primary)',
              borderColor: filterMode === 'CRITICAL' ? 'rgba(239, 68, 68, 0.4)' : 'var(--tprm-border)',
            }}
          >
            Critical Risk (2)
          </button>
        </div>

        {activeDocument && (
          <span style={{ fontSize: '0.75rem', color: 'var(--tprm-text-muted)' }}>
            Inspecting live document: <strong style={{ color: 'var(--tprm-text-primary)' }}>{activeDocument.document_id ? activeDocument.document_id.slice(0, 16) : 'Doc'}...</strong>
          </span>
        )}
      </div>

      {/* Dynamic Policy Cards Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: 16 }}>
        {displayedPolicies.map((p, idx) => (
          <div
            key={idx}
            className={`optiv-policy-card ${p.isTriggered ? 'triggered' : 'inactive'}`}
          >
            {/* Card Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <span className="badge badge-generic" style={{ fontWeight: 700 }}>
                  {p.category}
                </span>
                {p.isTriggered ? (
                  <span className="badge badge-success" style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                    <CheckCircle2 size={12} />
                    <span>Triggered in Document ({p.count})</span>
                  </span>
                ) : (
                  <span className="badge" style={{ backgroundColor: 'var(--tprm-surface-subtle)', color: 'var(--tprm-text-muted)', border: '1px solid var(--tprm-border)' }}>
                    Not in Current Document
                  </span>
                )}
              </div>

              <span className={`badge ${p.risk === 'CRITICAL' ? 'badge-danger' : p.risk === 'HIGH' ? 'badge-warning' : 'badge-info'}`}>
                {p.risk} RISK
              </span>
            </div>

            {/* Title & Regulatory Mandate */}
            <div>
              <h4 style={{ margin: 0, fontSize: '0.95rem', color: 'var(--tprm-text-primary)', fontWeight: 600 }}>
                {p.label}
              </h4>
              <div style={{ fontSize: '0.7rem', color: 'var(--tprm-text-muted)', marginTop: 2 }}>
                Mandate: {p.regulatoryMandate}
              </div>
            </div>

            {/* Applied Technique & Output Mask */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--tprm-text-muted)' }}>
                Applied Technique: <strong style={{ color: 'var(--tprm-text-primary)' }}>{p.technique}</strong>
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--tprm-text-muted)' }}>
                Output Representation:{' '}
                <code style={{ color: 'var(--tprm-cyan)', fontWeight: 700, fontFamily: 'var(--font-mono)' }}>
                  {p.mask}
                </code>
              </div>
            </div>

            {/* If Triggered in Active Document: Show Real Evidence */}
            {p.isTriggered && p.matches.length > 0 && (
              <div className="optiv-policy-evidence-box">
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4, color: 'var(--tprm-emerald)', fontWeight: 600 }}>
                  <Sparkles size={13} />
                  <span>Document Evidence Matches ({p.matches.length}):</span>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                  {p.matches.slice(0, 3).map((m, mIdx) => (
                    <div key={mIdx} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem' }}>
                      <span style={{ color: 'var(--tprm-text-primary)' }}>
                        Span [{m.start}, {m.end}): &ldquo;{m.value}&rdquo;
                      </span>
                      <span style={{ color: 'var(--tprm-cyan)', fontWeight: 600 }}>
                        &rarr; {m.masked_value}
                      </span>
                    </div>
                  ))}
                  {p.matches.length > 3 && (
                    <span style={{ color: 'var(--tprm-text-muted)', fontSize: '0.7rem' }}>
                      + {p.matches.length - 3} additional matches in document
                    </span>
                  )}
                </div>
              </div>
            )}

            {/* Rationale Footnote */}
            <p style={{ fontSize: '0.75rem', color: 'var(--tprm-text-muted)', lineHeight: 1.4, margin: 0, borderTop: '1px solid var(--tprm-border)', paddingTop: 8 }}>
              {p.rationale}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
};
