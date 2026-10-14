import React, { useState, useEffect, useMemo } from 'react';
import {
  Search,
  Download,
  Eye,
  RefreshCw,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import type { UserProfile } from '../../types';
import { PageHeader } from './PageHeader';
import { CopyButton } from './CopyButton';

interface ProcessingRunsViewProps {
  currentUser: UserProfile;
  onInspectRun: (documentId: string) => void;
}

export const ProcessingRunsView: React.FC<ProcessingRunsViewProps> = ({
  currentUser,
  onInspectRun,
}) => {
  const [runs, setRuns] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [pageSize, setPageSize] = useState<number>(15);

  const fetchRuns = async () => {
    setLoading(true);
    try {
      const url = statusFilter !== 'all' ? `/api/runs?status=${statusFilter}` : '/api/runs';
      const res = await fetch(url, {
        headers: { 'X-User-Email': currentUser.email },
      });
      if (res.ok) {
        const data = await res.json();
        setRuns(data.runs || []);
      }
    } catch (err) {
      console.warn('Failed to fetch processing runs', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRuns();
  }, [statusFilter, currentUser.email]);

  // Reset page when filter or search changes
  useEffect(() => {
    setCurrentPage(1);
  }, [searchQuery, statusFilter]);

  const filteredRuns = useMemo(() => {
    return runs.filter((r) => {
      if (!searchQuery) return true;
      const q = searchQuery.toLowerCase();
      return (
        r.document_id.toLowerCase().includes(q) ||
        (r.original_filename && r.original_filename.toLowerCase().includes(q))
      );
    });
  }, [runs, searchQuery]);

  const totalPages = Math.max(1, Math.ceil(filteredRuns.length / pageSize));
  const paginatedRuns = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return filteredRuns.slice(start, start + pageSize);
  }, [filteredRuns, currentPage, pageSize]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      {/* Unified Page Header */}
      <PageHeader
        title="Historical Processing Runs Ledger"
        description="Persisted document execution records, multi-stage transitions, duration telemetry, and fail-closed barrier evaluations."
        actions={
          <button
            onClick={fetchRuns}
            className="btn-secondary"
            disabled={loading}
            title="Refresh processing runs from server"
          >
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
            <span>Refresh Ledger</span>
          </button>
        }
      />

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
                placeholder="Search Document ID or filename..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>

            <select
              className="optiv-select"
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              aria-label="Filter runs by release status"
            >
              <option value="all">All Release Outcomes</option>
              <option value="success">Release Authorized</option>
              <option value="blocked">Release Withheld / Blocked</option>
              <option value="failed">Extraction / Validation Failed</option>
            </select>
          </div>

          <div style={{ fontSize: '0.8rem', color: 'var(--tprm-text-muted)' }}>
            Total Recorded Runs: <strong style={{ color: 'var(--tprm-text-primary)' }}>{runs.length}</strong>
          </div>
        </div>
      </div>

      {/* Runs Table with deliberate column widths & single-line IDs */}
      <div className="optiv-card" style={{ padding: 0, overflow: 'hidden' }}>
        {loading ? (
          <div style={{ padding: 48, textAlign: 'center', color: 'var(--tprm-text-muted)', fontSize: '0.85rem' }}>
            <RefreshCw size={20} className="animate-spin" style={{ margin: '0 auto 8px auto', display: 'block' }} />
            <span>Loading processing runs ledger...</span>
          </div>
        ) : filteredRuns.length === 0 ? (
          <div style={{ padding: 48, textAlign: 'center', color: 'var(--tprm-text-muted)', fontSize: '0.85rem' }}>
            No processing runs match the selected criteria.
          </div>
        ) : (
          <div style={{ overflowX: 'auto', width: '100%' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem', tableLayout: 'auto' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--tprm-border)', backgroundColor: 'var(--tprm-surface-subtle)', color: 'var(--tprm-text-muted)', textAlign: 'left' }}>
                  <th style={{ padding: '12px 16px', minWidth: 220, maxWidth: 280 }}>Document ID</th>
                  <th style={{ padding: '12px 16px', minWidth: 160 }}>Filename</th>
                  <th style={{ padding: '12px 16px', width: 90 }}>Format</th>
                  <th style={{ padding: '12px 16px', width: 140 }}>Verification</th>
                  <th style={{ padding: '12px 16px', width: 160 }}>Release Gate</th>
                  <th style={{ padding: '12px 16px', width: 120 }}>PII Masked</th>
                  <th style={{ padding: '12px 16px', width: 90 }}>Duration</th>
                  <th style={{ padding: '12px 16px', width: 120, textAlign: 'right' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {paginatedRuns.map((r, idx) => (
                  <tr
                    key={r.document_id || idx}
                    style={{
                      borderBottom: '1px solid var(--tprm-border)',
                      transition: 'background-color 0.15s ease',
                      cursor: 'pointer',
                    }}
                    onClick={() => onInspectRun(r.document_id)}
                    onMouseEnter={(e) => (e.currentTarget.style.backgroundColor = 'var(--tprm-surface-subtle)')}
                    onMouseLeave={(e) => (e.currentTarget.style.backgroundColor = 'transparent')}
                  >
                    <td style={{ padding: '12px 16px' }}>
                      <div className="optiv-doc-id-cell">
                        <span className="optiv-doc-id-text" title={r.document_id}>
                          {r.document_id}
                        </span>
                        <CopyButton text={r.document_id} />
                      </div>
                    </td>
                    <td style={{ padding: '12px 16px', color: 'var(--tprm-text-primary)', fontWeight: 500 }}>
                      {r.original_filename || 'document.txt'}
                    </td>
                    <td style={{ padding: '12px 16px' }}>
                      <span className="badge badge-generic">{r.source_type || r.file_type || 'txt'}</span>
                    </td>
                    <td style={{ padding: '12px 16px' }}>
                      <span className={`badge ${r.verification_status === 'PASS' ? 'badge-success' : 'badge-gov'}`}>
                        {r.verification_status || 'PENDING'}
                      </span>
                    </td>
                    <td style={{ padding: '12px 16px' }}>
                      <span className={`badge ${r.release_allowed ? 'badge-success' : 'badge-warning'}`}>
                        {r.release_allowed ? 'RELEASE AUTHORIZED' : 'WITHHELD'}
                      </span>
                    </td>
                    <td style={{ padding: '12px 16px', fontFamily: 'var(--font-mono)' }}>
                      {r.redactions_applied || 0} entities
                    </td>
                    <td style={{ padding: '12px 16px', fontFamily: 'var(--font-mono)', fontSize: '0.8rem', color: 'var(--tprm-text-muted)' }}>
                      {(r.duration_sec || 0).toFixed(3)}s
                    </td>
                    <td style={{ padding: '12px 16px', textAlign: 'right' }} onClick={(e) => e.stopPropagation()}>
                      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 6 }}>
                        <button
                          onClick={() => onInspectRun(r.document_id)}
                          className="optiv-btn-header"
                          style={{ height: 30, padding: '0 8px', fontSize: '0.75rem' }}
                          title="Inspect document diff and findings"
                        >
                          <Eye size={13} />
                          <span>Inspect</span>
                        </button>
                        {r.release_allowed && (
                          <button
                            onClick={() => window.open(`/api/artifact/${r.document_id}`, '_blank')}
                            className="optiv-btn-header icon-only"
                            style={{ height: 30, width: 30 }}
                            title="Download verified sanitized artifact"
                          >
                            <Download size={13} color="var(--tprm-emerald)" />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {/* Pagination Controls */}
            {filteredRuns.length > 0 && (
              <div className="optiv-pagination">
                <div className="optiv-pagination-info">
                  Showing <strong>{(currentPage - 1) * pageSize + 1}</strong> to{' '}
                  <strong>{Math.min(currentPage * pageSize, filteredRuns.length)}</strong> of{' '}
                  <strong>{filteredRuns.length}</strong> recorded runs
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
                      <option value={15}>15</option>
                      <option value={30}>30</option>
                      <option value={50}>50</option>
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
    </div>
  );
};
