import React, { useState, useEffect } from 'react';
import './tprm.css';
import './workspace.css';

// OPTIV Document Privacy & Audit Workspace Components
import { Navbar } from './components/optiv/Navbar';
import { Sidebar } from './components/optiv/Sidebar';
import type { OptivTab } from './components/optiv/Sidebar';
import { OverviewView } from './components/optiv/OverviewView';
import { DocumentWorkspaceView } from './components/optiv/DocumentWorkspaceView';
import { ProcessingRunsView } from './components/optiv/ProcessingRunsView';
import { PIIFindingsView } from './components/optiv/PIIFindingsView';
import { RedactionReviewView } from './components/optiv/RedactionReviewView';
import { VerificationView } from './components/optiv/VerificationView';
import { AuditLogsView } from './components/optiv/AuditLogsView';
import { ReportsDownloadsView } from './components/optiv/ReportsDownloadsView';
import { SettingsView } from './components/optiv/SettingsView';
import { AIAssistantDrawer } from './components/optiv/AIAssistantDrawer';

// TPRM Platform Components (preserves full TPRM functionality)
import { Header as TPRMHeader, LoginView } from './components/tprm/Header';
import { Sidebar as TPRMSidebar } from './components/tprm/Sidebar';
import type { NavigationTab as TPRMNavigationTab } from './components/tprm/Sidebar';
import { DashboardView as TPRMDashboardView } from './components/tprm/DashboardView';
import { VendorDirectoryView } from './components/tprm/VendorDirectoryView';
import { OnboardingWizardView } from './components/tprm/OnboardingWizardView';
import { QuestionnaireRunnerView } from './components/tprm/QuestionnaireRunnerView';
import { RiskFindingsView } from './components/tprm/RiskFindingsView';
import { TasksApprovalsView } from './components/tprm/TasksApprovalsView';
import { ReassessmentsView } from './components/tprm/ReassessmentsView';
import { WorkflowsView } from './components/tprm/WorkflowsView';
import { OrganizationAdminView } from './components/tprm/OrganizationAdminView';
import { AuditLedgerView as TPRMAuditLedgerView } from './components/tprm/AuditLedgerView';

import type { UserProfile, ScenarioFixture, NotificationItem } from './types';

const PERSONAS: Record<string, UserProfile> = {
  'admin@cadence.com': {
    id: 'usr_lead_auditor',
    email: 'admin@cadence.com',
    full_name: 'Daniela Figueroa',
    title: 'Lead Compliance Auditor & Privacy Officer',
    is_active: true,
    is_admin: true,
    groups: ['Vendor Risk Management Group', 'Legal Group', 'Compliance Officer'],
    group_roles: { 'Compliance Officer': 'Admin', 'Vendor Risk Management Group': 'Admin' },
    permissions: ['read', 'write', 'redact', 'release', 'audit', 'admin'],
  },
  'analyst@cadence.com': {
    id: 'usr_privacy_analyst',
    email: 'analyst@cadence.com',
    full_name: 'Marcus Vance',
    title: 'Senior Privacy & PII Analyst',
    is_active: true,
    is_admin: false,
    groups: ['Data Quality Group', 'Privacy Analysts'],
    group_roles: { 'Privacy Analysts': 'Edit' },
    permissions: ['read', 'write', 'redact', 'audit'],
  },
  'auditor@cadence.com': {
    id: 'usr_ext_auditor',
    email: 'auditor@cadence.com',
    full_name: 'Sarah Chen',
    title: 'Independent Control Auditor',
    is_active: true,
    is_admin: false,
    groups: ['Independent Audit Group'],
    group_roles: { 'Independent Audit Group': 'Reviewer' },
    permissions: ['read', 'audit'],
  },
};

export const App: React.FC = () => {
  // Theme state with localStorage persistence
  const [theme, setTheme] = useState<'light' | 'dark'>(() => {
    return (localStorage.getItem('optiv_theme') as 'light' | 'dark') || 'light';
  });

  // Active platform toggle: OPTIV Document Privacy Workspace (Default) vs TPRM Platform
  const [activePlatform, setActivePlatform] = useState<'pii_workspace' | 'tprm'>('pii_workspace');

  // OPTIV Workspace Tab
  const [optivTab, setOptivTab] = useState<OptivTab>('overview');

  // TPRM Platform Tab
  const [tprmTab, setTprmTab] = useState<TPRMNavigationTab>('dashboard');

  // Authenticated user persona
  const [currentUser, setCurrentUser] = useState<UserProfile>(PERSONAS['admin@cadence.com']);
  const [showLoginModal, setShowLoginModal] = useState<boolean>(false);

  // Scenarios & Metrics
  const [scenarios, setScenarios] = useState<ScenarioFixture[]>([]);
  const [openFindingsCount, setOpenFindingsCount] = useState<number>(0);
  const [blockedCount, setBlockedCount] = useState<number>(0);
  const [selectedWorkspaceDocId, setSelectedWorkspaceDocId] = useState<string | null>(null);

  // AI Assistant Drawer state
  const [assistantOpen, setAssistantOpen] = useState<boolean>(false);
  const [assistantDocId, setAssistantDocId] = useState<string>('');

  // TPRM live notifications
  const [notifications] = useState<NotificationItem[]>([]);
  const [activeAssessmentId, setActiveAssessmentId] = useState<string | null>(null);

  // Toggle and persist theme
  const handleToggleTheme = () => {
    const next = theme === 'light' ? 'dark' : 'light';
    setTheme(next);
    localStorage.setItem('optiv_theme', next);
  };

  // Switch persona
  const handleSwitchPersona = (email: string) => {
    const p = PERSONAS[email] || {
      id: `usr_${email}`,
      email,
      full_name: email.split('@')[0],
      is_active: true,
      is_admin: email.includes('admin'),
      groups: ['Default User Group'],
      group_roles: { 'Default User Group': 'Edit' },
    };
    setCurrentUser(p);
  };

  // Fetch scenarios and metrics
  useEffect(() => {
    fetch('/api/scenarios')
      .then((res) => res.json())
      .then((data) => setScenarios(data.scenarios || []))
      .catch(() => {});

    fetch('/api/overview/metrics', {
      headers: { 'X-User-Email': currentUser.email },
    })
      .then((res) => res.json())
      .then((data) => {
        setOpenFindingsCount(data.findings_detected || 0);
        setBlockedCount(data.documents_blocked_from_release || 0);
      })
      .catch(() => {});
  }, [currentUser.email]);

  const handleOpenAssistant = (docId?: string) => {
    setAssistantDocId(docId || selectedWorkspaceDocId || '03_mixed_pii.txt');
    setAssistantOpen(true);
  };

  const handleNavigateWorkspaceWithDoc = (docId?: string) => {
    if (docId) setSelectedWorkspaceDocId(docId);
    setOptivTab('workspace');
  };

  if (showLoginModal) {
    return (
      <LoginView
        theme={theme}
        onToggleTheme={handleToggleTheme}
        onLoginSuccess={(user) => {
          setCurrentUser(user);
          setShowLoginModal(false);
        }}
      />
    );
  }

  return (
    <div className={`enterprise-shell ${theme === 'dark' ? 'theme-dark' : 'theme-light'}`}>
      {/* Platform Header */}
      {activePlatform === 'pii_workspace' ? (
        <Navbar
          currentUser={currentUser}
          theme={theme}
          onToggleTheme={handleToggleTheme}
          onSwitchPersona={handleSwitchPersona}
          onLogout={() => setShowLoginModal(true)}
          currentView={optivTab}
          onTogglePlatform={() => setActivePlatform('tprm')}
          activePlatform={activePlatform}
        />
      ) : (
        <TPRMHeader
          currentUser={currentUser}
          onSwitchUser={(email) => handleSwitchPersona(email)}
          notifications={notifications}
          onMarkNotificationRead={() => {}}
          theme={theme}
          onToggleTheme={handleToggleTheme}
          onLogout={() => setShowLoginModal(true)}
          onSearch={() => {}}
        />
      )}

      {/* Main Workspace Body */}
      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        {/* Sidebar */}
        {activePlatform === 'pii_workspace' ? (
          <Sidebar
            currentTab={optivTab}
            onSelectTab={(tab) => setOptivTab(tab)}
            openFindingsCount={openFindingsCount}
            blockedCount={blockedCount}
            onOpenAssistant={() => handleOpenAssistant()}
          />
        ) : (
          <TPRMSidebar
            currentTab={tprmTab}
            onSelectTab={(tab) => setTprmTab(tab)}
            pendingApprovalsCount={0}
            pendingTasksCount={0}
            openRisksCount={0}
          />
        )}

        {/* Content Pane */}
        <main className="optiv-main">
          {activePlatform === 'pii_workspace' ? (
            <>
              {optivTab === 'overview' && (
                <OverviewView
                  currentUser={currentUser}
                  onNavigateToWorkspace={handleNavigateWorkspaceWithDoc}
                  onNavigateToTab={(tab) => setOptivTab(tab)}
                />
              )}

              {optivTab === 'workspace' && (
                <DocumentWorkspaceView
                  currentUser={currentUser}
                  initialDocumentId={selectedWorkspaceDocId}
                  onOpenAssistant={(docId) => handleOpenAssistant(docId)}
                  scenarios={scenarios}
                />
              )}

              {optivTab === 'runs' && (
                <ProcessingRunsView
                  currentUser={currentUser}
                  onInspectRun={(docId) => handleNavigateWorkspaceWithDoc(docId)}
                />
              )}

              {optivTab === 'findings' && (
                <PIIFindingsView
                  currentUser={currentUser}
                  onNavigateToWorkspace={(docId) => handleNavigateWorkspaceWithDoc(docId)}
                />
              )}

              {optivTab === 'redaction' && (
                <RedactionReviewView
                  currentUser={currentUser}
                  onNavigateToWorkspace={() => setOptivTab('workspace')}
                />
              )}

              {optivTab === 'verification' && (
                <VerificationView
                  currentUser={currentUser}
                  onNavigateToWorkspace={() => setOptivTab('workspace')}
                />
              )}

              {optivTab === 'audit' && <AuditLogsView currentUser={currentUser} />}

              {optivTab === 'reports' && <ReportsDownloadsView currentUser={currentUser} />}

              {optivTab === 'settings' && <SettingsView currentUser={currentUser} />}
            </>
          ) : (
            /* TPRM Views */
            <>
              {tprmTab === 'dashboard' && <TPRMDashboardView onNavigate={(tab) => setTprmTab(tab as any)} />}
              {tprmTab === 'directory' && <VendorDirectoryView currentUser={currentUser} onInitiateAssessment={(id) => { setActiveAssessmentId(id); setTprmTab('questionnaire'); }} onRefreshData={() => {}} />}
              {tprmTab === 'onboarding' && <OnboardingWizardView currentUser={currentUser} onComplete={() => setTprmTab('directory')} />}
              {tprmTab === 'questionnaire' && <QuestionnaireRunnerView currentUser={currentUser} initialAssessmentId={activeAssessmentId} onNavigateToVendor={() => setTprmTab('directory')} onRefreshMetrics={() => {}} />}
              {tprmTab === 'findings' && <RiskFindingsView currentUser={currentUser} onRefreshMetrics={() => {}} />}
              {tprmTab === 'tasks' && <TasksApprovalsView currentUser={currentUser} initialMode="my" onNavigateToVendor={() => setTprmTab('directory')} onNavigateToQuestionnaire={(id) => { setActiveAssessmentId(id); setTprmTab('questionnaire'); }} onRefreshMetrics={() => {}} />}
              {tprmTab === 'reassessments' && <ReassessmentsView currentUser={currentUser} onRefreshMetrics={() => {}} />}
              {tprmTab === 'workflows' && <WorkflowsView currentUser={currentUser} />}
              {tprmTab === 'organization' && <OrganizationAdminView currentUser={currentUser} onSelectUser={(u) => setCurrentUser(u)} />}
              {tprmTab === 'reports' && <TPRMDashboardView showExportPanel={true} onNavigate={(tab) => setTprmTab(tab as any)} />}
              {tprmTab === 'audit' && <TPRMAuditLedgerView />}
            </>
          )}
        </main>
      </div>

      {/* Grounded AI Assistant Drawer */}
      <AIAssistantDrawer
        isOpen={assistantOpen}
        onClose={() => setAssistantOpen(false)}
        documentId={assistantDocId}
      />
    </div>
  );
};

export default App;

