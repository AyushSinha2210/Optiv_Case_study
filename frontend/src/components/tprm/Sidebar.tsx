import React, { useState } from 'react';
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
  ChevronDown,
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
  const [collapsedGroups, setCollapsedGroups] = useState<Record<string, boolean>>({});

  const toggleGroup = (title: string) => {
    setCollapsedGroups((prev) => ({ ...prev, [title]: !prev[title] }));
  };

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
        { id: 'onboarding', label: 'Onboarding Requests', icon: UserPlus },
        { id: 'reassessments', label: 'Reassessments & Renewals', icon: RefreshCw },
        { id: 'offboarding', label: 'Offboarding & Closure', icon: UserX },
      ],
    },
    {
      title: 'RISK MANAGEMENT',
      items: [
        { id: 'assessments', label: 'Risk Assessments', icon: FileText },
        { id: 'questionnaire', label: 'DDQ Templates & Runner', icon: HelpCircle },
        { id: 'findings', label: 'Risk Findings & Controls', icon: AlertOctagon, badge: openRisksCount, alert: true },
      ],
    },
    {
      title: 'WORKFLOW MANAGEMENT',
      items: [
        { id: 'workflows', label: 'Workflows & Rules (App. A)', icon: GitBranch },
      ],
    },
    {
      title: 'ORGANIZATION & ADMIN',
      items: [
        { id: 'organization', label: 'Groups, Attributes & Integrations', icon: ShieldCheck },
      ],
    },
    {
      title: 'REPORTING & AUDIT',
      items: [
        { id: 'reports', label: 'Reports & CSV Exports', icon: BarChart3 },
        { id: 'audit', label: 'Immutable Audit Logs', icon: ScrollText },
      ],
    },
  ];

  return (
    <aside className="enterprise-sidebar">
      <div className="sidebar-scroll-area">
        {navSections.map((sec) => {
          const isCollapsed = Boolean(collapsedGroups[sec.title]);
          return (
            <div key={sec.title} className="nav-group">
              <div className="nav-group-header" onClick={() => toggleGroup(sec.title)}>
                <span>{sec.title}</span>
                {isCollapsed ? <ChevronRight size={12} /> : <ChevronDown size={12} />}
              </div>
              {!isCollapsed && (
                <div className="nav-group-items">
                  {sec.items.map((item) => {
                    const Icon = item.icon;
                    const isActive = currentTab === item.id;
                    return (
                      <button
                        key={item.id}
                        type="button"
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
              )}
            </div>
          );
        })}
      </div>
    </aside>
  );
};
