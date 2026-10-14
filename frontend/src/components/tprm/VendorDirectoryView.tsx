import React, { useState, useEffect } from 'react';
import {
  Search,
  Eye,
  ExternalLink,
  CheckCircle,
  XCircle,
  Clock,
  RefreshCw,
  Building,
  X,
  UserX,
  Archive,
  Share2,
} from 'lucide-react';
import type { VendorItem, UserProfile } from '../../types';

interface VendorDirectoryViewProps {
  currentUser: UserProfile;
  initialSearch?: string;
  initialStatusFilter?: string;
  onInitiateAssessment?: (assessmentId: string) => void;
  onOpenQuestionnaire?: (assessmentId: string) => void;
  onRefreshData?: () => void;
}

export const VendorDirectoryView: React.FC<VendorDirectoryViewProps> = ({
  currentUser,
  initialSearch = '',
  initialStatusFilter = '',
  onInitiateAssessment,
  onOpenQuestionnaire,
  onRefreshData,
}) => {
  const [vendors, setVendors] = useState<VendorItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [search, setSearch] = useState<string>(initialSearch);
  const [categoryFilter, setCategoryFilter] = useState<string>('');
  const [tierFilter, setTierFilter] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>(initialStatusFilter);

  const [selectedVendorId, setSelectedVendorId] = useState<string | null>(null);
  const [vendorDetails, setVendorDetails] = useState<any | null>(null);
  const [detailsLoading, setDetailsLoading] = useState<boolean>(false);
  const [actionBanner, setActionBanner] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // Decision Modal State (Approve / Reject / Offboard / Renew)
  const [decisionModal, setDecisionModal] = useState<{
    open: boolean;
    type: 'approve' | 'reject' | 'offboard' | 'renew';
    assessmentId?: string;
    vendorId: string;
  } | null>(null);
  const [decisionReason, setDecisionReason] = useState<string>('');
  const [renewalChoice, setRenewalChoice] = useState<string>('Renewed');
  const [decisionSubmitting, setDecisionSubmitting] = useState<boolean>(false);

  useEffect(() => {
    if (initialSearch !== undefined) setSearch(initialSearch);
  }, [initialSearch]);

  useEffect(() => {
    if (initialStatusFilter !== undefined) setStatusFilter(initialStatusFilter);
  }, [initialStatusFilter]);

  const fetchVendors = () => {
    setLoading(true);
    const params = new URLSearchParams();
    if (search) params.append('search', search);
    if (categoryFilter) params.append('category', categoryFilter);
    if (tierFilter) params.append('tier', tierFilter);
    if (statusFilter) params.append('lifecycle_status', statusFilter);

    fetch(`/api/tprm/v1/vendors?${params.toString()}`, {
      headers: { 'X-User-Email': currentUser.email },
    })
      .then((res) => res.json())
      .then((data) => {
        setVendors(data.items || []);
        setLoading(false);
      })
      .catch((err) => {
        console.error('Failed to load vendors', err);
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchVendors();
  }, [search, categoryFilter, tierFilter, statusFilter, currentUser.email]);

  const openVendorDrawer = (id: string) => {
    setSelectedVendorId(id);
    setDetailsLoading(true);
    setActionBanner(null);
    fetch(`/api/tprm/v1/vendors/${id}`, {
      headers: { 'X-User-Email': currentUser.email },
    })
      .then((res) => res.json())
      .then((data) => {
        setVendorDetails(data);
        setDetailsLoading(false);
      })
      .catch((err) => {
        console.error('Failed to load vendor details', err);
        setDetailsLoading(false);
      });
  };

  const handleDecisionSubmit = async () => {
    if (!decisionModal || !decisionReason.trim()) return;
    setDecisionSubmitting(true);
    setActionBanner(null);

    let endpoint = '';
    let bodyPayload: any = {};

    if (decisionModal.type === 'approve' || decisionModal.type === 'reject') {
      endpoint = `/api/tprm/v1/assessments/${decisionModal.assessmentId}/${decisionModal.type}`;
      bodyPayload = { decision_reason: decisionReason };
    } else if (decisionModal.type === 'offboard') {
      endpoint = `/api/tprm/v1/vendors/${decisionModal.vendorId}/offboard`;
      bodyPayload = { reason: decisionReason };
    } else if (decisionModal.type === 'renew') {
      endpoint = `/api/tprm/v1/vendors/${decisionModal.vendorId}/renew`;
      bodyPayload = { decision: renewalChoice, rationale: decisionReason };
    }

    try {
      const res = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-User-Email': currentUser.email,
        },
        body: JSON.stringify(bodyPayload),
      });

      if (res.ok) {
        setDecisionModal(null);
        setDecisionReason('');
        setActionBanner({ type: 'success', text: `Action '${decisionModal.type.toUpperCase()}' persisted and logged in audit trail.` });
        fetchVendors();
        if (selectedVendorId) openVendorDrawer(selectedVendorId);
        onRefreshData?.();
      } else {
        const err = await res.json();
        setActionBanner({ type: 'error', text: err.detail || 'Action failed' });
      }
    } catch (e: any) {
      setActionBanner({ type: 'error', text: e.message || 'Network error' });
    } finally {
      setDecisionSubmitting(false);
    }
  };

  const handleDirectVendorAction = async (vendorId: string, actionPath: 'close' | 'archive' | 'onetrust' | 'torii') => {
    setActionBanner(null);
    let url = `/api/tprm/v1/vendors/${vendorId}/${actionPath}`;
    if (actionPath === 'onetrust') url = `/api/tprm/v1/integrations/onetrust/sync/${vendorId}`;
    if (actionPath === 'torii') url = `/api/tprm/v1/integrations/torii/revoke/${vendorId}`;

    try {
      const res = await fetch(url, {
        method: 'POST',
        headers: { 'X-User-Email': currentUser.email },
      });
      if (res.ok) {
        const data = await res.json();
        setActionBanner({
          type: 'success',
          text:
            actionPath === 'close'
              ? 'Vendor manually moved to Closed stage.'
              : actionPath === 'archive'
              ? 'Closed vendor record manually archived.'
              : actionPath === 'onetrust'
              ? `Synced vendor risk payload to OneTrust adapter (${data.onetrust_payload?.stage}).`
              : `Simulated Torii offboarding asset revocation recorded (${data.details?.mode}).`,
        });
        fetchVendors();
        openVendorDrawer(vendorId);
        onRefreshData?.();
      } else {
        const err = await res.json();
        setActionBanner({ type: 'error', text: err.detail || 'Operation denied' });
      }
    } catch (e: any) {
      setActionBanner({ type: 'error', text: e.message || 'Error executing action' });
    }
  };

  const getTierBadge = (tier: string) => {
    if (tier === 'Tier 1') return <span className="tier-pill tier-pill-1">Tier 1</span>;
    if (tier === 'Tier 2') return <span className="tier-pill tier-pill-2">Tier 2</span>;
    return <span className="tier-pill tier-pill-3">Tier 3</span>;
  };

  const getStatusBadge = (status: string) => {
    if (status === 'Live') return <span className="badge badge-success"><CheckCircle size={12} /> Live</span>;
    if (status === 'In Progress') return <span className="badge badge-info"><Clock size={12} /> In Progress</span>;
    if (status === 'Review Reject') return <span className="badge badge-alert"><XCircle size={12} /> Review Reject</span>;
    if (status === 'Offboarding') return <span className="badge badge-purple">Offboarding</span>;
    if (status === 'Closed') return <span className="badge badge-neutral">Closed</span>;
    return <span className="badge badge-neutral">{status}</span>;
  };

  return (
    <div className="space-y-6">
      {/* Header & Filter Controls */}
      <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900">Vendor Directory & Third-Party Inventory</h2>
          <p className="text-xs text-slate-500 mt-1">
            Authoritative inventory classified under the 5 documented categories and 3 risk tiers (Section 5.1 / Table 9)
          </p>
        </div>
        <button type="button" className="btn btn-secondary" onClick={fetchVendors}>
          <RefreshCw size={14} /> Refresh Inventory
        </button>
      </div>

      {actionBanner && (
        <div
          className={`p-3 rounded-md border text-xs font-medium ${
            actionBanner.type === 'success'
              ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
              : 'bg-rose-50 border-rose-200 text-rose-800'
          }`}
        >
          {actionBanner.text}
        </div>
      )}

      <div className="bg-white border border-slate-200 rounded-lg p-4 shadow-sm flex flex-wrap items-center gap-4">
        <div className="relative flex-1 min-w-[240px]">
          <Search size={15} className="text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search vendor name, contact email, business owner..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-4 py-1.5 text-xs border border-slate-300 rounded-md bg-slate-50"
          />
        </div>

        <div className="flex items-center gap-2">
          <label className="text-xs font-semibold text-slate-600">Category:</label>
          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="text-xs border border-slate-300 rounded px-2.5 py-1.5 bg-slate-50"
          >
            <option value="">All Categories (5)</option>
            <option value="Service Provider and Vendor">Service Provider and Vendor</option>
            <option value="Revenue Partner">Revenue Partner</option>
            <option value="Marketing Partner">Marketing Partner</option>
            <option value="Staffing Vendor">Staffing Vendor</option>
            <option value="International Vendor">International Vendor</option>
          </select>
        </div>

        <div className="flex items-center gap-2">
          <label className="text-xs font-semibold text-slate-600">Tier:</label>
          <select
            value={tierFilter}
            onChange={(e) => setTierFilter(e.target.value)}
            className="text-xs border border-slate-300 rounded px-2.5 py-1.5 bg-slate-50"
          >
            <option value="">All Tiers (1–3)</option>
            <option value="Tier 1">Tier 1</option>
            <option value="Tier 2">Tier 2</option>
            <option value="Tier 3">Tier 3</option>
          </select>
        </div>

        <div className="flex items-center gap-2">
          <label className="text-xs font-semibold text-slate-600">Status:</label>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="text-xs border border-slate-300 rounded px-2.5 py-1.5 bg-slate-50"
          >
            <option value="">All Lifecycle States</option>
            <option value="New">New</option>
            <option value="In Progress">In Progress</option>
            <option value="Live">Live</option>
            <option value="Review Reject">Review Reject</option>
            <option value="Offboarding">Offboarding</option>
            <option value="Closed">Closed</option>
          </select>
        </div>
      </div>

      {/* Vendors Data Table */}
      <div className="bg-white border border-slate-200 rounded-lg shadow-sm overflow-x-auto">
        <table className="enterprise-table">
          <thead>
            <tr>
              <th>Vendor Name</th>
              <th>Category</th>
              <th>Risk Tier</th>
              <th>Type / Criticality</th>
              <th>Status</th>
              <th>Workflow & Stage</th>
              <th>Primary Contact</th>
              <th>Next Reassessment</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={9} className="text-center py-6 text-slate-500">
                  Loading vendors...
                </td>
              </tr>
            ) : vendors.length === 0 ? (
              <tr>
                <td colSpan={9} className="text-center py-6 text-slate-500">
                  No vendors found matching your filter criteria.
                </td>
              </tr>
            ) : (
              vendors.map((v: VendorItem) => (
                <tr key={v.id} className="cursor-pointer" onClick={() => openVendorDrawer(v.id)}>
                  <td className="font-semibold text-slate-900">
                    <div className="flex items-center gap-2">
                      <Building size={14} className="text-indigo-600" />
                      <span>{v.name}</span>
                      {v.is_archived && <span className="badge badge-neutral">Archived</span>}
                    </div>
                  </td>
                  <td>{v.vendor_category}</td>
                  <td>{getTierBadge(v.vendor_tier)}</td>
                  <td>
                    <span className="badge badge-neutral">{v.type}</span>{' '}
                    <span className="text-xs text-slate-500">({v.criticality})</span>
                  </td>
                  <td>{getStatusBadge(v.lifecycle_status)}</td>
                  <td>
                    <div className="font-mono text-xs text-slate-800">{v.current_workflow_name}</div>
                    <div className="text-[11px] text-indigo-600 font-semibold">{v.current_stage}</div>
                  </td>
                  <td className="text-xs text-slate-600">{v.primary_vendor_contact}</td>
                  <td className="text-xs">
                    {v.next_reassessment_due_date ? new Date(v.next_reassessment_due_date).toLocaleDateString() : '—'}
                  </td>
                  <td>
                    <button
                      type="button"
                      className="btn-link"
                      onClick={(e) => {
                        e.stopPropagation();
                        openVendorDrawer(v.id);
                      }}
                    >
                      <Eye size={14} /> Manage
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Slide-out Vendor Detail Drawer */}
      {selectedVendorId && (
        <div className="drawer-overlay" onClick={() => setSelectedVendorId(null)}>
          <div className="drawer-panel" onClick={(e) => e.stopPropagation()}>
            <div className="drawer-header">
              <div className="flex items-center gap-3">
                <Building size={20} className="text-indigo-600" />
                <div>
                  <h3 className="text-base font-bold text-slate-900">
                    {vendorDetails?.vendor?.name || 'Vendor Details'}
                  </h3>
                  <span className="text-xs text-slate-500 font-mono">ID: {selectedVendorId}</span>
                </div>
              </div>
              <button type="button" className="btn btn-sm btn-secondary" onClick={() => setSelectedVendorId(null)}>
                <X size={15} /> Close
              </button>
            </div>

            {detailsLoading || !vendorDetails ? (
              <div className="p-8 text-center text-xs text-slate-500">Loading vendor record...</div>
            ) : (
              <div className="drawer-body">
                {/* Lifecycle & Integration Actions Toolbar */}
                {currentUser.is_admin && (
                  <div className="drawer-section">
                    <h4>Lifecycle, Renewal, Offboarding & Integration Actions</h4>
                    <div className="flex flex-wrap gap-2">
                      <button
                        type="button"
                        className="btn btn-sm btn-secondary"
                        onClick={() =>
                          setDecisionModal({
                            open: true,
                            type: 'renew',
                            vendorId: vendorDetails.vendor.id,
                          })
                        }
                      >
                        Record Renewal Decision
                      </button>
                      {vendorDetails.vendor.lifecycle_status !== 'Offboarding' &&
                        vendorDetails.vendor.lifecycle_status !== 'Closed' && (
                          <button
                            type="button"
                            className="btn btn-sm btn-alert"
                            onClick={() =>
                              setDecisionModal({
                                open: true,
                                type: 'offboard',
                                vendorId: vendorDetails.vendor.id,
                              })
                            }
                          >
                            <UserX size={13} /> Initiate Offboarding
                          </button>
                        )}
                      {vendorDetails.vendor.lifecycle_status === 'Offboarding' && (
                        <>
                          <button
                            type="button"
                            className="btn btn-sm btn-secondary"
                            onClick={() => handleDirectVendorAction(vendorDetails.vendor.id, 'torii')}
                          >
                            Simulate Torii Revocation
                          </button>
                          <button
                            type="button"
                            className="btn btn-sm btn-primary"
                            onClick={() => handleDirectVendorAction(vendorDetails.vendor.id, 'close')}
                          >
                            Move to Closed Stage
                          </button>
                        </>
                      )}
                      {vendorDetails.vendor.lifecycle_status === 'Closed' && !vendorDetails.vendor.is_archived && (
                        <button
                          type="button"
                          className="btn btn-sm btn-secondary"
                          onClick={() => handleDirectVendorAction(vendorDetails.vendor.id, 'archive')}
                        >
                          <Archive size={13} /> Archive Vendor Record
                        </button>
                      )}
                      <button
                        type="button"
                        className="btn btn-sm btn-secondary"
                        onClick={() => handleDirectVendorAction(vendorDetails.vendor.id, 'onetrust')}
                      >
                        <Share2 size={13} /> Sync OneTrust Adapter
                      </button>
                    </div>
                  </div>
                )}

                {/* Section: Table 9 Attributes */}
                <div className="drawer-section">
                  <h4>Authoritative Vendor Attributes (Section 5.2)</h4>
                  <div className="attribute-grid">
                    <div className="attr-item">
                      <span className="attr-label">Vendor Category</span>
                      <span className="attr-val font-semibold">{vendorDetails.vendor.vendor_category}</span>
                    </div>
                    <div className="attr-item">
                      <span className="attr-label">Vendor Tier</span>
                      <span className="attr-val">{getTierBadge(vendorDetails.vendor.vendor_tier)}</span>
                    </div>
                    <div className="attr-item">
                      <span className="attr-label">Type</span>
                      <span className="attr-val">{vendorDetails.vendor.type}</span>
                    </div>
                    <div className="attr-item">
                      <span className="attr-label">Criticality (Optional)</span>
                      <span className="attr-val font-semibold">{vendorDetails.vendor.criticality}</span>
                    </div>
                    <div className="attr-item">
                      <span className="attr-label">Primary Vendor Contact</span>
                      <span className="attr-val text-xs font-mono">{vendorDetails.vendor.primary_vendor_contact}</span>
                    </div>
                    <div className="attr-item">
                      <span className="attr-label">Business Owner</span>
                      <span className="attr-val text-xs font-mono">{vendorDetails.vendor.business_owner}</span>
                    </div>
                    <div className="attr-item">
                      <span className="attr-label">Website</span>
                      <span className="attr-val text-xs">
                        <a
                          href={vendorDetails.vendor.website}
                          target="_blank"
                          rel="noreferrer"
                          className="text-indigo-600 inline-flex items-center gap-1"
                        >
                          {vendorDetails.vendor.website || 'N/A'} <ExternalLink size={11} />
                        </a>
                      </span>
                    </div>
                    <div className="attr-item">
                      <span className="attr-label">Lifecycle Status</span>
                      <span className="attr-val">{getStatusBadge(vendorDetails.vendor.lifecycle_status)}</span>
                    </div>
                    <div className="attr-item">
                      <span className="attr-label">Active Workflow</span>
                      <span className="attr-val font-mono text-xs">{vendorDetails.vendor.current_workflow_name}</span>
                    </div>
                    <div className="attr-item">
                      <span className="attr-label">Current Stage</span>
                      <span className="attr-val font-mono text-xs font-bold text-indigo-600">
                        {vendorDetails.vendor.current_stage}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Section: Assessments & Questionnaires */}
                <div className="drawer-section">
                  <h4>Assessments & Due Diligence ({vendorDetails.assessments.length})</h4>
                  {vendorDetails.assessments.length === 0 ? (
                    <p className="text-slate-500 text-xs">No assessments generated yet.</p>
                  ) : (
                    <div className="space-y-2">
                      {vendorDetails.assessments.map((a: any) => (
                        <div key={a.id} className="p-3 rounded border border-slate-200 bg-slate-50 space-y-2">
                          <div className="flex justify-between items-center">
                            <span className="font-semibold text-slate-900 text-xs">{a.template_code}</span>
                            <span className="badge badge-info">{a.status}</span>
                          </div>
                          <div className="text-xs text-slate-600">
                            Average Score: <strong>{a.overall_score !== null ? `${a.overall_score}%` : 'Pending'}</strong> • Due:{' '}
                            {a.due_date ? new Date(a.due_date).toLocaleDateString() : 'N/A'}
                          </div>
                          {a.decision_reason && (
                            <div className="text-[11px] text-slate-500">
                              Decision Note: <em>{a.decision_reason}</em>
                            </div>
                          )}
                          <div className="flex flex-wrap gap-2">
                            <button
                              type="button"
                              className="btn btn-sm btn-secondary"
                              onClick={() => {
                                setSelectedVendorId(null);
                                if (onInitiateAssessment) onInitiateAssessment(a.id);
                                else if (onOpenQuestionnaire) onOpenQuestionnaire(a.id);
                              }}
                            >
                              Open Questionnaire Runner
                            </button>
                            {currentUser.is_admin && a.status !== 'Approved' && (
                              <>
                                <button
                                  type="button"
                                  className="btn btn-sm btn-success"
                                  onClick={() =>
                                    setDecisionModal({
                                      open: true,
                                      type: 'approve',
                                      assessmentId: a.id,
                                      vendorId: vendorDetails.vendor.id,
                                    })
                                  }
                                >
                                  Approve (WR.*.3)
                                </button>
                                <button
                                  type="button"
                                  className="btn btn-sm btn-alert"
                                  onClick={() =>
                                    setDecisionModal({
                                      open: true,
                                      type: 'reject',
                                      assessmentId: a.id,
                                      vendorId: vendorDetails.vendor.id,
                                    })
                                  }
                                >
                                  Reject (WR.*.4)
                                </button>
                              </>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Section: Inherent Risk Findings */}
                <div className="drawer-section">
                  <h4>Inherent Risk Findings ({vendorDetails.findings.length})</h4>
                  {vendorDetails.findings.length === 0 ? (
                    <p className="text-slate-500 text-xs">Zero inherent risks flagged. Assessment posture clean.</p>
                  ) : (
                    <div className="space-y-2">
                      {vendorDetails.findings.map((f: any) => (
                        <div key={f.id} className="p-3 rounded border border-rose-200 bg-rose-50/40 space-y-1">
                          <div className="flex justify-between items-center">
                            <span className="font-semibold text-slate-900 text-xs">
                              {f.rule_code}: {f.risk_name}
                            </span>
                            <span className={`badge ${f.inherent_risk === 'High' ? 'badge-alert' : 'badge-warning'}`}>
                              {f.inherent_risk}
                            </span>
                          </div>
                          <div className="text-xs text-slate-700">
                            Control: <strong className="font-mono">{f.control_id}</strong> ({f.control_name})
                          </div>
                          <div className="text-xs text-slate-600">
                            Mitigation: {f.mitigation_recommendation}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Section: Workflow Transition History */}
                {vendorDetails.transitions && vendorDetails.transitions.length > 0 && (
                  <div className="drawer-section">
                    <h4>Workflow Transition History ({vendorDetails.transitions.length})</h4>
                    <div className="space-y-2">
                      {vendorDetails.transitions.map((tr: any) => (
                        <div key={tr.id} className="p-2.5 rounded border border-slate-200 bg-slate-50 text-xs">
                          <div className="flex justify-between font-semibold text-slate-900">
                            <span>
                              {tr.from_stage} → {tr.to_stage}
                            </span>
                            <span className="font-mono text-[11px] text-indigo-600">{tr.rule_name}</span>
                          </div>
                          <div className="text-[11px] text-slate-600 mt-0.5">{tr.decision_reason}</div>
                          <div className="text-[10px] text-slate-400 mt-0.5">
                            Actor: {tr.actor_email} • Trigger: {tr.trigger_name} • {new Date(tr.timestamp).toLocaleString()}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Section: Contracts & Renewals */}
                <div className="drawer-section">
                  <h4>Ironclad Contracts & Renewal Decisions ({vendorDetails.contracts.length})</h4>
                  <div className="space-y-2">
                    {vendorDetails.contracts.map((c: any) => (
                      <div key={c.id} className="p-2.5 rounded border border-slate-200 bg-slate-50 text-xs">
                        <div className="flex justify-between items-center">
                          <span className="font-semibold text-slate-900">{c.title}</span>
                          <span className="badge badge-neutral">{c.source}</span>
                        </div>
                        <div className="text-slate-600 mt-1">
                          Ref: <span className="font-mono">{c.contract_reference}</span> • Status: {c.status}
                        </div>
                      </div>
                    ))}
                    {vendorDetails.renewals &&
                      vendorDetails.renewals.map((r: any) => (
                        <div key={r.id} className="p-2.5 rounded border border-indigo-200 bg-indigo-50 text-xs">
                          <div className="font-semibold text-slate-900">Renewal Decision: {r.decision}</div>
                          <div className="text-slate-600 mt-0.5">{r.rationale}</div>
                        </div>
                      ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Decision Modal (Approve / Reject / Offboard / Renew) */}
      {decisionModal && (
        <div className="modal-backdrop">
          <div className="modal-dialog">
            <div className="modal-header">
              <h3 className="text-base font-bold text-slate-900">
                {decisionModal.type === 'approve'
                  ? 'Approve Third-Party Vendor (WR.*.3)'
                  : decisionModal.type === 'reject'
                  ? 'Reject Third-Party Vendor (WR.*.4 & WR.*.5)'
                  : decisionModal.type === 'offboard'
                  ? 'Initiate Third-Party Offboarding Workflow'
                  : 'Record Vendor Renewal Decision (Section 18)'}
              </h3>
              <button type="button" className="btn btn-sm btn-secondary" onClick={() => setDecisionModal(null)}>
                <X size={14} />
              </button>
            </div>
            <div className="modal-body space-y-3">
              <p className="text-xs text-slate-600">
                {decisionModal.type === 'approve'
                  ? 'Approving moves this third party to the Live stage, sets the reassessment timer (275d/640d), and sends approval notifications (WR.*.6).'
                  : decisionModal.type === 'reject'
                  ? 'Rejecting moves the vendor to the category-specific Review Reject stage, sends rejection notifications, and creates a 14-day task for the Business Owner with VRM collaboration (WR.*.5).'
                  : decisionModal.type === 'offboard'
                  ? 'Initiates stakeholder review and approval for offboarding before moving the vendor to Closed.'
                  : 'Records a formal renewal decision informed by the vendor’s reassessment results and open risk findings.'}
              </p>

              {decisionModal.type === 'renew' && (
                <div>
                  <label className="input-label">Renewal Decision Outcome:</label>
                  <select
                    className="form-select"
                    value={renewalChoice}
                    onChange={(e) => setRenewalChoice(e.target.value)}
                  >
                    <option value="Renewed">Renewed (Continue Relationship)</option>
                    <option value="Conditional Renewal">Conditional Renewal (Remediation Required)</option>
                    <option value="Non-Renewal / Offboard">Non-Renewal (Initiate Offboarding)</option>
                  </select>
                </div>
              )}

              <div>
                <label className="input-label">Mandatory Decision Justification / Audit Reason:</label>
                <textarea
                  className="input-textarea"
                  rows={4}
                  placeholder="Enter justification for this formal decision..."
                  value={decisionReason}
                  onChange={(e) => setDecisionReason(e.target.value)}
                />
              </div>
            </div>
            <div className="modal-footer">
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => setDecisionModal(null)}
                disabled={decisionSubmitting}
              >
                Cancel
              </button>
              <button
                type="button"
                className={`btn ${
                  decisionModal.type === 'approve' || decisionModal.type === 'renew' ? 'btn-success' : 'btn-alert'
                }`}
                onClick={handleDecisionSubmit}
                disabled={decisionSubmitting || !decisionReason.trim()}
              >
                {decisionSubmitting ? 'Recording...' : `Confirm ${decisionModal.type.toUpperCase()}`}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
