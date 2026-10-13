import React, { useState, useEffect } from 'react';
import {
  CheckSquare,
  Clock,
  AlertCircle,
  CheckCircle2,
  Search,
  ShieldCheck,
  RotateCw,
} from 'lucide-react';
import type { TaskItem, UserProfile } from '../../types';

interface TasksApprovalsViewProps {
  currentUser: UserProfile;
  onNavigateToVendor?: (vendorId: string) => void;
  onNavigateToQuestionnaire?: (assessmentId: string) => void;
}

export const TasksApprovalsView: React.FC<TasksApprovalsViewProps> = ({
  currentUser,
  onNavigateToVendor,
  onNavigateToQuestionnaire,
}) => {
  const [tasks, setTasks] = useState<TaskItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [statusFilter, setStatusFilter] = useState<string>('All');
  const [search, setSearch] = useState<string>('');
  const [activeTab, setActiveTab] = useState<'all' | 'my' | 'overdue'>('my');
  const [actionModal, setActionModal] = useState<{
    task: TaskItem;
    action: 'approve' | 'reject' | 'complete';
  } | null>(null);
  const [decisionReason, setDecisionReason] = useState<string>('');
  const [processing, setProcessing] = useState<boolean>(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const fetchTasks = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/tprm/v1/tasks');
      if (res.ok) {
        const data = await res.json();
        setTasks(data.items || []);
      }
    } catch (err) {
      console.error('Failed to load tasks', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTasks();
  }, []);

  const handleActionConfirm = async () => {
    if (!actionModal) return;
    setProcessing(true);
    setMessage(null);
    const { task, action } = actionModal;

    try {
      if (action === 'approve' || action === 'reject') {
        // Trigger workflow transition for the vendor
        const res = await fetch(`/api/tprm/v1/workflows/instances/${task.vendor_id}/transition`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            action: action === 'approve' ? 'Approve' : 'Reject',
            actor_email: currentUser.email,
            decision_reason: decisionReason || `${action.toUpperCase()} action taken via Tasks & Approvals queue`,
          }),
        });

        if (res.ok) {
          // Complete the task as well
          await fetch(`/api/tprm/v1/tasks/${task.id}/complete`, { method: 'POST' });
          setMessage({
            type: 'success',
            text: `Vendor successfully ${action === 'approve' ? 'Approved' : 'Rejected'} with recorded audit trail.`,
          });
          setActionModal(null);
          setDecisionReason('');
          await fetchTasks();
        } else {
          const err = await res.json();
          setMessage({ type: 'error', text: err.detail || `Failed to ${action} vendor` });
        }
      } else {
        // Simple task completion
        const res = await fetch(`/api/tprm/v1/tasks/${task.id}/complete`, { method: 'POST' });
        if (res.ok) {
          setMessage({ type: 'success', text: `Task "${task.title}" marked as Completed.` });
          setActionModal(null);
          await fetchTasks();
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

  // Filter tasks based on search, tab, and status
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
        !t.assignee_email ||
        t.assignee_email === currentUser.email ||
        (t.collaborator_group && currentUser.groups.includes(t.collaborator_group))
      );
    } else if (activeTab === 'overdue') {
      matchesTab = Boolean(t.is_overdue || t.status === 'Overdue');
    }

    return Boolean(matchesSearch && matchesStatus && matchesTab);
  });

  const pendingApprovalsCount = tasks.filter(
    (t) => t.task_type.includes('Approval') && t.status !== 'Completed'
  ).length;

  const overdueCount = tasks.filter((t) => t.is_overdue || t.status === 'Overdue').length;

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <CheckSquare className="w-6 h-6 text-indigo-600" />
            <h1 className="text-xl font-bold text-slate-900">Tasks & Approval Queue</h1>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Enforcing Table 13 SLAs: Assessment Completion (9d), Reviews (4d), High Risk Remediation (5d).
          </p>
        </div>

        <div className="flex items-center gap-3">
          <span className="text-xs font-semibold px-2.5 py-1 rounded bg-amber-50 text-amber-800 border border-amber-200 flex items-center gap-1.5">
            <ShieldCheck className="w-3.5 h-3.5 text-amber-600" />
            Pending Approvals: {pendingApprovalsCount}
          </span>
          <span className="text-xs font-semibold px-2.5 py-1 rounded bg-rose-50 text-rose-800 border border-rose-200 flex items-center gap-1.5">
            <AlertCircle className="w-3.5 h-3.5 text-rose-600" />
            SLA Breaches: {overdueCount}
          </span>
          <button
            onClick={fetchTasks}
            className="p-1.5 text-slate-500 hover:text-slate-800 border border-slate-200 rounded hover:bg-slate-50"
            title="Refresh Tasks"
          >
            <RotateCw className="w-4 h-4" />
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
            <AlertCircle className="w-5 h-5 text-rose-600 shrink-0" />
          )}
          <span>{message.text}</span>
        </div>
      )}

      {/* Tabs & Filters */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-3">
        <div className="flex items-center gap-2">
          <button
            onClick={() => setActiveTab('my')}
            className={`px-3.5 py-1.5 text-xs font-semibold rounded-md transition-all ${
              activeTab === 'my'
                ? 'bg-indigo-600 text-white shadow-xs'
                : 'text-slate-600 hover:bg-slate-100'
            }`}
          >
            My Queue & Group Tasks
          </button>
          <button
            onClick={() => setActiveTab('all')}
            className={`px-3.5 py-1.5 text-xs font-semibold rounded-md transition-all ${
              activeTab === 'all'
                ? 'bg-indigo-600 text-white shadow-xs'
                : 'text-slate-600 hover:bg-slate-100'
            }`}
          >
            All Organization Tasks ({tasks.length})
          </button>
          <button
            onClick={() => setActiveTab('overdue')}
            className={`px-3.5 py-1.5 text-xs font-semibold rounded-md transition-all ${
              activeTab === 'overdue'
                ? 'bg-rose-600 text-white shadow-xs'
                : 'text-rose-700 hover:bg-rose-50'
            }`}
          >
            Overdue / Escalations ({overdueCount})
          </button>
        </div>

        <div className="flex items-center gap-3">
          <div className="relative min-w-[200px]">
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search tasks..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-8 pr-3 py-1 text-xs border border-slate-300 rounded-md bg-slate-50 focus:bg-white focus:outline-none"
            />
          </div>

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="text-xs border border-slate-300 rounded px-2.5 py-1 bg-slate-50 focus:outline-none"
          >
            <option value="All">All Statuses</option>
            <option value="Pending">Pending</option>
            <option value="In Progress">In Progress</option>
            <option value="Completed">Completed</option>
            <option value="Overdue">Overdue</option>
          </select>
        </div>
      </div>

      {/* Tasks Table */}
      <div className="bg-white border border-slate-200 rounded-lg shadow-sm overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-slate-500">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mb-3"></div>
            <p className="text-sm">Synchronizing task queue and SLAs...</p>
          </div>
        ) : filteredTasks.length === 0 ? (
          <div className="p-12 text-center text-slate-500">
            <CheckCircle2 className="w-10 h-10 text-emerald-400 mx-auto mb-2" />
            <p className="text-sm font-medium text-slate-700">Queue is Clear</p>
            <p className="text-xs text-slate-400 mt-1">No pending tasks matching your filter criteria.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200 text-[11px] font-bold text-slate-600 uppercase tracking-wider">
                  <th className="py-3 px-4">Task Details</th>
                  <th className="py-3 px-4">Vendor Context</th>
                  <th className="py-3 px-4">Assigned To / Group</th>
                  <th className="py-3 px-4">SLA Due Date</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 text-xs text-slate-700">
                {filteredTasks.map((task) => (
                  <tr key={task.id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="py-3 px-4">
                      <div className="font-semibold text-slate-900 leading-snug">{task.title}</div>
                      <div className="text-[11px] text-slate-500 mt-0.5 font-mono">{task.task_type}</div>
                    </td>
                    <td className="py-3 px-4 whitespace-nowrap">
                      {onNavigateToVendor ? (
                        <button
                          onClick={() => onNavigateToVendor(task.vendor_id)}
                          className="font-medium text-slate-900 hover:text-indigo-600 text-left"
                        >
                          {task.vendor_name}
                        </button>
                      ) : (
                        <div className="font-medium text-slate-900">{task.vendor_name}</div>
                      )}
                      {task.assessment_id && (
                        <div>
                          {onNavigateToQuestionnaire ? (
                            <button
                              onClick={() => onNavigateToQuestionnaire(task.assessment_id!)}
                              className="text-[11px] text-indigo-600 font-mono hover:underline"
                            >
                              Assmt: {task.assessment_id.slice(0, 8)}...
                            </button>
                          ) : (
                            <div className="text-[11px] text-indigo-600 font-mono">
                              Assmt: {task.assessment_id.slice(0, 8)}...
                            </div>
                          )}
                        </div>
                      )}
                    </td>
                    <td className="py-3 px-4 whitespace-nowrap">
                      <div className="font-medium text-slate-800">
                        {task.collaborator_group || task.assignee_email || 'Unassigned'}
                      </div>
                      <div className="text-[10px] text-slate-400">
                        {task.assignee_email ? task.assignee_email : 'Group Task'}
                      </div>
                    </td>
                    <td className="py-3 px-4 whitespace-nowrap">
                      <div className="flex items-center gap-1.5 font-medium">
                        <Clock
                          className={`w-3.5 h-3.5 ${
                            task.is_overdue ? 'text-rose-600' : 'text-slate-400'
                          }`}
                        />
                        <span className={task.is_overdue ? 'text-rose-600 font-bold' : 'text-slate-800'}>
                          {task.due_date ? new Date(task.due_date).toLocaleDateString() : 'N/A'}
                        </span>
                      </div>
                      {task.is_overdue && (
                        <span className="text-[10px] font-bold text-rose-600 block mt-0.5">
                          SLA Breached
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-4 whitespace-nowrap">
                      <span
                        className={`inline-block px-2 py-0.5 rounded text-[11px] font-semibold ${
                          task.status === 'Completed'
                            ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                            : task.is_overdue
                            ? 'bg-rose-50 text-rose-700 border border-rose-200'
                            : 'bg-indigo-50 text-indigo-700 border border-indigo-200'
                        }`}
                      >
                        {task.is_overdue ? 'Overdue' : task.status}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right whitespace-nowrap">
                      {task.status !== 'Completed' ? (
                        <div className="inline-flex items-center gap-1.5">
                          {task.task_type.includes('Approval') ? (
                            <>
                              <button
                                onClick={() =>
                                  setActionModal({ task, action: 'approve' })
                                }
                                className="px-2.5 py-1 text-xs font-semibold text-white bg-emerald-600 hover:bg-emerald-700 rounded transition-colors shadow-xs"
                              >
                                Approve
                              </button>
                              <button
                                onClick={() =>
                                  setActionModal({ task, action: 'reject' })
                                }
                                className="px-2.5 py-1 text-xs font-semibold text-rose-700 bg-rose-50 hover:bg-rose-100 border border-rose-200 rounded transition-colors"
                              >
                                Reject
                              </button>
                            </>
                          ) : (
                            <button
                              onClick={() =>
                                setActionModal({ task, action: 'complete' })
                              }
                              className="px-2.5 py-1 text-xs font-semibold text-slate-700 bg-slate-100 hover:bg-slate-200 border border-slate-300 rounded transition-colors"
                            >
                              Complete
                            </button>
                          )}
                        </div>
                      ) : (
                        <span className="text-xs text-slate-400 font-medium flex items-center justify-end gap-1">
                          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
                          Done
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Decision / Action Modal */}
      {actionModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-lg shadow-xl border border-slate-200 max-w-md w-full p-6 space-y-4">
            <div className="flex items-start justify-between border-b border-slate-100 pb-3">
              <div>
                <h3 className="text-base font-bold text-slate-900 capitalize">
                  {actionModal.action} Task: {actionModal.task.title}
                </h3>
                <p className="text-xs text-slate-500 mt-0.5">Vendor: {actionModal.task.vendor_name}</p>
              </div>
              <button
                onClick={() => setActionModal(null)}
                className="text-slate-400 hover:text-slate-600 text-sm font-bold"
              >
                ✕
              </button>
            </div>

            <div className="text-xs bg-slate-50 p-3 rounded border border-slate-200 space-y-1">
              <div><strong>Task Type:</strong> {actionModal.task.task_type}</div>
              <div><strong>Assigned To:</strong> {actionModal.task.collaborator_group || actionModal.task.assignee_email || 'Unassigned'}</div>
              <div><strong>Due Date:</strong> {actionModal.task.due_date || 'N/A'}</div>
            </div>

            {(actionModal.action === 'approve' || actionModal.action === 'reject') && (
              <div className="space-y-2">
                <label className="text-xs font-semibold text-slate-700">
                  {actionModal.action === 'reject' ? 'Mandatory Rejection Rationale:' : 'Approval Decision Reason:'}
                </label>
                <textarea
                  rows={3}
                  required={actionModal.action === 'reject'}
                  value={decisionReason}
                  onChange={(e) => setDecisionReason(e.target.value)}
                  placeholder={
                    actionModal.action === 'reject'
                      ? 'State non-compliance reason, risk findings, or missing requirements...'
                      : 'Approval comments or terms (optional)...'
                  }
                  className="w-full text-xs border border-slate-300 rounded p-2.5 bg-slate-50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>
            )}

            <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setActionModal(null)}
                className="px-3.5 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-100 rounded-md border border-slate-300"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleActionConfirm}
                disabled={processing || (actionModal.action === 'reject' && !decisionReason.trim())}
                className={`px-4 py-1.5 text-xs font-semibold text-white rounded-md shadow-xs disabled:opacity-50 ${
                  actionModal.action === 'reject'
                    ? 'bg-rose-600 hover:bg-rose-700'
                    : actionModal.action === 'approve'
                    ? 'bg-emerald-600 hover:bg-emerald-700'
                    : 'bg-indigo-600 hover:bg-indigo-700'
                }`}
              >
                {processing
                  ? 'Processing...'
                  : actionModal.action === 'approve'
                  ? 'Confirm Approval'
                  : actionModal.action === 'reject'
                  ? 'Confirm Rejection'
                  : 'Complete Task'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
