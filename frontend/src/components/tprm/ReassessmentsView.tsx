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
import type { VendorItem } from '../../types';

export const ReassessmentsView: React.FC = () => {
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
      const res = await fetch('/api/tprm/v1/vendors');
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
      });
      if (res.ok) {
        const result = await res.json();
        setJobResult(result);
        setMessage({
          type: 'success',
          text: `Daily automated reassessment scan completed: ${result.reassessments_created} reassessment tasks and ${result.notifications_sent} notifications dispatched.`,
        });
        await fetchVendors();
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
      // Trigger reassessment workflow or create assessment
      const res = await fetch('/api/tprm/v1/assessments', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          vendor_id: vendor.id,
          template_code: vendor.vendor_tier === 'Tier 3' ? 'T3_v1' : 'T1-2_v1',
        }),
      });
      if (res.ok) {
        setMessage({
          type: 'success',
          text: `Reassessment successfully initiated for ${vendor.name}. Respondent notified.`,
        });
        await fetchVendors();
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
      {/* Header Banner */}
      <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <Calendar className="w-6 h-6 text-indigo-600" />
            <h1 className="text-xl font-bold text-slate-900">Periodic Reassessment Schedule</h1>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Section 21 Cadence Policy: Tier 1 every 12 months (275d trigger), Tier 2 & Tier 3 every 24 months (640d trigger).
          </p>
        </div>

        <div className="flex items-center gap-3">
          {jobResult && (
            <span className="text-xs bg-indigo-50 text-indigo-700 px-2 py-1 rounded border border-indigo-200">
              Tasks: {jobResult.reassessments_created} | Notifs: {jobResult.notifications_sent}
            </span>
          )}
          <button
            onClick={fetchVendors}
            className="p-1.5 text-slate-500 hover:text-slate-800 border border-slate-200 rounded hover:bg-slate-50"
            title="Refresh Vendors"
          >
            <RotateCw className="w-4 h-4" />
          </button>
          <button
            onClick={handleRunDailyAutomation}
            disabled={runningJob}
            className="inline-flex items-center gap-2 px-3.5 py-2 text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-700 rounded-md transition-colors shadow-sm disabled:opacity-50"
          >
            <Play className="w-3.5 h-3.5 fill-current" />
            {runningJob ? 'Executing Reassessment Engine...' : 'Run Daily Automation Job'}
          </button>
        </div>
      </div>

      {message && (
        <div
          className={`p-4 rounded-md border text-sm flex items-center gap-3 ${
            message.type === 'success'
              ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
              : 'bg-rose-50 border-rose-200 text-rose-800'
          }`}
        >
          {message.type === 'success' ? (
            <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />
          ) : (
            <AlertTriangle className="w-5 h-5 text-rose-600 shrink-0" />
          )}
          <span>{message.text}</span>
        </div>
      )}

      {/* Cadence Policy Reference Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-800">Tier 1 Vendors</span>
            <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-rose-50 text-rose-700 border border-rose-200">
              12 Months Cycle
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-2">
            Reassessment tasks initiated at <strong>275 days (9 months)</strong> post-approval. 90-day grace period for due diligence.
          </p>
        </div>

        <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-800">Tier 2 Vendors</span>
            <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-amber-50 text-amber-700 border border-amber-200">
              24 Months Cycle
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-2">
            Reassessment tasks initiated at <strong>640 days (21 months)</strong> post-approval. 90-day grace period before renewal.
          </p>
        </div>

        <div className="bg-white p-4 rounded-lg border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-800">Tier 3 Vendors</span>
            <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200">
              24 Months Cycle
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-2">
            Reassessment tasks initiated at <strong>640 days</strong> post-approval. Utilizes Due Diligence Questionnaire T3 v1.
          </p>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="bg-white border border-slate-200 rounded-lg p-4 shadow-sm flex flex-wrap items-center justify-between gap-4">
        <div className="relative flex-1 max-w-sm">
          <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search vendor by name or category..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 text-xs border border-slate-300 rounded-md bg-slate-50 focus:bg-white focus:outline-none"
          />
        </div>

        <div className="flex items-center gap-2">
          <label className="text-xs font-medium text-slate-600">Filter Tier:</label>
          <select
            value={tierFilter}
            onChange={(e) => setTierFilter(e.target.value)}
            className="text-xs border border-slate-300 rounded px-2.5 py-1.5 bg-slate-50 focus:outline-none"
          >
            <option value="All">All Tiers</option>
            <option value="Tier 1">Tier 1 (Annual)</option>
            <option value="Tier 2">Tier 2 (Biennial)</option>
            <option value="Tier 3">Tier 3 (Biennial)</option>
          </select>
        </div>
      </div>

      {/* Schedule Table */}
      <div className="bg-white border border-slate-200 rounded-lg shadow-sm overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-slate-500">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mb-3"></div>
            <p className="text-sm">Calculating reassessment deadlines...</p>
          </div>
        ) : filteredVendors.length === 0 ? (
          <div className="p-12 text-center text-slate-500">
            <Calendar className="w-10 h-10 text-slate-300 mx-auto mb-2" />
            <p className="text-sm font-medium text-slate-700">No Reassessment Records</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200 text-[11px] font-bold text-slate-600 uppercase tracking-wider">
                  <th className="py-3 px-4">Vendor Name</th>
                  <th className="py-3 px-4">Tier & Category</th>
                  <th className="py-3 px-4">Last Assessment</th>
                  <th className="py-3 px-4">Next Due Date</th>
                  <th className="py-3 px-4">Lifecycle Status</th>
                  <th className="py-3 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 text-xs text-slate-700">
                {filteredVendors.map((vendor) => {
                  const dueDate = vendor.next_reassessment_due_date
                    ? new Date(vendor.next_reassessment_due_date)
                    : null;
                  const isDue = dueDate && dueDate <= new Date();

                  return (
                    <tr key={vendor.id} className="hover:bg-slate-50/80 transition-colors">
                      <td className="py-3 px-4 font-semibold text-slate-900 whitespace-nowrap">
                        {vendor.name}
                        <div className="text-[11px] text-slate-400 font-normal">{vendor.primary_vendor_contact}</div>
                      </td>
                      <td className="py-3 px-4 whitespace-nowrap">
                        <span
                          className={`font-semibold px-2 py-0.5 rounded text-[10px] mr-2 ${
                            vendor.vendor_tier === 'Tier 1'
                              ? 'bg-rose-100 text-rose-800'
                              : vendor.vendor_tier === 'Tier 2'
                              ? 'bg-amber-100 text-amber-800'
                              : 'bg-emerald-100 text-emerald-800'
                          }`}
                        >
                          {vendor.vendor_tier}
                        </span>
                        <span className="text-slate-600">{vendor.vendor_category}</span>
                      </td>
                      <td className="py-3 px-4 whitespace-nowrap">
                        {vendor.last_assessment_completion_date ? (
                          new Date(vendor.last_assessment_completion_date).toLocaleDateString()
                        ) : (
                          <span className="text-slate-400">Initial Onboarding</span>
                        )}
                      </td>
                      <td className="py-3 px-4 whitespace-nowrap">
                        {dueDate ? (
                          <div className="flex items-center gap-1.5">
                            <Clock
                              className={`w-3.5 h-3.5 ${isDue ? 'text-rose-600' : 'text-slate-400'}`}
                            />
                            <span className={isDue ? 'text-rose-600 font-bold' : 'text-slate-800'}>
                              {dueDate.toLocaleDateString()}
                            </span>
                          </div>
                        ) : (
                          <span className="text-slate-400">Calculated upon Live</span>
                        )}
                      </td>
                      <td className="py-3 px-4 whitespace-nowrap">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                            vendor.lifecycle_status === 'Live'
                              ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                              : 'bg-slate-100 text-slate-700 border border-slate-200'
                          }`}
                        >
                          {vendor.lifecycle_status}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-right whitespace-nowrap">
                        <button
                          onClick={() => handleLaunchReassessment(vendor)}
                          disabled={launchingId === vendor.id}
                          className="px-2.5 py-1 text-xs font-semibold text-indigo-600 hover:text-indigo-800 hover:bg-indigo-50 border border-indigo-200 rounded transition-colors disabled:opacity-50"
                        >
                          {launchingId === vendor.id ? 'Launching...' : 'Initiate Reassessment'}
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
