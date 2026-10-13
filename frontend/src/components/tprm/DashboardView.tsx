import React, { useState, useEffect } from 'react';
import {
  ShieldAlert,
  Users,
  Clock,
  AlertTriangle,
  RefreshCw,
  PlusCircle,
  Building,
  TrendingUp,
  Download,
} from 'lucide-react';
import type { DashboardSummary } from '../../types';

interface DashboardViewProps {
  summary?: DashboardSummary | null;
  onNavigate: (tab: any) => void;
  onTriggerReassessments?: () => void;
  loading?: boolean;
  showExportPanel?: boolean;
}

export const DashboardView: React.FC<DashboardViewProps> = ({
  summary: propSummary,
  onNavigate,
  onTriggerReassessments,
  loading: propLoading,
  showExportPanel = false,
}) => {
  const [internalSummary, setInternalSummary] = useState<DashboardSummary | null>(propSummary || null);
  const [loading, setLoading] = useState<boolean>(propLoading !== undefined ? propLoading : !propSummary);
  const [runningJob, setRunningJob] = useState<boolean>(false);
  const [jobBanner, setJobBanner] = useState<string | null>(null);

  const fetchSummary = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/tprm/v1/reports/summary');
      if (res.ok) {
        const data = await res.json();
        setInternalSummary(data);
      }
    } catch (err) {
      console.error('Failed to load dashboard summary', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (propSummary) {
      setInternalSummary(propSummary);
      setLoading(false);
      return;
    }
    fetchSummary();
  }, [propSummary]);

  const handleRunReassessments = async () => {
    if (onTriggerReassessments) {
      onTriggerReassessments();
      return;
    }
    setRunningJob(true);
    setJobBanner(null);
    try {
      const res = await fetch('/api/tprm/v1/tasks/automation/run-reassessments', { method: 'POST' });
      if (res.ok) {
        const data = await res.json();
        setJobBanner(
          `Daily Automation Executed (AR.T1.1 / AR.T2.1 / AR.T3.1): ${data.reassessments_created ?? 0} reassessment(s) launched, ${data.sla_reminders_sent ?? 0} SLA reminder(s) sent.`
        );
        await fetchSummary();
      }
    } catch (e) {
      console.error(e);
    } finally {
      setRunningJob(false);
    }
  };

  const handleExportReport = (reportType: string) => {
    window.open(`/api/tprm/v1/reports/export/${reportType}`, '_blank');
  };

  const summary = internalSummary;

  if (loading || !summary) {
    return (
      <div className="p-12 text-center text-slate-500 bg-white border border-slate-200 rounded-lg">
        <p className="text-sm">Loading live TPRM operational indicators...</p>
      </div>
    );
  }

  const liveVendorsCount = summary.vendors_by_status['Live'] || 0;
  const inProgressCount = summary.vendors_by_status['In Progress'] || 0;

  return (
    <div className="space-y-6">
      <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900">
            {showExportPanel ? 'Operational Reports & Authorized Exports' : 'Third-Party Risk Management Dashboard'}
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            Real-time Integrated Risk Management (IRM) oversight for <strong>Cadence Design Systems</strong> • OneTrust TPRM & Ironclad CLM
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button"
            className="btn btn-secondary"
            onClick={() => handleExportReport('vendors')}
          >
            <Download size={14} />
            <span>Export Vendors CSV</span>
          </button>
          <button
            type="button"
            className="btn btn-secondary"
            onClick={() => handleExportReport('findings')}
          >
            <Download size={14} />
            <span>Export Findings CSV</span>
          </button>
          <button
            type="button"
            className="btn btn-secondary"
            onClick={handleRunReassessments}
            disabled={runningJob}
          >
            <RefreshCw size={14} />
            <span>{runningJob ? 'Running Daily Automation...' : 'Run Daily Reassessment Job'}</span>
          </button>
          <button
            type="button"
            className="btn btn-primary"
            onClick={() => onNavigate('onboarding')}
          >
            <PlusCircle size={14} />
            <span>Onboard New Vendor</span>
          </button>
        </div>
      </div>

      {jobBanner && (
        <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-md text-xs font-medium">
          {jobBanner}
        </div>
      )}

      {/* Primary KPI Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div
          className="bg-white border border-slate-200 rounded-lg p-4 shadow-sm cursor-pointer"
          onClick={() => onNavigate('directory')}
        >
          <div className="flex items-center justify-between text-xs font-semibold text-slate-500">
            <span>TOTAL THIRD PARTIES</span>
            <Users size={18} className="text-indigo-600" />
          </div>
          <div className="text-2xl font-bold text-slate-900 mt-2">{summary.total_vendors}</div>
          <div className="text-xs text-slate-500 mt-1">
            <span className="text-emerald-600 font-semibold">{liveVendorsCount} Live</span> • {inProgressCount} In Progress
          </div>
        </div>

        <div
          className="bg-white border border-slate-200 rounded-lg p-4 shadow-sm cursor-pointer"
          onClick={() => onNavigate('findings')}
        >
          <div className="flex items-center justify-between text-xs font-semibold text-slate-500">
            <span>HIGH INHERENT RISKS</span>
            <ShieldAlert size={18} className="text-rose-600" />
          </div>
          <div className="text-2xl font-bold text-rose-600 mt-2">{summary.risk_findings.high}</div>
          <div className="text-xs text-slate-500 mt-1">
            {summary.risk_findings.medium} Medium • {summary.risk_findings.open} Total Open Findings
          </div>
        </div>

        <div
          className="bg-white border border-slate-200 rounded-lg p-4 shadow-sm cursor-pointer"
          onClick={() => onNavigate('assessments')}
        >
          <div className="flex items-center justify-between text-xs font-semibold text-slate-500">
            <span>PENDING ASSESSMENTS</span>
            <Clock size={18} className="text-amber-500" />
          </div>
          <div className="text-2xl font-bold text-amber-600 mt-2">{summary.assessments.pending}</div>
          <div className="text-xs text-slate-500 mt-1">
            {summary.assessments.approved} Approved • {summary.assessments.rejected} Rejected
          </div>
        </div>

        <div
          className="bg-white border border-slate-200 rounded-lg p-4 shadow-sm cursor-pointer"
          onClick={() => onNavigate('tasks')}
        >
          <div className="flex items-center justify-between text-xs font-semibold text-slate-500">
            <span>PENDING TASKS & SLAS</span>
            <AlertTriangle size={18} className="text-purple-600" />
          </div>
          <div className="text-2xl font-bold text-slate-900 mt-2">{summary.sla_and_tasks.pending_tasks}</div>
          <div className="text-xs text-slate-500 mt-1">
            <span className={summary.sla_and_tasks.overdue_tasks > 0 ? 'text-rose-600 font-bold' : 'text-slate-400'}>
              {summary.sla_and_tasks.overdue_tasks} Overdue SLAs
            </span>
            {' • '}
            <span>{summary.sla_and_tasks.reassessments_due} Reassessments Due</span>
          </div>
        </div>
      </div>

      {/* Grid: Categories & Tiers Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div className="flex items-center gap-2">
              <Building size={16} className="text-indigo-600" />
              <h3 className="text-sm font-bold text-slate-900">Vendor Category Distribution (Section 2.1 / 4.1)</h3>
            </div>
            <span className="badge badge-neutral">5 Documented Categories</span>
          </div>
          <div className="space-y-3">
            {Object.entries(summary.vendors_by_category).map(([cat, count]) => {
              const pct = summary.total_vendors > 0 ? Math.round((count / summary.total_vendors) * 100) : 0;
              return (
                <div key={cat} className="space-y-1">
                  <div className="flex justify-between text-xs">
                    <span className="font-medium text-slate-800">{cat}</span>
                    <span className="text-slate-500">{count} vendor(s) ({pct}%)</span>
                  </div>
                  <div style={{ width: '100%', backgroundColor: '#e2e8f0', height: '8px', borderRadius: '9999px', overflow: 'hidden' }}>
                    <div style={{ width: `${pct}%`, backgroundColor: '#4f46e5', height: '8px', borderRadius: '9999px' }} />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div className="flex items-center gap-2">
              <TrendingUp size={16} className="text-indigo-600" />
              <h3 className="text-sm font-bold text-slate-900">Vendor Risk Tier & Reassessment Cadence (Section 2.3)</h3>
            </div>
            <span className="badge badge-neutral">Separate from Category</span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div className="p-3.5 bg-rose-50 rounded-lg border border-rose-200">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-rose-800">Tier 1</span>
                <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-white text-rose-800 border border-rose-200">
                  12m / 275d (SLA.6)
                </span>
              </div>
              <div className="text-2xl font-bold text-rose-900 mt-2">{summary.vendors_by_tier['Tier 1'] || 0}</div>
              <p className="text-[11px] text-slate-600 mt-1">
                Annual review cadence. Uses Due Diligence Questionnaire T1-2 v1.
              </p>
            </div>

            <div className="p-3.5 bg-amber-50 rounded-lg border border-amber-200">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-amber-800">Tier 2</span>
                <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-white text-amber-800 border border-amber-200">
                  24m / 640d (SLA.7)
                </span>
              </div>
              <div className="text-2xl font-bold text-amber-900 mt-2">{summary.vendors_by_tier['Tier 2'] || 0}</div>
              <p className="text-[11px] text-slate-600 mt-1">
                24-month review cadence. Uses Due Diligence Questionnaire T1-2 v1.
              </p>
            </div>

            <div className="p-3.5 bg-emerald-50 rounded-lg border border-emerald-200">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-emerald-800">Tier 3</span>
                <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-white text-emerald-800 border border-emerald-200">
                  24m / 640d (SLA.7)
                </span>
              </div>
              <div className="text-2xl font-bold text-emerald-900 mt-2">{summary.vendors_by_tier['Tier 3'] || 0}</div>
              <p className="text-[11px] text-slate-600 mt-1">
                24-month cadence. Uses DDQ T3 v1 with Auto-Approve rule QR.73 / WR.T3.3.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Authorized Reports & Export Center */}
      <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm space-y-3">
        <h3 className="text-sm font-bold text-slate-900">Authorized Compliance & Audit Report Exports (Section 24)</h3>
        <p className="text-xs text-slate-500">
          Every report export queries real persisted relational rows, respects RBAC access boundaries, and records a tamper-evident <code>REPORT_EXPORTED</code> audit event.
        </p>
        <div className="flex flex-wrap gap-3 pt-1">
          <button type="button" className="btn btn-secondary" onClick={() => handleExportReport('vendors')}>
            <Download size={14} /> Download Vendor Inventory & Classification CSV
          </button>
          <button type="button" className="btn btn-secondary" onClick={() => handleExportReport('assessments')}>
            <Download size={14} /> Download Assessment Status & Scores CSV
          </button>
          <button type="button" className="btn btn-secondary" onClick={() => handleExportReport('findings')}>
            <Download size={14} /> Download Appendix E Risk Findings & Controls CSV
          </button>
          <button type="button" className="btn btn-secondary" onClick={() => handleExportReport('audit')}>
            <Download size={14} /> Download Immutable Audit Trail CSV
          </button>
        </div>
      </div>
    </div>
  );
};
