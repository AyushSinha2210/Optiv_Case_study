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
} from 'lucide-react';
import type { DashboardSummary } from '../../types';

interface DashboardViewProps {
  summary?: DashboardSummary | null;
  onNavigate: (tab: any) => void;
  onTriggerReassessments?: () => void;
  loading?: boolean;
}

export const DashboardView: React.FC<DashboardViewProps> = ({
  summary: propSummary,
  onNavigate,
  onTriggerReassessments,
  loading: propLoading,
}) => {
  const [internalSummary, setInternalSummary] = useState<DashboardSummary | null>(propSummary || null);
  const [loading, setLoading] = useState<boolean>(propLoading !== undefined ? propLoading : !propSummary);
  const [runningJob, setRunningJob] = useState<boolean>(false);

  useEffect(() => {
    if (propSummary) {
      setInternalSummary(propSummary);
      setLoading(false);
      return;
    }
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
    fetchSummary();
  }, [propSummary]);

  const handleRunReassessments = async () => {
    if (onTriggerReassessments) {
      onTriggerReassessments();
      return;
    }
    setRunningJob(true);
    try {
      const res = await fetch('/api/tprm/v1/tasks/automation/run-reassessments', { method: 'POST' });
      if (res.ok) {
        // Refresh summary
        const sumRes = await fetch('/api/tprm/v1/reports/summary');
        if (sumRes.ok) {
          const data = await sumRes.json();
          setInternalSummary(data);
        }
      }
    } catch (e) {
      console.error(e);
    } finally {
      setRunningJob(false);
    }
  };

  const summary = internalSummary;

  if (loading || !summary) {
    return (
      <div className="p-12 text-center text-slate-500 bg-white border border-slate-200 rounded-lg">
        <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mb-3"></div>
        <p className="text-sm">Loading live TPRM operational indicators...</p>
      </div>
    );
  }

  const liveVendorsCount = summary.vendors_by_status['Live'] || 0;
  const inProgressCount = summary.vendors_by_status['In Progress'] || 0;

  return (
    <div className="space-y-6">
      {/* Top Banner / Welcome */}
      <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900">Third-Party Risk Management Dashboard</h2>
          <p className="text-xs text-slate-500 mt-1">
            Real-time governance oversight for <strong>Cadence Financial Group</strong> • Integrated OneTrust & Ironclad Workstreams
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-slate-700 bg-slate-100 hover:bg-slate-200 border border-slate-300 rounded-md transition-colors"
            onClick={handleRunReassessments}
            disabled={runningJob}
          >
            <RefreshCw size={14} className={runningJob ? 'animate-spin' : ''} />
            <span>{runningJob ? 'Running Job...' : 'Run Reassessment Scheduler'}</span>
          </button>
          <button
            className="inline-flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-700 rounded-md transition-colors shadow-sm"
            onClick={() => onNavigate('onboarding')}
          >
            <PlusCircle size={14} />
            <span>Onboard New Vendor</span>
          </button>
        </div>
      </div>

      {/* Primary KPI Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div
          className="bg-white border border-slate-200 rounded-lg p-4 shadow-xs hover:border-indigo-400 cursor-pointer transition-colors"
          onClick={() => onNavigate('directory')}
        >
          <div className="flex items-center justify-between text-xs font-semibold text-slate-500">
            <span>TOTAL THIRD PARTIES</span>
            <Users className="w-5 h-5 text-indigo-600" />
          </div>
          <div className="text-2xl font-bold text-slate-900 mt-2">{summary.total_vendors}</div>
          <div className="text-xs text-slate-500 mt-1">
            <span className="text-emerald-600 font-medium">{liveVendorsCount} Live</span> • {inProgressCount} In Review
          </div>
        </div>

        <div
          className="bg-white border border-slate-200 rounded-lg p-4 shadow-xs hover:border-rose-400 cursor-pointer transition-colors"
          onClick={() => onNavigate('findings')}
        >
          <div className="flex items-center justify-between text-xs font-semibold text-slate-500">
            <span>HIGH INHERENT RISKS</span>
            <ShieldAlert className="w-5 h-5 text-rose-600" />
          </div>
          <div className="text-2xl font-bold text-rose-600 mt-2">{summary.risk_findings.high}</div>
          <div className="text-xs text-slate-500 mt-1">
            {summary.risk_findings.medium} Medium • {summary.risk_findings.low} Low Risks
          </div>
        </div>

        <div
          className="bg-white border border-slate-200 rounded-lg p-4 shadow-xs hover:border-amber-400 cursor-pointer transition-colors"
          onClick={() => onNavigate('assessments')}
        >
          <div className="flex items-center justify-between text-xs font-semibold text-slate-500">
            <span>PENDING ASSESSMENTS</span>
            <Clock className="w-5 h-5 text-amber-500" />
          </div>
          <div className="text-2xl font-bold text-amber-600 mt-2">{summary.assessments.pending}</div>
          <div className="text-xs text-slate-500 mt-1">
            {summary.assessments.approved} Approved • {summary.assessments.rejected} Rejected
          </div>
        </div>

        <div
          className="bg-white border border-slate-200 rounded-lg p-4 shadow-xs hover:border-purple-400 cursor-pointer transition-colors"
          onClick={() => onNavigate('tasks')}
        >
          <div className="flex items-center justify-between text-xs font-semibold text-slate-500">
            <span>PENDING TASKS & SLAS</span>
            <AlertTriangle className="w-5 h-5 text-purple-600" />
          </div>
          <div className="text-2xl font-bold text-slate-900 mt-2">{summary.sla_and_tasks.pending_tasks}</div>
          <div className="text-xs text-slate-500 mt-1">
            <span className={summary.sla_and_tasks.overdue_tasks > 0 ? 'text-rose-600 font-bold' : 'text-slate-400'}>
              {summary.sla_and_tasks.overdue_tasks} Overdue SLAs
            </span>
          </div>
        </div>
      </div>

      {/* Grid: Categories & Tiers Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Category Breakdown (Table 4 Taxonomy) */}
        <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div className="flex items-center gap-2">
              <Building size={16} className="text-indigo-600" />
              <h3 className="text-sm font-bold text-slate-900">Third-Party Taxonomy Breakdown (Section 2.1)</h3>
            </div>
            <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-slate-100 text-slate-600 border border-slate-200">
              5 Standard Categories
            </span>
          </div>
          <div className="space-y-3">
            {Object.entries(summary.vendors_by_category).map(([cat, count]) => {
              const pct = summary.total_vendors > 0 ? Math.round((count / summary.total_vendors) * 100) : 0;
              return (
                <div key={cat} className="space-y-1">
                  <div className="flex justify-between text-xs">
                    <span className="font-medium text-slate-700">{cat}</span>
                    <span className="text-slate-500">{count} vendors ({pct}%)</span>
                  </div>
                  <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
                    <div className="bg-indigo-600 h-2 rounded-full" style={{ width: `${pct}%` }}></div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Risk Tiering Breakdown (Table 9) */}
        <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div className="flex items-center gap-2">
              <TrendingUp size={16} className="text-indigo-600" />
              <h3 className="text-sm font-bold text-slate-900">Risk Tier Distribution & Reassessment Cadence</h3>
            </div>
            <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-slate-100 text-slate-600 border border-slate-200">
              Table 9 Criticality
            </span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div className="p-3.5 bg-rose-50/50 rounded-lg border border-rose-200">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-rose-800">Tier 1</span>
                <span className="text-[9px] font-bold px-1.5 py-0.2 rounded bg-rose-200/60 text-rose-800">
                  12m / 275d
                </span>
              </div>
              <div className="text-2xl font-bold text-rose-900 mt-2">{summary.vendors_by_tier['Tier 1'] || 0}</div>
              <p className="text-[11px] text-slate-500 mt-1 leading-snug">
                Annual reassessment. Full Due Diligence Questionnaire T1-2 v1.
              </p>
            </div>

            <div className="p-3.5 bg-amber-50/50 rounded-lg border border-amber-200">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-amber-800">Tier 2</span>
                <span className="text-[9px] font-bold px-1.5 py-0.2 rounded bg-amber-200/60 text-amber-800">
                  24m / 640d
                </span>
              </div>
              <div className="text-2xl font-bold text-amber-900 mt-2">{summary.vendors_by_tier['Tier 2'] || 0}</div>
              <p className="text-[11px] text-slate-500 mt-1 leading-snug">
                Bi-annual reassessment. Full Due Diligence Questionnaire T1-2 v1.
              </p>
            </div>

            <div className="p-3.5 bg-emerald-50/50 rounded-lg border border-emerald-200">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-emerald-800">Tier 3</span>
                <span className="text-[9px] font-bold px-1.5 py-0.2 rounded bg-emerald-200/60 text-emerald-800">
                  24m / 640d
                </span>
              </div>
              <div className="text-2xl font-bold text-emerald-900 mt-2">{summary.vendors_by_tier['Tier 3'] || 0}</div>
              <p className="text-[11px] text-slate-500 mt-1 leading-snug">
                Bi-annual reassessment. Fast-track DDQ T3 v1 with auto-approval (WR.T3.3).
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
