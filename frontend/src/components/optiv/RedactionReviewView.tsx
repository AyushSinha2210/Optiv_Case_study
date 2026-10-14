import React, { useState, useMemo } from 'react';
import {
  CheckCircle2,
  ExternalLink,
  Filter,
  Layers,
  ChevronDown,
  ChevronUp,
  Lock,
} from 'lucide-react';
import type { UserProfile, ProcessResponse } from '../../types';
import { PageHeader } from './PageHeader';
import { CopyButton } from './CopyButton';

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
  const [expandedCards, setExpandedCards] = useState<Record<string, boolean>>({});

  const toggleExpand = (category: string) => {
    setExpandedCards((prev) => ({ ...prev, [category]: !prev[category] }));
  };

  const basePolicies = [
    {
      category: 'GOVERNMENT_ID',
      label: 'Government-Issued Identifiers (SSN, Aadhaar, PAN)',
      technique: 'Deterministic Token Replacement',
      mask: '[REDACTED_GOVERNMENT_ID]',
      rationale: 'Zero tolerance under GLBA / Privacy Act; glyphs eliminated permanently to prevent re-identification.',
      risk: 'CRITICAL',
      regulatoryMandate: 'GLBA §501(b) / Privacy Act 1974 / 5 U.S.C. § 552a',
      ruleId: 'RULE_GOV_ID_STRICT',
    },
    {
      category: 'FINANCIAL_IDENTIFIER',
      label: 'Financial & Card Accounts (Credit Cards, Bank Routing)',
      technique: 'Luhn-Validated Token Substitution',
      mask: '[REDACTED_FINANCIAL_IDENTIFIER]',
      rationale: 'PCI-DSS Req 3.4 mandate; no full card numbers permitted in downstream analysis contexts.',
      risk: 'CRITICAL',
      regulatoryMandate: 'PCI-DSS Req 3.4 / FTC Safeguards Rule',
      ruleId: 'RULE_FIN_CARD_LUHN',
    },
    {
      category: 'EMAIL',
      label: 'Email Addresses (Corporate & Personal)',
      technique: 'Contextual Semantic Token',
      mask: '[REDACTED_EMAIL]',
      rationale: 'Prevents direct phishing, executive enumeration, or contact harvesting by downstream models.',
      risk: 'HIGH',
      regulatoryMandate: 'CAN-SPAM Act / GDPR Article 6',
      ruleId: 'RULE_EMAIL_SEMANTIC',
    },
    {
      category: 'PHONE',
      label: 'Telephone Numbers (National & International E.164)',
      technique: 'Contextual Semantic Token',
      mask: '[REDACTED_PHONE]',
      rationale: 'Protects customer and employee direct dial numbers from prompt leakage.',
      risk: 'HIGH',
      regulatoryMandate: 'TCPA / GDPR Article 5(1)(c)',
      ruleId: 'RULE_PHONE_NANP_E164',
    },
    {
      category: 'PERSON',
      label: 'Personal Names (Customer, Executive, Officer)',
      technique: 'Entity Replacement Token',
      mask: '[REDACTED_PERSON]',
      rationale: 'Mitigates privacy exposure in case summaries, credit memos, and narrative risk summaries.',
      risk: 'MEDIUM',
      regulatoryMandate: 'CCPA / CPRA §1798.140 / NIST Privacy Framework',
      ruleId: 'RULE_PERSON_NER_CONTEXT',
    },
    {
      category: 'IP_ADDRESS',
      label: 'IP Addresses (IPv4 & IPv6)',
      technique: 'Network Token Masking',
      mask: '[REDACTED_IP_ADDRESS]',
      rationale: 'Prevents internal network topology and infrastructure disclosure to external LLMs.',
      risk: 'MEDIUM',
      regulatoryMandate: 'NIST SP 800-53 SC-7 / ISO 27001 A.13',
      ruleId: 'RULE_IP_SUBNET_MASK',
    },
    {
      category: 'EMPLOYEE_ID',
      label: 'Employee Corporate Identifiers',
      technique: 'Internal Identifier Masking',
      mask: '[REDACTED_EMPLOYEE_ID]',
      rationale: 'Eliminates internal badge and staff correlation tokens across ingested records.',
      risk: 'MEDIUM',
      regulatoryMandate: 'Cadence Enterprise Information Security Policy',
      ruleId: 'RULE_CORP_BADGE_ID',
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
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      {/* Unified Page Header */}
      <PageHeader
        title="Redaction Policy & Rule Review"
        description="Review enterprise privacy policies, inspect triggered detection rules, and verify applied masking tokens without exposing raw sensitive values."
        actions={
          <button
            onClick={onNavigateToWorkspace}
            className="btn-primary"
            title="Open Document Comparison Workspace"
          >
            <span>Open Document Workspace</span>
            <ExternalLink size={14} />
          </button>
        }
      />

      {/* Active Document Context Banner */}
      <div className="optiv-doc-banner">
        <div className="optiv-doc-banner-info">
          <div className="optiv-doc-icon-wrap">
            <Layers size={22} />
          </div>
          <div className="optiv-doc-meta">
            <div className="optiv-doc-title-row">
              <span className="optiv-doc-title">
                {activeDocument
                  ? `Policy Scope: ${activeDocument.document_id} (${activeDocument.source_type?.toUpperCase() || 'DOCUMENT'})`
                  : 'Enterprise Policy & Masking Taxonomy'}
              </span>
              {activeDocument?.document_id && <CopyButton text={activeDocument.document_id} />}
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
      </div>

      {/* Filter Tabs */}
      <div className="optiv-card" style={{ padding: '14px 18px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
          <Filter size={15} color="var(--tprm-text-muted)" />
          <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--tprm-text-muted)' }}>Policy Scope:</span>

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
            Triggered in Current Document ({triggeredCount})
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
            Critical Risk Only (2)
          </button>
        </div>

        <div style={{ fontSize: '0.75rem', color: 'var(--tprm-text-muted)', display: 'flex', alignItems: 'center', gap: 6 }}>
          <Lock size={12} color="var(--tprm-emerald)" />
          <span>Evidence preview is privacy-protected: raw values masked by policy</span>
        </div>
      </div>

      {/* Policy Cards Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: 18 }}>
        {displayedPolicies.map((p) => {
          const isExpanded = !!expandedCards[p.category];

          return (
            <div
              key={p.category}
              className={`optiv-policy-card ${p.isTriggered ? 'triggered' : 'inactive'}`}
              style={{
                display: 'flex',
                flexDirection: 'column',
                gap: 12,
                opacity: p.isTriggered ? 1 : 0.85,
              }}
            >
              {/* Card Header: Category & Status */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span className="badge badge-generic" style={{ fontWeight: 700 }}>
                    {p.category}
                  </span>
                  {p.isTriggered ? (
                    <span className="badge badge-success" style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                      <CheckCircle2 size={12} />
                      <span>Triggered ({p.count})</span>
                    </span>
                  ) : (
                    <span className="badge" style={{ backgroundColor: 'var(--tprm-surface-subtle)', color: 'var(--tprm-text-muted)', border: '1px solid var(--tprm-border)' }}>
                      Not Triggered
                    </span>
                  )}
                </div>

                <span className={`badge ${p.risk === 'CRITICAL' ? 'badge-danger' : p.risk === 'HIGH' ? 'badge-warning' : 'badge-info'}`}>
                  {p.risk} RISK
                </span>
              </div>

              {/* Policy Title & Rule ID */}
              <div>
                <h3 style={{ margin: 0, fontSize: '0.975rem', color: 'var(--tprm-text-primary)', fontWeight: 700 }}>
                  {p.label}
                </h3>
                <div style={{ fontSize: '0.725rem', fontFamily: 'var(--font-mono)', color: 'var(--tprm-text-muted)', marginTop: 2 }}>
                  Rule ID: {p.ruleId}
                </div>
              </div>

              {/* Approach & Mask Token */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6, padding: '10px 12px', borderRadius: 8, backgroundColor: 'var(--tprm-surface-subtle)', border: '1px solid var(--tprm-border)' }}>
                <div style={{ fontSize: '0.775rem', color: 'var(--tprm-text-muted)' }}>
                  Redaction Approach: <strong style={{ color: 'var(--tprm-text-primary)' }}>{p.technique}</strong>
                </div>
                <div style={{ fontSize: '0.775rem', color: 'var(--tprm-text-muted)' }}>
                  Masking Token:{' '}
                  <code style={{ color: 'var(--tprm-cyan)', fontWeight: 700, fontFamily: 'var(--font-mono)', padding: '2px 5px', borderRadius: 4, backgroundColor: 'var(--tprm-surface)', border: '1px solid var(--tprm-border)' }}>
                    {p.mask}
                  </code>
                </div>
              </div>

              {/* Evidence Matches (Privacy-Safe: Values are masked, never raw PII) */}
              {p.isTriggered && p.matches.length > 0 && (
                <div className="optiv-policy-evidence-box">
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 6 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6, color: 'var(--tprm-emerald)', fontWeight: 600, fontSize: '0.775rem' }}>
                      <CheckCircle2 size={13} />
                      <span>Document Findings ({p.matches.length}):</span>
                    </div>
                    <span style={{ fontSize: '0.675rem', color: 'var(--tprm-text-muted)' }}>
                      Safe Span References
                    </span>
                  </div>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                    {p.matches.slice(0, 3).map((m, mIdx) => (
                      <div key={mIdx} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.75rem', padding: '3px 0' }}>
                        <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--tprm-text-secondary)' }}>
                          Span [{m.start}, {m.end}) &bull; Conf {Math.round((m.confidence ?? 0.95) * 100)}%
                        </span>
                        <span style={{ color: 'var(--tprm-cyan)', fontWeight: 600, fontFamily: 'var(--font-mono)' }}>
                          &rarr; {m.masked_value || p.mask}
                        </span>
                      </div>
                    ))}
                    {p.matches.length > 3 && (
                      <div style={{ color: 'var(--tprm-text-muted)', fontSize: '0.7rem', marginTop: 2 }}>
                        + {p.matches.length - 3} additional matches safely masked
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Expandable Section for Legal Rationale & Policy Detail */}
              <div style={{ marginTop: 'auto', paddingTop: 8 }}>
                <button
                  type="button"
                  onClick={() => toggleExpand(p.category)}
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
                  {isExpanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                  <span>{isExpanded ? 'Hide Policy Details & Legal Mandate' : 'View Legal Mandate & Rationale'}</span>
                </button>

                {isExpanded && (
                  <div style={{ marginTop: 8, padding: 10, borderRadius: 6, backgroundColor: 'var(--tprm-surface-subtle)', border: '1px solid var(--tprm-border)', fontSize: '0.75rem', lineHeight: 1.5 }}>
                    <div style={{ fontWeight: 600, color: 'var(--tprm-text-primary)', marginBottom: 2 }}>
                      Statutory Basis:
                    </div>
                    <div style={{ color: 'var(--tprm-text-secondary)', marginBottom: 6 }}>
                      {p.regulatoryMandate}
                    </div>
                    <div style={{ fontWeight: 600, color: 'var(--tprm-text-primary)', marginBottom: 2 }}>
                      Compliance Rationale:
                    </div>
                    <div style={{ color: 'var(--tprm-text-muted)' }}>
                      {p.rationale}
                    </div>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
