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

import type { UserProfile, ScenarioFixture, NotificationItem, ProcessResponse } from './types';

// Default authorized security session without arbitrary switchable accounts
const DEFAULT_OPERATOR: UserProfile = {
  id: 'usr_optiv_operator',
  email: 'privacy@optiv.security',
  full_name: 'Optiv Privacy & Security Officer',
  title: 'Lead Privacy Officer & Security Engineer',
  is_active: true,
  is_admin: true,
  groups: ['Privacy Engineering Group', 'Security Compliance Group'],
  group_roles: { 'Privacy Engineering Group': 'Admin', 'Security Compliance Group': 'Admin' },
  permissions: ['read', 'write', 'redact', 'release', 'audit', 'admin'],
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

  // Single authorized session
  const [currentUser, setCurrentUser] = useState<UserProfile>(DEFAULT_OPERATOR);
  const [showLoginModal, setShowLoginModal] = useState<boolean>(false);

  // Active Document State across all views
  const [activeDocument, setActiveDocument] = useState<ProcessResponse | null>(null);
  const [selectedWorkspaceDocId, setSelectedWorkspaceDocId] = useState<string | null>(null);
  const [selectedEntityIndex, setSelectedEntityIndex] = useState<number | null>(null);

  // Scenarios & Metrics
  const [scenarios, setScenarios] = useState<ScenarioFixture[]>([]);
  const [openFindingsCount, setOpenFindingsCount] = useState<number>(0);
  const [blockedCount, setBlockedCount] = useState<number>(0);

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

  // Sync active document
  const handleDocumentChange = (doc: ProcessResponse) => {
    setActiveDocument(doc);
    setSelectedWorkspaceDocId(doc.document_id);
    if (doc.entities) {
      setOpenFindingsCount(doc.entities.length);
    }
    setBlockedCount(doc.release_allowed ? 0 : 1);
  };

  // Fetch initial scenarios and latest processing run so views behave with a live document
  useEffect(() => {
    fetch('/api/scenarios')
      .then((res) => res.json())
      .then((data) => {
        setScenarios(data.scenarios || []);
      })
      .catch(() => {});

    // Load latest run from server
    fetch('/api/runs?limit=1')
      .then((res) => res.json())
      .then((data) => {
        if (data.runs && data.runs.length > 0) {
          const latest = data.runs[0];
          setActiveDocument(latest);
          setSelectedWorkspaceDocId(latest.document_id);
          if (latest.entities) {
            setOpenFindingsCount(latest.entities.length);
          }
          setBlockedCount(latest.release_allowed ? 0 : 1);
        }
      })
      .catch(() => {});

    fetch('/api/overview/metrics')
      .then((res) => res.json())
      .then((data) => {
        setOpenFindingsCount((prev) => (prev > 0 ? prev : data.findings_detected || 0));
        setBlockedCount((prev) => (prev > 0 ? prev : data.documents_blocked_from_release || 0));
      })
      .catch(() => {});
  }, []);

  const handleOpenAssistant = (docId?: string) => {
    setAssistantDocId(docId || activeDocument?.document_id || '03_mixed_pii.txt');
    setAssistantOpen(true);
  };

  const handleNavigateWorkspaceWithDoc = (docId?: string, entityIdx?: number) => {
    if (docId) setSelectedWorkspaceDocId(docId);
    if (entityIdx !== undefined) setSelectedEntityIndex(entityIdx);
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
          theme={theme}
          onToggleTheme={handleToggleTheme}
          currentView={optivTab}
          activeDocument={activeDocument}
          onTogglePlatform={() => setActivePlatform('tprm')}
          activePlatform={activePlatform}
        />
      ) : (
        <TPRMHeader
          currentUser={currentUser}
          onSwitchUser={() => {}}
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
                  activeDocument={activeDocument}
                  onNavigateToWorkspace={handleNavigateWorkspaceWithDoc}
                  onNavigateToTab={(tab) => setOptivTab(tab)}
                />
              )}

              {optivTab === 'workspace' && (
                <DocumentWorkspaceView
                  currentUser={currentUser}
                  initialDocumentId={selectedWorkspaceDocId}
                  initialEntityIndex={selectedEntityIndex}
                  activeDocument={activeDocument}
                  onDocumentChange={handleDocumentChange}
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
                  activeDocument={activeDocument}
                  onNavigateToWorkspace={(docId, entityIdx) => handleNavigateWorkspaceWithDoc(docId, entityIdx)}
                />
              )}

              {optivTab === 'redaction' && (
                <RedactionReviewView
                  currentUser={currentUser}
                  activeDocument={activeDocument}
                  onNavigateToWorkspace={() => setOptivTab('workspace')}
                />
              )}

              {optivTab === 'verification' && (
                <VerificationView
                  currentUser={currentUser}
                  activeDocument={activeDocument}
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
