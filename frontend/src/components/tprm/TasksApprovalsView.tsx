import React, { useState, useEffect } from 'react';
import {
  CheckSquare,
  Clock,
  AlertCircle,
  CheckCircle2,
  Search,
  ShieldCheck,
  RotateCw,
  X,
} from 'lucide-react';
import type { TaskItem, UserProfile } from '../../types';

interface TasksApprovalsViewProps {
  currentUser: UserProfile;
  initialMode?: 'all' | 'my' | 'approvals' | 'overdue';
  onNavigateToVendor?: (vendorId: string) => void;
  onNavigateToQuestionnaire?: (assessmentId: string) => void;
  onRefreshMetrics?: () => void;
}

export const TasksApprovalsView: React.FC<TasksApprovalsViewProps> = ({
  currentUser,
  initialMode = 'my',
  onNavigateToVendor,
  onNavigateToQuestionnaire,
  onRefreshMetrics,
}) => {
  const [tasks, setTasks] = useState<TaskItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [statusFilter, setStatusFilter] = useState<string>('All');
  const [search, setSearch] = useState<string>('');
  const [activeTab, setActiveTab] = useState<'all' | 'my' | 'approvals' | 'overdue'>(initialMode);
  const [actionModal, setActionModal] = useState<{
    task: TaskItem;
    action: 'approve' | 'reject' | 'complete';
  } | null>(null);
  const [decisionReason, setDecisionReason] = useState<string>('');
  const [processing, setProcessing] = useState<boolean>(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  useEffect(() => {
    setActiveTab(initialMode);
  }, [initialMode]);

  const fetchTasks = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/tprm/v1/tasks', {
        headers: { 'X-User-Email': currentUser.email },
      });
      if (res.ok) {
        const data = await res.json();
        setTasks(data.items || data.tasks || []);
      }
    } catch (err) {
      console.error('Failed to load tasks', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTasks();
  }, [currentUser.email]);

  const handleActionConfirm = async () => {
    if (!actionModal) return;
    setProcessing(true);
    setMessage(null);
    const { task, action } = actionModal;
    const headers = {
      'Content-Type': 'application/json',
      'X-User-Email': currentUser.email,
    };

    try {
      if (action === 'approve' || action === 'reject') {
        const res = await fetch(`/api/tprm/v1/workflows/instances/${task.vendor_id}/transition`, {
          method: 'POST',
          headers,
          body: JSON.stringify({
            action: action === 'approve' ? 'Approve' : 'Reject',
            actor_email: currentUser.email,
            decision_reason: decisionReason || `${action.toUpperCase()} decision recorded via Approvals Queue`,
          }),
        });

        if (res.ok) {
          await fetch(`/api/tprm/v1/tasks/${task.id}/complete`, { method: 'POST', headers });
          setMessage({
            type: 'success',
            text: `Vendor '${task.vendor_name}' ${action === 'approve' ? 'Approved (moved to Live)' : 'Rejected (moved to Review Reject with 14-day Business Owner task)'}.`,
          });
          setActionModal(null);
          setDecisionReason('');
          await fetchTasks();
          onRefreshMetrics?.();
        } else {
          const err = await res.json();
          setMessage({ type: 'error', text: err.detail || `Failed to ${action} vendor` });
        }
      } else {
        const res = await fetch(`/api/tprm/v1/tasks/${task.id}/complete`, {
          method: 'POST',
          headers,
        });
        if (res.ok) {
          setMessage({ type: 'success', text: `Task "${task.title}" marked as Completed.` });
          setActionModal(null);
          await fetchTasks();
          onRefreshMetrics?.();
        } else {
          setMessage({ type: 'error', text: 'Failed to complete task' });
        }
      }
    } catch (err) {
      setMessage({ type: 'error', text: 'Network error executing task action' });
    } finally {
      setProcessing(false);
    }
  };

  const filteredTasks = tasks.filter((t) => {
    const matchesSearch =
      search === '' ||
      t.title.toLowerCase().includes(search.toLowerCase()) ||
      t.vendor_name.toLowerCase().includes(search.toLowerCase()) ||
      t.task_type.toLowerCase().includes(search.toLowerCase());

    const matchesStatus = statusFilter === 'All' || t.status === statusFilter;

    let matchesTab = true;
    if (activeTab === 'my') {
      matchesTab = Boolean(
        currentUser.is_admin ||
        !t.assignee_email ||
        t.assignee_email === currentUser.email ||
        (t.collaborator_group && currentUser.groups.includes(t.collaborator_group))
      );
    } else if (activeTab === 'approvals') {
      matchesTab = Boolean(t.task_type.includes('Approval') || t.title.includes('Assessment Submitted'));
    } else if (activeTab === 'overdue') {
      matchesTab = Boolean(t.is_overdue || t.status === 'Overdue');
    }

    return Boolean(matchesSearch && matchesStatus && matchesTab);
  });

  const pendingApprovalsCount = tasks.filter(
    (t) => (t.task_type.includes('Approval') || t.title.includes('Assessment Submitted')) && t.status !== 'Completed'
  ).length;

  const overdueCount = tasks.filter((t) => t.is_overdue || t.status === 'Overdue').length;

  return (
    <div className="space-y-6">
      <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <CheckSquare size={20} className="text-indigo-600" />
            <h1 className="text-xl font-bold text-slate-900">Tasks, SLAs & Approvals Queue</h1>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Enforcing Appendix D Timelines: Assessment Completion (SLA.1: 9d/5d), Review Responses (SLA.2: 4d/2d), High/Medium/Low Risk Response (SLA.3: 9d, SLA.4: 14d, SLA.5: 19d), and Reject Review (14d).
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="badge badge-warning">
            <ShieldCheck size={12} /> Pending Approvals: {pendingApprovalsCount}
          </span>
          <span className="badge badge-alert">
            <AlertCircle size={12} /> Overdue SLAs: {overdueCount}
          </span>
          <button
            type="button"
            onClick={fetchTasks}
            className="btn btn-sm btn-secondary"
            title="Refresh Tasks"
          >
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
          {message.type === 'success' ? (
            <CheckCircle2 size={16} className="text-emerald-600 shrink-0" />
          ) : (
            <AlertCircle size={16} className="text-rose-600 shrink-0" />
          )}
          <span>{message.text}</span>
        </div>
      )}

      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-3">
        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button"
            onClick={() => setActiveTab('my')}
            className={`btn btn-sm ${activeTab === 'my' ? 'btn-primary' : 'btn-secondary'}`}
          >
            My Queue & Group Tasks
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('approvals')}
            className={`btn btn-sm ${activeTab === 'approvals' ? 'btn-primary' : 'btn-secondary'}`}
          >
            VRM Approvals Queue ({pendingApprovalsCount})
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('all')}
            className={`btn btn-sm ${activeTab === 'all' ? 'btn-primary' : 'btn-secondary'}`}
          >
            All Organization Tasks ({tasks.length})
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('overdue')}
            className={`btn btn-sm ${activeTab === 'overdue' ? 'btn-alert' : 'btn-secondary'}`}
          >
            Overdue / Escalations ({overdueCount})
          </button>
        </div>

        <div className="flex items-center gap-3">
          <div className="relative min-w-[200px]">
            <Search size={14} className="text-slate-400 absolute left-2.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search tasks..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-8 pr-3 py-1.5 text-xs border border-slate-300 rounded-md bg-slate-50"
            />
          </div>

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="text-xs border border-slate-300 rounded px-2.5 py-1.5 bg-slate-50"
          >
            <option value="All">All Statuses</option>
            <option value="Pending">Pending</option>
            <option value="Completed">Completed</option>
          </select>
        </div>
      </div>

      <div className="bg-white border border-slate-200 rounded-lg shadow-sm overflow-x-auto">
        {loading ? (
          <div className="p-12 text-center text-slate-500">
            <p className="text-sm">Synchronizing task queue and SLAs...</p>
          </div>
        ) : filteredTasks.length === 0 ? (
          <div className="p-12 text-center text-slate-500">
            <p className="text-sm font-medium text-slate-700">No tasks matching current filter</p>
          </div>
        ) : (
          <table className="enterprise-table">
            <thead>
              <tr>
                <th>Task Title & Rule</th>
                <th>Vendor & Assessment</th>
                <th>Assignee & Collaborator Group</th>
                <th>SLA Due Date</th>
                <th>Status</th>
                <th className="text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredTasks.map((task) => {
                const isApprovalTask =
                  task.task_type.includes('Approval') || task.title.includes('Assessment Submitted');
                return (
                  <tr key={task.id}>
                    <td>
                      <div className="font-semibold text-slate-900">{task.title}</div>
                      <div className="text-xs text-slate-500 mt-0.5">{task.description}</div>
                    </td>
                    <td className="whitespace-nowrap">
                      <button
                        type="button"
                        onClick={() => onNavigateToVendor?.(task.vendor_id)}
                        className="btn-link"
                      >
                        {task.vendor_name}
                      </button>
                      {task.assessment_id && (
                        <div>
                          <button
                            type="button"
                            onClick={() => onNavigateToQuestionnaire?.(task.assessment_id!)}
                            className="text-[11px] font-mono text-indigo-600"
                          >
                            Open Questionnaire →
                          </button>
                        </div>
                      )}
                    </td>
                    <td className="whitespace-nowrap">
                      <div className="font-medium text-slate-800">
                        {task.collaborator_group || 'Vendor Risk Management Group'}
                      </div>
                      <div className="text-[11px] text-slate-500 font-mono">
                        {task.assignee_email || 'Group Assignment'}
                      </div>
                    </td>
                    <td className="whitespace-nowrap">
                      <div className="flex items-center gap-1.5 font-medium">
                        <Clock size={13} className={task.is_overdue ? 'text-rose-600' : 'text-slate-400'} />
                        <span className={task.is_overdue ? 'text-rose-600 font-bold' : 'text-slate-800'}>
                          {task.due_date ? new Date(task.due_date).toLocaleDateString() : 'N/A'}
                        </span>
                      </div>
                    </td>
                    <td>
                      <span
                        className={`badge ${
                          task.status === 'Completed'
                            ? 'badge-success'
                            : task.is_overdue
                            ? 'badge-alert'
                            : 'badge-info'
                        }`}
                      >
                        {task.is_overdue && task.status !== 'Completed' ? 'Overdue' : task.status}
                      </span>
                    </td>
                    <td className="text-right whitespace-nowrap">
                      {task.status !== 'Completed' ? (
                        <div className="inline-flex items-center gap-1.5">
                          {isApprovalTask && currentUser.is_admin && (
                            <>
                              <button
                                type="button"
                                onClick={() => setActionModal({ task, action: 'approve' })}
                                className="btn btn-sm btn-success"
                              >
                                Approve
                              </button>
                              <button
                                type="button"
                                onClick={() => setActionModal({ task, action: 'reject' })}
                                className="btn btn-sm btn-alert"
                              >
                                Reject
                              </button>
                            </>
                          )}
                          <button
                            type="button"
                            onClick={() => setActionModal({ task, action: 'complete' })}
                            className="btn btn-sm btn-secondary"
                          >
                            Complete Task
                          </button>
                        </div>
                      ) : (
                        <span className="text-xs text-emerald-600 font-semibold">Completed</span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>

      {actionModal && (
        <div className="modal-backdrop">
          <div className="modal-dialog">
            <div className="modal-header">
              <h3 className="text-base font-bold text-slate-900 capitalize">
                {actionModal.action} Task: {actionModal.task.title}
              </h3>
              <button
                type="button"
                onClick={() => setActionModal(null)}
                className="btn btn-sm btn-secondary"
                aria-label="Close dialog"
              >
                <X size={16} />
              </button>
            </div>

            <div className="modal-body space-y-3">
              <div className="text-xs bg-slate-50 p-3 rounded border border-slate-200 space-y-1">
                <div><strong>Vendor:</strong> {actionModal.task.vendor_name}</div>
                <div><strong>Task Type:</strong> {actionModal.task.task_type}</div>
                <div><strong>Collaborator Group:</strong> {actionModal.task.collaborator_group || 'VRM'}</div>
              </div>

              {(actionModal.action === 'approve' || actionModal.action === 'reject') && (
                <div>
                  <label className="input-label">
                    {actionModal.action === 'reject' ? 'Mandatory Rejection Rationale (WR.*.4):' : 'Approval Decision Note (WR.*.3):'}
                  </label>
                  <textarea
                    rows={3}
                    value={decisionReason}
                    onChange={(e) => setDecisionReason(e.target.value)}
                    placeholder="Enter formal justification for the audit log..."
                    className="input-textarea"
                  />
                </div>
              )}
            </div>

            <div className="modal-footer">
              <button
                type="button"
                onClick={() => setActionModal(null)}
                className="btn btn-secondary"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleActionConfirm}
                disabled={processing || (actionModal.action === 'reject' && !decisionReason.trim())}
                className={`btn ${
                  actionModal.action === 'reject'
                    ? 'btn-alert'
                    : actionModal.action === 'approve'
                    ? 'btn-success'
                    : 'btn-primary'
                }`}
              >
                {processing ? 'Processing...' : `Confirm ${actionModal.action.toUpperCase()}`}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
