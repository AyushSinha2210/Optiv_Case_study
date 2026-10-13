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
} from 'lucide-react';
import type { VendorItem, UserProfile } from '../../types';

interface VendorDirectoryViewProps {
  currentUser: UserProfile;
  onInitiateAssessment?: (assessmentId: string) => void;
  onOpenQuestionnaire?: (assessmentId: string) => void;
  onRefreshData?: () => void;
}

export const VendorDirectoryView: React.FC<VendorDirectoryViewProps> = ({
  currentUser,
  onInitiateAssessment,
  onOpenQuestionnaire,
  onRefreshData,
}) => {
  const [vendors, setVendors] = useState<VendorItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [search, setSearch] = useState<string>('');
  const [categoryFilter, setCategoryFilter] = useState<string>('');
  const [tierFilter, setTierFilter] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('');

  const [selectedVendorId, setSelectedVendorId] = useState<string | null>(null);
  const [vendorDetails, setVendorDetails] = useState<any | null>(null);
  const [detailsLoading, setDetailsLoading] = useState<boolean>(false);

  // Decision Modal State
  const [decisionModal, setDecisionModal] = useState<{ open: boolean; type: 'approve' | 'reject'; assessmentId: string } | null>(null);
  const [decisionReason, setDecisionReason] = useState<string>('');
  const [decisionSubmitting, setDecisionSubmitting] = useState<boolean>(false);

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

    const endpoint = `/api/tprm/v1/assessments/${decisionModal.assessmentId}/${decisionModal.type}`;
    try {
      const res = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-User-Email': currentUser.email,
        },
        body: JSON.stringify({ decision_reason: decisionReason }),
      });

      if (res.ok) {
        setDecisionModal(null);
        setDecisionReason('');
        fetchVendors();
        if (selectedVendorId) openVendorDrawer(selectedVendorId);
        onRefreshData?.();
      } else {
        const err = await res.json();
        alert(`Decision failed: ${err.detail || 'Error'}`);
      }
    } catch (e) {
      alert(`Error submitting decision: ${e}`);
    } finally {
      setDecisionSubmitting(false);
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
    <div className="directory-view-container">
      {/* Header & Filter Controls */}
      <div className="view-header-row">
        <div>
          <h2>Vendor Directory & Third-Party Inventory</h2>
          <p>Authoritative inventory classified under the 5 standard categories and 3 risk tiers</p>
        </div>
        <button className="btn btn-secondary" onClick={fetchVendors}>
          <RefreshCw size={14} /> Refresh
        </button>
      </div>

      <div className="filter-bar glass-panel">
        <div className="filter-search">
          <Search size={16} className="text-muted" />
          <input
            type="text"
            placeholder="Search vendor name, contact email, business owner..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>

        <div className="filter-group">
          <label>Category:</label>
          <select value={categoryFilter} onChange={(e) => setCategoryFilter(e.target.value)}>
            <option value="">All Categories</option>
            <option value="Service Provider and Vendor">Service Provider and Vendor</option>
            <option value="Revenue Partner">Revenue Partner</option>
            <option value="Marketing Partner">Marketing Partner</option>
            <option value="Staffing Vendor">Staffing Vendor</option>
            <option value="International Vendor">International Vendor</option>
          </select>
        </div>

        <div className="filter-group">
          <label>Tier:</label>
          <select value={tierFilter} onChange={(e) => setTierFilter(e.target.value)}>
            <option value="">All Tiers</option>
            <option value="Tier 1">Tier 1</option>
            <option value="Tier 2">Tier 2</option>
            <option value="Tier 3">Tier 3</option>
          </select>
        </div>

        <div className="filter-group">
          <label>Status:</label>
          <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
            <option value="">All Statuses</option>
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
      <div className="table-card glass-panel">
        <table className="enterprise-table">
          <thead>
            <tr>
              <th>Vendor Name</th>
              <th>Category</th>
              <th>Risk Tier</th>
              <th>Type</th>
              <th>Status</th>
              <th>Current Stage</th>
              <th>Primary Contact</th>
              <th>Next Reassessment</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={9} className="text-center py-6 text-muted">
                  Loading vendors...
                </td>
              </tr>
            ) : vendors.length === 0 ? (
              <tr>
                <td colSpan={9} className="text-center py-6 text-muted">
                  No vendors found matching your filter criteria.
                </td>
              </tr>
            ) : (
              vendors.map((v: VendorItem) => (
                <tr key={v.id} className="cursor-pointer" onClick={() => openVendorDrawer(v.id)}>
                  <td className="font-semibold text-white">
                    <div className="flex items-center gap-2">
                      <Building size={14} className="text-cyan" />
                      <span>{v.name}</span>
                    </div>
                  </td>
                  <td>{v.vendor_category}</td>
                  <td>{getTierBadge(v.vendor_tier)}</td>
                  <td><span className="badge badge-neutral">{v.type}</span></td>
                  <td>{getStatusBadge(v.lifecycle_status)}</td>
                  <td className="text-xs text-muted">{v.current_stage}</td>
                  <td className="text-xs text-muted">{v.primary_vendor_contact}</td>
                  <td className="text-xs">
                    {v.next_reassessment_due_date ? new Date(v.next_reassessment_due_date).toLocaleDateString() : '—'}
                  </td>
                  <td>
                    <button
                      className="btn-link"
                      onClick={(e) => {
                        e.stopPropagation();
                        openVendorDrawer(v.id);
                      }}
                    >
                      <Eye size={14} /> View
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
          <div className="drawer-panel glass-panel" onClick={(e) => e.stopPropagation()}>
            <div className="drawer-header">
              <div className="flex items-center gap-3">
                <Building size={20} className="text-cyan" />
                <div>
                  <h3>{vendorDetails?.vendor?.name || 'Vendor Details'}</h3>
                  <span className="text-xs text-muted">ID: {selectedVendorId}</span>
                </div>
              </div>
              <button className="icon-close" onClick={() => setSelectedVendorId(null)}>
                <X size={18} />
              </button>
            </div>

            {detailsLoading || !vendorDetails ? (
              <div className="drawer-body-loading">Loading vendor record...</div>
            ) : (
              <div className="drawer-body">
                {/* Section: Table 9 Attributes */}
                <div className="drawer-section">
                  <h4>Authoritative Attributes (Table 9)</h4>
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
                      <span className="attr-label">Criticality</span>
                      <span className="attr-val font-semibold text-purple">{vendorDetails.vendor.criticality}</span>
                    </div>
                    <div className="attr-item">
                      <span className="attr-label">Primary Vendor Contact</span>
                      <span className="attr-val text-xs text-cyan">{vendorDetails.vendor.primary_vendor_contact}</span>
                    </div>
                    <div className="attr-item">
                      <span className="attr-label">Business Owner</span>
                      <span className="attr-val text-xs">{vendorDetails.vendor.business_owner}</span>
                    </div>
                    <div className="attr-item">
                      <span className="attr-label">Website</span>
                      <span className="attr-val text-xs">
                        <a href={vendorDetails.vendor.website} target="_blank" rel="noreferrer" className="text-cyan flex items-center gap-1">
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
                      <span className="attr-val font-mono text-xs text-amber">{vendorDetails.vendor.current_stage}</span>
                    </div>
                  </div>
                </div>

                {/* Section: Assessments & Questionnaires */}
                <div className="drawer-section">
                  <h4>Assessments & Due Diligence</h4>
                  {vendorDetails.assessments.length === 0 ? (
                    <p className="text-muted text-xs">No assessments generated yet.</p>
                  ) : (
                    <div className="drawer-list">
                      {vendorDetails.assessments.map((a: any) => (
                        <div key={a.id} className="assessment-card-mini">
                          <div className="flex justify-between items-center mb-1">
                            <span className="font-semibold text-white">{a.template_code}</span>
                            <span className="badge badge-info">{a.status}</span>
                          </div>
                          <div className="text-xs text-muted mb-2">
                            Score: {a.overall_score !== null ? `${a.overall_score}%` : 'Pending'} • Due: {a.due_date ? new Date(a.due_date).toLocaleDateString() : 'N/A'}
                          </div>
                          <div className="flex gap-2">
                            <button
                              className="btn btn-sm btn-secondary"
                              onClick={() => {
                                setSelectedVendorId(null);
                                if (onInitiateAssessment) onInitiateAssessment(a.id);
                                else if (onOpenQuestionnaire) onOpenQuestionnaire(a.id);
                              }}
                            >
                              Open Questionnaire Runner
                            </button>
                            {currentUser.is_admin && a.status === 'In Review' && (
                              <>
                                <button
                                  className="btn btn-sm btn-success"
                                  onClick={() => setDecisionModal({ open: true, type: 'approve', assessmentId: a.id })}
                                >
                                  Approve
                                </button>
                                <button
                                  className="btn btn-sm btn-alert"
                                  onClick={() => setDecisionModal({ open: true, type: 'reject', assessmentId: a.id })}
                                >
                                  Reject
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
                    <p className="text-muted text-xs">Zero inherent risks flagged. Assessment posture clean.</p>
                  ) : (
                    <div className="drawer-list">
                      {vendorDetails.findings.map((f: any) => (
                        <div key={f.id} className="finding-card-mini">
                          <div className="flex justify-between items-center mb-1">
                            <span className="font-semibold text-white text-xs">{f.risk_name}</span>
                            <span className={`badge ${f.inherent_risk === 'High' ? 'badge-alert' : f.inherent_risk === 'Medium' ? 'badge-warning' : 'badge-neutral'}`}>
                              {f.inherent_risk}
                            </span>
                          </div>
                          <div className="text-xs text-muted">
                            Control: <strong className="text-cyan">{f.control_id}</strong> ({f.control_name})
                          </div>
                          <div className="text-xs text-slate-300 mt-1">
                            Mitigation: {f.mitigation_recommendation}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                {/* Section: Contracts */}
                <div className="drawer-section">
                  <h4>Contracts & Agreements ({vendorDetails.contracts.length})</h4>
                  {vendorDetails.contracts.length === 0 ? (
                    <p className="text-muted text-xs">No active Ironclad contracts mapped.</p>
                  ) : (
                    <div className="drawer-list">
                      {vendorDetails.contracts.map((c: any) => (
                        <div key={c.id} className="contract-card-mini">
                          <div className="flex justify-between items-center">
                            <span className="font-semibold text-white text-xs">{c.title}</span>
                            <span className="badge badge-neutral">{c.source}</span>
                          </div>
                          <div className="text-xs text-muted mt-1">
                            Ref: {c.contract_reference} • Status: {c.status}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Decision Modal (Approve / Reject) */}
      {decisionModal && (
        <div className="modal-backdrop">
          <div className="modal-dialog glass-panel">
            <div className="modal-header">
              <h3>
                {decisionModal.type === 'approve' ? 'Approve Third-Party Vendor (WR.*.3)' : 'Reject Third-Party Vendor (WR.*.4)'}
              </h3>
              <button className="icon-close" onClick={() => setDecisionModal(null)}>
                <X size={18} />
              </button>
            </div>
            <div className="modal-body">
              <p className="text-sm text-slate-300 mb-3">
                {decisionModal.type === 'approve'
                  ? 'Approving moves this third party to the Live stage, updates last assessment completion date, and dispatches approval notifications to stakeholders (WR.*.6).'
                  : 'Rejecting advances the vendor to the Review Reject stage, dispatches rejection notifications, and automatically generates a 14-day follow-up task for the Business Owner (WR.*.5).'}
              </p>
              <label className="input-label">Mandatory Decision Justification / Audit Reason:</label>
              <textarea
                className="input-textarea"
                rows={4}
                placeholder="Enter justification for this formal decision..."
                value={decisionReason}
                onChange={(e) => setDecisionReason(e.target.value)}
              />
            </div>
            <div className="modal-footer">
              <button className="btn btn-secondary" onClick={() => setDecisionModal(null)} disabled={decisionSubmitting}>
                Cancel
              </button>
              <button
                className={`btn ${decisionModal.type === 'approve' ? 'btn-success' : 'btn-alert'}`}
                onClick={handleDecisionSubmit}
                disabled={decisionSubmitting || !decisionReason.trim()}
              >
                {decisionSubmitting ? 'Recording...' : `Confirm ${decisionModal.type === 'approve' ? 'Approval' : 'Rejection'}`}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
