import React, { useState } from 'react';
import {
  Shield,
  Building2,
  Check,
  Search,
} from 'lucide-react';
import type { UserProfile } from '../../types';

interface OrganizationAdminViewProps {
  currentUser: UserProfile;
  onSelectUser: (user: UserProfile) => void;
}

export const OrganizationAdminView: React.FC<OrganizationAdminViewProps> = ({
  currentUser,
  onSelectUser,
}) => {
  const [search, setSearch] = useState<string>('');

  // Table 5 Roster of Users from Cadence_TPRM_Training.docx
  const usersRoster: UserProfile[] = [
    {
      id: 'usr_vrm_01',
      email: 'daniela.figueroa@cadence.com',
      full_name: 'Daniela Figueroa',
      is_active: true,
      is_admin: true,
      groups: ['Vendor Risk Management'],
      group_roles: { 'Vendor Risk Management': 'Lead Reviewer / Administrator' },
    },
    {
      id: 'usr_proc_01',
      email: 'bridgett.gatewood@cadence.com',
      full_name: 'Bridgett Gatewood',
      is_active: true,
      is_admin: false,
      groups: ['Procurement'],
      group_roles: { Procurement: 'Contract Manager' },
    },
    {
      id: 'usr_sec_01',
      email: 'sarah.chen@cadence.com',
      full_name: 'Sarah Chen',
      is_active: true,
      is_admin: false,
      groups: ['Security'],
      group_roles: { Security: 'Principal Security Architect' },
    },
    {
      id: 'usr_leg_01',
      email: 'marcus.vance@cadence.com',
      full_name: 'Marcus Vance',
      is_active: true,
      is_admin: false,
      groups: ['Legal'],
      group_roles: { Legal: 'Legal Counsel' },
    },
    {
      id: 'usr_priv_01',
      email: 'elena.rostova@cadence.com',
      full_name: 'Elena Rostova',
      is_active: true,
      is_admin: false,
      groups: ['Privacy'],
      group_roles: { Privacy: 'Data Privacy Officer' },
    },
    {
      id: 'usr_it_01',
      email: 'david.kim@cadence.com',
      full_name: 'David Kim',
      is_active: true,
      is_admin: false,
      groups: ['IT'],
      group_roles: { IT: 'IT Operations Reviewer' },
    },
    {
      id: 'usr_comp_01',
      email: 'rachel.green@cadence.com',
      full_name: 'Rachel Green',
      is_active: true,
      is_admin: false,
      groups: ['Compliance'],
      group_roles: { Compliance: 'Regulatory Compliance Officer' },
    },
    {
      id: 'usr_fin_01',
      email: 'thomas.wright@cadence.com',
      full_name: 'Thomas Wright',
      is_active: true,
      is_admin: false,
      groups: ['Finance'],
      group_roles: { Finance: 'Financial Risk Analyst' },
    },
    {
      id: 'usr_dq_01',
      email: 'jessica.taylor@cadence.com',
      full_name: 'Jessica Taylor',
      is_active: true,
      is_admin: false,
      groups: ['Data Quality'],
      group_roles: { 'Data Quality': 'Data Quality Specialist' },
    },
  ];

  // RBAC Matrix
  const rbacMatrix = [
    {
      group: 'Vendor Risk Management (VRM)',
      permissions: [
        'Full TPRM Administrator',
        'Create & Classify Vendors',
        'Final Workflow Approvals & Rejections',
        'Approve Assessment Reassessments',
        'Manage Templates & Risk Rules',
      ],
      scope: 'Enterprise-wide across all vendor categories',
    },
    {
      group: 'Security',
      permissions: [
        'Review Security Assessment Sections',
        'Evaluate SOC 2 / ISO 27001 Controls',
        'Flag Security Risk Findings',
        'Approve/Reject Security Mitigations',
      ],
      scope: 'Security controls (QRC_001 - QRC_030)',
    },
    {
      group: 'Legal',
      permissions: [
        'Review Contractual / Regulatory Sections',
        'Verify Governing Law & Indemnification',
        'Approve Legal Risk Findings',
        'Ironclad Contract Sign-off',
      ],
      scope: 'Legal compliance and contract terms',
    },
    {
      group: 'Privacy',
      permissions: [
        'Review GDPR / CCPA Data Processing Sections',
        'Verify Cross-Border Data Transfers',
        'Approve Privacy Mitigations',
      ],
      scope: 'PII, Privacy controls, DPA clauses',
    },
    {
      group: 'Procurement',
      permissions: [
        'Onboard Vendor Intake',
        'Manage Vendor Contracts & Renewals',
        'Initiate Offboarding Deprovisioning',
        'View Assessment Summary',
      ],
      scope: 'Commercial vendor lifecycle',
    },
    {
      group: 'IT & Infrastructure',
      permissions: [
        'Review Architecture & Integration Sections',
        'Verify Torii Deprovisioning Tasks',
        'Network & SSO Integration Approval',
      ],
      scope: 'IT systems, SaaS tools, asset revocation',
    },
  ];

  const filteredUsers = usersRoster.filter(
    (u) =>
      search === '' ||
      u.full_name.toLowerCase().includes(search.toLowerCase()) ||
      u.email.toLowerCase().includes(search.toLowerCase()) ||
      u.groups.some((g) => g.toLowerCase().includes(search.toLowerCase()))
  );

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <Building2 className="w-6 h-6 text-indigo-600" />
            <h1 className="text-xl font-bold text-slate-900">Organization & Access Management</h1>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Section 10 & 16: Enterprise Hierarchy, 10 Table 5 Review Groups, and Group-Based Role Permissions.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold px-2.5 py-1 rounded bg-indigo-50 text-indigo-700 border border-indigo-200">
            Active Persona: {currentUser.full_name} ({currentUser.groups[0] || 'Admin'})
          </span>
        </div>
      </div>

      {/* Users Roster Section */}
      <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-3">
          <div>
            <h3 className="text-base font-bold text-slate-900">Cadence TPRM Staff Roster (Table 5)</h3>
            <p className="text-xs text-slate-500">
              Select any persona to immediately switch context and test group-specific review permissions.
            </p>
          </div>

          <div className="relative min-w-[220px]">
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search staff roster..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-8 pr-3 py-1 text-xs border border-slate-300 rounded-md bg-slate-50 focus:bg-white focus:outline-none"
            />
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200 text-[11px] font-bold text-slate-600 uppercase tracking-wider">
                <th className="py-2.5 px-4">Staff Member</th>
                <th className="py-2.5 px-4">Primary Review Group</th>
                <th className="py-2.5 px-4">Role Title</th>
                <th className="py-2.5 px-4">System Access</th>
                <th className="py-2.5 px-4 text-right">Switch Context</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200 text-xs text-slate-700">
              {filteredUsers.map((user) => {
                const isCurrent = user.email === currentUser.email;
                return (
                  <tr key={user.id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="py-2.5 px-4 font-semibold text-slate-900 whitespace-nowrap">
                      {user.full_name}
                      <div className="text-[11px] text-slate-400 font-normal">{user.email}</div>
                    </td>
                    <td className="py-2.5 px-4 whitespace-nowrap">
                      <span className="font-semibold text-slate-800 bg-slate-100 px-2 py-0.5 rounded border border-slate-200 text-[11px]">
                        {user.groups[0]}
                      </span>
                    </td>
                    <td className="py-2.5 px-4 whitespace-nowrap text-slate-600">
                      {user.group_roles[user.groups[0]] || 'Specialist'}
                    </td>
                    <td className="py-2.5 px-4 whitespace-nowrap">
                      {user.is_admin ? (
                        <span className="text-indigo-700 font-semibold bg-indigo-50 px-2 py-0.5 rounded text-[10px]">
                          Administrator
                        </span>
                      ) : (
                        <span className="text-slate-600 bg-slate-100 px-2 py-0.5 rounded text-[10px]">
                          Reviewer
                        </span>
                      )}
                    </td>
                    <td className="py-2.5 px-4 text-right whitespace-nowrap">
                      {isCurrent ? (
                        <span className="inline-flex items-center gap-1 text-[11px] font-bold text-emerald-600">
                          <Check className="w-3.5 h-3.5" />
                          Active Persona
                        </span>
                      ) : (
                        <button
                          onClick={() => onSelectUser(user)}
                          className="px-2.5 py-1 text-xs font-semibold text-indigo-600 hover:text-indigo-800 hover:bg-indigo-50 border border-indigo-200 rounded transition-colors"
                        >
                          Switch to User
                        </button>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Role & Permission Matrix */}
      <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm space-y-4">
        <div className="border-b border-slate-100 pb-3">
          <h3 className="text-base font-bold text-slate-900">
            Least-Privilege Group Responsibility Matrix
          </h3>
          <p className="text-xs text-slate-500">
            Rigid authorization separating Reviewer domains from Administrative workflow transitions.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {rbacMatrix.map((item, idx) => (
            <div key={idx} className="p-4 rounded-lg border border-slate-200 bg-slate-50/50 space-y-3">
              <div className="flex items-center gap-2">
                <Shield className="w-4 h-4 text-indigo-600" />
                <h4 className="text-xs font-bold text-slate-900">{item.group}</h4>
              </div>
              <ul className="text-xs text-slate-600 space-y-1.5 list-disc pl-4">
                {item.permissions.map((p, pIdx) => (
                  <li key={pIdx}>{p}</li>
                ))}
              </ul>
              <div className="pt-2 border-t border-slate-200 text-[11px] text-slate-500">
                <strong>Scope:</strong> {item.scope}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
