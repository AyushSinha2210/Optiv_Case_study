import React, { useState } from 'react';
import {
  Shield,
  Search,
  Bell,
  Building2,
  ChevronDown,
  CheckCircle2,
  Sun,
  Moon,
  LogOut,
} from 'lucide-react';
import type { UserProfile, NotificationItem } from '../../types';

interface HeaderProps {
  currentUser: UserProfile;
  onSwitchUser: (email: string) => void;
  notifications: NotificationItem[];
  onMarkNotificationRead: (id: string) => void;
  onSearch: (query: string) => void;
  theme?: 'light' | 'dark';
  onToggleTheme?: () => void;
  onLogout?: () => void;
}

const AVAILABLE_PERSONAS = [
  { email: 'daniela.figueroa@cadence.com', name: 'Daniela Figueroa (Synthetic)', role: 'VRM Admin / Legal / Finance / DQ' },
  { email: 'bridgett.gatewood@cadence.com', name: 'Bridgett Gatewood (Synthetic)', role: 'VRM Admin' },
  { email: 'kc.burney@cadence.com', name: 'KC Burney (Synthetic)', role: 'VRM Admin' },
  { email: 'jyoti.karwal@cadence.com', name: 'Jyoti Karwal (Synthetic)', role: 'VRM Admin / IT Group' },
  { email: 'tamika.oliver@cadence.com', name: 'Tamika Oliver (Synthetic)', role: 'VRM Edit / Compliance Group' },
  { email: 'shimane.smith@cadence.com', name: 'Shimane Smith (Synthetic)', role: 'VRM Edit / Legal Group' },
  { email: 'chris.schmitz@cadence.com', name: 'Chris Schmitz (Synthetic)', role: 'VRM Edit / Procurement Group' },
  { email: 'chris.ott@cadence.com', name: 'Chris Ott (Synthetic)', role: 'VRM Edit / Security Group' },
  { email: 'rob.tilney@cadence.com', name: 'Rob Tilney (Synthetic)', role: 'VRM Edit / IT Group' },
  { email: 'dayo.seton@cadence.com', name: 'Dayo Seton (Synthetic)', role: 'Privacy Group (Edit)' },
  { email: 'melisa.cardozo@cadence.com', name: 'Melisa Cardozo (Synthetic)', role: 'Security Group (Edit)' },
  { email: 'security@apexcloud.com', name: 'Apex Cloud Contact', role: 'Primary Vendor Contact (Respondent)' },
];

export const Header: React.FC<HeaderProps> = ({
  currentUser,
  onSwitchUser,
  notifications,
  onMarkNotificationRead,
  onSearch,
  theme = 'light',
  onToggleTheme,
  onLogout,
}) => {
  const [showUserDropdown, setShowUserDropdown] = useState(false);
  const [showNotifDropdown, setShowNotifDropdown] = useState(false);
  const [searchInput, setSearchInput] = useState('');

  const unreadCount = notifications.filter((n) => !n.is_read).length;

  return (
    <header className="enterprise-header">
      <div className="header-brand">
        <div className="logo-badge">
          <Shield className="logo-icon" size={18} />
        </div>
        <div className="brand-text">
          <div className="brand-title">CADENCE TPRM</div>
          <div className="brand-subtitle">OneTrust TPRM Configuration • Integrated Risk Management</div>
        </div>
        <div className="org-context-pill">
          <Building2 size={13} className="text-cyan" />
          <span>Cadence Design Systems</span>
        </div>
      </div>

      <form
        className="header-search-bar"
        onSubmit={(e) => {
          e.preventDefault();
          onSearch(searchInput);
        }}
      >
        <Search size={15} className="search-icon" />
        <input
          type="text"
          value={searchInput}
          placeholder="Search vendors, questionnaires, controls (QRC_*), rules (QR.* / WR.*)..."
          onChange={(e) => {
            setSearchInput(e.target.value);
            onSearch(e.target.value);
          }}
        />
      </form>

      <div className="header-actions">
        {onToggleTheme && (
          <button
            type="button"
            className="icon-button"
            onClick={onToggleTheme}
            title="Switch Light / Dark Enterprise Theme"
          >
            {theme === 'dark' ? <Sun size={15} /> : <Moon size={15} />}
            <span>{theme === 'dark' ? 'Light' : 'Dark'}</span>
          </button>
        )}

        <div className="dropdown-container">
          <button
            type="button"
            className={`icon-button ${unreadCount > 0 ? 'has-badge' : ''}`}
            onClick={() => {
              setShowNotifDropdown(!showNotifDropdown);
              setShowUserDropdown(false);
            }}
            title="Notifications & SLA Reminders"
          >
            <Bell size={16} />
            {unreadCount > 0 && <span className="notification-badge">{unreadCount}</span>}
          </button>

          {showNotifDropdown && (
            <div className="popover-menu notifications-menu">
              <div className="popover-header">
                <span>In-App Notifications & SLA Alerts</span>
                <span className="badge badge-info">{unreadCount} Unread</span>
              </div>
              <div className="popover-list">
                {notifications.length === 0 ? (
                  <div className="popover-empty">No notifications yet.</div>
                ) : (
                  notifications.map((n) => (
                    <div
                      key={n.id}
                      className={`notification-item ${n.is_read ? 'read' : 'unread'}`}
                      onClick={() => onMarkNotificationRead(n.id)}
                    >
                      <div className="notif-header">
                        <span className="notif-subject">{n.subject}</span>
                        <span className="notif-time">
                          {new Date(n.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </span>
                      </div>
                      <div className="notif-body">{n.body}</div>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
        </div>

        <div className="dropdown-container">
          <button
            type="button"
            className="user-profile-button"
            onClick={() => {
              setShowUserDropdown(!showUserDropdown);
              setShowNotifDropdown(false);
            }}
          >
            <div className="user-avatar">
              {(currentUser.full_name || 'U').charAt(0)}
            </div>
            <div className="user-info-text">
              <span className="user-name">{currentUser.full_name}</span>
              <span className="user-role-badge">
                {currentUser.is_admin ? 'VRM ADMIN' : (currentUser.groups?.[0] || 'Reviewer')}
              </span>
            </div>
            <ChevronDown size={14} />
          </button>

          {showUserDropdown && (
            <div className="popover-menu persona-menu">
              <div className="popover-header">
                <span>Switch Role / Group Persona (Table 5 RBAC)</span>
                {onLogout && (
                  <button
                    type="button"
                    onClick={() => {
                      setShowUserDropdown(false);
                      onLogout();
                    }}
                    className="btn-link text-xs"
                  >
                    <LogOut size={12} /> IAM Sign-In Portal
                  </button>
                )}
              </div>
              <div className="popover-list">
                {AVAILABLE_PERSONAS.map((p) => (
                  <div
                    key={p.email}
                    className={`persona-item ${p.email === currentUser.email ? 'selected' : ''}`}
                    onClick={() => {
                      onSwitchUser(p.email);
                      setShowUserDropdown(false);
                    }}
                  >
                    <div className="persona-info">
                      <div className="persona-name">{p.name}</div>
                      <div className="persona-role">{p.role}</div>
                      <div className="persona-email">{p.email}</div>
                    </div>
                    {p.email === currentUser.email && <CheckCircle2 size={16} className="text-cyan" />}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};


// ========================================================
// ENTERPRISE IAM ROLE & GROUP HIERARCHY LOGIN VIEW
// ========================================================
interface LoginViewProps {
  onLoginSuccess: (user: UserProfile, token?: string) => void;
  theme: "light" | "dark";
  onToggleTheme: () => void;
}

const HIERARCHY_GROUPS = [
  {
    group: "Vendor Risk Management Group (Admin)",
    department: "Vendor Risk Management (VRM)",
    permission: "Full Admin",
    roleCode: "TPRM_ADMIN",
    description: "Executive decision-making body. Full access to configure workflows, templates, attributes, and approve/reject third parties.",
    users: [
      { email: "daniela.figueroa@cadence.com", name: "Daniela Figueroa (Synthetic Demo)", title: "VRM Executive Lead" },
      { email: "bridgett.gatewood@cadence.com", name: "Bridgett Gatewood (Synthetic Demo)", title: "VRM Principal Administrator" },
      { email: "kc.burney@cadence.com", name: "KC Burney (Synthetic Demo)", title: "VRM Director" },
      { email: "jyoti.karwal@cadence.com", name: "Jyoti Karwal (Synthetic Demo)", title: "VRM & IT Governance Lead" },
    ],
  },
  {
    group: "Vendor Risk Management Group (Edit)",
    department: "Vendor Risk Management (VRM)",
    permission: "Edit / Review",
    roleCode: "VRM_EDIT",
    description: "Operational VRM reviewers with edit access across assessments and cross-departmental risk triage.",
    users: [
      { email: "tamika.oliver@cadence.com", name: "Tamika Oliver (Synthetic Demo)", title: "Compliance & VRM Specialist" },
      { email: "shimane.smith@cadence.com", name: "Shimane Smith (Synthetic Demo)", title: "Legal Counsel & VRM Reviewer" },
      { email: "chris.schmitz@cadence.com", name: "Chris Schmitz (Synthetic Demo)", title: "Procurement Lead & VRM Reviewer" },
      { email: "chris.ott@cadence.com", name: "Chris Ott (Synthetic Demo)", title: "Security Architect & VRM Reviewer" },
      { email: "rob.tilney@cadence.com", name: "Rob Tilney (Synthetic Demo)", title: "IT Systems Reviewer & VRM Edit" },
    ],
  },
  {
    group: "Security Group",
    department: "Information Security (SEC)",
    permission: "Edit (Security & Technical)",
    roleCode: "DEPT_REVIEWER",
    description: "Reviews Section 4 Security controls (QRC_Sec_4.9–4.35), SOC 2 / ISO 27001 / PCI certifications, penetration tests, and BCP/DRP.",
    users: [
      { email: "chris.ott@cadence.com", name: "Chris Ott (Synthetic Demo)", title: "Security Architect" },
      { email: "melisa.cardozo@cadence.com", name: "Melisa Cardozo (Synthetic Demo)", title: "Security Compliance Analyst" },
      { email: "dk.koran@cadence.com", name: "DK Koran (Synthetic Demo)", title: "Cloud Security Reviewer" },
      { email: "erik.hansen@cadence.com", name: "Erik Hansen (Synthetic Demo)", title: "Penetration Testing Reviewer" },
    ],
  },
  {
    group: "Privacy Group",
    department: "Data Privacy (PRIV)",
    permission: "Edit (Privacy & AI)",
    roleCode: "DEPT_REVIEWER",
    description: "Reviews Section 4 Privacy & AI controls (QRC_Pri_4.1–4.8), GDPR cross-border transfers, data subjects, and LLM governance.",
    users: [
      { email: "dayo.seton@cadence.com", name: "Dayo Seton (Synthetic Demo)", title: "Privacy & AI Governance Lead" },
    ],
  },
  {
    group: "Legal, IT, Finance, Procurement, Compliance & Data Quality Groups",
    department: "Operations (LEGAL / IT / FIN / PROC / COMP / DQ)",
    permission: "Edit (Departmental Sections)",
    roleCode: "DEPT_REVIEWER",
    description: "Reviews Section 1 Legal, Section 2 Compliance/AML, Section 3 Finance, Section 5 IT/SSO, Section 7 Procurement/ESG, and Data Quality.",
    users: [
      { email: "shimane.smith@cadence.com", name: "Shimane Smith (Legal Group)", title: "Legal Counsel" },
      { email: "rob.tilney@cadence.com", name: "Rob Tilney (IT Group)", title: "IT Systems Reviewer" },
      { email: "chris.schmitz@cadence.com", name: "Chris Schmitz (Procurement Group)", title: "Procurement Lead" },
      { email: "tamika.oliver@cadence.com", name: "Tamika Oliver (Compliance Group)", title: "Compliance Specialist" },
      { email: "security@apexcloud.com", name: "Apex Cloud PVC (External Respondent)", title: "Primary Vendor Contact" },
    ],
  },
];

export const LoginView: React.FC<LoginViewProps> = ({ onLoginSuccess, theme, onToggleTheme }) => {
  const [selectedGroupIdx, setSelectedGroupIdx] = useState<number>(0);
  const [selectedEmail, setSelectedEmail] = useState<string>("daniela.figueroa@cadence.com");
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleSignIn = async (emailToLogin: string) => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/tprm/v1/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: emailToLogin }),
      });
      if (res.ok) {
        const data = await res.json();
        onLoginSuccess(data.user, data.access_token);
      } else {
        const err = await res.json().catch(() => ({ detail: "Authentication failed" }));
        setError(err.detail || "Invalid credentials");
      }
    } catch (e: any) {
      setError(e.message || "Network error connecting to authentication service");
    } finally {
      setLoading(false);
    }
  };

  const activeGroup = HIERARCHY_GROUPS[selectedGroupIdx];

  return (
    <div className={`enterprise-shell ${theme === "dark" ? "theme-dark" : "theme-light"}`}>
      <header className="enterprise-header">
        <div className="header-brand">
          <div className="logo-badge">
            <Shield size={18} />
          </div>
          <div className="brand-text">
            <div className="brand-title">CADENCE ENTERPRISE TPRM CONSOLE</div>
            <div className="brand-subtitle">IAM Role & Group Hierarchy Sign-In • OneTrust TPRM Architecture</div>
          </div>
          <div className="org-context-pill">
            <Building2 size={13} className="text-cyan" />
            <span>Organization: Cadence Design Systems</span>
          </div>
        </div>
        <div className="header-actions">
          <button type="button" className="icon-button" onClick={onToggleTheme}>
            <span>Theme: {theme === "dark" ? "Dark Enterprise" : "Light Enterprise"}</span>
          </button>
        </div>
      </header>

      <main className="enterprise-main">
        <div className="max-w-2xl mx-auto mb-6 text-center">
          <h1 className="text-2xl font-bold text-slate-900">
            Enterprise Identity & Organizational Access Portal
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Hierarchy: <strong>Organization</strong> → <strong>Departments (9)</strong> → <strong>User Groups (Table 5)</strong> → <strong>Users</strong> → <strong>Assigned Roles</strong> → <strong>Permissions</strong>
          </p>
        </div>

        {error && (
          <div className="p-3 mb-4 bg-rose-50 border border-rose-200 text-rose-800 rounded-md text-xs text-center">
            {error}
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="bg-white border border-slate-200 rounded-lg p-4 shadow-sm space-y-2">
            <h2 className="text-xs font-bold text-slate-800 uppercase tracking-wider pb-2 border-b border-slate-100">
              1. Select TPRM User Group
            </h2>
            {HIERARCHY_GROUPS.map((g, idx) => (
              <button
                key={g.group}
                type="button"
                onClick={() => {
                  setSelectedGroupIdx(idx);
                  setSelectedEmail(g.users[0].email);
                }}
                className={`w-full text-left p-3 rounded-md border transition-all ${
                  selectedGroupIdx === idx ? "border-indigo-600 bg-indigo-50/40" : "border-slate-200 bg-white"
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-slate-900">{g.group}</span>
                  <span className="badge badge-neutral">{g.permission}</span>
                </div>
                <div className="text-[11px] text-slate-500 mt-1">Dept: {g.department}</div>
              </button>
            ))}
          </div>

          <div className="lg:col-span-2 space-y-6">
            <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm space-y-4">
              <div className="border-b border-slate-100 pb-3">
                <span className="badge badge-info">
                  Role: {activeGroup.roleCode} • {activeGroup.permission}
                </span>
                <h3 className="text-base font-bold text-slate-900 mt-1">{activeGroup.group}</h3>
                <p className="text-xs text-slate-500 mt-0.5">{activeGroup.description}</p>
              </div>

              <div>
                <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                  2. Select Authorized Group Member (Synthetic Demo Roster)
                </h4>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {activeGroup.users.map((u) => {
                    const isSelected = selectedEmail === u.email;
                    return (
                      <div
                        key={u.email}
                        onClick={() => setSelectedEmail(u.email)}
                        className={`p-3 rounded-md border cursor-pointer flex items-center justify-between ${
                          isSelected ? "border-indigo-600 bg-indigo-50/40" : "border-slate-200 bg-slate-50"
                        }`}
                      >
                        <div>
                          <div className="text-xs font-bold text-slate-900">{u.name}</div>
                          <div className="text-[11px] text-slate-600">{u.title}</div>
                          <div className="text-[10px] text-slate-500 font-mono mt-0.5">{u.email}</div>
                        </div>
                        {isSelected && <CheckCircle2 size={16} className="text-indigo-600 shrink-0" />}
                      </div>
                    );
                  })}
                </div>
              </div>

              <div className="pt-3 border-t border-slate-100 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div className="text-xs text-slate-600">
                  Selected Identity: <code className="font-mono font-bold text-slate-900">{selectedEmail}</code>
                </div>
                <button
                  type="button"
                  disabled={loading}
                  onClick={() => handleSignIn(selectedEmail)}
                  className="btn btn-primary"
                >
                  <span>{loading ? "Authenticating..." : "Sign In to TPRM Console"}</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};
