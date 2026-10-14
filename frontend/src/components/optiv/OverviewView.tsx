import React, { useState, useEffect } from 'react';
import {
  FileText,
  PlaySquare,
  ShieldAlert,
  ShieldCheck,
  AlertTriangle,
  Clock,
  CheckCircle,
  XCircle,
  ArrowRight,
  TrendingUp,
  RefreshCw,
} from 'lucide-react';
import type { OverviewMetrics, UserProfile, ProcessResponse } from '../../types';

interface OverviewViewProps {
  currentUser: UserProfile;
  activeDocument?: ProcessResponse | null;
  onNavigateToWorkspace: (documentId?: string) => void;
  onNavigateToTab: (tab: any) => void;
}

export const OverviewView: React.FC<OverviewViewProps> = ({
  currentUser,
  activeDocument,
  onNavigateToWorkspace,
  onNavigateToTab,
}) => {
  const [metrics, setMetrics] = useState<OverviewMetrics | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchMetrics = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/overview/metrics', {
        headers: { 'X-User-Email': currentUser.email },
      });
      if (res.ok) {
        const data = await res.json();
        setMetrics(data);
      }
    } catch (err) {
      console.warn('Failed to fetch overview metrics', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMetrics();
  }, [currentUser.email]);

  const kpis = [
    {
      title: 'Documents Received',
      value: metrics?.documents_received ?? 0,
      icon: <FileText size={20} color="var(--tprm-indigo)" />,
      change: 'Ingested & Parsed',
      tab: 'runs',
    },
    {
      title: 'Runs Completed',
      value: metrics?.processing_runs_completed ?? 0,
      icon: <PlaySquare size={20} color="var(--tprm-cyan)" />,
      change: 'E2E Pipeline Runs',
      tab: 'runs',
    },
    {
      title: 'PII Findings Flagged',
      value: metrics?.findings_detected ?? 0,
      icon: <ShieldAlert size={20} color="#ef4444" />,
      change: 'Sensitive Spans',
      tab: 'findings',
    },
    {
      title: 'Successfully Masked',
      value: metrics?.findings_successfully_masked ?? 0,
      icon: <ShieldCheck size={20} color="var(--tprm-emerald)" />,
      change: 'Redacted Contextually',
      tab: 'redaction',
    },
    {
      title: 'Verification Failures',
      value: metrics?.verification_failures ?? 0,
      icon: <AlertTriangle size={20} color="#f59e0b" />,
      change: 'Residual PII Caught',
      tab: 'verification',
    },
    {
      title: 'Awaiting Review',
      value: metrics?.documents_awaiting_review ?? 0,
      icon: <Clock size={20} color="#8b5cf6" />,
      change: 'Manual Review Queue',
      tab: 'findings',
    },
    {
      title: 'Blocked from Release',
      value: metrics?.documents_blocked_from_release ?? 0,
      icon: <XCircle size={20} color="var(--tprm-rose)" />,
      change: 'Withheld at Gate',
      tab: 'verification',
    },
    {
      title: 'Approved for Release',
      value: metrics?.documents_approved_for_release ?? 0,
      icon: <CheckCircle size={20} color="var(--tprm-emerald)" />,
      change: 'Cleared for Downstream',
      tab: 'reports',
    },
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      {/* Header Banner */}
      <div className="optiv-card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 16 }}>
        <div>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 700, margin: 0, color: 'var(--tprm-text-primary)' }}>
            OPTIV Document Privacy & Control Operations
          </h2>
          <p style={{ fontSize: '0.825rem', color: 'var(--tprm-text-muted)', margin: '4px 0 0' }}>
            Multi-stage scanning, PII redaction pipeline, independent verification gates, and tamper-evident audit logs.
          </p>
        </div>

        <div style={{ display: 'flex', gap: 10 }}>
          <button
            onClick={fetchMetrics}
            className="btn-secondary"
            style={{ fontSize: '0.8rem', padding: '6px 12px' }}
            disabled={loading}
          >
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
            <span>Refresh</span>
          </button>
          <button
            onClick={() => onNavigateToWorkspace()}
            className="btn-primary"
            style={{ fontSize: '0.8rem', padding: '6px 14px' }}
          >
            <FileText size={15} />
            <span>Open Document Workspace</span>
          </button>
        </div>
      </div>

      {/* Active Document Highlight Banner */}
      {activeDocument && (
        <div className="optiv-doc-banner">
          <div className="optiv-doc-banner-info">
            <div className="optiv-doc-icon-wrap" style={{ backgroundColor: activeDocument.release_allowed ? 'var(--tprm-emerald-light)' : 'rgba(239, 68, 68, 0.15)', color: activeDocument.release_allowed ? 'var(--tprm-emerald)' : 'var(--tprm-rose)' }}>
              <FileText size={22} />
            </div>
            <div className="optiv-doc-meta">
              <div className="optiv-doc-title-row">
                <span className="optiv-doc-title">Active Document: {activeDocument.document_id}</span>
                <span className={`badge ${activeDocument.release_allowed ? 'badge-success' : 'badge-danger'}`}>
                  {activeDocument.release_allowed ? 'RELEASE AUTHORIZED' : 'GATE BLOCKED'}
                </span>
                <span className="badge badge-info">{activeDocument.source_type?.toUpperCase()}</span>
              </div>
              <div className="optiv-doc-stats-row">
                <span>Findings: <strong style={{ color: 'var(--tprm-text-primary)' }}>{activeDocument.entities?.length ?? activeDocument.redactions_applied ?? 0}</strong></span>
                <span>•</span>
                <span>Redactions Applied: <strong style={{ color: 'var(--tprm-text-primary)' }}>{activeDocument.redactions_applied ?? 0}</strong></span>
                <span>•</span>
                <span>Verification: <strong style={{ color: activeDocument.verification_status === 'PASS' ? 'var(--tprm-emerald)' : 'var(--tprm-rose)' }}>{activeDocument.verification_status || 'UNKNOWN'}</strong></span>
              </div>
            </div>
          </div>
          <div style={{ display: 'flex', gap: 10 }}>
            <button
              onClick={() => onNavigateToTab('findings')}
              className="optiv-btn-header"
            >
              Inspect {activeDocument.entities?.length ?? activeDocument.redactions_applied ?? 0} Findings
            </button>
            <button
              onClick={() => onNavigateToWorkspace(activeDocument.document_id)}
              className="btn-primary"
              style={{ fontSize: '0.8rem', padding: '6px 14px' }}
            >
              View in Diff Workspace
            </button>
          </div>
        </div>
      )}

      {/* KPI Cards Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 16 }}>
        {kpis.map((kpi, idx) => (
          <div
            key={idx}
            className="optiv-card"
            style={{ cursor: 'pointer', transition: 'all 0.15s ease' }}
            onClick={() => onNavigateToTab(kpi.tab)}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
              <span style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--tprm-text-secondary)' }}>
                {kpi.title}
              </span>
              <div style={{ padding: 6, borderRadius: 8, backgroundColor: 'var(--tprm-surface-subtle)' }}>
                {kpi.icon}
              </div>
            </div>
            <div style={{ fontSize: '1.75rem', fontWeight: 800, color: 'var(--tprm-text-primary)', marginBottom: 4 }}>
              {loading ? '-' : kpi.value}
            </div>
            <div style={{ fontSize: '0.725rem', color: 'var(--tprm-text-muted)', display: 'flex', alignItems: 'center', gap: 4 }}>
              <TrendingUp size={12} color="var(--tprm-emerald)" />
              <span>{kpi.change}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Two Column Layout: Category Distribution & Recent Runs */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(420px, 1fr))', gap: 20 }}>
        {/* Left: Category Distribution */}
        <div className="optiv-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
            <h3 style={{ fontSize: '1rem', fontWeight: 700, margin: 0, color: 'var(--tprm-text-primary)' }}>
              PII Category Detection Distribution
            </h3>
            <span style={{ fontSize: '0.75rem', color: 'var(--tprm-text-muted)' }}>Live Counts</span>
          </div>

          {metrics?.category_breakdown && Object.keys(metrics.category_breakdown).length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              {Object.entries(metrics.category_breakdown).map(([category, count]) => {
                const total = metrics.findings_detected || 1;
                const pct = Math.round((count / total) * 100);
                return (
                  <div key={category}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', marginBottom: 4 }}>
                      <span style={{ fontWeight: 600, color: 'var(--tprm-text-primary)' }}>{category}</span>
                      <span style={{ color: 'var(--tprm-text-muted)', fontFamily: 'var(--font-mono)' }}>
                        {count} ({pct}%)
                      </span>
                    </div>
                    <div style={{ width: '100%', height: 6, backgroundColor: 'var(--tprm-surface-subtle)', borderRadius: 3, overflow: 'hidden' }}>
                      <div
                        style={{
                          width: `${pct}%`,
                          height: '100%',
                          backgroundColor:
                            category.includes('GOV') || category.includes('CARD') || category.includes('SSN')
                              ? '#ef4444'
                              : category.includes('EMAIL')
                              ? '#06b6d4'
                              : category.includes('PHONE')
                              ? '#10b981'
                              : '#6366f1',
                          borderRadius: 3,
                        }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div style={{ padding: '32px 16px', textAlign: 'center', color: 'var(--tprm-text-muted)', fontSize: '0.85rem' }}>
              No PII detections recorded yet. Process a document or demo scenario in the workspace.
            </div>
          )}
        </div>

        {/* Right: Governance Posture & Mandates */}
        <div className="optiv-card" style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          <h3 style={{ fontSize: '1rem', fontWeight: 700, margin: 0, color: 'var(--tprm-text-primary)' }}>
            Governance Mandates & System Invariants
          </h3>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            <div style={{ padding: 12, borderRadius: 8, backgroundColor: 'var(--tprm-surface-subtle)', border: '1px solid var(--tprm-border)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                <CheckCircle size={16} color="var(--tprm-emerald)" />
                <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--tprm-text-primary)' }}>
                  Zero-Leakage Release Gate
                </span>
              </div>
              <p style={{ fontSize: '0.75rem', color: 'var(--tprm-text-muted)', margin: 0, lineHeight: 1.4 }}>
                Documents are released if and only if independent post-redaction verification produces a strict <code>PASS</code>.
              </p>
            </div>

            <div style={{ padding: 12, borderRadius: 8, backgroundColor: 'var(--tprm-surface-subtle)', border: '1px solid var(--tprm-border)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                <CheckCircle size={16} color="var(--tprm-emerald)" />
                <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--tprm-text-primary)' }}>
                  80% Structure Retention Invariant
                </span>
              </div>
              <p style={{ fontSize: '0.75rem', color: 'var(--tprm-text-muted)', margin: 0, lineHeight: 1.4 }}>
                Preceding and succeeding layout context is preserved so downstream LLMs can interpret business content.
              </p>
            </div>

            <div style={{ padding: 12, borderRadius: 8, backgroundColor: 'var(--tprm-surface-subtle)', border: '1px solid var(--tprm-border)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                <CheckCircle size={16} color="var(--tprm-emerald)" />
                <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--tprm-text-primary)' }}>
                  Metadata-Only Audit Projection
                </span>
              </div>
              <p style={{ fontSize: '0.75rem', color: 'var(--tprm-text-muted)', margin: 0, lineHeight: 1.4 }}>
                Zero sensitive document text or matched PII values are retained in audit records or exported reports.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Activity Table */}
      <div className="optiv-card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <h3 style={{ fontSize: '1rem', fontWeight: 700, margin: 0, color: 'var(--tprm-text-primary)' }}>
            Recent Processing Activity
          </h3>
          <button
            onClick={() => onNavigateToTab('runs')}
            className="btn-link"
            style={{ fontSize: '0.8rem', display: 'flex', alignItems: 'center', gap: 4 }}
          >
            <span>View All Runs</span>
            <ArrowRight size={14} />
          </button>
        </div>

        {metrics?.recent_activity && metrics.recent_activity.length > 0 ? (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--tprm-border)', color: 'var(--tprm-text-muted)', textAlign: 'left' }}>
                  <th style={{ padding: '10px 12px' }}>Document ID</th>
                  <th style={{ padding: '10px 12px' }}>Filename</th>
                  <th style={{ padding: '10px 12px' }}>Format</th>
                  <th style={{ padding: '10px 12px' }}>Verification</th>
                  <th style={{ padding: '10px 12px' }}>Release Gate</th>
                  <th style={{ padding: '10px 12px' }}>Duration</th>
                  <th style={{ padding: '10px 12px', textAlign: 'right' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {metrics.recent_activity.map((run, idx) => (
                  <tr key={idx} style={{ borderBottom: '1px solid var(--tprm-border)' }}>
                    <td style={{ padding: '10px 12px', fontFamily: 'var(--font-mono)', fontWeight: 600 }}>
                      {run.document_id}
                    </td>
                    <td style={{ padding: '10px 12px' }}>{run.original_filename || 'document.txt'}</td>
                    <td style={{ padding: '10px 12px' }}>
                      <span className="badge badge-generic">{run.source_type || run.file_type || 'txt'}</span>
                    </td>
                    <td style={{ padding: '10px 12px' }}>
                      <span className={`badge ${run.verification_status === 'PASS' ? 'badge-success' : 'badge-gov'}`}>
                        {run.verification_status || 'PENDING'}
                      </span>
                    </td>
                    <td style={{ padding: '10px 12px' }}>
                      <span className={`badge ${run.release_allowed ? 'badge-success' : 'badge-warning'}`}>
                        {run.release_allowed ? 'AUTHORIZED' : 'WITHHELD'}
                      </span>
                    </td>
                    <td style={{ padding: '10px 12px', fontFamily: 'var(--font-mono)' }}>
                      {(run.duration_sec || 0).toFixed(3)}s
                    </td>
                    <td style={{ padding: '10px 12px', textAlign: 'right' }}>
                      <button
                        onClick={() => onNavigateToWorkspace(run.document_id)}
                        className="btn-secondary"
                        style={{ fontSize: '0.75rem', padding: '4px 8px' }}
                      >
                        Inspect
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div style={{ padding: '32px 16px', textAlign: 'center', color: 'var(--tprm-text-muted)', fontSize: '0.85rem' }}>
            No recent processing runs found.
          </div>
        )}
      </div>
    </div>
  );
};
