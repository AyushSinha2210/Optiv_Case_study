import React from 'react';
import type { UserProfile } from '../../types';

interface RedactionReviewViewProps {
  currentUser?: UserProfile;
  onNavigateToWorkspace: () => void;
}

export const RedactionReviewView: React.FC<RedactionReviewViewProps> = ({
  onNavigateToWorkspace,
}) => {
  const policies = [
    {
      category: 'GOVERNMENT_ID',
      label: 'Government-Issued Identifiers (SSN, Aadhaar, PAN)',
      technique: 'Deterministic Token Replacement',
      mask: '[REDACTED_GOVERNMENT_ID]',
      rationale: 'Zero tolerance under GLBA / Privacy Act; glyphs eliminated permanently.',
      risk: 'CRITICAL',
    },
    {
      category: 'FINANCIAL_IDENTIFIER',
      label: 'Financial & Card Accounts (Credit Cards, Bank Accounts)',
      technique: 'Luhn-Validated Token Substitution',
      mask: '[REDACTED_FINANCIAL_IDENTIFIER]',
      rationale: 'PCI-DSS DSS 3.4 mandate; no partial card numbers permitted in LLM context.',
      risk: 'CRITICAL',
    },
    {
      category: 'EMAIL',
      label: 'Email Addresses (Corporate & Personal)',
      technique: 'Contextual Semantic Token',
      mask: '[REDACTED_EMAIL]',
      rationale: 'Prevents direct phishing or contact harvesting by downstream models.',
      risk: 'HIGH',
    },
    {
      category: 'PHONE',
      label: 'Telephone Numbers (National & International E.164)',
      technique: 'Contextual Semantic Token',
      mask: '[REDACTED_PHONE]',
      rationale: 'Protects customer and employee direct dial numbers from prompt leakage.',
      risk: 'HIGH',
    },
    {
      category: 'PERSON',
      label: 'Personal Names (Customer, Executive, Officer)',
      technique: 'Entity Replacement Token',
      mask: '[REDACTED_PERSON]',
      rationale: 'Mitigates privacy exposure in case summaries and credit memos.',
      risk: 'MEDIUM',
    },
    {
      category: 'IP_ADDRESS',
      label: 'IP Addresses (IPv4 & IPv6)',
      technique: 'Network Token Masking',
      mask: '[REDACTED_IP_ADDRESS]',
      rationale: 'Prevents internal network topology disclosure to external LLMs.',
      risk: 'MEDIUM',
    },
    {
      category: 'EMPLOYEE_ID',
      label: 'Employee Corporate Identifiers',
      technique: 'Internal Identifier Masking',
      mask: '[REDACTED_EMPLOYEE_ID]',
      rationale: 'Eliminates internal badge and staff correlation tokens.',
      risk: 'MEDIUM',
    },
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      {/* Header */}
      <div className="optiv-card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 700, margin: 0, color: 'var(--tprm-text-primary)' }}>
            Policy Evaluation & Masking Taxonomy Matrix
          </h2>
          <p style={{ fontSize: '0.8rem', color: 'var(--tprm-text-muted)', margin: '4px 0 0' }}>
            Authoritative sanitization techniques mapped to regulatory frameworks and business invariants.
          </p>
        </div>

        <button
          onClick={onNavigateToWorkspace}
          className="btn-primary"
          style={{ fontSize: '0.8rem', padding: '6px 14px' }}
        >
          Open Document Workspace
        </button>
      </div>

      {/* Policy Rules Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: 16 }}>
        {policies.map((p, idx) => (
          <div key={idx} className="optiv-card" style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span className="badge badge-generic" style={{ fontWeight: 700 }}>
                {p.category}
              </span>
              <span className={`badge ${p.risk === 'CRITICAL' ? 'badge-gov' : 'badge-warning'}`}>
                {p.risk} RISK
              </span>
            </div>

            <h4 style={{ margin: 0, fontSize: '0.9rem', color: 'var(--tprm-text-primary)' }}>
              {p.label}
            </h4>

            <div style={{ fontSize: '0.75rem', backgroundColor: 'var(--tprm-surface-subtle)', padding: 10, borderRadius: 6, border: '1px solid var(--tprm-border)' }}>
              <div style={{ color: 'var(--tprm-text-muted)', marginBottom: 2 }}>Applied Technique:</div>
              <div style={{ fontWeight: 600, color: 'var(--tprm-text-primary)' }}>{p.technique}</div>
              <div style={{ color: 'var(--tprm-text-muted)', marginTop: 6, marginBottom: 2 }}>Output Representation:</div>
              <code style={{ color: 'var(--tprm-emerald)', fontWeight: 700 }}>{p.mask}</code>
            </div>

            <p style={{ fontSize: '0.75rem', color: 'var(--tprm-text-muted)', margin: 0, lineHeight: 1.4 }}>
              {p.rationale}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
};
