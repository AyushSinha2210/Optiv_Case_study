import React, { useState, useEffect, useMemo } from 'react';
import {
  Search,
  Download,
  RefreshCw,
  CheckCircle,
  XCircle,
  ChevronDown,
  ChevronUp,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import type { UserProfile, AuditEvent } from '../../types';
import { PageHeader } from './PageHeader';
import { CopyButton } from './CopyButton';

interface AuditLogsViewProps {
  currentUser: UserProfile;
}

export const AuditLogsView: React.FC<AuditLogsViewProps> = ({ currentUser }) => {
  const [events, setEvents] = useState<AuditEvent[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [stageFilter, setStageFilter] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [expandedEventId, setExpandedEventId] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [pageSize, setPageSize] = useState<number>(15);

  const fetchAuditEvents = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (stageFilter !== 'ALL') params.append('stage', stageFilter);
      params.append('limit', '100');

      const res = await fetch(`/api/audit?${params.toString()}`, {
        headers: { 'X-User-Email': currentUser.email },
      });
      if (res.ok) {
        const data = await res.json();
        setEvents(data.events || []);
      }
    } catch (err) {
      console.warn('Failed to fetch audit events', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAuditEvents();
  }, [stageFilter, currentUser.email]);

  useEffect(() => {
    setCurrentPage(1);
  }, [searchQuery, stageFilter]);

  const handleExportJSON = () => {
    const dataStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(events, null, 2));
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute('href', dataStr);
    downloadAnchor.setAttribute('download', `optiv_audit_trail_${new Date().toISOString().slice(0, 10)}.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
  };

  const handleExportCSV = () => {
    if (events.length === 0) return;
    const headers = ['EventID', 'Timestamp', 'EventType', 'Stage', 'DocumentID', 'Status', 'ReleaseDecision'];
    const rows = events.map((e) => [
      e.event_id || '',
      e.timestamp || '',
      e.event_type || '',
      e.stage || '',
      e.document_id || '',
      e.status || '',
      e.release_decision ? 'TRUE' : 'FALSE',
    ]);
    const csvContent = [headers.join(','), ...rows.map((r) => r.map((c) => `"${c}"`).join(','))].join('\n');
    const dataStr = 'data:text/csv;charset=utf-8,' + encodeURIComponent(csvContent);
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute('href', dataStr);
    downloadAnchor.setAttribute('download', `optiv_audit_trail_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
  };

  const filteredEvents = useMemo(() => {
    return events.filter((e) => {
      if (!searchQuery) return true;
      const q = searchQuery.toLowerCase();
      return (
        (e.event_id && e.event_id.toLowerCase().includes(q)) ||
        (e.document_id && e.document_id.toLowerCase().includes(q)) ||
        (e.event_type && e.event_type.toLowerCase().includes(q))
      );
    });
  }, [events, searchQuery]);

  const totalPages = Math.max(1, Math.ceil(filteredEvents.length / pageSize));
  const paginatedEvents = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return filteredEvents.slice(start, start + pageSize);
  }, [filteredEvents, currentPage, pageSize]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      {/* Unified Page Header */}
      <PageHeader
        title="Tamper-Evident Immutable Audit Trail"
        description="Append-only cryptographic audit records with strict metadata-only projection: zero document text or PII leaked."
        actions={
          <div style={{ display: 'flex', gap: 8 }}>
            <button
              onClick={handleExportJSON}
              className="btn-secondary"
              disabled={events.length === 0}
              title="Export all events in JSON format"
            >
              <Download size={14} />
              <span>Export JSON</span>
            </button>
            <button
              onClick={handleExportCSV}
              className="btn-secondary"
              disabled={events.length === 0}
              title="Export all events in CSV format"
            >
              <Download size={14} />
              <span>Export CSV</span>
            </button>
            <button
              onClick={fetchAuditEvents}
              className="btn-secondary"
              disabled={loading}
              title="Refresh audit trail"
            >
              <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
              <span>Refresh</span>
            </button>
          </div>
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
                placeholder="Search Event ID, Doc ID, Type..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>

            <select
              className="optiv-select"
              value={stageFilter}
              onChange={(e) => setStageFilter(e.target.value)}
              aria-label="Filter audit events by pipeline stage"
            >
              <option value="ALL">All Lifecycle Stages</option>
              <option value="INGESTION">Ingestion</option>
              <option value="NORMALIZATION">Normalization</option>
              <option value="DETECTION">Detection</option>
              <option value="REDACTION">Redaction</option>
              <option value="VERIFICATION">Verification</option>
              <option value="RELEASE_GATE">Release Gate</option>
            </select>
          </div>

          <div style={{ fontSize: '0.8rem', color: 'var(--tprm-text-muted)' }}>
            Total Audit Records: <strong style={{ color: 'var(--tprm-text-primary)' }}>{events.length}</strong>
          </div>
        </div>
      </div>

      {/* Events Timeline List */}
      <div className="optiv-card" style={{ padding: 0, overflow: 'hidden' }}>
        {loading ? (
          <div style={{ padding: 48, textAlign: 'center', color: 'var(--tprm-text-muted)', fontSize: '0.85rem' }}>
            <RefreshCw size={20} className="animate-spin" style={{ margin: '0 auto 8px auto', display: 'block' }} />
            <span>Loading immutable audit records...</span>
          </div>
        ) : filteredEvents.length === 0 ? (
          <div style={{ padding: 48, textAlign: 'center', color: 'var(--tprm-text-muted)', fontSize: '0.85rem' }}>
            No audit records match the selected criteria.
          </div>
        ) : (
          <div>
            {paginatedEvents.map((evt, idx) => {
              const eventKey = evt.event_id || `evt-${idx}`;
              const isExpanded = expandedEventId === eventKey;
              const isSuccess = evt.status === 'success';

              return (
                <div
                  key={eventKey}
                  style={{
                    borderBottom: '1px solid var(--tprm-border)',
                    backgroundColor: isExpanded ? 'var(--tprm-surface-subtle)' : undefined,
                  }}
                >
                  <div
                    onClick={() => setExpandedEventId(isExpanded ? null : eventKey)}
                    style={{
                      padding: '14px 20px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      cursor: 'pointer',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
                      <div style={{ padding: 6, borderRadius: '50%', backgroundColor: isSuccess ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)' }}>
                        {isSuccess ? <CheckCircle size={15} color="var(--tprm-emerald)" /> : <XCircle size={15} color="var(--tprm-rose)" />}
                      </div>

                      <div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                          <span style={{ fontSize: '0.875rem', fontWeight: 700, color: 'var(--tprm-text-primary)' }}>
                            {evt.event_type}
                          </span>
                          <span className="badge badge-generic" style={{ fontSize: '0.675rem' }}>
                            {evt.stage}
                          </span>
                        </div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: '0.725rem', color: 'var(--tprm-text-muted)', fontFamily: 'var(--font-mono)', marginTop: 2 }}>
                          <span>{evt.event_id || 'evt-system'}</span>
                          <span>&bull;</span>
                          <span>Doc: {evt.document_id || 'general'}</span>
                          {evt.document_id && <CopyButton text={evt.document_id} iconSize={11} />}
                        </div>
                      </div>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
                      <span style={{ fontSize: '0.75rem', color: 'var(--tprm-text-muted)', fontFamily: 'var(--font-mono)' }}>
                        {evt.timestamp ? new Date(evt.timestamp).toLocaleString() : ''}
                      </span>
                      {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                    </div>
                  </div>

                  {/* Expanded Event Details */}
                  {isExpanded && (
                    <div style={{ padding: '0 20px 16px 20px', fontSize: '0.75rem', color: 'var(--tprm-text-secondary)' }}>
                      <div style={{ backgroundColor: 'var(--tprm-surface)', padding: 14, borderRadius: 8, border: '1px solid var(--tprm-border)', fontFamily: 'var(--font-mono)' }}>
                        <pre style={{ margin: 0, whiteSpace: 'pre-wrap', lineHeight: 1.5 }}>
                          {JSON.stringify(evt, null, 2)}
                        </pre>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}

            {/* Pagination Controls */}
            {filteredEvents.length > 0 && (
              <div className="optiv-pagination">
                <div className="optiv-pagination-info">
                  Showing <strong>{(currentPage - 1) * pageSize + 1}</strong> to{' '}
                  <strong>{Math.min(currentPage * pageSize, filteredEvents.length)}</strong> of{' '}
                  <strong>{filteredEvents.length}</strong> audit records
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
