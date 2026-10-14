import React from 'react';
import {
  LayoutDashboard,
  FileText,
  PlaySquare,
  ShieldAlert,
  EyeOff,
  CheckCircle2,
  ScrollText,
  Download,
  Settings,
  HelpCircle,
} from 'lucide-react';

export type OptivTab =
  | 'overview'
  | 'workspace'
  | 'runs'
  | 'findings'
  | 'redaction'
  | 'verification'
  | 'audit'
  | 'reports'
  | 'settings';

interface SidebarProps {
  currentTab: OptivTab;
  onSelectTab: (tab: OptivTab) => void;
  openFindingsCount?: number;
  blockedCount?: number;
  onOpenAssistant: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentTab,
  onSelectTab,
  openFindingsCount = 0,
  blockedCount = 0,
  onOpenAssistant,
}) => {
  const navItems: { id: OptivTab; label: string; icon: React.ReactNode; badge?: React.ReactNode }[] = [
    { id: 'overview', label: 'Overview', icon: <LayoutDashboard size={18} /> },
    { id: 'workspace', label: 'Document Workspace', icon: <FileText size={18} /> },
    { id: 'runs', label: 'Processing Runs', icon: <PlaySquare size={18} /> },
    {
      id: 'findings',
      label: 'PII Findings',
      icon: <ShieldAlert size={18} />,
      badge: openFindingsCount > 0 ? (
        <span className="badge badge-gov" style={{ marginLeft: 'auto', fontSize: '0.7rem', padding: '2px 6px' }}>
          {openFindingsCount}
        </span>
      ) : null,
    },
    { id: 'redaction', label: 'Redaction Review', icon: <EyeOff size={18} /> },
    {
      id: 'verification',
      label: 'Verification',
      icon: <CheckCircle2 size={18} />,
      badge: blockedCount > 0 ? (
        <span className="badge badge-warning" style={{ marginLeft: 'auto', fontSize: '0.7rem', padding: '2px 6px' }}>
          {blockedCount} Blocked
        </span>
      ) : null,
    },
    { id: 'audit', label: 'Audit Logs', icon: <ScrollText size={18} /> },
    { id: 'reports', label: 'Reports & Downloads', icon: <Download size={18} /> },
    { id: 'settings', label: 'Settings', icon: <Settings size={18} /> },
  ];

  return (
    <aside className="optiv-sidebar">
      {/* Navigation Group */}
      <div style={{ flex: 1 }}>
        <div style={{ fontSize: '0.7rem', fontWeight: 700, textTransform: 'uppercase', color: 'var(--tprm-text-muted)', padding: '0 12px 10px', letterSpacing: '0.05em' }}>
          Navigation
        </div>

        {navItems.map((item) => (
          <button
            key={item.id}
            onClick={() => onSelectTab(item.id)}
            className={`optiv-nav-item ${currentTab === item.id ? 'active' : ''}`}
          >
            {item.icon}
            <span>{item.label}</span>
            {item.badge}
          </button>
        ))}
      </div>

      {/* AI Assistant Quick Trigger Card */}
      <div
        className="optiv-card"
        style={{
          marginTop: 'auto',
          padding: 14,
          background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(14, 165, 233, 0.1) 100%)',
          borderColor: 'rgba(99, 102, 241, 0.25)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
          <HelpCircle size={16} color="var(--tprm-indigo)" />
          <span style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--tprm-text-primary)' }}>
            AI Privacy Copilot
          </span>
        </div>
        <p style={{ fontSize: '0.725rem', color: 'var(--tprm-text-muted)', marginBottom: 10, lineHeight: 1.4 }}>
          Grounded explanations of release barriers, PII classification, and residual re-scans.
        </p>
        <button
          onClick={onOpenAssistant}
          className="btn-primary"
          style={{ width: '100%', fontSize: '0.75rem', padding: '6px 12px', justifyContent: 'center' }}
        >
          Ask Copilot
        </button>
      </div>
    </aside>
  );
};
