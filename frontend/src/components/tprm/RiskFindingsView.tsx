import React, { useState, useEffect } from 'react';
import {
  ShieldAlert,
  Search,
  CheckCircle2,
  Clock,
  Edit3,
  RotateCw,
} from 'lucide-react';
import type { RiskFindingItem, UserProfile } from '../../types';

interface RiskFindingsViewProps {
  currentUser?: UserProfile;
  onRefreshMetrics?: () => void;
}

export const RiskFindingsView: React.FC<RiskFindingsViewProps> = ({
  currentUser,
  onRefreshMetrics,
}) => {
  const [findings, setFindings] = useState<RiskFindingItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [search, setSearch] = useState<string>('');
  const [severityFilter, setSeverityFilter] = useState<string>('All');
  const [statusFilter, setStatusFilter] = useState<string>('All');
  const [groupFilter, setGroupFilter] = useState<string>('All');
  const [selectedFinding, setSelectedFinding] = useState<RiskFindingItem | null>(null);
  const [mitigationText, setMitigationText] = useState<string>('');
  const [newStatus, setNewStatus] = useState<string>('Open');
  const [saving, setSaving] = useState<boolean>(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const fetchFindings = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/tprm/v1/assessments/findings/all', {
        headers: currentUser ? { 'X-User-Email': currentUser.email } : {},
      });
      if (res.ok) {
        const data = await res.json();
        setFindings(data.items || data.findings || []);
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

  const handleEditClick = (f: RiskFindingItem) => {
    setSelectedFinding(f);
    setMitigationText(f.mitigation_recommendation || '');
    setNewStatus(f.status || 'Open');
  };

  const handleSaveMitigation = async () => {
    if (!selectedFinding) return;
    setSaving(true);
    setMessage(null);
    try {
      const res = await fetch(`/api/tprm/v1/assessments/findings/${selectedFinding.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          ...(currentUser ? { 'X-User-Email': currentUser.email } : {}),
        },
        body: JSON.stringify({
          status: newStatus,
          mitigation_recommendation: mitigationText,
          plan_description: mitigationText,
        }),
      });
      if (res.ok) {
        setMessage({
          type: 'success',
          text: `Risk finding ${selectedFinding.rule_code} (${selectedFinding.control_id}) persisted to database with status '${newStatus}'.`,
        });
        setSelectedFinding(null);
        await fetchFindings();
        onRefreshMetrics?.();
      } else {
        const err = await res.json();
        setMessage({ type: 'error', text: err.detail || 'Failed to update finding' });
      }
    } catch (err) {
      setMessage({ type: 'error', text: 'Network error updating finding' });
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
    const matchesGroup = groupFilter === 'All' || f.responsible_group.includes(groupFilter);

    return matchesSearch && matchesSeverity && matchesStatus && matchesGroup;
  });

  return (
    <div className="space-y-6">
      <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <ShieldAlert size={20} className="text-rose-600" />
            <h1 className="text-xl font-bold text-slate-900">Appendix E Risk Findings & Controls Ledger</h1>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Authoritative risk findings mapped to custom controls (<code>QRC_CL_*</code>, <code>QRC_CmL_*</code>, <code>QRC_Fin_*</code>, <code>QRC_Pri_*</code>, <code>QRC_Sec_*</code>, <code>QRC_IT_*</code>, <code>QRC_Mar_*</code>, <code>QRC_Pcr_*</code>, <code>QRC_RR_*</code>) and SLA.3/4/5 response windows.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="badge badge-alert">
            High Severity: {findings.filter((f) => f.inherent_risk === 'High').length}
          </span>
          <span className="badge badge-warning">
            Medium Severity: {findings.filter((f) => f.inherent_risk === 'Medium').length}
          </span>
          <button type="button" className="btn btn-sm btn-secondary" onClick={fetchFindings}>
            <RotateCw size={13} /> Refresh
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
          <CheckCircle2 size={16} className="text-emerald-600 shrink-0" />
          <span>{message.text}</span>
        </div>
      )}

      <div className="bg-white border border-slate-200 rounded-lg p-4 shadow-sm flex flex-wrap items-center gap-4">
        <div className="relative flex-1 min-w-[240px]">
          <Search size={15} className="text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search by risk statement, rule code (QR.*), control ID (QRC_*) or vendor..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-4 py-1.5 text-xs border border-slate-300 rounded-md bg-slate-50"
          />
        </div>

        <div className="flex items-center gap-2">
          <label className="text-xs font-medium text-slate-600">Severity:</label>
          <select
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
            className="text-xs border border-slate-300 rounded px-2.5 py-1.5 bg-slate-50"
          >
            <option value="All">All Severities</option>
            <option value="High">High Risk (SLA.3: 5+4=9d)</option>
            <option value="Medium">Medium Risk (SLA.4: 10+4=14d)</option>
            <option value="Low">Low Risk (SLA.5: 15+4=19d)</option>
          </select>
        </div>

        <div className="flex items-center gap-2">
          <label className="text-xs font-medium text-slate-600">Status:</label>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="text-xs border border-slate-300 rounded px-2.5 py-1.5 bg-slate-50"
          >
            <option value="All">All Statuses</option>
            <option value="Open">Open</option>
            <option value="Acknowledged">Acknowledged (Risk Response)</option>
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
            className="text-xs border border-slate-300 rounded px-2.5 py-1.5 bg-slate-50"
          >
            <option value="All">All TPRM Groups</option>
            <option value="Security Group">Security Group</option>
            <option value="Privacy Group">Privacy Group</option>
            <option value="Legal Group">Legal Group</option>
            <option value="Finance Group">Finance Group</option>
            <option value="Compliance Group">Compliance Group</option>
            <option value="Procurement Group">Procurement Group</option>
            <option value="IT Group">IT Group</option>
          </select>
        </div>
      </div>

      <div className="bg-white border border-slate-200 rounded-lg shadow-sm overflow-x-auto">
        {loading ? (
          <div className="p-12 text-center text-slate-500">
            <p className="text-sm">Evaluating risk findings across active assessments...</p>
          </div>
        ) : filteredFindings.length === 0 ? (
          <div className="p-12 text-center text-slate-500">
            <p className="text-sm font-medium text-slate-700">No Risk Findings Match Filter</p>
          </div>
        ) : (
          <table className="enterprise-table">
            <thead>
              <tr>
                <th>Rule & Severity</th>
                <th>Risk Name & Mitigation Guidance</th>
                <th>Vendor & Control Reference</th>
                <th>Responsible Group & SLA Deadline</th>
                <th>Status</th>
                <th className="text-right">Action</th>
              </tr>
            </thead>
            <tbody>
              {filteredFindings.map((finding) => (
                <tr key={finding.id}>
                  <td className="whitespace-nowrap">
                    <div className="flex items-center gap-2">
                      <span className="font-mono font-bold text-indigo-700">{finding.rule_code}</span>
                      <span className={`badge ${finding.inherent_risk === 'High' ? 'badge-alert' : 'badge-warning'}`}>
                        {finding.inherent_risk}
                      </span>
                    </div>
                  </td>
                  <td>
                    <div className="font-semibold text-slate-900">{finding.risk_name}</div>
                    <div className="text-xs text-slate-500 mt-0.5">{finding.mitigation_recommendation}</div>
                  </td>
                  <td>
                    <div className="font-semibold text-slate-900">{finding.vendor_name}</div>
                    <div className="font-mono text-xs text-indigo-600">
                      {finding.control_id} — {finding.control_name}
                    </div>
                  </td>
                  <td className="whitespace-nowrap">
                    <div className="font-medium text-slate-800">{finding.responsible_group}</div>
                    <div className="text-xs text-slate-500 flex items-center gap-1 mt-0.5">
                      <Clock size={12} />
                      <span>{finding.due_date ? new Date(finding.due_date).toLocaleDateString() : 'SLA'}</span>
                    </div>
                  </td>
                  <td>
                    <span
                      className={`badge ${
                        finding.status === 'Open'
                          ? 'badge-alert'
                          : finding.status === 'Closed'
                          ? 'badge-success'
                          : 'badge-info'
                      }`}
                    >
                      {finding.status}
                    </span>
                  </td>
                  <td className="text-right">
                    <button
                      type="button"
                      onClick={() => handleEditClick(finding)}
                      className="btn btn-sm btn-secondary"
                    >
                      <Edit3 size={13} /> Manage
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {selectedFinding && (
        <div className="modal-backdrop">
          <div className="modal-dialog">
            <div className="modal-header">
              <div>
                <span className="badge badge-alert">{selectedFinding.rule_code}</span>
                <h3 className="text-base font-bold text-slate-900 mt-1">
                  Update Risk Finding & Mitigation Plan
                </h3>
              </div>
              <button
                type="button"
                onClick={() => setSelectedFinding(null)}
                className="btn btn-sm btn-secondary"
              >
                ✕
              </button>
            </div>

            <div className="modal-body space-y-3">
              <div className="text-xs space-y-1 bg-slate-50 p-3 rounded border border-slate-200">
                <div><strong>Risk Name:</strong> {selectedFinding.risk_name}</div>
                <div><strong>Control ID:</strong> {selectedFinding.control_id} ({selectedFinding.control_name})</div>
                <div><strong>Vendor:</strong> {selectedFinding.vendor_name}</div>
                <div><strong>Inherent Risk:</strong> {selectedFinding.inherent_risk}</div>
              </div>

              <div>
                <label className="input-label">Finding Lifecycle Status:</label>
                <select
                  value={newStatus}
                  onChange={(e) => setNewStatus(e.target.value)}
                  className="form-select"
                >
                  <option value="Open">Open (Action Required)</option>
                  <option value="Acknowledged">Acknowledged (SLA.3/4/5 Risk Response Recorded)</option>
                  <option value="Remediating">Remediating (Remediation Plan in Progress)</option>
                  <option value="Accepted">Risk Accepted (Documented Exception)</option>
                  <option value="Closed">Closed (Verified & Remediated)</option>
                </select>
              </div>

              <div>
                <label className="input-label">Mitigation Plan & Control Evidence Notes:</label>
                <textarea
                  rows={4}
                  value={mitigationText}
                  onChange={(e) => setMitigationText(e.target.value)}
                  className="input-textarea"
                />
              </div>
            </div>

            <div className="modal-footer">
              <button
                type="button"
                onClick={() => setSelectedFinding(null)}
                className="btn btn-secondary"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleSaveMitigation}
                disabled={saving}
                className="btn btn-primary"
              >
                {saving ? 'Persisting...' : 'Persist Finding Update'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
