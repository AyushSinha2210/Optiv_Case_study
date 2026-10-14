import React, { useState, useEffect, useMemo } from 'react';
import {
  ShieldAlert,
  Search,
  RefreshCw,
  X,
  FileText,
  ExternalLink,
  CheckCircle2,
  AlertTriangle,
  SlidersHorizontal,
  FolderOpen,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import type { UserProfile, PIIFinding, ProcessResponse } from '../../types';
import { PageHeader } from './PageHeader';
import { CopyButton } from './CopyButton';

interface PIIFindingsViewProps {
  currentUser?: UserProfile;
  activeDocument?: ProcessResponse | null;
  onNavigateToWorkspace: (documentId: string, entityIndex?: number) => void;
}

export const PIIFindingsView: React.FC<PIIFindingsViewProps> = ({
  activeDocument,
  onNavigateToWorkspace,
}) => {
  const [availableRuns, setAvailableRuns] = useState<{ document_id: string; original_filename?: string }[]>([]);
  const [selectedDocId, setSelectedDocId] = useState<string>(activeDocument?.document_id || 'active');
  const [findings, setFindings] = useState<PIIFinding[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [categoryFilter, setCategoryFilter] = useState<string>('ALL');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [selectedFinding, setSelectedFinding] = useState<PIIFinding | null>(null);
  const [reviewNotes, setReviewNotes] = useState<string>('');
  const [updating, setUpdating] = useState<boolean>(false);
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [pageSize, setPageSize] = useState<number>(20);

  // Reset page when filters change
  useEffect(() => {
    setCurrentPage(1);
  }, [selectedDocId, categoryFilter, statusFilter, searchQuery]);

  // Sync selectedDocId with activeDocument when activeDocument changes
  useEffect(() => {
    if (activeDocument?.document_id) {
      setSelectedDocId(activeDocument.document_id);
    }
  }, [activeDocument?.document_id]);

  // Fetch available runs for the document switcher
  useEffect(() => {
    fetch('/api/runs?limit=30')
      .then((res) => res.json())
      .then((data) => {
        if (data.runs) {
          setAvailableRuns(data.runs);
        }
      })
      .catch(() => {});
  }, []);

  // Fetch findings for the active or selected document
  const fetchFindings = async () => {
    setLoading(true);
    try {
      // If we are looking at active document and it has entities, use them directly for real-time behavior
      const docIdToQuery = selectedDocId === 'active' || (activeDocument && selectedDocId === activeDocument.document_id)
        ? activeDocument?.document_id
        : selectedDocId;

      const params = new URLSearchParams();
      if (docIdToQuery && docIdToQuery !== 'all') {
        params.append('document_id', docIdToQuery);
      }
      if (categoryFilter !== 'ALL') params.append('category', categoryFilter);
      if (statusFilter !== 'ALL') params.append('status', statusFilter);
      params.append('limit', '100');

      const res = await fetch(`/api/findings?${params.toString()}`);
      if (res.ok) {
        const data = await res.json();
        // If DB query returned findings, use them
        if (data.findings && data.findings.length > 0) {
          setFindings(data.findings);
        } else if (activeDocument && (selectedDocId === 'active' || selectedDocId === activeDocument.document_id)) {
          // If fresh from memory/pipeline and not yet committed in query, map from activeDocument.entities
          const mapped: PIIFinding[] = (activeDocument.entities || []).map((e, idx) => ({
            id: `fnd-${activeDocument.document_id}-${idx + 1}`,
            document_id: activeDocument.document_id,
            finding_index: idx + 1,
            type: e.type || 'PII',
            start: e.start ?? 0,
            end: e.end ?? 0,
            confidence: e.confidence ?? 0.95,
            value: e.value || '',
            masked_value: e.masked_value || '[REDACTED]',
            detector_method: e.detector_method || 'pattern_matcher',
            rule_id: e.rule_id || `RULE_${e.type?.toUpperCase()}`,
            rationale: e.rationale || `Detected ${e.type} pattern`,
            status: activeDocument.release_allowed ? 'MASKED' : 'FLAGGED',
            verification_result: activeDocument.verification_status === 'PASS' ? 'VERIFIED_REMOVED' : 'FAIL',
            page_or_slide: e.page || 1,
            risk_level: ['GOVERNMENT_ID', 'FINANCIAL_IDENTIFIER'].includes(e.type) ? 'CRITICAL' : 'HIGH',
          }));
          setFindings(mapped);
        } else {
          setFindings([]);
        }
      }
    } catch (err) {
      console.warn('Failed to fetch PII findings', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFindings();
  }, [selectedDocId, categoryFilter, statusFilter, activeDocument]);

  const handleApplyReview = async (newStatus: string) => {
    if (!selectedFinding) return;
    setUpdating(true);
    try {
      const res = await fetch(`/api/findings/${selectedFinding.id}/review`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
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
      } else {
        // Fallback local update
        setSelectedFinding((prev) => prev ? { ...prev, status: newStatus } : null);
        setFindings((prev) =>
          prev.map((f) => (f.id === selectedFinding.id ? { ...f, status: newStatus } : f))
        );
      }
    } catch (err) {
      console.error('Failed to update finding review', err);
    } finally {
      setUpdating(false);
    }
  };

  const filteredFindings = useMemo(() => {
    return findings.filter((f) => {
      if (!searchQuery) return true;
      const q = searchQuery.toLowerCase();
      return (
        f.id.toLowerCase().includes(q) ||
        f.document_id.toLowerCase().includes(q) ||
        f.type.toLowerCase().includes(q) ||
        (f.rule_id && f.rule_id.toLowerCase().includes(q))
      );
    });
  }, [findings, searchQuery]);

  const totalPages = Math.max(1, Math.ceil(filteredFindings.length / pageSize));
  const paginatedFindings = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return filteredFindings.slice(start, start + pageSize);
  }, [filteredFindings, currentPage, pageSize]);

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

  const activeDocId = activeDocument?.document_id;
  const isViewingActive = selectedDocId === 'active' || (activeDocId && selectedDocId === activeDocId);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      {/* Standardized Page Header */}
      <PageHeader
        title="Classified PII Findings Ledger"
        description="Granular entity-level inspection, detector confidence scores, contextual classification rationale, and manual review exception management."
        actions={
          <button
            onClick={fetchFindings}
            className="btn-secondary"
            disabled={loading}
            title="Refresh findings from server"
          >
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
            <span>Refresh Findings</span>
          </button>
        }
      />

      {/* Dynamic Document Context Banner */}
      <div className="optiv-doc-banner">
        <div className="optiv-doc-banner-info">
          <div className="optiv-doc-icon-wrap">
            <FileText size={22} />
          </div>
          <div className="optiv-doc-meta">
            <div className="optiv-doc-title-row">
              <span className="optiv-doc-title">
                {isViewingActive && activeDocument
                  ? `Active Document Findings: ${activeDocument.source_type?.toUpperCase() || 'FILE'}`
                  : `Document Findings Ledger: ${selectedDocId}`}
              </span>
              <CopyButton text={isViewingActive && activeDocument ? activeDocument.document_id : selectedDocId} />
              {isViewingActive && activeDocument && (
                <span className={`badge ${activeDocument.release_allowed ? 'badge-success' : 'badge-danger'}`}>
                  {activeDocument.release_allowed ? 'GATE: PASS' : 'GATE: BLOCKED'}
                </span>
              )}
            </div>
            <div className="optiv-doc-stats-row">
              <span className="optiv-doc-stat-item">
                <span>Document ID:</span>
                <span className="optiv-doc-stat-val">
                  {isViewingActive && activeDocument ? activeDocument.document_id : selectedDocId}
                </span>
              </span>
              <span>•</span>
              <span className="optiv-doc-stat-item">
                <span>Classified Findings:</span>
                <span className="optiv-doc-stat-val">{findings.length}</span>
              </span>
              <span>•</span>
              <span className="optiv-doc-stat-item">
                <span>Redactions Applied:</span>
                <span className="optiv-doc-stat-val">
                  {isViewingActive && activeDocument ? activeDocument.redactions_applied : findings.filter(f => f.status === 'MASKED').length}
                </span>
              </span>
            </div>
          </div>
        </div>

        {/* Document Selector Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.8rem', color: 'var(--tprm-text-muted)' }}>
            <FolderOpen size={15} />
            <span>Scope:</span>
          </div>
          <select
            className="optiv-select"
            value={selectedDocId}
            onChange={(e) => setSelectedDocId(e.target.value)}
          >
            {activeDocument && (
              <option value={activeDocument.document_id}>
                Current Active ({activeDocument.document_id.slice(0, 16)}...)
              </option>
            )}
            <option value="all">All Ingested Documents</option>
            {availableRuns
              .filter((r) => r.document_id !== activeDocument?.document_id)
              .map((r) => (
                <option key={r.document_id} value={r.document_id}>
                  {r.original_filename || r.document_id.slice(0, 18)}
                </option>
              ))}
          </select>

          {isViewingActive && activeDocument && (
            <button
              onClick={() => onNavigateToWorkspace(activeDocument.document_id)}
              className="optiv-btn-header"
              style={{ height: 36, backgroundColor: 'var(--tprm-indigo-light)', color: 'var(--tprm-indigo)', borderColor: 'rgba(99, 102, 241, 0.3)' }}
            >
              <ExternalLink size={14} />
              <span>Inspect in Workspace Diff</span>
            </button>
          )}
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="optiv-card" style={{ padding: '14px 18px' }}>
        <div className="optiv-filter-bar" style={{ justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, flex: 1, minWidth: 260 }}>
            <div style={{ position: 'relative', width: '100%', maxWidth: 360 }}>
              <Search size={15} color="var(--tprm-text-muted)" style={{ position: 'absolute', left: 10, top: 11 }} />
              <input
                type="text"
                className="optiv-input-search"
                style={{ width: '100%', paddingLeft: 32 }}
                placeholder="Search Finding ID, Rule, Type..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>

            <select
              className="optiv-select"
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
            >
              <option value="ALL">All Categories</option>
              <option value="GOVERNMENT_ID">Government IDs</option>
              <option value="FINANCIAL_IDENTIFIER">Financial / Card</option>
              <option value="EMAIL">Email Addresses</option>
              <option value="PHONE">Phone Numbers</option>
              <option value="PERSON">Persons</option>
              <option value="IP_ADDRESS">IP Addresses</option>
              <option value="EMPLOYEE_ID">Employee IDs</option>
            </select>

            <select
              className="optiv-select"
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
            >
              <option value="ALL">All Review Statuses</option>
              <option value="MASKED">Masked / Redacted</option>
              <option value="FLAGGED">Flagged / Unresolved</option>
              <option value="MANUAL_REVIEW">Pending Manual Review</option>
              <option value="PRESERVED">Preserved by Exception</option>
            </select>
          </div>

          <button
            onClick={fetchFindings}
            className="optiv-btn-header"
            style={{ height: 36 }}
            disabled={loading}
          >
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Findings Table */}
      <div className="optiv-card" style={{ padding: 0, overflow: 'hidden' }}>
        {loading ? (
          <div style={{ padding: 40, textAlign: 'center', color: 'var(--tprm-text-muted)' }}>
            <RefreshCw size={24} className="animate-spin" style={{ margin: '0 auto 10px' }} />
            <div>Loading classified findings...</div>
          </div>
        ) : filteredFindings.length === 0 ? (
          <div style={{ padding: 50, textAlign: 'center', color: 'var(--tprm-text-muted)' }}>
            <ShieldAlert size={36} color="var(--tprm-text-muted)" style={{ margin: '0 auto 12px' }} />
            <h3 style={{ margin: '0 0 6px', color: 'var(--tprm-text-primary)' }}>
              No Sensitive Findings for This Document
            </h3>
            <p style={{ margin: '0 0 16px', fontSize: '0.85rem' }}>
              The selected document has zero active findings matching the current filters.
            </p>
            {activeDocument && (
              <button
                onClick={() => onNavigateToWorkspace(activeDocument.document_id)}
                className="btn-primary"
                style={{ fontSize: '0.85rem', padding: '8px 16px', margin: '0 auto' }}
              >
                Open Document Workspace
              </button>
            )}
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.85rem' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--tprm-border)', backgroundColor: 'var(--tprm-surface-subtle)' }}>
                  <th style={{ padding: '12px 16px', fontWeight: 600, color: 'var(--tprm-text-secondary)' }}>Finding ID</th>
                  <th style={{ padding: '12px 16px', fontWeight: 600, color: 'var(--tprm-text-secondary)' }}>Category</th>
                  <th style={{ padding: '12px 16px', fontWeight: 600, color: 'var(--tprm-text-secondary)' }}>Span Location</th>
                  <th style={{ padding: '12px 16px', fontWeight: 600, color: 'var(--tprm-text-secondary)' }}>Confidence</th>
                  <th style={{ padding: '12px 16px', fontWeight: 600, color: 'var(--tprm-text-secondary)' }}>Replacement Mask</th>
                  <th style={{ padding: '12px 16px', fontWeight: 600, color: 'var(--tprm-text-secondary)' }}>Status</th>
                  <th style={{ padding: '12px 16px', fontWeight: 600, color: 'var(--tprm-text-secondary)', textAlign: 'right' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {paginatedFindings.map((f, idx) => (
                  <tr
                    key={f.id || idx}
                    style={{
                      borderBottom: '1px solid var(--tprm-border)',
                      cursor: 'pointer',
                      transition: 'background-color 0.15s ease',
                    }}
                    onClick={() => setSelectedFinding(f)}
                    onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = 'var(--tprm-surface-subtle)')}
                    onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = 'transparent')}
                  >
                    <td style={{ padding: '12px 16px' }}>
                      <div className="optiv-doc-id-cell">
                        <span className="optiv-doc-id-text" title={f.id}>
                          {f.id}
                        </span>
                        <CopyButton text={f.id} />
                      </div>
                    </td>
                    <td style={{ padding: '12px 16px' }}>
                      <span className={`badge ${getBadgeClass(f.type)}`} style={{ fontWeight: 600 }}>
                        {f.type}
                      </span>
                    </td>
                    <td style={{ padding: '12px 16px', fontFamily: 'var(--font-mono)', color: 'var(--tprm-text-muted)', fontSize: '0.8rem' }}>
                      [{f.start}, {f.end})
                    </td>
                    <td style={{ padding: '12px 16px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                        <div style={{ width: 40, height: 6, borderRadius: 3, backgroundColor: 'var(--tprm-border)', overflow: 'hidden' }}>
                          <div
                            style={{
                              width: `${Math.round(f.confidence * 100)}%`,
                              height: '100%',
                              backgroundColor: f.confidence >= 0.9 ? 'var(--tprm-emerald)' : '#f59e0b',
                            }}
                          />
                        </div>
                        <span style={{ fontSize: '0.8rem', fontWeight: 600 }}>
                          {Math.round(f.confidence * 100)}%
                        </span>
                      </div>
                    </td>
                    <td style={{ padding: '12px 16px', fontFamily: 'var(--font-mono)', fontSize: '0.8rem', color: 'var(--tprm-cyan)' }}>
                      {f.masked_value || '[REDACTED]'}
                    </td>
                    <td style={{ padding: '12px 16px' }}>
                      <span className={`badge ${f.status === 'MASKED' ? 'badge-success' : f.status === 'MANUAL_REVIEW' ? 'badge-warning' : 'badge-danger'}`}>
                        {f.status}
                      </span>
                    </td>
                    <td style={{ padding: '12px 16px', textAlign: 'right' }}>
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: 6 }} onClick={(e) => e.stopPropagation()}>
                        <button
                          onClick={() => onNavigateToWorkspace(f.document_id, f.finding_index - 1)}
                          className="optiv-btn-header icon-only"
                          title="Jump to this entity in Document Workspace Diff"
                        >
                          <ExternalLink size={14} color="var(--tprm-indigo)" />
                        </button>
                        <button
                          onClick={() => setSelectedFinding(f)}
                          className="optiv-btn-header icon-only"
                          title="Review / Edit Exception"
                        >
                          <SlidersHorizontal size={14} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {filteredFindings.length > 0 && (
              <div className="optiv-pagination">
                <div className="optiv-pagination-info">
                  Showing <strong>{(currentPage - 1) * pageSize + 1}</strong> to{' '}
                  <strong>{Math.min(currentPage * pageSize, filteredFindings.length)}</strong> of{' '}
                  <strong>{filteredFindings.length}</strong> findings
                </div>
                <div className="optiv-pagination-actions">
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginRight: 8, fontSize: '0.8rem', color: 'var(--tprm-text-muted)' }}>
                    <span>Rows:</span>
                    <select
                      className="optiv-select"
                      style={{ height: 30, padding: '0 6px', fontSize: '0.75rem' }}
                      value={pageSize}
                      onChange={(e) => {
                        setPageSize(Number(e.target.value));
                        setCurrentPage(1);
                      }}
                    >
                      <option value={10}>10</option>
                      <option value={20}>20</option>
                      <option value={50}>50</option>
                      <option value={100}>100</option>
                    </select>
                  </div>
                  <button
                    type="button"
                    className="optiv-pagination-btn"
                    disabled={currentPage <= 1}
                    onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                    aria-label="Previous page"
                  >
                    <ChevronLeft size={14} />
                    <span>Previous</span>
                  </button>
                  <span style={{ fontSize: '0.8rem', fontWeight: 600, padding: '0 4px', color: 'var(--tprm-text-primary)' }}>
                    {currentPage} / {totalPages}
                  </span>
                  <button
                    type="button"
                    className="optiv-pagination-btn"
                    disabled={currentPage >= totalPages}
                    onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                    aria-label="Next page"
                  >
                    <span>Next</span>
                    <ChevronRight size={14} />
                  </button>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Review Drawer Modal */}
      {selectedFinding && (
        <div className="ai-drawer-overlay" onClick={() => setSelectedFinding(null)}>
          <div className="ai-drawer" onClick={(e) => e.stopPropagation()} style={{ width: 500, padding: 24, overflowY: 'auto' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--tprm-border)', paddingBottom: 16 }}>
              <div>
                <h3 style={{ margin: 0, fontSize: '1.1rem', color: 'var(--tprm-text-primary)' }}>
                  Finding Detail & Review
                </h3>
                <span style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)', color: 'var(--tprm-text-muted)' }}>
                  {selectedFinding.id}
                </span>
              </div>
              <button
                onClick={() => setSelectedFinding(null)}
                className="optiv-btn-header icon-only"
              >
                <X size={16} />
              </button>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 16, marginTop: 20 }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                <div style={{ background: 'var(--tprm-surface-subtle)', padding: 10, borderRadius: 6 }}>
                  <div style={{ fontSize: '0.7rem', color: 'var(--tprm-text-muted)' }}>ENTITY CATEGORY</div>
                  <div style={{ fontWeight: 700, marginTop: 2 }}>{selectedFinding.type}</div>
                </div>
                <div style={{ background: 'var(--tprm-surface-subtle)', padding: 10, borderRadius: 6 }}>
                  <div style={{ fontSize: '0.7rem', color: 'var(--tprm-text-muted)' }}>CONFIDENCE SCORE</div>
                  <div style={{ fontWeight: 700, marginTop: 2 }}>{Math.round(selectedFinding.confidence * 100)}%</div>
                </div>
              </div>

              <div>
                <div style={{ fontSize: '0.75rem', color: 'var(--tprm-text-muted)', marginBottom: 4 }}>DETECTION SPAN</div>
                <div style={{ background: 'var(--tprm-surface-subtle)', padding: '8px 12px', borderRadius: 6, fontFamily: 'var(--font-mono)', fontSize: '0.8rem' }}>
                  Characters [{selectedFinding.start}, {selectedFinding.end}) • Length: {selectedFinding.end - selectedFinding.start}
                </div>
              </div>

              <div>
                <div style={{ fontSize: '0.75rem', color: 'var(--tprm-text-muted)', marginBottom: 4 }}>REPLACEMENT MASK</div>
                <div style={{ background: 'var(--tprm-surface-subtle)', padding: '8px 12px', borderRadius: 6, fontFamily: 'var(--font-mono)', fontSize: '0.85rem', color: 'var(--tprm-cyan)' }}>
                  {selectedFinding.masked_value}
                </div>
              </div>

              <div>
                <div style={{ fontSize: '0.75rem', color: 'var(--tprm-text-muted)', marginBottom: 4 }}>RULE & RATIONALE</div>
                <div style={{ background: 'var(--tprm-surface-subtle)', padding: '10px 12px', borderRadius: 6, fontSize: '0.8rem', lineHeight: 1.5 }}>
                  <div style={{ fontWeight: 600, color: 'var(--tprm-text-primary)', marginBottom: 2 }}>{selectedFinding.rule_id}</div>
                  <div style={{ color: 'var(--tprm-text-secondary)' }}>{selectedFinding.rationale}</div>
                </div>
              </div>

              <div>
                <div style={{ fontSize: '0.75rem', color: 'var(--tprm-text-muted)', marginBottom: 4 }}>REVIEWER NOTES / EXCEPTION JUSTIFICATION</div>
                <textarea
                  value={reviewNotes}
                  onChange={(e) => setReviewNotes(e.target.value)}
                  placeholder="Document the justification for confirming or modifying this finding..."
                  style={{
                    width: '100%',
                    height: 80,
                    padding: 10,
                    borderRadius: 6,
                    border: '1px solid var(--tprm-border)',
                    backgroundColor: 'var(--tprm-surface-subtle)',
                    color: 'var(--tprm-text-primary)',
                    fontSize: '0.8rem',
                    resize: 'none',
                    outline: 'none',
                    boxSizing: 'border-box',
                  }}
                />
              </div>

              <div style={{ display: 'flex', gap: 10, marginTop: 8 }}>
                <button
                  onClick={() => handleApplyReview('MASKED')}
                  className="btn-primary"
                  style={{ flex: 1, padding: '9px 12px', fontSize: '0.8rem' }}
                  disabled={updating}
                >
                  <CheckCircle2 size={15} style={{ marginRight: 6 }} />
                  Confirm Redaction
                </button>
                <button
                  onClick={() => handleApplyReview('PRESERVED')}
                  className="btn-secondary"
                  style={{ flex: 1, padding: '9px 12px', fontSize: '0.8rem', color: '#f59e0b' }}
                  disabled={updating}
                >
                  <AlertTriangle size={15} style={{ marginRight: 6 }} />
                  Preserve as Exception
                </button>
              </div>

              <button
                onClick={() => onNavigateToWorkspace(selectedFinding.document_id, selectedFinding.finding_index - 1)}
                className="optiv-btn-header"
                style={{ height: 38, justifyContent: 'center', width: '100%', marginTop: 4 }}
              >
                <ExternalLink size={14} style={{ marginRight: 6 }} />
                <span>Jump to Finding in Workspace Diff</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
