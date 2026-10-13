import React, { useState, useEffect } from 'react';
import {
  ShieldAlert,
  Search,
  RefreshCw,
  X,
  FileText,
} from 'lucide-react';
import type { UserProfile, PIIFinding } from '../../types';

interface PIIFindingsViewProps {
  currentUser: UserProfile;
  onNavigateToWorkspace: (documentId: string) => void;
}

export const PIIFindingsView: React.FC<PIIFindingsViewProps> = ({
  currentUser,
  onNavigateToWorkspace,
}) => {
  const [findings, setFindings] = useState<PIIFinding[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [categoryFilter, setCategoryFilter] = useState<string>('ALL');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [selectedFinding, setSelectedFinding] = useState<PIIFinding | null>(null);
  const [reviewNotes, setReviewNotes] = useState<string>('');
  const [updating, setUpdating] = useState<boolean>(false);

  const fetchFindings = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (categoryFilter !== 'ALL') params.append('category', categoryFilter);
      if (statusFilter !== 'ALL') params.append('status', statusFilter);
      params.append('limit', '100');

      const res = await fetch(`/api/findings?${params.toString()}`, {
        headers: { 'X-User-Email': currentUser.email },
      });
      if (res.ok) {
        const data = await res.json();
        setFindings(data.findings || []);
      }
    } catch (err) {
      console.warn('Failed to fetch PII findings', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFindings();
  }, [categoryFilter, statusFilter, currentUser.email]);

  const handleApplyReview = async (newStatus: string) => {
    if (!selectedFinding) return;
    setUpdating(true);
    try {
      const res = await fetch(`/api/findings/${selectedFinding.id}/review`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-User-Email': currentUser.email,
        },
        body: JSON.stringify({
          status: newStatus,
          notes: reviewNotes,
        }),
      });
      if (res.ok) {
        const data = await res.json();
        setSelectedFinding(data.finding);
        setFindings((prev) =>
          prev.map((f) => (f.id === selectedFinding.id ? data.finding : f))
        );
        setReviewNotes('');
      }
    } catch (err) {
      console.error('Failed to update finding review', err);
    } finally {
      setUpdating(false);
    }
  };

  const filteredFindings = findings.filter((f) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      f.id.toLowerCase().includes(q) ||
      f.document_id.toLowerCase().includes(q) ||
      f.type.toLowerCase().includes(q) ||
      (f.rule_id && f.rule_id.toLowerCase().includes(q))
    );
  });

  const getBadgeClass = (type: string) => {
    switch (type.toUpperCase()) {
      case 'EMAIL': return 'badge-email';
      case 'PHONE': return 'badge-phone';
      case 'GOVERNMENT_ID': return 'badge-gov';
      case 'FINANCIAL_IDENTIFIER': return 'badge-card';
      case 'EMPLOYEE_ID': return 'badge-emp';
      case 'IP_ADDRESS': return 'badge-ip';
      case 'PERSON': return 'badge-person';
      default: return 'badge-generic';
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      {/* Header & Controls */}
      <div className="optiv-card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 14 }}>
        <div>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 700, margin: 0, color: 'var(--tprm-text-primary)' }}>
            Classified Sensitive PII Findings & Evidence Ledger
          </h2>
          <p style={{ fontSize: '0.8rem', color: 'var(--tprm-text-muted)', margin: '4px 0 0' }}>
            Zero-leakage inspection, detection confidence telemetry, and authorized reviewer exception management.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
          {/* Search */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '6px 10px', borderRadius: 6, border: '1px solid var(--tprm-border)', backgroundColor: 'var(--tprm-surface)' }}>
            <Search size={14} color="var(--tprm-text-muted)" />
            <input
              type="text"
              placeholder="Search Finding ID, Rule, Type..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{ border: 'none', background: 'transparent', outline: 'none', fontSize: '0.8rem', color: 'var(--tprm-text-primary)' }}
            />
          </div>

          {/* Category Filter */}
          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            style={{
              padding: '6px 10px',
              borderRadius: 6,
              border: '1px solid var(--tprm-border)',
              backgroundColor: 'var(--tprm-surface)',
              color: 'var(--tprm-text-primary)',
              fontSize: '0.8rem',
            }}
          >
            <option value="ALL">All Categories</option>
            <option value="EMAIL">Email</option>
            <option value="PHONE">Phone</option>
            <option value="GOVERNMENT_ID">Government ID</option>
            <option value="FINANCIAL_IDENTIFIER">Financial Card / Account</option>
            <option value="PERSON">Personal Name</option>
            <option value="EMPLOYEE_ID">Employee ID</option>
            <option value="IP_ADDRESS">IP Address</option>
          </select>

          {/* Status Filter */}
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            style={{
              padding: '6px 10px',
              borderRadius: 6,
              border: '1px solid var(--tprm-border)',
              backgroundColor: 'var(--tprm-surface)',
              color: 'var(--tprm-text-primary)',
              fontSize: '0.8rem',
            }}
          >
            <option value="ALL">All Review Statuses</option>
            <option value="MASKED">Masked / Redacted</option>
            <option value="FLAGGED">Flagged / Unresolved</option>
            <option value="MANUAL_REVIEW">Manual Review Required</option>
            <option value="PRESERVED">Preserved Exception</option>
          </select>

          <button onClick={fetchFindings} className="btn-secondary" style={{ padding: '6px 12px', fontSize: '0.8rem' }}>
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Main Content Area */}
      <div style={{ display: 'grid', gridTemplateColumns: selectedFinding ? '1fr 380px' : '1fr', gap: 20 }}>
        {/* Findings Table */}
        <div className="optiv-card" style={{ padding: 0, overflow: 'hidden' }}>
          {loading ? (
            <div style={{ padding: 40, textAlign: 'center', color: 'var(--tprm-text-muted)', fontSize: '0.85rem' }}>
              Loading PII findings...
            </div>
          ) : filteredFindings.length === 0 ? (
            <div style={{ padding: 40, textAlign: 'center', color: 'var(--tprm-text-muted)', fontSize: '0.85rem' }}>
              No PII findings found matching current filters.
            </div>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--tprm-border)', backgroundColor: 'var(--tprm-surface-subtle)', color: 'var(--tprm-text-muted)', textAlign: 'left' }}>
                    <th style={{ padding: '12px 16px' }}>Finding ID</th>
                    <th style={{ padding: '12px 16px' }}>Category</th>
                    <th style={{ padding: '12px 16px' }}>Span Location</th>
                    <th style={{ padding: '12px 16px' }}>Confidence</th>
                    <th style={{ padding: '12px 16px' }}>Replacement Mask</th>
                    <th style={{ padding: '12px 16px' }}>Status</th>
                    <th style={{ padding: '12px 16px', textAlign: 'right' }}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredFindings.map((f, idx) => (
                    <tr
                      key={idx}
                      style={{
                        borderBottom: '1px solid var(--tprm-border)',
                        backgroundColor: selectedFinding?.id === f.id ? 'var(--tprm-surface-subtle)' : undefined,
                        cursor: 'pointer',
                      }}
                      onClick={() => setSelectedFinding(f)}
                    >
                      <td style={{ padding: '12px 16px', fontFamily: 'var(--font-mono)', fontWeight: 600 }}>
                        {f.id}
                      </td>
                      <td style={{ padding: '12px 16px' }}>
                        <span className={`badge ${getBadgeClass(f.type)}`}>{f.type}</span>
                      </td>
                      <td style={{ padding: '12px 16px', fontFamily: 'var(--font-mono)', fontSize: '0.75rem' }}>
                        [{f.start}, {f.end})
                      </td>
                      <td style={{ padding: '12px 16px' }}>
                        <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem' }}>
                          {(f.confidence * 100).toFixed(0)}%
                        </span>
                      </td>
                      <td style={{ padding: '12px 16px', fontFamily: 'var(--font-mono)', color: 'var(--tprm-emerald)' }}>
                        {f.masked_value}
                      </td>
                      <td style={{ padding: '12px 16px' }}>
                        <span className={`badge ${f.status === 'MASKED' ? 'badge-success' : f.status === 'MANUAL_REVIEW' ? 'badge-warning' : 'badge-gov'}`}>
                          {f.status}
                        </span>
                      </td>
                      <td style={{ padding: '12px 16px', textAlign: 'right' }}>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            onNavigateToWorkspace(f.document_id);
                          }}
                          className="btn-secondary"
                          style={{ padding: '3px 8px', fontSize: '0.75rem' }}
                          title="View in Document Workspace"
                        >
                          <FileText size={12} />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Selected Finding Inspection Drawer */}
        {selectedFinding && (
          <div className="optiv-card" style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--tprm-border)', paddingBottom: 10 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <ShieldAlert size={16} color="var(--tprm-indigo)" />
                <h4 style={{ fontSize: '0.9rem', fontWeight: 700, margin: 0, color: 'var(--tprm-text-primary)' }}>
                  Finding Inspection Details
                </h4>
              </div>
              <button
                onClick={() => setSelectedFinding(null)}
                style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--tprm-text-muted)' }}
              >
                <X size={16} />
              </button>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 10, fontSize: '0.8rem' }}>
              <div>
                <span style={{ color: 'var(--tprm-text-muted)' }}>Finding ID:</span>
                <div style={{ fontFamily: 'var(--font-mono)', fontWeight: 600, color: 'var(--tprm-text-primary)' }}>
                  {selectedFinding.id}
                </div>
              </div>

              <div>
                <span style={{ color: 'var(--tprm-text-muted)' }}>Document ID:</span>
                <div style={{ fontFamily: 'var(--font-mono)', color: 'var(--tprm-indigo)', cursor: 'pointer' }} onClick={() => onNavigateToWorkspace(selectedFinding.document_id)}>
                  {selectedFinding.document_id}
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
                <div>
                  <span style={{ color: 'var(--tprm-text-muted)' }}>Category:</span>
                  <div><span className={`badge ${getBadgeClass(selectedFinding.type)}`}>{selectedFinding.type}</span></div>
                </div>
                <div>
                  <span style={{ color: 'var(--tprm-text-muted)' }}>Risk Level:</span>
                  <div><span className="badge badge-gov">{selectedFinding.risk_level || 'HIGH'}</span></div>
                </div>
              </div>

              <div>
                <span style={{ color: 'var(--tprm-text-muted)' }}>Character Span:</span>
                <div style={{ fontFamily: 'var(--font-mono)' }}>
                  [{selectedFinding.start}, {selectedFinding.end}) • Length: {selectedFinding.end - selectedFinding.start} characters
                </div>
              </div>

              <div>
                <span style={{ color: 'var(--tprm-text-muted)' }}>Detection Rule & Method:</span>
                <div style={{ fontWeight: 600, color: 'var(--tprm-text-primary)' }}>
                  {selectedFinding.rule_id} ({selectedFinding.detector_method})
                </div>
              </div>

              <div>
                <span style={{ color: 'var(--tprm-text-muted)' }}>Classification Rationale:</span>
                <p style={{ margin: '4px 0 0', color: 'var(--tprm-text-secondary)', lineHeight: 1.4 }}>
                  {selectedFinding.rationale || 'Conforms to Cadence Financial Governance Mandate'}
                </p>
              </div>

              <div>
                <span style={{ color: 'var(--tprm-text-muted)' }}>Replacement Mask:</span>
                <div style={{ fontFamily: 'var(--font-mono)', color: 'var(--tprm-emerald)', fontWeight: 600 }}>
                  {selectedFinding.masked_value}
                </div>
              </div>

              <div>
                <span style={{ color: 'var(--tprm-text-muted)' }}>Post-Redaction Verification:</span>
                <div>
                  <span className="badge badge-success">
                    {selectedFinding.verification_result || 'VERIFIED REMOVED'}
                  </span>
                </div>
              </div>
            </div>

            {/* Reviewer Action Area */}
            <div style={{ marginTop: 10, paddingTop: 10, borderTop: '1px solid var(--tprm-border)' }}>
              <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--tprm-text-secondary)', display: 'block', marginBottom: 6 }}>
                Compliance Officer Review Action:
              </span>

              <textarea
                placeholder="Review notes or justification..."
                value={reviewNotes}
                onChange={(e) => setReviewNotes(e.target.value)}
                style={{
                  width: '100%',
                  fontSize: '0.75rem',
                  padding: '6px 8px',
                  borderRadius: 6,
                  border: '1px solid var(--tprm-border)',
                  backgroundColor: 'var(--tprm-surface-subtle)',
                  color: 'var(--tprm-text-primary)',
                  marginBottom: 8,
                  resize: 'none',
                  height: 50,
                }}
              />

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6 }}>
                <button
                  onClick={() => handleApplyReview('MASKED')}
                  disabled={updating}
                  className="btn-primary"
                  style={{ fontSize: '0.7rem', padding: '6px 8px', justifyContent: 'center' }}
                >
                  Confirm Masking
                </button>
                <button
                  onClick={() => handleApplyReview('MANUAL_REVIEW')}
                  disabled={updating}
                  className="btn-secondary"
                  style={{ fontSize: '0.7rem', padding: '6px 8px', justifyContent: 'center' }}
                >
                  Flag for Review
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
