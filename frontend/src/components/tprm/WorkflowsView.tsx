import React, { useState, useEffect } from 'react';
import {
  GitMerge,
  ShieldCheck,
  ChevronRight,
} from 'lucide-react';
import type { WorkflowItem } from '../../types';

export const WorkflowsView: React.FC = () => {
  const [workflows, setWorkflows] = useState<WorkflowItem[]>([]);
  const [selectedWorkflow, setSelectedWorkflow] = useState<WorkflowItem | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  const fetchWorkflows = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/tprm/v1/workflows');
      if (res.ok) {
        const data = await res.json();
        setWorkflows(data.items || []);
        if (data.items && data.items.length > 0) {
          setSelectedWorkflow(data.items[0]);
        }
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

  // Workflow stages definitions based on Cadence TPRM Training Section 4 & Appendix A
  const getWorkflowStages = (workflowName: string) => {
    if (workflowName.includes('Tier3')) {
      return [
        { name: 'Initial Intake', group: 'Business Owner' },
        { name: 'Due Diligence Questionnaire T3', group: 'Primary Vendor Contact' },
        { name: 'Automated Risk Evaluation', group: 'System (Appendix E)' },
        { name: 'Auto-Approval Evaluation (WR.T3.3)', group: 'System / VRM' },
        { name: 'Live', group: 'Procurement / VRM' },
      ];
    }
    if (workflowName.includes('Onboarding')) {
      return [
        { name: 'Intake Pre-Screening', group: 'Business Owner' },
        { name: 'Category & Tier Classification', group: 'VRM / Procurement' },
        { name: 'Routing Dispatch (WR.ON.1-6)', group: 'Workflow Engine' },
        { name: 'Dispatched to Category Flow', group: 'Category Specialist' },
      ];
    }
    return [
      { name: 'Stage 1: Due Diligence Questionnaire T1-2', group: 'Vendor Respondent' },
      { name: 'Stage 2: Cross-Departmental Reviews', group: 'Legal, Security, IT, Privacy' },
      { name: 'Stage 3: Risk Finding Mitigation', group: 'Responsible Functional Reviewers' },
      { name: 'Stage 4: Final VRM & Committee Approval', group: 'VRM & Executive Approvers' },
      { name: 'Stage 5: Live Vendor Contract Activation', group: 'Procurement' },
    ];
  };

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <GitMerge className="w-6 h-6 text-indigo-600" />
            <h1 className="text-xl font-bold text-slate-900">Configured Workflows & Engine States</h1>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Section 4 & Appendix A: 7 Specialized Workflows with Category-Specific Stages, Transition Invariants & Auto-Approvals.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold px-2.5 py-1 rounded bg-indigo-50 text-indigo-700 border border-indigo-200">
            Active Definitions: {workflows.length}
          </span>
        </div>
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Workflow Definitions Selector */}
        <div className="bg-white border border-slate-200 rounded-lg p-4 shadow-sm space-y-3">
          <h2 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
            Workflow Catalog (7 Configured)
          </h2>

          {loading ? (
            <div className="p-8 text-center text-slate-500">
              <div className="inline-block animate-spin rounded-full h-6 w-6 border-b-2 border-indigo-600 mb-2"></div>
              <p className="text-xs">Loading workflow definitions...</p>
            </div>
          ) : (
            <div className="space-y-2">
              {workflows.map((wf) => {
                const isSelected = selectedWorkflow?.id === wf.id;
                return (
                  <button
                    key={wf.id}
                    onClick={() => setSelectedWorkflow(wf)}
                    className={`w-full text-left p-3 rounded-lg border transition-all ${
                      isSelected
                        ? 'border-indigo-600 bg-indigo-50/40 shadow-xs'
                        : 'border-slate-200 hover:bg-slate-50 bg-white'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-slate-900">{wf.name}</span>
                      <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 border border-slate-200">
                        {wf.instances_count || 0} active
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-500 mt-1 line-clamp-2">{wf.description}</p>
                  </button>
                );
              })}
            </div>
          )}
        </div>

        {/* Right Column (2 cols): Selected Workflow Visualization & Rules */}
        <div className="lg:col-span-2 space-y-6">
          {selectedWorkflow ? (
            <>
              {/* Stages Progression Card */}
              <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm space-y-4">
                <div className="border-b border-slate-100 pb-3">
                  <div className="flex items-center justify-between">
                    <h3 className="text-base font-bold text-slate-900">{selectedWorkflow.name}</h3>
                    <span className="text-xs font-semibold px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200">
                      FSM Verified
                    </span>
                  </div>
                  <p className="text-xs text-slate-500 mt-1">{selectedWorkflow.description}</p>
                </div>

                <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                  Configured Stage Hierarchy
                </h4>

                <div className="space-y-3">
                  {getWorkflowStages(selectedWorkflow.name).map((stage, idx, arr) => (
                    <div key={idx} className="relative">
                      <div className="flex items-start gap-3 p-3.5 rounded-lg border border-slate-200 bg-slate-50/50">
                        <div className="w-6 h-6 rounded-full bg-indigo-600 text-white font-bold text-xs flex items-center justify-center shrink-0">
                          {idx + 1}
                        </div>
                        <div className="flex-1">
                          <div className="text-xs font-bold text-slate-900">{stage.name}</div>
                          <div className="text-[11px] text-slate-500 mt-0.5">
                            <strong>Responsible Group:</strong> {stage.group}
                          </div>
                        </div>
                      </div>
                      {idx < arr.length - 1 && (
                        <div className="flex justify-center my-1 text-slate-300">
                          <ChevronRight className="w-4 h-4 rotate-90" />
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {/* Appendix A Governance Rules */}
              <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm space-y-3">
                <div className="flex items-center gap-2 pb-2 border-b border-slate-100">
                  <ShieldCheck className="w-4 h-4 text-indigo-600" />
                  <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                    Authoritative Transition Invariants
                  </h4>
                </div>

                <div className="text-xs space-y-2 text-slate-600">
                  <div className="p-2.5 bg-slate-50 rounded border border-slate-200">
                    <strong>Pre-Condition:</strong> All required questionnaire responses must be verified prior to stage advancement.
                  </div>
                  <div className="p-2.5 bg-slate-50 rounded border border-slate-200">
                    <strong>Multi-Department Signoff:</strong> Security, Legal, IT, and Privacy reviews must be resolved before VRM final approval.
                  </div>
                  <div className="p-2.5 bg-slate-50 rounded border border-slate-200">
                    <strong>Tier 3 Fast Path:</strong> WR.T3.3 allows auto-approval only when zero High/Medium inherent risks are triggered.
                  </div>
                  <div className="p-2.5 bg-slate-50 rounded border border-slate-200">
                    <strong>Rejection Invariant:</strong> Any rejection moves vendor directly to 'Review Reject' stage, requiring explicit reason.
                  </div>
                </div>
              </div>
            </>
          ) : (
            <div className="p-12 text-center text-slate-400 bg-white rounded-lg border border-slate-200">
              Select a workflow to inspect its configuration and state transitions.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
