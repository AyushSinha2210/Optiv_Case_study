import React from 'react';
import {
  LayoutDashboard,
  CheckSquare,
  Stamp,
  Users,
  UserPlus,
  RefreshCw,
  UserX,
  FileText,
  HelpCircle,
  AlertOctagon,
  GitBranch,
  ShieldCheck,
  BarChart3,
  ScrollText,
  ChevronRight,
} from 'lucide-react';

export type NavigationTab =
  | 'dashboard'
  | 'tasks'
  | 'approvals'
  | 'directory'
  | 'onboarding'
  | 'reassessments'
  | 'offboarding'
  | 'assessments'
  | 'questionnaire'
  | 'findings'
  | 'workflows'
  | 'organization'
  | 'reports'
  | 'audit';

interface SidebarProps {
  currentTab: NavigationTab;
  onSelectTab: (tab: NavigationTab) => void;
  pendingApprovalsCount: number;
  pendingTasksCount: number;
  openRisksCount: number;
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentTab,
  onSelectTab,
  pendingApprovalsCount,
  pendingTasksCount,
  openRisksCount,
}) => {
  const navSections = [
    {
      title: 'OVERVIEW',
      items: [
        { id: 'dashboard', label: 'Risk Dashboard', icon: LayoutDashboard },
        { id: 'tasks', label: 'My Tasks & SLAs', icon: CheckSquare, badge: pendingTasksCount },
        { id: 'approvals', label: 'Approvals Queue', icon: Stamp, badge: pendingApprovalsCount, alert: true },
      ],
    },
    {
      title: 'THIRD-PARTY MANAGEMENT',
      items: [
        { id: 'directory', label: 'Vendor Directory', icon: Users },
        { id: 'onboarding', label: 'Onboarding Wizard', icon: UserPlus },
        { id: 'reassessments', label: 'Reassessments & Renewals', icon: RefreshCw },
        { id: 'offboarding', label: 'Offboarding Management', icon: UserX },
      ],
    },
    {
      title: 'RISK MANAGEMENT',
      items: [
        { id: 'assessments', label: 'Assessments Inbox', icon: FileText },
        { id: 'questionnaire', label: 'Questionnaire Runner', icon: HelpCircle },
        { id: 'findings', label: 'Risk Findings Ledger', icon: AlertOctagon, badge: openRisksCount, alert: true },
      ],
    },
    {
      title: 'WORKFLOW AUTOMATION',
      items: [
        { id: 'workflows', label: 'Workflows & State FSM', icon: GitBranch },
      ],
    },
    {
      title: 'ORGANIZATION & GOVERNANCE',
      items: [
        { id: 'organization', label: 'User Groups & RBAC', icon: ShieldCheck },
      ],
    },
    {
      title: 'REPORTING & AUDIT',
      items: [
        { id: 'reports', label: 'Operational Reports', icon: BarChart3 },
        { id: 'audit', label: 'Immutable Audit Log', icon: ScrollText },
      ],
    },
  ];

  return (
    <aside className="enterprise-sidebar">
      <div className="sidebar-scroll-area">
        {navSections.map((sec, secIdx) => (
          <div key={secIdx} className="nav-group">
            <div className="nav-group-header">{sec.title}</div>
            <div className="nav-group-items">
              {sec.items.map((item) => {
                const Icon = item.icon;
                const isActive = currentTab === item.id;
                return (
                  <button
                    key={item.id}
                    className={`nav-item ${isActive ? 'active' : ''}`}
                    onClick={() => onSelectTab(item.id as NavigationTab)}
                  >
                    <Icon size={16} className="nav-item-icon" />
                    <span className="nav-item-label">{item.label}</span>
                    {item.badge !== undefined && item.badge > 0 && (
                      <span className={`nav-item-badge ${item.alert ? 'alert' : ''}`}>
                        {item.badge}
                      </span>
                    )}
                    {isActive && <ChevronRight size={14} className="active-indicator" />}
                  </button>
                );
              })}
            </div>
          </div>
        ))}
      </div>
    </aside>
  );
};
