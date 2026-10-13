import React, { useState } from 'react';
import {
  GitBranch,
  CheckCircle,
  AlertCircle,
  ArrowRight,
  Webhook,
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

  // Real-time FSM Routing Preview Calculation (Appendix A: WR.ON.1-6)
  const getRoutingPreview = () => {
    if (vendorTier === 'Tier 3') {
      return {
        rule: 'WR.ON.6 -> WR.T3.1 -> WR.T3.2',
        targetWorkflow: 'CD_Tier3 Workflow',
        launchStage: 'Launching Tier3',
        template: 'Due Diligence Questionnaire T3 v1',
        approver: 'Vendor Risk Management Group',
        autoApproval: 'Enabled upon favorable responses (QR.73 / WR.T3.3: "The third-party is Approved")',
      };
    }

    switch (vendorCategory) {
      case 'Revenue Partner':
        return {
          rule: 'WR.ON.1 -> WR.RP.1 -> WR.RP.2',
          targetWorkflow: 'CD_Revenue Partners Workflow',
          launchStage: 'Launching RevPart',
          template: 'Due Diligence Questionnaire T1-2 v1',
          approver: 'Vendor Risk Management Group',
          autoApproval: 'Disabled (Requires VRM Admin approval WR.RP.3)',
        };
      case 'Marketing Partner':
        return {
          rule: 'WR.ON.2 -> WR.MP.1 -> WR.MP.2',
          targetWorkflow: 'CD_Marketing Partners Workflow',
          launchStage: 'Launching MarPart',
          template: 'Due Diligence Questionnaire T1-2 v1',
          approver: 'Vendor Risk Management Group',
          autoApproval: 'Disabled (Requires VRM Admin approval WR.MP.3)',
        };
      case 'International Vendor':
        return {
          rule: 'WR.ON.3 -> WR.IV.1 -> WR.IV.2',
          targetWorkflow: 'CD_International Vendors Workflow',
          launchStage: 'Launching IntVen',
          template: 'Due Diligence Questionnaire T1-2 v1',
          approver: 'Vendor Risk Management Group',
          autoApproval: 'Disabled (Requires VRM Admin approval WR.IV.3)',
        };
      case 'Staffing Vendor':
        return {
          rule: 'WR.ON.5 -> WR.SV.1 -> WR.SV.2',
          targetWorkflow: 'CD_Staffing Vendors Workflow',
          launchStage: 'Launching StafVen',
          template: 'Due Diligence Questionnaire T1-2 v1',
          approver: 'Vendor Risk Management Group',
          autoApproval: 'Disabled (Requires VRM Admin approval WR.SV.3)',
        };
      case 'Service Provider and Vendor':
      default:
        return {
          rule: 'WR.ON.4 -> WR.SP.1 -> WR.SP.2',
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

  const handleSimulateIroncladWebhook = async () => {
    setError(null);
    setSubmitting(true);
    const sampleName = name.trim() || `Ironclad CLM Partner ${Math.floor(100 + Math.random() * 900)}`;
    const samplePvc = primaryVendorContact.trim() || 'compliance@ironcladpartner.com';
    try {
      const res = await fetch('/api/tprm/v1/integrations/ironclad/webhook', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          event_type: 'contract.executed',
          contract_id: `IC-AUTO-${Date.now().toString().slice(-5)}`,
          contract_data: {
            title: `Ironclad MSA — ${sampleName}`,
            contract_reference: `IC-AUTO-${Date.now().toString().slice(-5)}`,
          },
          vendor_data: {
            name: sampleName,
            type,
            criticality,
            primary_vendor_contact: samplePvc,
            business_owner: businessOwner || currentUser.email,
            vendor_tier: vendorTier,
            vendor_category: vendorCategory,
            website: website || 'https://ironcladpartner.com',
          },
        }),
      });
      if (res.ok) {
        const data = await res.json();
        setSuccessResult({
          vendor_id: data.vendor_id,
          name: data.vendor_name,
          workflow: preview.targetWorkflow,
          stage: data.current_stage,
          source: 'Ironclad Webhook Adapter',
        });
      } else {
        const err = await res.json();
        setError(err.detail || 'Ironclad webhook ingestion failed');
      }
    } catch (e: any) {
      setError(e.message || 'Error calling Ironclad webhook');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900">Third-Party Onboarding Request & Ironclad Intake</h2>
          <p className="text-xs text-slate-500 mt-1">
            Captures authoritative Section 5.2 attributes and routes through <strong>CD_Onboarding Workflow</strong> (Trigger: <code>On_T_Assign Workflow</code>)
          </p>
        </div>
        <button
          type="button"
          className="btn btn-secondary"
          disabled={submitting}
          onClick={handleSimulateIroncladWebhook}
        >
          <Webhook size={14} />
          <span>Simulate Ironclad CLM Webhook Intake</span>
        </button>
      </div>

      {successResult ? (
        <div className="bg-white border border-slate-200 rounded-lg p-8 shadow-sm text-center space-y-4">
          <CheckCircle size={42} className="text-emerald-600 mx-auto" />
          <h3 className="text-xl font-bold text-slate-900">Vendor Successfully Onboarded & Routed!</h3>
          <p className="text-xs text-slate-600">
            Vendor <strong>{successResult.name}</strong> entered <strong>CD_Onboarding Workflow</strong> (Stage: <code>New Third Party</code>) and was automatically routed to:
          </p>
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-md bg-indigo-50 border border-indigo-200 text-xs font-mono">
            <GitBranch size={15} className="text-indigo-600" />
            <span className="font-bold text-indigo-700">{successResult.workflow}</span>
            <ArrowRight size={14} className="text-slate-400" />
            <span className="font-bold text-slate-900">{successResult.stage}</span>
          </div>
          <div className="pt-2">
            <button
              type="button"
              className="btn btn-primary"
              onClick={() => {
                if (onVendorCreated) onVendorCreated(successResult.vendor_id);
                if (onComplete) onComplete(successResult);
              }}
            >
              View in Vendor Directory
            </button>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <form className="lg:col-span-2 bg-white border border-slate-200 rounded-lg p-5 shadow-sm space-y-4" onSubmit={handleSubmit}>
            <h3 className="text-sm font-bold text-slate-900 border-b border-slate-100 pb-2">
              1. Authoritative Vendor Attributes (Section 5.2 Mapping: Ironclad → OneTrust)
            </h3>

            {error && (
              <div className="p-3 bg-rose-50 border border-rose-200 text-rose-800 rounded text-xs flex items-center gap-2">
                <AlertCircle size={15} />
                <span>{error}</span>
              </div>
            )}

            <div>
              <label className="input-label">Name (Third-Party Legal Name) *</label>
              <input
                type="text"
                required
                className="form-input"
                placeholder="e.g. Apex Global Cloud Solutions Inc"
                value={name}
                onChange={(e) => setName(e.target.value)}
              />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="input-label">Vendor Category (Section 5.1 / 6.7) *</label>
                <select
                  className="form-select"
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

              <div>
                <label className="input-label">Vendor Tier (Section 5.7 / 6.6) *</label>
                <select
                  className="form-select"
                  value={vendorTier}
                  onChange={(e) => setVendorTier(e.target.value as VendorTier)}
                >
                  <option value="Tier 1">Tier 1 (High Risk / Annual Reassessment)</option>
                  <option value="Tier 2">Tier 2 (Medium Risk / 24-Month Reassessment)</option>
                  <option value="Tier 3">Tier 3 (Simplified DDQ T3 v1 / 24-Month)</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="input-label">Type (Nature of Engagement — Section 6.2)</label>
                <select
                  className="form-select"
                  value={type}
                  onChange={(e) => setType(e.target.value as VendorType)}
                >
                  <option value="Consulting">Consulting</option>
                  <option value="Operations">Operations</option>
                  <option value="Regulatory">Regulatory</option>
                  <option value="Strategic">Strategic</option>
                  <option value="Technology">Technology</option>
                  <option value="Unknown">Unknown</option>
                </select>
              </div>

              <div>
                <label className="input-label">Criticality (Optional — Section 6.3)</label>
                <select
                  className="form-select"
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

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="input-label">Primary vendor contact (Mandatory POC Email) *</label>
                <input
                  type="email"
                  required
                  className="form-input"
                  placeholder="pvc@vendor.com"
                  value={primaryVendorContact}
                  onChange={(e) => setPrimaryVendorContact(e.target.value)}
                />
              </div>

              <div>
                <label className="input-label">Business Owner (Internal POC Email) *</label>
                <input
                  type="email"
                  required
                  className="form-input"
                  placeholder="internal.owner@cadence.com"
                  value={businessOwner}
                  onChange={(e) => setBusinessOwner(e.target.value)}
                />
              </div>
            </div>

            <div>
              <label className="input-label">Website (Vendor Domain — Section 6.8)</label>
              <input
                type="url"
                className="form-input"
                placeholder="https://www.vendor.com"
                value={website}
                onChange={(e) => setWebsite(e.target.value)}
              />
            </div>

            <button type="submit" className="btn btn-primary w-full" disabled={submitting}>
              {submitting ? 'Onboarding & Routing...' : 'Initiate Vendor Onboarding (WR.ON.1–6)'}
            </button>
          </form>

          {/* Workflow Routing Simulation Panel */}
          <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm space-y-4">
            <div className="flex items-center gap-2 border-b border-slate-100 pb-2">
              <GitBranch size={16} className="text-indigo-600" />
              <h3 className="text-sm font-bold text-slate-900">Automated Workflow Routing Preview</h3>
            </div>
            <p className="text-xs text-slate-500">
              Evaluated dynamically against Appendix A rules upon vendor creation.
            </p>

            <div className="space-y-3 text-xs">
              <div className="p-3 rounded border border-slate-200 bg-slate-50">
                <div className="font-bold text-slate-900">1. Entry Workflow & Stage</div>
                <div className="text-slate-600 mt-0.5">
                  <code>CD_Onboarding Workflow</code> → Stage: <code>New Third Party</code> (Note: <code>Live</code> stage in Onboarding workflow is present but not used).
                </div>
              </div>

              <div className="p-3 rounded border border-indigo-200 bg-indigo-50/40">
                <div className="font-bold text-indigo-700">2. Rule Sequence: {preview.rule}</div>
                <div className="text-slate-700 mt-0.5">
                  Category: <strong>{vendorCategory}</strong> • Tier: <strong>{vendorTier}</strong>
                </div>
              </div>

              <div className="p-3 rounded border border-slate-200 bg-slate-50">
                <div className="font-bold text-slate-900">3. Destination Workflow & Stage</div>
                <div className="font-mono text-indigo-600 font-bold mt-0.5">{preview.targetWorkflow}</div>
                <div className="text-slate-600">Stage: <strong>{preview.launchStage}</strong></div>
              </div>

              <div className="p-3 rounded border border-slate-200 bg-slate-50">
                <div className="font-bold text-slate-900">4. Questionnaire & SLA.1 (9 Days)</div>
                <div className="text-slate-600 mt-0.5">
                  Launches <strong>{preview.template}</strong> to <code>{primaryVendorContact || 'Primary Vendor Contact'}</code> (9-day deadline, 5-day reminder).
                </div>
              </div>

              <div className="p-3 rounded border border-slate-200 bg-slate-50">
                <div className="font-bold text-slate-900">5. Governance & Approval</div>
                <div className="text-slate-600 mt-0.5">
                  Approver: <strong>{preview.approver}</strong> • {preview.autoApproval}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
