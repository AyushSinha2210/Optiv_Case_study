import React, { useState, useEffect } from 'react';
import {
  Building2,
  Check,
  Search,
  Users,
  Settings,
  Link2,
  Plus,
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
  const [subTab, setSubTab] = useState<'hierarchy' | 'attributes' | 'integrations'>('hierarchy');
  const [search, setSearch] = useState<string>('');
  const [usersList, setUsersList] = useState<UserProfile[]>([]);
  const [hierarchy, setHierarchy] = useState<any | null>(null);
  const [attributes, setAttributes] = useState<any[]>([]);
  const [integrations, setIntegrations] = useState<any[]>([]);
  const [banner, setBanner] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // Create Group Form State
  const [newGroupName, setNewGroupName] = useState('');
  const [newGroupDesc, setNewGroupDesc] = useState('');
  const [newGroupPerm, setNewGroupPerm] = useState('Edit');

  // Create Attribute Form State
  const [newAttrKey, setNewAttrKey] = useState('');
  const [newAttrDesc, setNewAttrDesc] = useState('');
  const [newAttrType, setNewAttrType] = useState('Single select');
  const [newAttrOpts, setNewAttrOpts] = useState('');
  const [optionInputMap, setOptionInputMap] = useState<Record<string, string>>({});

  const loadData = async () => {
    const headers = { 'X-User-Email': currentUser.email };
    try {
      const [uRes, hRes, aRes, iRes] = await Promise.all([
        fetch('/api/tprm/v1/auth/users', { headers }),
        fetch('/api/tprm/v1/auth/hierarchy', { headers }),
        fetch('/api/tprm/v1/vendors/attributes/inventory', { headers }),
        fetch('/api/tprm/v1/integrations/status', { headers }),
      ]);
      if (uRes.ok) {
        const uData = await uRes.json();
        setUsersList(uData.users || uData.items || []);
      }
      if (hRes.ok) {
        setHierarchy(await hRes.json());
      }
      if (aRes.ok) {
        const aData = await aRes.json();
        setAttributes(aData.items || aData.attributes || []);
      }
      if (iRes.ok) {
        const iData = await iRes.json();
        setIntegrations(iData.integrations || []);
      }
    } catch (e) {
      console.error('Failed to load organization admin data', e);
    }
  };

  useEffect(() => {
    loadData();
  }, [currentUser.email]);

  const handleCreateGroup = async (e: React.FormEvent) => {
    e.preventDefault();
    setBanner(null);
    try {
      const res = await fetch('/api/tprm/v1/auth/groups', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-User-Email': currentUser.email },
        body: JSON.stringify({
          name: newGroupName,
          description: newGroupDesc,
          default_permission: newGroupPerm,
        }),
      });
      if (res.ok) {
        setBanner({ type: 'success', text: `User Group '${newGroupName}' created (Section 6.1).` });
        setNewGroupName('');
        setNewGroupDesc('');
        await loadData();
      } else {
        const err = await res.json();
        setBanner({ type: 'error', text: err.detail || 'Failed to create group' });
      }
    } catch (err) {
      setBanner({ type: 'error', text: 'Network error creating group' });
    }
  };

  const handleToggleUserStatus = async (userId: string) => {
    setBanner(null);
    try {
      const res = await fetch(`/api/tprm/v1/auth/users/${userId}/toggle-active`, {
        method: 'POST',
        headers: { 'X-User-Email': currentUser.email },
      });
      if (res.ok) {
        const data = await res.json();
        setBanner({
          type: 'success',
          text: `User account status updated to ${data.is_active ? 'Active' : 'Deactivated'} (Annual Membership Review Sec 6.1).`,
        });
        await loadData();
      } else {
        const err = await res.json();
        setBanner({ type: 'error', text: err.detail || 'Cannot toggle user status' });
      }
    } catch (e) {
      setBanner({ type: 'error', text: 'Error updating user status' });
    }
  };

  const handleCreateAttribute = async (e: React.FormEvent) => {
    e.preventDefault();
    setBanner(null);
    try {
      const opts = newAttrOpts
        .split(',')
        .map((s) => s.trim())
        .filter(Boolean);
      const res = await fetch('/api/tprm/v1/vendors/attributes/inventory', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-User-Email': currentUser.email },
        body: JSON.stringify({
          key_name: newAttrKey,
          description_key: newAttrDesc,
          response_type: newAttrType,
          options: opts,
        }),
      });
      if (res.ok) {
        setBanner({ type: 'success', text: `Custom attribute '${newAttrKey}' added to Attribute Manager (Section 6.2).` });
        setNewAttrKey('');
        setNewAttrDesc('');
        setNewAttrOpts('');
        await loadData();
      } else {
        const err = await res.json();
        setBanner({ type: 'error', text: err.detail || 'Failed to create attribute' });
      }
    } catch (e) {
      setBanner({ type: 'error', text: 'Error creating attribute' });
    }
  };

  const handleUpdateAttribute = async (attrId: string, payload: any) => {
    setBanner(null);
    try {
      const res = await fetch(`/api/tprm/v1/vendors/attributes/inventory/${attrId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json', 'X-User-Email': currentUser.email },
        body: JSON.stringify(payload),
      });
      if (res.ok) {
        setBanner({ type: 'success', text: 'Attribute configuration updated and logged.' });
        await loadData();
      } else {
        const err = await res.json();
        setBanner({ type: 'error', text: err.detail || 'Update blocked' });
      }
    } catch (e) {
      setBanner({ type: 'error', text: 'Error updating attribute' });
    }
  };

  const filteredUsers = usersList.filter(
    (u) =>
      search === '' ||
      u.full_name.toLowerCase().includes(search.toLowerCase()) ||
      u.email.toLowerCase().includes(search.toLowerCase()) ||
      u.groups.some((g) => g.toLowerCase().includes(search.toLowerCase()))
  );

  return (
    <div className="space-y-6">
      <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <Building2 size={20} className="text-indigo-600" />
            <h1 className="text-xl font-bold text-slate-900">
              Organization, User Groups, Attribute Manager & Integrations
            </h1>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Section 4.2, 5.2, 6.1 & 6.2: Organization → 9 Departments → 9 User Groups → 15 Synthetic Demo Users → Roles & Permissions.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button"
            onClick={() => setSubTab('hierarchy')}
            className={`btn btn-sm ${subTab === 'hierarchy' ? 'btn-primary' : 'btn-secondary'}`}
          >
            <Users size={13} /> User Groups & RBAC (Sec 6.1)
          </button>
          <button
            type="button"
            onClick={() => setSubTab('attributes')}
            className={`btn btn-sm ${subTab === 'attributes' ? 'btn-primary' : 'btn-secondary'}`}
          >
            <Settings size={13} /> Attribute Manager (Sec 6.2)
          </button>
          <button
            type="button"
            onClick={() => setSubTab('integrations')}
            className={`btn btn-sm ${subTab === 'integrations' ? 'btn-primary' : 'btn-secondary'}`}
          >
            <Link2 size={13} /> Integration Adapters (Sec 1.3–1.5)
          </button>
        </div>
      </div>

      {banner && (
        <div
          className={`p-3 rounded-md border text-xs font-medium ${
            banner.type === 'success'
              ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
              : 'bg-rose-50 border-rose-200 text-rose-800'
          }`}
        >
          {banner.text}
        </div>
      )}

      {/* SUB-TAB 1: User Groups, Roster & Hierarchy */}
      {subTab === 'hierarchy' && (
        <div className="space-y-6">
          <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-3">
              <div>
                <h3 className="text-base font-bold text-slate-900">
                  Authoritative Table 5 User Roster (15 Synthetic Demo Accounts)
                </h3>
                <p className="text-xs text-slate-500">
                  Distinguishes <strong>Vendor Risk Management Group Admin</strong> (Daniela Figueroa, Bridgett Gatewood, KC Burney, Jyoti Karwal) from <strong>Edit</strong> reviewers (Tamika Oliver, Shimane Smith, Chris Schmitz, Chris Ott, Rob Tilney, etc.).
                </p>
              </div>

              <div className="relative min-w-[220px]">
                <Search size={14} className="text-slate-400 absolute left-2.5 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  placeholder="Search user or group..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="w-full pl-8 pr-3 py-1.5 text-xs border border-slate-300 rounded-md bg-slate-50"
                />
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="enterprise-table">
                <thead>
                  <tr>
                    <th>Synthetic Staff Member</th>
                    <th>Assigned User Groups (Table 5)</th>
                    <th>Group Permission Level</th>
                    <th>Account Status</th>
                    <th className="text-right">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredUsers.map((user) => {
                    const isCurrent = user.email === currentUser.email;
                    return (
                      <tr key={user.id}>
                        <td className="font-semibold text-slate-900">
                          {user.full_name}
                          <div className="text-[11px] text-slate-500 font-mono">{user.email}</div>
                        </td>
                        <td>
                          <div className="flex flex-wrap gap-1">
                            {user.groups.map((g) => (
                              <span key={g} className="badge badge-neutral">
                                {g} ({user.group_roles?.[g] || 'Edit'})
                              </span>
                            ))}
                          </div>
                        </td>
                        <td>
                          {user.is_admin ? (
                            <span className="badge badge-info">Full Admin (TPRM_ADMIN)</span>
                          ) : (
                            <span className="badge badge-neutral">Edit / Reviewer</span>
                          )}
                        </td>
                        <td>
                          <span className={`badge ${user.is_active ? 'badge-success' : 'badge-alert'}`}>
                            {user.is_active ? 'Active' : 'Deactivated'}
                          </span>
                        </td>
                        <td className="text-right whitespace-nowrap">
                          <div className="inline-flex items-center gap-2">
                            {isCurrent ? (
                              <span className="text-xs font-bold text-emerald-600 inline-flex items-center gap-1">
                                <Check size={13} /> Active Persona
                              </span>
                            ) : (
                              <button
                                type="button"
                                onClick={() => onSelectUser(user)}
                                className="btn btn-sm btn-secondary"
                              >
                                Switch Persona
                              </button>
                            )}
                            {currentUser.is_admin && !isCurrent && (
                              <button
                                type="button"
                                onClick={() => handleToggleUserStatus(user.id)}
                                className="btn btn-sm btn-secondary"
                              >
                                {user.is_active ? 'Deactivate' : 'Activate'}
                              </button>
                            )}
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {/* User Groups & Create User Group (Section 6.1) */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 bg-white border border-slate-200 rounded-lg p-5 shadow-sm space-y-3">
              <h3 className="text-sm font-bold text-slate-900">
                Configured User Groups & Departmental Review Scope (Section 4.2)
              </h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {(hierarchy?.groups || []).map((g: any) => (
                  <div key={g.id} className="p-3.5 rounded-lg border border-slate-200 bg-slate-50 space-y-1.5">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-slate-900">{g.name}</span>
                      <span className={`badge ${g.default_permission === 'Admin' ? 'badge-info' : 'badge-neutral'}`}>
                        {g.default_permission} ({g.members_count} members)
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-600">{g.description}</p>
                    <div className="text-[10px] text-indigo-700 font-semibold">
                      Review Scope: {(g.review_sections || []).join(', ')}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {currentUser.is_admin && (
              <form className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm space-y-3" onSubmit={handleCreateGroup}>
                <h3 className="text-sm font-bold text-slate-900 border-b border-slate-100 pb-2">
                  Create User Group (Section 6.1)
                </h3>
                <div>
                  <label className="input-label">Group Name *</label>
                  <input
                    type="text"
                    required
                    value={newGroupName}
                    onChange={(e) => setNewGroupName(e.target.value)}
                    placeholder="e.g. TPRM_Executive_Audit_Group"
                    className="form-input"
                  />
                </div>
                <div>
                  <label className="input-label">Description *</label>
                  <textarea
                    rows={3}
                    required
                    value={newGroupDesc}
                    onChange={(e) => setNewGroupDesc(e.target.value)}
                    placeholder="Enter group responsibility description..."
                    className="input-textarea"
                  />
                </div>
                <div>
                  <label className="input-label">Default Permission Level</label>
                  <select
                    value={newGroupPerm}
                    onChange={(e) => setNewGroupPerm(e.target.value)}
                    className="form-select"
                  >
                    <option value="Edit">Edit (Reviewer)</option>
                    <option value="Admin">Admin (TPRM Administrator)</option>
                  </select>
                </div>
                <button type="submit" className="btn btn-primary w-full">
                  <Plus size={14} /> Create User Group
                </button>
              </form>
            )}
          </div>
        </div>
      )}

      {/* SUB-TAB 2: Attribute Manager (Section 6.2 & 6.9) */}
      {subTab === 'attributes' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 bg-white border border-slate-200 rounded-lg p-5 shadow-sm space-y-3">
            <h3 className="text-base font-bold text-slate-900">
              Inventory Manager — Vendor Attributes (Section 5.2 & 6.2)
            </h3>
            <p className="text-xs text-slate-500">
              Workflow-driving attributes (<code>Vendor Tier</code>, <code>Vendor Category</code>, <code>Primary vendor contact</code>, <code>Business Owner</code>) are protected from accidental deactivation (Section 6.9).
            </p>
            <div className="overflow-x-auto">
              <table className="enterprise-table">
                <thead>
                  <tr>
                    <th>Key Name</th>
                    <th>Response Type & Source</th>
                    <th>Permitted Options</th>
                    <th>Status</th>
                    <th>Add Option / Action</th>
                  </tr>
                </thead>
                <tbody>
                  {attributes.map((a) => (
                    <tr key={a.id}>
                      <td>
                        <div className="font-bold text-slate-900">{a.key_name}</div>
                        <div className="text-[11px] text-slate-500">{a.description_key}</div>
                      </td>
                      <td className="whitespace-nowrap">
                        <span className="badge badge-neutral">{a.response_type}</span>{' '}
                        <span className="badge badge-info">{a.source}</span>
                      </td>
                      <td>
                        <div className="flex flex-wrap gap-1">
                          {(a.options || []).length === 0 ? (
                            <span className="text-xs text-slate-400">Freeform ({a.response_type})</span>
                          ) : (
                            a.options.map((o: string) => (
                              <span key={o} className="badge badge-neutral">{o}</span>
                            ))
                          )}
                        </div>
                      </td>
                      <td>
                        <span className={`badge ${a.is_active ? 'badge-success' : 'badge-alert'}`}>
                          {a.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                      <td className="whitespace-nowrap">
                        {currentUser.is_admin && (
                          <div className="flex items-center gap-1.5">
                            {a.response_type === 'Single select' && (
                              <>
                                <input
                                  type="text"
                                  placeholder="New option (e.g. Tier 4)"
                                  value={optionInputMap[a.id] || ''}
                                  onChange={(e) =>
                                    setOptionInputMap((prev) => ({ ...prev, [a.id]: e.target.value }))
                                  }
                                  className="form-input"
                                  style={{ width: '130px', padding: '4px 8px', fontSize: '11px' }}
                                />
                                <button
                                  type="button"
                                  className="btn btn-sm btn-secondary"
                                  onClick={() => {
                                    const val = optionInputMap[a.id];
                                    if (val) {
                                      handleUpdateAttribute(a.id, { add_option: val });
                                      setOptionInputMap((prev) => ({ ...prev, [a.id]: '' }));
                                    }
                                  }}
                                >
                                  Add
                                </button>
                              </>
                            )}
                            <button
                              type="button"
                              className="btn btn-sm btn-secondary"
                              onClick={() => handleUpdateAttribute(a.id, { is_active: !a.is_active })}
                            >
                              {a.is_active ? 'Deactivate' : 'Activate'}
                            </button>
                          </div>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {currentUser.is_admin && (
            <form className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm space-y-3" onSubmit={handleCreateAttribute}>
              <h3 className="text-sm font-bold text-slate-900 border-b border-slate-100 pb-2">
                Add Custom Vendor Attribute (Section 6.2)
              </h3>
              <div>
                <label className="input-label">Name of Key *</label>
                <input
                  type="text"
                  required
                  value={newAttrKey}
                  onChange={(e) => setNewAttrKey(e.target.value)}
                  placeholder="e.g. Data Classification Scope"
                  className="form-input"
                />
              </div>
              <div>
                <label className="input-label">Description Key *</label>
                <textarea
                  rows={3}
                  required
                  value={newAttrDesc}
                  onChange={(e) => setNewAttrDesc(e.target.value)}
                  placeholder="Explain the attribute's purpose..."
                  className="input-textarea"
                />
              </div>
              <div>
                <label className="input-label">Response Type *</label>
                <select
                  value={newAttrType}
                  onChange={(e) => setNewAttrType(e.target.value)}
                  className="form-select"
                >
                  <option value="Single select">Single select</option>
                  <option value="Text">Text</option>
                  <option value="Email">Email</option>
                  <option value="URL">URL</option>
                </select>
              </div>
              {newAttrType === 'Single select' && (
                <div>
                  <label className="input-label">Option Values (Comma-separated)</label>
                  <input
                    type="text"
                    value={newAttrOpts}
                    onChange={(e) => setNewAttrOpts(e.target.value)}
                    placeholder="Restricted, Confidential, Public"
                    className="form-input"
                  />
                </div>
              )}
              <button type="submit" className="btn btn-primary w-full">
                Save Attribute
              </button>
            </form>
          )}
        </div>
      )}

      {/* SUB-TAB 3: Integration Boundary & Adapter Status (Section 1.3–1.5, 21) */}
      {subTab === 'integrations' && (
        <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm space-y-4">
          <h3 className="text-base font-bold text-slate-900">
            External Integration Boundary & Adapter Status (Section 1.3, 1.4, 1.5 & 21)
          </h3>
          <p className="text-xs text-slate-500">
            Clearly distinguishes active internal workflow capabilities and local development adapters from external third-party APIs requiring production credentials.
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {integrations.map((item) => (
              <div key={item.id} className="p-4 rounded-lg border border-slate-200 bg-slate-50 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-bold text-slate-900">{item.name}</span>
                  <span className="badge badge-info">{item.status}</span>
                </div>
                <p className="text-xs text-slate-600">{item.role}</p>
                <div className="text-xs text-slate-700">
                  <strong>Direction:</strong> {item.direction}
                </div>
                <div className="text-xs text-indigo-700 font-semibold">
                  <strong>Adapter Mode:</strong> {item.mode}
                </div>
                <div className="text-[11px] font-mono text-slate-500">
                  Endpoint: {item.endpoint}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
