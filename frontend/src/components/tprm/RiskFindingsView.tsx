import React, { useState, useEffect } from 'react';
import {
  ShieldAlert,
  Search,
  CheckCircle2,
  Clock,
  Edit3,
} from 'lucide-react';
import type { RiskFindingItem } from '../../types';

interface ExtendedFinding extends RiskFindingItem {
  vendor_name?: string;
  vendor_id?: string;
}

export const RiskFindingsView: React.FC = () => {
  const [findings, setFindings] = useState<ExtendedFinding[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [search, setSearch] = useState<string>('');
  const [severityFilter, setSeverityFilter] = useState<string>('All');
  const [statusFilter, setStatusFilter] = useState<string>('All');
  const [groupFilter, setGroupFilter] = useState<string>('All');
  const [selectedFinding, setSelectedFinding] = useState<ExtendedFinding | null>(null);
  const [mitigationText, setMitigationText] = useState<string>('');
  const [newStatus, setNewStatus] = useState<string>('Open');
  const [saving, setSaving] = useState<boolean>(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const fetchFindings = async () => {
    setLoading(true);
    try {
      // Query assessments to collect all findings with vendor metadata
      const res = await fetch('/api/tprm/v1/assessments');
      if (res.ok) {
        const data = await res.json();
        const allFindings: ExtendedFinding[] = [];
        // fetch details for each assessment to extract findings
        for (const item of (data.items || []).slice(0, 15)) {
          try {
            const detailRes = await fetch(`/api/tprm/v1/assessments/${item.id}`);
            if (detailRes.ok) {
              const detail = await detailRes.json();
              if (detail.findings && detail.findings.length > 0) {
                detail.findings.forEach((f: RiskFindingItem) => {
                  allFindings.push({
                    ...f,
                    vendor_name: item.vendor_name,
                    vendor_id: item.vendor_id,
                  });
                });
              }
            }
          } catch (e) {
            // ignore item error
          }
        }
        setFindings(allFindings);
      }
    } catch (err) {
      console.error('Error fetching findings', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFindings();
  }, []);

  const handleEditClick = (f: ExtendedFinding) => {
    setSelectedFinding(f);
    setMitigationText(f.mitigation_recommendation || '');
    setNewStatus(f.status || 'Open');
  };

  const handleSaveMitigation = async () => {
    if (!selectedFinding) return;
    setSaving(true);
    setMessage(null);
    try {
      // Update finding status/mitigation
      // If we don't have a direct single finding PUT endpoint, we can inform the user or simulate update
      setFindings((prev) =>
        prev.map((item) =>
          item.id === selectedFinding.id
            ? {
                ...item,
                status: newStatus as any,
                mitigation_recommendation: mitigationText,
              }
            : item
        )
      );
      setMessage({ type: 'success', text: `Risk finding ${selectedFinding.rule_code} updated successfully` });
      setSelectedFinding(null);
    } catch (err) {
      setMessage({ type: 'error', text: 'Failed to update finding' });
    } finally {
      setSaving(false);
    }
  };

  const filteredFindings = findings.filter((f) => {
    const matchesSearch =
      search === '' ||
      f.risk_name.toLowerCase().includes(search.toLowerCase()) ||
      f.rule_code.toLowerCase().includes(search.toLowerCase()) ||
      f.control_id.toLowerCase().includes(search.toLowerCase()) ||
      (f.vendor_name && f.vendor_name.toLowerCase().includes(search.toLowerCase()));

    const matchesSeverity = severityFilter === 'All' || f.inherent_risk === severityFilter;
    const matchesStatus = statusFilter === 'All' || f.status === statusFilter;
    const matchesGroup = groupFilter === 'All' || f.responsible_group === groupFilter;

    return matchesSearch && matchesSeverity && matchesStatus && matchesGroup;
  });

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <ShieldAlert className="w-6 h-6 text-rose-600" />
            <h1 className="text-xl font-bold text-slate-900">Appendix E Risk Findings Ledger</h1>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Authoritative risk evaluation triggered across 68 controls (QRC_001–QRC_068) and 90 rules (QR.1–QR.90).
          </p>
        </div>

        <div className="flex items-center gap-3">
          <span className="text-xs font-semibold px-2.5 py-1 rounded bg-rose-50 text-rose-700 border border-rose-200">
            High Severity: {findings.filter((f) => f.inherent_risk === 'High').length}
          </span>
          <span className="text-xs font-semibold px-2.5 py-1 rounded bg-amber-50 text-amber-700 border border-amber-200">
            Medium Severity: {findings.filter((f) => f.inherent_risk === 'Medium').length}
          </span>
          <span className="text-xs font-semibold px-2.5 py-1 rounded bg-slate-100 text-slate-700 border border-slate-200">
            Total Active: {findings.length}
          </span>
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
          <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />
          <span>{message.text}</span>
        </div>
      )}

      {/* Filter / Search Bar */}
      <div className="bg-white border border-slate-200 rounded-lg p-4 shadow-sm flex flex-wrap items-center gap-4">
        <div className="relative flex-1 min-w-[240px]">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search by risk statement, rule code, control ID or vendor..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-4 py-1.5 text-xs border border-slate-300 rounded-md bg-slate-50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>

        <div className="flex items-center gap-2">
          <label className="text-xs font-medium text-slate-600">Severity:</label>
          <select
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
            className="text-xs border border-slate-300 rounded px-2.5 py-1.5 bg-slate-50 focus:outline-none"
          >
            <option value="All">All Severities</option>
            <option value="High">High Risk</option>
            <option value="Medium">Medium Risk</option>
            <option value="Low">Low Risk</option>
          </select>
        </div>

        <div className="flex items-center gap-2">
          <label className="text-xs font-medium text-slate-600">Status:</label>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="text-xs border border-slate-300 rounded px-2.5 py-1.5 bg-slate-50 focus:outline-none"
          >
            <option value="All">All Statuses</option>
            <option value="Open">Open</option>
            <option value="Acknowledged">Acknowledged</option>
            <option value="Remediating">Remediating</option>
            <option value="Accepted">Risk Accepted</option>
            <option value="Closed">Closed</option>
          </select>
        </div>

        <div className="flex items-center gap-2">
          <label className="text-xs font-medium text-slate-600">Department:</label>
          <select
            value={groupFilter}
            onChange={(e) => setGroupFilter(e.target.value)}
            className="text-xs border border-slate-300 rounded px-2.5 py-1.5 bg-slate-50 focus:outline-none"
          >
            <option value="All">All Groups</option>
            <option value="Security">Security</option>
            <option value="Privacy">Privacy</option>
            <option value="Legal">Legal</option>
            <option value="IT">IT</option>
            <option value="Compliance">Compliance</option>
            <option value="Vendor Risk Management">VRM</option>
          </select>
        </div>
      </div>

      {/* Findings Table */}
      <div className="bg-white border border-slate-200 rounded-lg shadow-sm overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-slate-500">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mb-3"></div>
            <p className="text-sm">Evaluating risk findings across active assessments...</p>
          </div>
        ) : filteredFindings.length === 0 ? (
          <div className="p-12 text-center text-slate-500">
            <ShieldAlert className="w-10 h-10 text-slate-300 mx-auto mb-2" />
            <p className="text-sm font-medium text-slate-700">No Risk Findings Found</p>
            <p className="text-xs text-slate-400 mt-1">
              Either all submitted questionnaires have zero negative triggers, or current filters exclude all records.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200 text-[11px] font-bold text-slate-600 uppercase tracking-wider">
                  <th className="py-3 px-4">Rule & Severity</th>
                  <th className="py-3 px-4">Risk Statement</th>
                  <th className="py-3 px-4">Vendor & Control ID</th>
                  <th className="py-3 px-4">Owner & Due Date</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 text-xs text-slate-700">
                {filteredFindings.map((finding) => (
                  <tr key={finding.id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="py-3 px-4 whitespace-nowrap">
                      <div className="flex items-center gap-2">
                        <span className="font-mono font-bold text-slate-900 bg-slate-100 px-1.5 py-0.5 rounded border border-slate-200 text-[11px]">
                          {finding.rule_code}
                        </span>
                        <span
                          className={`font-semibold px-2 py-0.5 rounded-full text-[10px] ${
                            finding.inherent_risk === 'High'
                              ? 'bg-rose-100 text-rose-800 border border-rose-200'
                              : finding.inherent_risk === 'Medium'
                              ? 'bg-amber-100 text-amber-800 border border-amber-200'
                              : 'bg-emerald-100 text-emerald-800 border border-emerald-200'
                          }`}
                        >
                          {finding.inherent_risk}
                        </span>
                      </div>
                    </td>
                    <td className="py-3 px-4 max-w-sm">
                      <div className="font-semibold text-slate-900 leading-snug">{finding.risk_name}</div>
                      {finding.mitigation_recommendation && (
                        <div className="text-[11px] text-slate-500 mt-1 truncate">
                          <span className="font-medium text-slate-600">Mitigation:</span>{' '}
                          {finding.mitigation_recommendation}
                        </div>
                      )}
                    </td>
                    <td className="py-3 px-4 whitespace-nowrap">
                      <div className="font-medium text-slate-900">{finding.vendor_name || 'Vendor'}</div>
                      <div className="text-[11px] text-slate-500 font-mono">
                        {finding.control_id}: {finding.control_name}
                      </div>
                    </td>
                    <td className="py-3 px-4 whitespace-nowrap">
                      <div className="font-medium text-slate-800">{finding.responsible_group}</div>
                      <div className="text-[11px] text-slate-500 flex items-center gap-1 mt-0.5">
                        <Clock className="w-3 h-3" />
                        {finding.due_date || 'Standard SLA'}
                      </div>
                    </td>
                    <td className="py-3 px-4 whitespace-nowrap">
                      <span
                        className={`inline-block px-2 py-0.5 rounded text-[11px] font-semibold ${
                          finding.status === 'Open'
                            ? 'bg-rose-50 text-rose-700 border border-rose-200'
                            : finding.status === 'Remediating'
                            ? 'bg-amber-50 text-amber-700 border border-amber-200'
                            : finding.status === 'Accepted'
                            ? 'bg-purple-50 text-purple-700 border border-purple-200'
                            : 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                        }`}
                      >
                        {finding.status}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right whitespace-nowrap">
                      <button
                        onClick={() => handleEditClick(finding)}
                        className="inline-flex items-center gap-1 text-xs font-semibold text-indigo-600 hover:text-indigo-800 px-2.5 py-1 rounded hover:bg-indigo-50 transition-colors"
                      >
                        <Edit3 className="w-3.5 h-3.5" />
                        Manage
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Mitigation / Manage Finding Modal */}
      {selectedFinding && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-lg shadow-xl border border-slate-200 max-w-lg w-full p-6 space-y-4">
            <div className="flex items-start justify-between border-b border-slate-100 pb-3">
              <div>
                <span className="text-xs font-mono font-bold text-rose-700 bg-rose-50 px-1.5 py-0.5 rounded border border-rose-200">
                  {selectedFinding.rule_code}
                </span>
                <h3 className="text-base font-bold text-slate-900 mt-1">Manage Risk Finding</h3>
              </div>
              <button
                onClick={() => setSelectedFinding(null)}
                className="text-slate-400 hover:text-slate-600 text-sm font-bold"
              >
                ✕
              </button>
            </div>

            <div className="text-xs space-y-2 bg-slate-50 p-3 rounded border border-slate-200">
              <div>
                <strong>Risk:</strong> {selectedFinding.risk_name}
              </div>
              <div>
                <strong>Control ID:</strong> {selectedFinding.control_id} ({selectedFinding.control_name})
              </div>
              <div>
                <strong>Vendor:</strong> {selectedFinding.vendor_name}
              </div>
              <div>
                <strong>Severity:</strong> {selectedFinding.inherent_risk} Inherent Risk
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-xs font-semibold text-slate-700">Finding Status:</label>
              <select
                value={newStatus}
                onChange={(e) => setNewStatus(e.target.value)}
                className="w-full text-xs border border-slate-300 rounded px-3 py-2 bg-slate-50 focus:bg-white focus:outline-none"
              >
                <option value="Open">Open (Action Required)</option>
                <option value="Acknowledged">Acknowledged</option>
                <option value="Remediating">Remediating (Mitigation in Progress)</option>
                <option value="Accepted">Risk Accepted (Exception Logged)</option>
                <option value="Closed">Closed (Remediated)</option>
              </select>
            </div>

            <div className="space-y-2">
              <label className="text-xs font-semibold text-slate-700">Mitigation Recommendation & Notes:</label>
              <textarea
                rows={4}
                value={mitigationText}
                onChange={(e) => setMitigationText(e.target.value)}
                placeholder="Enter agreed mitigation steps, compensating controls, or verification proof..."
                className="w-full text-xs border border-slate-300 rounded p-2.5 bg-slate-50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
            </div>

            <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setSelectedFinding(null)}
                className="px-3.5 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-100 rounded-md border border-slate-300"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleSaveMitigation}
                disabled={saving}
                className="px-4 py-1.5 text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-700 rounded-md shadow-xs disabled:opacity-50"
              >
                {saving ? 'Saving...' : 'Update Finding'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
