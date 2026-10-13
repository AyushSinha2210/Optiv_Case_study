import React, { useState, useEffect } from 'react';
import {
  Calendar,
  Clock,
  Play,
  CheckCircle2,
  AlertTriangle,
  RotateCw,
  Search,
} from 'lucide-react';
import type { VendorItem, UserProfile } from '../../types';

interface ReassessmentsViewProps {
  currentUser?: UserProfile;
  onRefreshMetrics?: () => void;
}

export const ReassessmentsView: React.FC<ReassessmentsViewProps> = ({
  currentUser,
  onRefreshMetrics,
}) => {
  const [vendors, setVendors] = useState<VendorItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [runningJob, setRunningJob] = useState<boolean>(false);
  const [jobResult, setJobResult] = useState<any | null>(null);
  const [search, setSearch] = useState<string>('');
  const [tierFilter, setTierFilter] = useState<string>('All');
  const [launchingId, setLaunchingId] = useState<string | null>(null);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const fetchVendors = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/tprm/v1/vendors', {
        headers: currentUser ? { 'X-User-Email': currentUser.email } : {},
      });
      if (res.ok) {
        const data = await res.json();
        setVendors(data.items || []);
      }
    } catch (err) {
      console.error('Failed to load vendors for reassessments', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchVendors();
  }, []);

  const handleRunDailyAutomation = async () => {
    setRunningJob(true);
    setMessage(null);
    setJobResult(null);
    try {
      const res = await fetch('/api/tprm/v1/tasks/automation/run-reassessments', {
        method: 'POST',
        headers: currentUser ? { 'X-User-Email': currentUser.email } : {},
      });
      if (res.ok) {
        const result = await res.json();
        setJobResult(result);
        setMessage({
          type: 'success',
          text: `Daily Reassessment Automation Executed (AR.T1.1 >= 275d, AR.T2.1 >= 640d, AR.T3.1 >= 640d): ${result.reassessments_created ?? 0} reassessment(s) launched (Copy Previous Assessment = Yes) and ${result.notifications_sent ?? 0} notifications ('Vendor Upcoming Re-Assessment') dispatched.`,
        });
        await fetchVendors();
        onRefreshMetrics?.();
      } else {
        setMessage({ type: 'error', text: 'Failed to run reassessment engine' });
      }
    } catch (err) {
      setMessage({ type: 'error', text: 'Network error invoking automation' });
    } finally {
      setRunningJob(false);
    }
  };

  const handleLaunchReassessment = async (vendor: VendorItem) => {
    setLaunchingId(vendor.id);
    setMessage(null);
    try {
      const res = await fetch('/api/tprm/v1/assessments', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(currentUser ? { 'X-User-Email': currentUser.email } : {}),
        },
        body: JSON.stringify({
          vendor_id: vendor.id,
          template_code: vendor.vendor_tier === 'Tier 3' ? 'T3_v1' : 'T1-2_v1',
        }),
      });
      if (res.ok) {
        setMessage({
          type: 'success',
          text: `Reassessment questionnaire (${vendor.vendor_tier === 'Tier 3' ? 'T3_v1' : 'T1-2_v1'}) launched for ${vendor.name}. Primary Vendor Contact notified.`,
        });
        await fetchVendors();
        onRefreshMetrics?.();
      } else {
        const err = await res.json();
        setMessage({ type: 'error', text: err.detail || 'Failed to initiate reassessment' });
      }
    } catch (err) {
      setMessage({ type: 'error', text: 'Network error launching reassessment' });
    } finally {
      setLaunchingId(null);
    }
  };

  const filteredVendors = vendors.filter((v) => {
    const matchesSearch =
      search === '' ||
      v.name.toLowerCase().includes(search.toLowerCase()) ||
      v.vendor_category.toLowerCase().includes(search.toLowerCase());
    const matchesTier = tierFilter === 'All' || v.vendor_tier === tierFilter;
    return matchesSearch && matchesTier;
  });

  return (
    <div className="space-y-6">
      <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <Calendar size={20} className="text-indigo-600" />
            <h1 className="text-xl font-bold text-slate-900">Reassessment Automation & Renewal Schedule</h1>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Appendix A Automation Rules (<code>AR.T1.1</code>, <code>AR.T2.1</code>, <code>AR.T3.1</code>) & Appendix D Timelines (<code>SLA.6</code>: 275 days, <code>SLA.7</code>: 640 days).
          </p>
        </div>

        <div className="flex items-center gap-2">
          {jobResult && (
            <span className="badge badge-info">
              Launched: {jobResult.reassessments_created} | Reminders: {jobResult.sla_reminders_sent}
            </span>
          )}
          <button
            type="button"
            onClick={fetchVendors}
            className="btn btn-sm btn-secondary"
          >
            <RotateCw size={13} /> Refresh
          </button>
          <button
            type="button"
            onClick={handleRunDailyAutomation}
            disabled={runningJob}
            className="btn btn-primary"
          >
            <Play size={14} />
            <span>{runningJob ? 'Running Daily Automation...' : 'Run Daily Reassessment Job'}</span>
          </button>
        </div>
      </div>

      {message && (
        <div
          className={`p-4 rounded-md border text-xs font-medium flex items-center gap-3 ${
            message.type === 'success'
              ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
              : 'bg-rose-50 border-rose-200 text-rose-800'
          }`}
        >
          {message.type === 'success' ? (
            <CheckCircle2 size={16} className="text-emerald-600 shrink-0" />
          ) : (
            <AlertTriangle size={16} className="text-rose-600 shrink-0" />
          )}
          <span>{message.text}</span>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-800">AR.T1.1 — Tier 1 Reassessment</span>
            <span className="badge badge-alert">Annual (275 Days / SLA.6)</span>
          </div>
          <p className="text-xs text-slate-500 mt-2">
            Daily check: when Last Assessment Completion Date &ge; <strong>275 days</strong> (90 days before 1 year), sends <code>Due Diligence Questionnaire T1-2 v1</code> with <code>Copy Previous Assessment = Yes</code> and emails Business Owners (<code>Vendor Upcoming Re-Assessment</code>).
          </p>
        </div>

        <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-800">AR.T2.1 — Tier 2 Reassessment</span>
            <span className="badge badge-warning">24 Months (640 Days / SLA.7)</span>
          </div>
          <p className="text-xs text-slate-500 mt-2">
            Daily check: when Last Assessment Completion Date &ge; <strong>640 days</strong> (90 days before 2 years), sends <code>Due Diligence Questionnaire T1-2 v1</code> with <code>Copy Previous Assessment = Yes</code> and notifies Business Owners.
          </p>
        </div>

        <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-800">AR.T3.1 — Tier 3 Reassessment</span>
            <span className="badge badge-success">24 Months (640 Days / SLA.7)</span>
          </div>
          <p className="text-xs text-slate-500 mt-2">
            Daily check: when Last Assessment Completion Date &ge; <strong>640 days</strong> (revised from earlier 3-year process to 2 years), sends <code>Due Diligence Questionnaire T3 v1</code> with <code>Copy Previous Assessment = Yes</code>.
          </p>
        </div>
      </div>

      <div className="bg-white border border-slate-200 rounded-lg p-4 shadow-sm flex flex-wrap items-center justify-between gap-4">
        <div className="relative flex-1 max-w-sm">
          <Search size={14} className="text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search vendor by name or category..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 text-xs border border-slate-300 rounded-md bg-slate-50"
          />
        </div>

        <div className="flex items-center gap-2">
          <label className="text-xs font-medium text-slate-600">Filter Tier:</label>
          <select
            value={tierFilter}
            onChange={(e) => setTierFilter(e.target.value)}
            className="text-xs border border-slate-300 rounded px-2.5 py-1.5 bg-slate-50"
          >
            <option value="All">All Tiers</option>
            <option value="Tier 1">Tier 1 (Annual / 275d)</option>
            <option value="Tier 2">Tier 2 (24 Months / 640d)</option>
            <option value="Tier 3">Tier 3 (24 Months / 640d)</option>
          </select>
        </div>
      </div>

      <div className="bg-white border border-slate-200 rounded-lg shadow-sm overflow-x-auto">
        {loading ? (
          <div className="p-12 text-center text-slate-500">
            <p className="text-sm">Calculating reassessment deadlines...</p>
          </div>
        ) : (
          <table className="enterprise-table">
            <thead>
              <tr>
                <th>Vendor Name</th>
                <th>Tier & Category</th>
                <th>Last Assessment Completion</th>
                <th>Next Reassessment Due</th>
                <th>Renewal Status</th>
                <th>Lifecycle Status</th>
                <th className="text-right">Action</th>
              </tr>
            </thead>
            <tbody>
              {filteredVendors.map((vendor) => {
                const dueDate = vendor.next_reassessment_due_date
                  ? new Date(vendor.next_reassessment_due_date)
                  : null;
                const isDueSoon = dueDate && (dueDate.getTime() - Date.now()) / (1000 * 3600 * 24) <= 90;

                return (
                  <tr key={vendor.id}>
                    <td className="font-semibold text-slate-900">
                      {vendor.name}
                      <div className="text-[11px] text-slate-500 font-mono">{vendor.primary_vendor_contact}</div>
                    </td>
                    <td>
                      <span className={`tier-pill tier-pill-${vendor.vendor_tier.slice(-1)} mr-2`}>
                        {vendor.vendor_tier}
                      </span>
                      <span className="text-xs text-slate-600">{vendor.vendor_category}</span>
                    </td>
                    <td className="text-xs">
                      {vendor.last_assessment_completion_date
                        ? new Date(vendor.last_assessment_completion_date).toLocaleDateString()
                        : 'Initial Onboarding'}
                    </td>
                    <td className="text-xs">
                      {dueDate ? (
                        <div className="flex items-center gap-1.5">
                          <Clock size={13} className={isDueSoon ? 'text-rose-600' : 'text-slate-400'} />
                          <span className={isDueSoon ? 'text-rose-600 font-bold' : 'text-slate-800'}>
                            {dueDate.toLocaleDateString()} {isDueSoon ? '(Within 90d SLA Window)' : ''}
                          </span>
                        </div>
                      ) : (
                        <span className="text-slate-400">Set upon Live</span>
                      )}
                    </td>
                    <td>
                      <span className="badge badge-neutral">{vendor.renewal_status || 'Active'}</span>
                    </td>
                    <td>
                      <span className={`badge ${vendor.lifecycle_status === 'Live' ? 'badge-success' : 'badge-info'}`}>
                        {vendor.lifecycle_status}
                      </span>
                    </td>
                    <td className="text-right">
                      <button
                        type="button"
                        onClick={() => handleLaunchReassessment(vendor)}
                        disabled={launchingId === vendor.id}
                        className="btn btn-sm btn-secondary"
                      >
                        {launchingId === vendor.id ? 'Launching...' : 'Launch Reassessment'}
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};
