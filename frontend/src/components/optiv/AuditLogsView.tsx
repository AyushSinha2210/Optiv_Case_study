import React, { useState, useEffect } from 'react';
import {
  Search,
  Download,
  RefreshCw,
  CheckCircle,
  XCircle,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import type { UserProfile, AuditEvent } from '../../types';

interface AuditLogsViewProps {
  currentUser: UserProfile;
}

export const AuditLogsView: React.FC<AuditLogsViewProps> = ({ currentUser }) => {
  const [events, setEvents] = useState<AuditEvent[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [stageFilter, setStageFilter] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [expandedEventId, setExpandedEventId] = useState<string | null>(null);

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
    const headers = ['event_id', 'document_id', 'timestamp', 'stage', 'event_type', 'status', 'verification_status', 'release_decision'];
    const rows = events.map((e) => [
      e.event_id || '',
      e.document_id || '',
      e.timestamp || '',
      e.stage || '',
      e.event_type || '',
      e.status || '',
      e.verification_status || '',
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

  const filteredEvents = events.filter((e) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      (e.event_id && e.event_id.toLowerCase().includes(q)) ||
      (e.document_id && e.document_id.toLowerCase().includes(q)) ||
      (e.event_type && e.event_type.toLowerCase().includes(q))
    );
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      {/* Header & Controls */}
      <div className="optiv-card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 14 }}>
        <div>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 700, margin: 0, color: 'var(--tprm-text-primary)' }}>
            Tamper-Evident Immutable Audit Trail
          </h2>
          <p style={{ fontSize: '0.8rem', color: 'var(--tprm-text-muted)', margin: '4px 0 0' }}>
            Allowlist metadata serialization guaranteeing zero document text or PII leakage in audit records.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
          {/* Search */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '6px 10px', borderRadius: 6, border: '1px solid var(--tprm-border)', backgroundColor: 'var(--tprm-surface)' }}>
            <Search size={14} color="var(--tprm-text-muted)" />
            <input
              type="text"
              placeholder="Search Event ID, Doc ID..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{ border: 'none', background: 'transparent', outline: 'none', fontSize: '0.8rem', color: 'var(--tprm-text-primary)' }}
            />
          </div>

          {/* Stage Filter */}
          <select
            value={stageFilter}
            onChange={(e) => setStageFilter(e.target.value)}
            style={{
              padding: '6px 10px',
              borderRadius: 6,
              border: '1px solid var(--tprm-border)',
              backgroundColor: 'var(--tprm-surface)',
              color: 'var(--tprm-text-primary)',
              fontSize: '0.8rem',
            }}
          >
            <option value="ALL">All Lifecycle Stages</option>
            <option value="RECEIVED">RECEIVED</option>
            <option value="VALIDATED">VALIDATED</option>
            <option value="EXTRACTED">EXTRACTED</option>
            <option value="DETECTED">DETECTED</option>
            <option value="REDACTED">REDACTED</option>
            <option value="VERIFIED">VERIFIED</option>
            <option value="RELEASED">RELEASED</option>
            <option value="FAILED">FAILED</option>
          </select>

          <button onClick={handleExportJSON} className="btn-secondary" style={{ padding: '6px 12px', fontSize: '0.8rem' }}>
            <Download size={13} />
            <span>JSON</span>
          </button>
          <button onClick={handleExportCSV} className="btn-secondary" style={{ padding: '6px 12px', fontSize: '0.8rem' }}>
            <Download size={13} />
            <span>CSV</span>
          </button>
          <button onClick={fetchAuditEvents} className="btn-secondary" style={{ padding: '6px 10px', fontSize: '0.8rem' }}>
            <RefreshCw size={13} className={loading ? 'animate-spin' : ''} />
          </button>
        </div>
      </div>

      {/* Events Timeline List */}
      <div className="optiv-card" style={{ padding: 0, overflow: 'hidden' }}>
        {loading ? (
          <div style={{ padding: 40, textAlign: 'center', color: 'var(--tprm-text-muted)', fontSize: '0.85rem' }}>
            Loading audit records...
          </div>
        ) : filteredEvents.length === 0 ? (
          <div style={{ padding: 40, textAlign: 'center', color: 'var(--tprm-text-muted)', fontSize: '0.85rem' }}>
            No audit records found matching current criteria.
          </div>
        ) : (
          <div>
            {filteredEvents.map((evt, idx) => {
              const isExpanded = expandedEventId === (evt.event_id || `evt-${idx}`);
              const isSuccess = evt.status === 'success';

              return (
                <div
                  key={idx}
                  style={{
                    borderBottom: '1px solid var(--tprm-border)',
                    backgroundColor: isExpanded ? 'var(--tprm-surface-subtle)' : undefined,
                  }}
                >
                  <div
                    onClick={() => setExpandedEventId(isExpanded ? null : (evt.event_id || `evt-${idx}`))}
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
                          <span style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--tprm-text-primary)' }}>
                            {evt.event_type}
                          </span>
                          <span className="badge badge-generic" style={{ fontSize: '0.65rem' }}>
                            {evt.stage}
                          </span>
                        </div>
                        <div style={{ fontSize: '0.725rem', color: 'var(--tprm-text-muted)', fontFamily: 'var(--font-mono)', marginTop: 2 }}>
                          {evt.event_id || 'evt-system'} • Doc: {evt.document_id || 'doc-general'}
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
                      <div style={{ backgroundColor: 'var(--tprm-surface)', padding: 12, borderRadius: 6, border: '1px solid var(--tprm-border)', fontFamily: 'var(--font-mono)' }}>
                        <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>
                          {JSON.stringify(evt, null, 2)}
                        </pre>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};
