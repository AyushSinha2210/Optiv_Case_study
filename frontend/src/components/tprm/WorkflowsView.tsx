import React, { useState, useEffect } from 'react';
import {
  GitMerge,
  ShieldCheck,
  Copy,
  Clock,
  History,
  RotateCw,
} from 'lucide-react';
import type { WorkflowItem, SLAConfigItem, WorkflowTransitionItem, UserProfile } from '../../types';

interface WorkflowsViewProps {
  currentUser?: UserProfile;
}

export const WorkflowsView: React.FC<WorkflowsViewProps> = ({ currentUser }) => {
  const [workflows, setWorkflows] = useState<WorkflowItem[]>([]);
  const [slas, setSlas] = useState<SLAConfigItem[]>([]);
  const [reassessmentRules, setReassessmentRules] = useState<any[]>([]);
  const [transitions, setTransitions] = useState<WorkflowTransitionItem[]>([]);
  const [selectedWorkflow, setSelectedWorkflow] = useState<WorkflowItem | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [cloneName, setCloneName] = useState<string>('');
  const [cloneMessage, setCloneMessage] = useState<string | null>(null);

  const fetchWorkflows = async () => {
    setLoading(true);
    try {
      const [wfRes, trRes] = await Promise.all([
        fetch('/api/tprm/v1/workflows', { headers: currentUser ? { 'X-User-Email': currentUser.email } : {} }),
        fetch('/api/tprm/v1/workflows/transitions', { headers: currentUser ? { 'X-User-Email': currentUser.email } : {} }),
      ]);
      if (wfRes.ok) {
        const data = await wfRes.json();
        const wfList = data.items || data.workflows || [];
        setWorkflows(wfList);
        setSlas(data.slas || []);
        setReassessmentRules(data.reassessment_rules || []);
        if (wfList.length > 0 && !selectedWorkflow) {
          setSelectedWorkflow(wfList[0]);
        }
      }
      if (trRes.ok) {
        const trData = await trRes.json();
        setTransitions(trData.items || trData.transitions || []);
      }
    } catch (err) {
      console.error('Failed to load workflows', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchWorkflows();
  }, []);

  const handleCloneWorkflow = async () => {
    if (!selectedWorkflow || !cloneName.trim()) return;
    setCloneMessage(null);
    try {
      const res = await fetch('/api/tprm/v1/workflows/clone', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(currentUser ? { 'X-User-Email': currentUser.email } : {}),
        },
        body: JSON.stringify({
          source_workflow_name: selectedWorkflow.name,
          new_workflow_name: cloneName.trim(),
        }),
      });
      if (res.ok) {
        const data = await res.json();
        setCloneMessage(`Cloned '${selectedWorkflow.name}' into draft workflow '${data.name}' (Section 6.4).`);
        setCloneName('');
        await fetchWorkflows();
      } else {
        const err = await res.json();
        setCloneMessage(`Error: ${err.detail || 'Clone failed'}`);
      }
    } catch (e) {
      setCloneMessage('Network error cloning workflow');
    }
  };

  return (
    <div className="space-y-6">
      <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <GitMerge size={20} className="text-indigo-600" />
            <h1 className="text-xl font-bold text-slate-900">
              Workflow Definitions, Appendix A Rules & Appendix D SLAs
            </h1>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Section 4.2, 6.4 & Appendix A: All 7 configured workflows, 45 workflow & reassessment automation rules, and 7 SLA timelines.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="badge badge-info">Configured Workflows: {workflows.length}</span>
          <span className="badge badge-success">Appendix A Rules: 45</span>
          <span className="badge badge-purple">Appendix D SLAs: {slas.length}</span>
        </div>
      </div>

      {cloneMessage && (
        <div className="p-3 bg-indigo-50 border border-indigo-200 text-indigo-800 rounded text-xs font-medium">
          {cloneMessage}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Workflow Catalog */}
        <div className="bg-white border border-slate-200 rounded-lg p-4 shadow-sm space-y-3">
          <h2 className="text-xs font-bold text-slate-700 uppercase tracking-wider">
            Vendor Workflows (Section 6.4)
          </h2>

          {loading ? (
            <div className="p-8 text-center text-xs text-slate-500">Loading workflow definitions...</div>
          ) : (
            <div className="space-y-2">
              {workflows.map((wf) => {
                const isSelected = selectedWorkflow?.id === wf.id;
                return (
                  <button
                    key={wf.id}
                    type="button"
                    onClick={() => setSelectedWorkflow(wf)}
                    className={`w-full text-left p-3 rounded-lg border transition-all ${
                      isSelected ? 'border-indigo-600 bg-indigo-50/40' : 'border-slate-200 bg-white'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-slate-900">{wf.name}</span>
                      <span className={`badge ${wf.status === 'Draft' ? 'badge-warning' : 'badge-success'}`}>
                        {wf.status || 'Published'} ({wf.instances_count || 0})
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-500 mt-1">{wf.description}</p>
                  </button>
                );
              })}
            </div>
          )}

          {/* Clone Workflow Box (Section 6.4) */}
          {selectedWorkflow && currentUser?.is_admin && (
            <div className="pt-3 border-t border-slate-200 space-y-2">
              <label className="text-xs font-bold text-slate-700">
                Clone Selected Workflow (Section 6.4):
              </label>
              <input
                type="text"
                placeholder="e.g. CD_Custom_Draft_Workflow"
                value={cloneName}
                onChange={(e) => setCloneName(e.target.value)}
                className="form-input"
              />
              <button
                type="button"
                onClick={handleCloneWorkflow}
                disabled={!cloneName.trim()}
                className="btn btn-sm btn-secondary w-full"
              >
                <Copy size={13} /> Clone Workflow to Draft
              </button>
            </div>
          )}
        </div>

        {/* Right Column (2 cols): Stages & Appendix A Rules */}
        <div className="lg:col-span-2 space-y-6">
          {selectedWorkflow && (
            <>
              <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm space-y-4">
                <div className="border-b border-slate-100 pb-3 flex items-center justify-between">
                  <div>
                    <h3 className="text-base font-bold text-slate-900">{selectedWorkflow.name}</h3>
                    <p className="text-xs text-slate-500 mt-0.5">{selectedWorkflow.description}</p>
                  </div>
                  <span className="badge badge-info">
                    {(selectedWorkflow.stages || []).length} Configured Stages
                  </span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
                  {(selectedWorkflow.stages || []).map((stg, idx) => (
                    <div
                      key={stg.name}
                      className={`p-3 rounded-lg border ${
                        stg.is_used ? 'border-indigo-200 bg-slate-50' : 'border-slate-200 bg-slate-100'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold text-slate-900">
                          {idx + 1}. {stg.name}
                        </span>
                        <span className={`badge ${stg.is_used ? 'badge-success' : 'badge-neutral'}`}>
                          {stg.is_used ? 'Active Stage' : 'Present / Not Used'}
                        </span>
                      </div>
                      <p className="text-[11px] text-slate-600 mt-1">{stg.description}</p>
                    </div>
                  ))}
                </div>
              </div>

              {/* Appendix A Rules for Selected Workflow */}
              <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm space-y-3">
                <div className="flex items-center gap-2 pb-2 border-b border-slate-100">
                  <ShieldCheck size={16} className="text-indigo-600" />
                  <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                    Appendix A Stage & Workflow Rules for {selectedWorkflow.name} ({(selectedWorkflow.rules || []).length} Rules)
                  </h4>
                </div>

                <div className="overflow-x-auto">
                  <table className="enterprise-table">
                    <thead>
                      <tr>
                        <th>Rule ID (Source SR. NO.)</th>
                        <th>Rule Name & Type</th>
                        <th>Stage & Trigger</th>
                        <th>Condition</th>
                        <th>Action</th>
                      </tr>
                    </thead>
                    <tbody>
                      {(selectedWorkflow.rules || []).map((r) => (
                        <tr key={r.rule_code}>
                          <td className="font-mono font-bold text-indigo-600">
                            {r.rule_code}
                            {r.source_sr_no !== r.rule_code && (
                              <div className="text-[10px] text-amber-600">Source: {r.source_sr_no}</div>
                            )}
                          </td>
                          <td>
                            <div className="font-semibold text-slate-900">{r.rule_name}</div>
                            <span className="badge badge-neutral">{r.rule_type}</span>
                          </td>
                          <td className="text-xs">
                            <div className="font-semibold">{r.stage_name}</div>
                            {r.trigger_name && (
                              <div className="text-[11px] text-slate-500 font-mono">
                                {r.trigger_name} ({r.trigger_type})
                              </div>
                            )}
                          </td>
                          <td className="text-xs text-slate-700">
                            {r.condition_expression}
                            {r.discrepancy_note && (
                              <div className="text-[10px] text-amber-700 mt-0.5">{r.discrepancy_note}</div>
                            )}
                          </td>
                          <td className="text-xs font-medium text-slate-900">{r.action_expression}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </>
          )}

          {/* Appendix D SLAs Table */}
          <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm space-y-3">
            <div className="flex items-center gap-2 pb-2 border-b border-slate-100">
              <Clock size={16} className="text-indigo-600" />
              <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                Appendix D Service-Level Agreements & Timelines (SLA.1 – SLA.7)
              </h4>
            </div>
            <div className="overflow-x-auto">
              <table className="enterprise-table">
                <thead>
                  <tr>
                    <th>SLA No.</th>
                    <th>SLA Name</th>
                    <th>Timeline (Days)</th>
                    <th>Effective Deadline</th>
                    <th>Reminder (Days)</th>
                    <th>Description</th>
                  </tr>
                </thead>
                <tbody>
                  {slas.map((s) => (
                    <tr key={s.sla_no}>
                      <td className="font-mono font-bold text-indigo-600">{s.sla_no}</td>
                      <td className="font-semibold text-slate-900">{s.sla_name}</td>
                      <td className="font-mono">{s.timeline_days}d</td>
                      <td className="font-mono font-bold">{s.effective_deadline_days}d</td>
                      <td className="font-mono">{s.reminder_days !== null ? `${s.reminder_days}d` : '—'}</td>
                      <td className="text-xs text-slate-600">{s.description}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Section 21 Annual Reassessment Cadence Rules Table */}
          {reassessmentRules.length > 0 && (
            <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm space-y-3">
              <div className="flex items-center gap-2 pb-2 border-b border-slate-100">
                <RotateCw size={16} className="text-indigo-600" />
                <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                  Section 21 Annual Reassessment Rules (AR.T1.1 – AR.T3.1)
                </h4>
              </div>
              <div className="overflow-x-auto">
                <table className="enterprise-table">
                  <thead>
                    <tr>
                      <th>Rule Code</th>
                      <th>Rule Name</th>
                      <th>Trigger Type</th>
                      <th>Condition Expression</th>
                      <th>Action Expression</th>
                      <th>Description</th>
                    </tr>
                  </thead>
                  <tbody>
                    {reassessmentRules.map((r) => (
                      <tr key={r.rule_code}>
                        <td className="font-mono font-bold text-indigo-600">{r.rule_code}</td>
                        <td className="font-semibold text-slate-900">{r.rule_name}</td>
                        <td><span className="badge badge-neutral">{r.trigger_type}</span></td>
                        <td className="text-xs text-slate-700">{r.condition_expression}</td>
                        <td className="text-xs font-medium text-slate-900">{r.action_expression}</td>
                        <td className="text-xs text-slate-600">{r.description}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Recent Persisted Workflow Transitions */}
          <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm space-y-3">
            <div className="flex items-center gap-2 pb-2 border-b border-slate-100">
              <History size={16} className="text-indigo-600" />
              <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                Recent Persisted Workflow Transitions ({transitions.length})
              </h4>
            </div>
            <div className="overflow-x-auto">
              <table className="enterprise-table">
                <thead>
                  <tr>
                    <th>Timestamp</th>
                    <th>Actor</th>
                    <th>Transition</th>
                    <th>Trigger & Rule</th>
                    <th>Reason</th>
                  </tr>
                </thead>
                <tbody>
                  {transitions.slice(0, 12).map((t) => (
                    <tr key={t.id}>
                      <td className="font-mono text-xs">{new Date(t.timestamp).toLocaleString()}</td>
                      <td className="text-xs">{t.actor_email}</td>
                      <td className="font-semibold text-xs">
                        {t.from_stage} → {t.to_stage}
                      </td>
                      <td className="font-mono text-xs text-indigo-600">
                        {t.trigger_name} ({t.rule_name})
                      </td>
                      <td className="text-xs text-slate-600">{t.decision_reason}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
