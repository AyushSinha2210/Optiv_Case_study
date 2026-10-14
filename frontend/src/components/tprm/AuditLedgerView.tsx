import React, { useState, useEffect } from 'react';
import {
  Shield,
  Search,
  ChevronDown,
  ChevronRight,
  Database,
  Lock,
  RotateCw,
  Download,
} from 'lucide-react';
import type { AuditLogItem } from '../../types';

export const AuditLedgerView: React.FC = () => {
  const [logs, setLogs] = useState<AuditLogItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [search, setSearch] = useState<string>('');
  const [entityFilter, setEntityFilter] = useState<string>('All');
  const [expandedLogId, setExpandedLogId] = useState<string | null>(null);

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/tprm/v1/audit?limit=150');
      if (res.ok) {
        const data = await res.json();
        setLogs(data.items || data.logs || []);
      }
    } catch (err) {
      console.error('Failed to load audit logs', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, []);

  const filteredLogs = logs.filter((log) => {
    const matchesSearch =
      search === '' ||
      log.actor_email.toLowerCase().includes(search.toLowerCase()) ||
      log.action.toLowerCase().includes(search.toLowerCase()) ||
      log.entity_id.toLowerCase().includes(search.toLowerCase());

    const matchesEntity =
      entityFilter === 'All' || log.entity_type.toUpperCase() === entityFilter.toUpperCase();

    return matchesSearch && matchesEntity;
  });

  return (
    <div className="space-y-6">
      <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <Shield size={20} className="text-indigo-600" />
            <h1 className="text-xl font-bold text-slate-900">Immutable Audit Trail Ledger</h1>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Section 24: Tamper-evident append-only compliance logging for vendor classification, workflow transitions, questionnaire versioning, risk evaluation, and approvals.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="badge badge-success">
            <Lock size={12} /> Append-Only Enforced ({logs.length} Events)
          </span>
          <button
            type="button"
            onClick={() => window.open('/api/tprm/v1/reports/export/audit', '_blank')}
            className="btn btn-sm btn-secondary"
          >
            <Download size={13} /> Export Audit CSV
          </button>
          <button
            type="button"
            onClick={fetchLogs}
            className="btn btn-sm btn-secondary"
            title="Refresh Audit Logs"
          >
            <RotateCw size={13} /> Refresh
          </button>
        </div>
      </div>

      <div className="bg-white border border-slate-200 rounded-lg p-4 shadow-sm flex flex-wrap items-center justify-between gap-4">
        <div className="relative flex-1 max-w-md">
          <Search size={14} className="text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search by actor email, action code, or entity ID..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 text-xs border border-slate-300 rounded-md bg-slate-50"
          />
        </div>

        <div className="flex items-center gap-2">
          <label className="text-xs font-medium text-slate-600">Entity Type:</label>
          <select
            value={entityFilter}
            onChange={(e) => setEntityFilter(e.target.value)}
            className="text-xs border border-slate-300 rounded px-2.5 py-1.5 bg-slate-50"
          >
            <option value="All">All Entities</option>
            <option value="VENDOR">VENDOR</option>
            <option value="ASSESSMENT">ASSESSMENT</option>
            <option value="WORKFLOW">WORKFLOW</option>
            <option value="QUESTIONNAIRE">QUESTIONNAIRE</option>
            <option value="TASK">TASK</option>
            <option value="USER">USER</option>
            <option value="USER_GROUP">USER_GROUP</option>
            <option value="ATTRIBUTE">ATTRIBUTE</option>
            <option value="INTEGRATION">INTEGRATION</option>
            <option value="REPORT">REPORT</option>
          </select>
        </div>
      </div>

      <div className="bg-white border border-slate-200 rounded-lg shadow-sm overflow-x-auto">
        {loading ? (
          <div className="p-12 text-center text-slate-500">
            <p className="text-sm">Retrieving immutable audit records...</p>
          </div>
        ) : filteredLogs.length === 0 ? (
          <div className="p-12 text-center text-slate-500">
            <Database size={32} className="text-slate-400 mx-auto mb-2" />
            <p className="text-sm font-medium text-slate-700">No Audit Logs Found</p>
          </div>
        ) : (
          <table className="enterprise-table">
            <thead>
              <tr>
                <th style={{ width: '36px' }}></th>
                <th>Timestamp (UTC)</th>
                <th>Actor</th>
                <th>Action</th>
                <th>Entity Type</th>
                <th>Entity Reference</th>
              </tr>
            </thead>
            <tbody>
              {filteredLogs.map((log) => {
                const isExpanded = expandedLogId === log.id;
                return (
                  <React.Fragment key={log.id}>
                    <tr
                      onClick={() => setExpandedLogId(isExpanded ? null : log.id)}
                      className="cursor-pointer"
                    >
                      <td className="text-center text-slate-400">
                        {isExpanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                      </td>
                      <td className="whitespace-nowrap font-mono text-xs text-slate-600">
                        {new Date(log.timestamp).toLocaleString()}
                      </td>
                      <td className="whitespace-nowrap font-medium text-slate-900">
                        {log.actor_email}
                      </td>
                      <td className="whitespace-nowrap">
                        <span className="font-mono font-bold text-xs px-2 py-0.5 rounded bg-slate-100 text-slate-800 border border-slate-200">
                          {log.action}
                        </span>
                      </td>
                      <td className="whitespace-nowrap">
                        <span className="badge badge-info">{log.entity_type}</span>
                      </td>
                      <td className="whitespace-nowrap font-mono text-xs text-slate-500">
                        {log.entity_id}
                      </td>
                    </tr>

                    {isExpanded && (
                      <tr>
                        <td colSpan={6} className="p-4 bg-slate-50">
                          <div className="bg-slate-900 text-emerald-400 font-mono text-xs p-4 rounded-md overflow-x-auto">
                            <div className="text-slate-400 text-[10px] uppercase font-bold mb-2">
                              Audit Event Structured Payload:
                            </div>
                            <pre>{JSON.stringify(log.details, null, 2)}</pre>
                          </div>
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                );
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};
