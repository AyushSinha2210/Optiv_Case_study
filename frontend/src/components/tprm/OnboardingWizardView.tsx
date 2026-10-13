import React, { useState } from 'react';
import {
  GitBranch,
  CheckCircle,
  AlertCircle,
  ArrowRight,
  Building,
  Mail,
  Globe,
} from 'lucide-react';
import type { UserProfile, VendorCategory, VendorTier, VendorType, Criticality } from '../../types';

interface OnboardingWizardViewProps {
  currentUser: UserProfile;
  onVendorCreated?: (vendorId: string) => void;
  onComplete?: (vendor: any) => void;
}

export const OnboardingWizardView: React.FC<OnboardingWizardViewProps> = ({
  currentUser,
  onVendorCreated,
  onComplete,
}) => {
  const [name, setName] = useState('');
  const [type, setType] = useState<VendorType>('Technology');
  const [criticality, setCriticality] = useState<Criticality>('Medium');
  const [primaryVendorContact, setPrimaryVendorContact] = useState('');
  const [businessOwner, setBusinessOwner] = useState(currentUser.email);
  const [vendorTier, setVendorTier] = useState<VendorTier>('Tier 2');
  const [vendorCategory, setVendorCategory] = useState<VendorCategory>('Service Provider and Vendor');
  const [website, setWebsite] = useState('');

  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successResult, setSuccessResult] = useState<any | null>(null);

  // Real-time FSM Routing Preview Calculation (Table 10: WR.ON.1-6)
  const getRoutingPreview = () => {
    if (vendorTier === 'Tier 3') {
      return {
        rule: 'WR.ON.6',
        targetWorkflow: 'CD_Tier3 Workflow',
        launchStage: 'Launching Tier3',
        template: 'Due Diligence Questionnaire T3 v1',
        approver: 'Vendor Risk Management Group',
        autoApproval: 'Enabled upon favorable responses (QR.73 / WR.T3.3)',
      };
    }

    switch (vendorCategory) {
      case 'Revenue Partner':
        return {
          rule: 'WR.ON.1',
          targetWorkflow: 'CD_Revenue Partners Workflow',
          launchStage: 'Launching RevPart',
          template: 'Due Diligence Questionnaire T1-2 v1',
          approver: 'Vendor Risk Management Group',
          autoApproval: 'Disabled (Requires VRM Admin approval WR.RP.3)',
        };
      case 'Marketing Partner':
        return {
          rule: 'WR.ON.2',
          targetWorkflow: 'CD_Marketing Partners Workflow',
          launchStage: 'Launching MarPart',
          template: 'Due Diligence Questionnaire T1-2 v1',
          approver: 'Vendor Risk Management Group',
          autoApproval: 'Disabled (Requires VRM Admin approval WR.MP.3)',
        };
      case 'International Vendor':
        return {
          rule: 'WR.ON.3',
          targetWorkflow: 'CD_International Vendors Workflow',
          launchStage: 'Launching IntVen',
          template: 'Due Diligence Questionnaire T1-2 v1',
          approver: 'Vendor Risk Management Group',
          autoApproval: 'Disabled (Requires VRM Admin approval WR.IV.3)',
        };
      case 'Staffing Vendor':
        return {
          rule: 'WR.ON.5',
          targetWorkflow: 'CD_Staffing Vendors Workflow',
          launchStage: 'Launching StafVen',
          template: 'Due Diligence Questionnaire T1-2 v1',
          approver: 'Vendor Risk Management Group',
          autoApproval: 'Disabled (Requires VRM Admin approval WR.SV.3)',
        };
      case 'Service Provider and Vendor':
      default:
        return {
          rule: 'WR.ON.4',
          targetWorkflow: 'CD_Service Providers Workflow',
          launchStage: 'Launching ServPro',
          template: 'Due Diligence Questionnaire T1-2 v1',
          approver: 'Vendor Risk Management Group',
          autoApproval: 'Disabled (Requires VRM Admin approval WR.SP.3)',
        };
    }
  };

  const preview = getRoutingPreview();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);

    try {
      const res = await fetch('/api/tprm/v1/vendors', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-User-Email': currentUser.email,
        },
        body: JSON.stringify({
          name,
          type,
          criticality,
          primary_vendor_contact: primaryVendorContact,
          business_owner: businessOwner,
          vendor_tier: vendorTier,
          vendor_category: vendorCategory,
          website,
        }),
      });

      if (res.ok) {
        const data = await res.json();
        setSuccessResult(data);
      } else {
        const err = await res.json();
        setError(err.detail || 'Failed to onboard vendor.');
      }
    } catch (err: any) {
      setError(err.message || 'Network error.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="onboarding-wizard-container">
      <div className="view-header-row mb-6">
        <div>
          <h2>Third-Party Onboarding Wizard</h2>
          <p>
            Standardized intake capturing authoritative <strong>Table 9</strong> attributes with dynamic workflow assignment
          </p>
        </div>
      </div>

      {successResult ? (
        <div className="glass-panel success-box text-center py-10">
          <CheckCircle size={48} className="text-emerald mx-auto mb-4" />
          <h3 className="text-xl font-bold mb-2">Vendor Successfully Onboarded!</h3>
          <p className="text-slate-300 mb-4">
            Vendor <strong>{successResult.name}</strong> was ingested into <strong>CD_Onboarding Workflow</strong> and automatically routed to:
          </p>
          <div className="routing-result-pill mx-auto mb-6">
            <GitBranch size={16} className="text-cyan" />
            <span className="font-mono text-cyan">{successResult.workflow}</span>
            <ArrowRight size={14} className="text-muted" />
            <span className="font-mono text-amber">{successResult.stage}</span>
          </div>
          <button
            className="btn btn-primary"
            onClick={() => {
              if (onVendorCreated) onVendorCreated(successResult.vendor_id);
              if (onComplete) onComplete(successResult);
            }}
          >
            Open Vendor Record
          </button>
        </div>
      ) : (
        <div className="onboarding-grid">
          {/* Intake Form */}
          <form className="glass-panel intake-form" onSubmit={handleSubmit}>
            <h3 className="form-section-title">1. Authoritative Vendor Metadata (Table 9)</h3>

            {error && (
              <div className="error-banner mb-4">
                <AlertCircle size={16} />
                <span>{error}</span>
              </div>
            )}

            <div className="form-group">
              <label className="input-label">
                Vendor Legal Name <span className="text-crimson">*</span>
              </label>
              <div className="input-with-icon">
                <Building size={16} className="text-muted" />
                <input
                  type="text"
                  required
                  placeholder="e.g. Apex Global Cloud Solutions Inc"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                />
              </div>
            </div>

            <div className="form-row-2">
              <div className="form-group">
                <label className="input-label">Vendor Category (Table 4)</label>
                <select
                  value={vendorCategory}
                  onChange={(e) => setVendorCategory(e.target.value as VendorCategory)}
                >
                  <option value="Service Provider and Vendor">Service Provider and Vendor</option>
                  <option value="Revenue Partner">Revenue Partner</option>
                  <option value="Marketing Partner">Marketing Partner</option>
                  <option value="Staffing Vendor">Staffing Vendor</option>
                  <option value="International Vendor">International Vendor</option>
                </select>
              </div>

              <div className="form-group">
                <label className="input-label">Vendor Risk Tier (Table 9)</label>
                <select
                  value={vendorTier}
                  onChange={(e) => setVendorTier(e.target.value as VendorTier)}
                >
                  <option value="Tier 1">Tier 1 (High Sensitivity / Annual Reassessment)</option>
                  <option value="Tier 2">Tier 2 (Medium Sensitivity / Bi-annual Reassessment)</option>
                  <option value="Tier 3">Tier 3 (Low Sensitivity / Auto-approval eligible)</option>
                </select>
              </div>
            </div>

            <div className="form-row-2">
              <div className="form-group">
                <label className="input-label">Engagement Type</label>
                <select
                  value={type}
                  onChange={(e) => setType(e.target.value as VendorType)}
                >
                  <option value="Technology">Technology</option>
                  <option value="Consulting">Consulting</option>
                  <option value="Operations">Operations</option>
                  <option value="Regulatory">Regulatory</option>
                  <option value="Strategic">Strategic</option>
                  <option value="Unknown">Unknown</option>
                </select>
              </div>

              <div className="form-group">
                <label className="input-label">Business Criticality</label>
                <select
                  value={criticality}
                  onChange={(e) => setCriticality(e.target.value as Criticality)}
                >
                  <option value="Critical">Critical</option>
                  <option value="High">High</option>
                  <option value="Medium">Medium</option>
                  <option value="Low">Low</option>
                </select>
              </div>
            </div>

            <div className="form-row-2">
              <div className="form-group">
                <label className="input-label">
                  Primary Vendor Contact (PVC Email) <span className="text-crimson">*</span>
                </label>
                <div className="input-with-icon">
                  <Mail size={16} className="text-muted" />
                  <input
                    type="email"
                    required
                    placeholder="pvc@vendor.com"
                    value={primaryVendorContact}
                    onChange={(e) => setPrimaryVendorContact(e.target.value)}
                  />
                </div>
              </div>

              <div className="form-group">
                <label className="input-label">
                  Cadence Business Owner Email <span className="text-crimson">*</span>
                </label>
                <div className="input-with-icon">
                  <Mail size={16} className="text-muted" />
                  <input
                    type="email"
                    required
                    placeholder="internal.owner@cadence.com"
                    value={businessOwner}
                    onChange={(e) => setBusinessOwner(e.target.value)}
                  />
                </div>
              </div>
            </div>

            <div className="form-group">
              <label className="input-label">Website Domain</label>
              <div className="input-with-icon">
                <Globe size={16} className="text-muted" />
                <input
                  type="url"
                  placeholder="https://www.vendor.com"
                  value={website}
                  onChange={(e) => setWebsite(e.target.value)}
                />
              </div>
            </div>

            <button type="submit" className="btn btn-primary w-full mt-4" disabled={submitting}>
              {submitting ? 'Onboarding & Routing...' : 'Initiate Vendor Onboarding (WR.ON.*)'}
            </button>
          </form>

          {/* Workflow Routing Simulation Panel */}
          <div className="glass-panel routing-preview-card">
            <h3 className="preview-title">
              <GitBranch size={16} className="text-cyan" />
              <span>Automated Workflow Routing Preview</span>
            </h3>
            <p className="text-xs text-muted mb-4">
              Evaluated strictly against Table 6, 7, 8, 10 routing logic upon intake creation.
            </p>

            <div className="preview-step">
              <div className="step-num">1</div>
              <div className="step-content">
                <span className="step-title">Gateway Intake</span>
                <span className="step-desc">Vendor enters <strong>CD_Onboarding Workflow</strong> in stage <code>New Third Party</code>.</span>
              </div>
            </div>

            <div className="preview-step active">
              <div className="step-num">2</div>
              <div className="step-content">
                <span className="step-title">Rule Evaluation: {preview.rule}</span>
                <span className="step-desc">
                  Category: <strong>{vendorCategory}</strong> • Tier: <strong>{vendorTier}</strong>
                </span>
              </div>
            </div>

            <div className="preview-step">
              <div className="step-num">3</div>
              <div className="step-content">
                <span className="step-title">Assigned Workflow Path</span>
                <div className="assigned-path-box">
                  <div className="font-mono text-cyan text-sm">{preview.targetWorkflow}</div>
                  <div className="text-xs text-slate-300">Initial Stage: <strong>{preview.launchStage}</strong></div>
                </div>
              </div>
            </div>

            <div className="preview-step">
              <div className="step-num">4</div>
              <div className="step-content">
                <span className="step-title">Questionnaire Distribution</span>
                <span className="step-desc">Dispatches <strong>{preview.template}</strong> to <code>{primaryVendorContact || 'vendor POC'}</code>.</span>
              </div>
            </div>

            <div className="preview-step">
              <div className="step-num">5</div>
              <div className="step-content">
                <span className="step-title">Decision Governance</span>
                <span className="step-desc">Approver: <strong>{preview.approver}</strong> • {preview.autoApproval}</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
