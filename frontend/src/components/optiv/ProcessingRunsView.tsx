import React, { useState, useEffect } from 'react';
import {
  Search,
  Download,
  Eye,
  RefreshCw,
} from 'lucide-react';
import type { UserProfile } from '../../types';

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

  const filteredRuns = runs.filter((r) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      r.document_id.toLowerCase().includes(q) ||
      (r.original_filename && r.original_filename.toLowerCase().includes(q))
    );
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      {/* Header & Filter Controls */}
      <div className="optiv-card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 14 }}>
        <div>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 700, margin: 0, color: 'var(--tprm-text-primary)' }}>
            Historical Processing Runs Ledger
          </h2>
          <p style={{ fontSize: '0.8rem', color: 'var(--tprm-text-muted)', margin: '4px 0 0' }}>
            Persisted execution records, stage transitions, and fail-closed barrier evaluations.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
          {/* Search Box */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '6px 10px', borderRadius: 6, border: '1px solid var(--tprm-border)', backgroundColor: 'var(--tprm-surface)' }}>
            <Search size={14} color="var(--tprm-text-muted)" />
            <input
              type="text"
              placeholder="Search Document ID or name..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{ border: 'none', background: 'transparent', outline: 'none', fontSize: '0.8rem', color: 'var(--tprm-text-primary)' }}
            />
          </div>

          {/* Status Filter */}
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            style={{
              padding: '6px 12px',
              borderRadius: 6,
              border: '1px solid var(--tprm-border)',
              backgroundColor: 'var(--tprm-surface)',
              color: 'var(--tprm-text-primary)',
              fontSize: '0.8rem',
            }}
          >
            <option value="all">All Outcomes</option>
            <option value="success">Success / Released</option>
            <option value="blocked">Blocked Gate</option>
            <option value="failed">Extraction / Validation Failed</option>
          </select>

          <button
            onClick={fetchRuns}
            className="btn-secondary"
            style={{ padding: '6px 12px', fontSize: '0.8rem' }}
          >
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Runs Table */}
      <div className="optiv-card" style={{ padding: 0, overflow: 'hidden' }}>
        {loading ? (
          <div style={{ padding: 40, textAlign: 'center', color: 'var(--tprm-text-muted)', fontSize: '0.85rem' }}>
            Loading processing runs...
          </div>
        ) : filteredRuns.length === 0 ? (
          <div style={{ padding: 40, textAlign: 'center', color: 'var(--tprm-text-muted)', fontSize: '0.85rem' }}>
            No processing runs match current criteria.
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--tprm-border)', backgroundColor: 'var(--tprm-surface-subtle)', color: 'var(--tprm-text-muted)', textAlign: 'left' }}>
                  <th style={{ padding: '12px 16px' }}>Document ID</th>
                  <th style={{ padding: '12px 16px' }}>Filename</th>
                  <th style={{ padding: '12px 16px' }}>Format</th>
                  <th style={{ padding: '12px 16px' }}>Verification</th>
                  <th style={{ padding: '12px 16px' }}>Release Gate</th>
                  <th style={{ padding: '12px 16px' }}>PII Masked</th>
                  <th style={{ padding: '12px 16px' }}>Duration</th>
                  <th style={{ padding: '12px 16px', textAlign: 'right' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredRuns.map((r, idx) => (
                  <tr key={idx} style={{ borderBottom: '1px solid var(--tprm-border)' }}>
                    <td style={{ padding: '12px 16px', fontFamily: 'var(--font-mono)', fontWeight: 600 }}>
                      {r.document_id}
                    </td>
                    <td style={{ padding: '12px 16px', color: 'var(--tprm-text-primary)' }}>
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
                    <td style={{ padding: '12px 16px', fontFamily: 'var(--font-mono)', fontSize: '0.8rem' }}>
                      {(r.duration_sec || 0).toFixed(3)}s
                    </td>
                    <td style={{ padding: '12px 16px', textAlign: 'right' }}>
                      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 6 }}>
                        <button
                          onClick={() => onInspectRun(r.document_id)}
                          className="btn-secondary"
                          style={{ padding: '4px 8px', fontSize: '0.75rem', display: 'flex', alignItems: 'center', gap: 4 }}
                        >
                          <Eye size={13} />
                          <span>Inspect</span>
                        </button>
                        {r.release_allowed && (
                          <button
                            onClick={() => window.open(`/api/artifact/${r.document_id}`, '_blank')}
                            className="btn-secondary"
                            style={{ padding: '4px 8px', fontSize: '0.75rem' }}
                            title="Download Sanitized Output"
                          >
                            <Download size={13} />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
