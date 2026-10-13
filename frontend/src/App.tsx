import React, { useState, useEffect } from 'react';
import './tprm.css';
import { Header, LoginView } from './components/tprm/Header';
import { Sidebar } from './components/tprm/Sidebar';
import type { NavigationTab } from './components/tprm/Sidebar';
import { DashboardView } from './components/tprm/DashboardView';
import { VendorDirectoryView } from './components/tprm/VendorDirectoryView';
import { OnboardingWizardView } from './components/tprm/OnboardingWizardView';
import { QuestionnaireRunnerView } from './components/tprm/QuestionnaireRunnerView';
import { RiskFindingsView } from './components/tprm/RiskFindingsView';
import { TasksApprovalsView } from './components/tprm/TasksApprovalsView';
import { ReassessmentsView } from './components/tprm/ReassessmentsView';
import { WorkflowsView } from './components/tprm/WorkflowsView';
import { OrganizationAdminView } from './components/tprm/OrganizationAdminView';
import { AuditLedgerView } from './components/tprm/AuditLedgerView';

// Legacy components for Case Study PII Guard testing
import { PipelineStages } from './components/PipelineStages';
import { DocumentComparison } from './components/DocumentComparison';
import { AIAssistant } from './components/AIAssistant';
import { AuditLedger } from './components/AuditLedger';
import type { ProcessResponse, ScenarioFixture, UserProfile, NotificationItem } from './types';
import { Play } from 'lucide-react';

const DEFAULT_USER: UserProfile = {
  id: 'usr_vrm_01',
  email: 'daniela.figueroa@cadence.com',
  full_name: 'Daniela Figueroa (Synthetic Demo)',
  title: 'VRM Executive Lead',
  is_active: true,
  is_admin: true,
  groups: ['Vendor Risk Management Group', 'Legal Group', 'Finance Group', 'Data Quality Group'],
  group_roles: {
    'Vendor Risk Management Group': 'Admin',
    'Legal Group': 'Edit',
    'Finance Group': 'Edit',
    'Data Quality Group': 'Edit',
  },
};

export const App: React.FC = () => {
  const [currentUser, setCurrentUser] = useState<UserProfile>(DEFAULT_USER);
  const [showLoginPortal, setShowLoginPortal] = useState<boolean>(false);
  const [theme, setTheme] = useState<'light' | 'dark'>('light');
  const [currentTab, setCurrentTab] = useState<NavigationTab | 'pii_guard'>('dashboard');
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [activeAssessmentId, setActiveAssessmentId] = useState<string | null>(null);
  const [globalSearchQuery, setGlobalSearchQuery] = useState<string>('');

  // Live Metrics for Sidebar badges
  const [pendingApprovalsCount, setPendingApprovalsCount] = useState<number>(0);
  const [pendingTasksCount, setPendingTasksCount] = useState<number>(0);
  const [openRisksCount, setOpenRisksCount] = useState<number>(0);

  // Legacy pipeline state
  const [scenarios, setScenarios] = useState<ScenarioFixture[]>([]);
  const [selectedScenario, setSelectedScenario] = useState<string>('03_mixed_pii.txt');
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [inputMode, setInputMode] = useState<'scenario' | 'upload'>('scenario');
  const [simulateFailure, setSimulateFailure] = useState<boolean>(false);
  const [legacyTab, setLegacyTab] = useState<'stages' | 'comparison' | 'assistant' | 'audit'>('stages');
  const [legacyProcessing, setLegacyProcessing] = useState<boolean>(false);
  const [legacyResult, setLegacyResult] = useState<ProcessResponse | null>(null);
  const [legacyError, setLegacyError] = useState<string | null>(null);

  const refreshMetrics = async (userEmail: string = currentUser.email) => {
    try {
      const headers = { 'X-User-Email': userEmail };
      const [summaryRes, tasksRes, notifRes] = await Promise.all([
        fetch('/api/tprm/v1/reports/summary', { headers }),
        fetch('/api/tprm/v1/tasks', { headers }),
        fetch('/api/tprm/v1/tasks/notifications', { headers }),
      ]);

      if (summaryRes.ok) {
        const summary = await summaryRes.json();
        setOpenRisksCount(summary.risk_findings?.open || 0);
        setPendingTasksCount(summary.sla_and_tasks?.pending_tasks || 0);
      }

      if (tasksRes.ok) {
        const tasksData = await tasksRes.json();
        const taskList = tasksData.items || tasksData.tasks || [];
        const approvals = taskList.filter(
          (t: any) => (t.task_type.includes('Approval') || t.title.includes('Assessment Submitted')) && t.status !== 'Completed'
        ).length;
        setPendingApprovalsCount(approvals);
      }

      if (notifRes.ok) {
        const notifData = await notifRes.json();
        setNotifications(notifData.items || notifData.notifications || []);
      }
    } catch (err) {
      console.warn('TPRM metrics fetch error', err);
    }
  };

  useEffect(() => {
    refreshMetrics(currentUser.email);

    fetch('/api/scenarios')
      .then((res) => res.json())
      .then((data) => setScenarios(data.scenarios || []))
      .catch(() => {});
  }, [currentUser.email]);

  const handleSwitchUser = async (email: string) => {
    try {
      const res = await fetch(`/api/tprm/v1/auth/me?email=${encodeURIComponent(email)}`, {
        headers: { 'X-User-Email': email },
      });
      if (res.ok) {
        const data = await res.json();
        const resolvedUser = data.user || data;
        setCurrentUser(resolvedUser);
        await refreshMetrics(resolvedUser.email);
      }
    } catch (err) {
      console.error('Error switching user', err);
    }
  };

  const handleMarkNotificationRead = async (id: string) => {
    setNotifications((prev) =>
      prev.map((n) => (n.id === id ? { ...n, is_read: true } : n))
    );
    try {
      await fetch(`/api/tprm/v1/tasks/notifications/${id}/read`, {
        method: 'POST',
        headers: { 'X-User-Email': currentUser.email },
      });
    } catch (e) {
      // ignore
    }
  };

  const handleExecuteLegacyPipeline = async () => {
    setLegacyError(null);
    setLegacyProcessing(true);
    try {
      const formData = new FormData();
      formData.append('simulate_verification_failure', simulateFailure.toString());
      if (inputMode === 'scenario') {
        formData.append('scenario_filename', selectedScenario);
      } else {
        if (!uploadedFile) {
          setLegacyError('Please select a file to upload.');
          setLegacyProcessing(false);
          return;
        }
        formData.append('file', uploadedFile);
      }

      const res = await fetch('/api/process', {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({ detail: 'Pipeline execution failed' }));
        throw new Error(errData.detail || 'Execution failed');
      }

      const data: ProcessResponse = await res.json();
      setLegacyResult(data);
    } catch (err: any) {
      setLegacyError(err.message || 'Error executing PII Guard pipeline');
    } finally {
      setLegacyProcessing(false);
    }
  };

  if (showLoginPortal) {
    return (
      <LoginView
        theme={theme}
        onToggleTheme={() => setTheme((t) => (t === 'light' ? 'dark' : 'light'))}
        onLoginSuccess={(user) => {
          setCurrentUser(user);
          setShowLoginPortal(false);
          refreshMetrics(user.email);
        }}
      />
    );
  }

  return (
    <div className={`enterprise-shell ${theme === 'dark' ? 'theme-dark' : 'theme-light'}`}>
      <Header
        currentUser={currentUser}
        onSwitchUser={handleSwitchUser}
        notifications={notifications}
        onMarkNotificationRead={handleMarkNotificationRead}
        theme={theme}
        onToggleTheme={() => setTheme((t) => (t === 'light' ? 'dark' : 'light'))}
        onLogout={() => setShowLoginPortal(true)}
        onSearch={(q) => {
          setGlobalSearchQuery(q);
          if (q && currentTab !== 'directory' && currentTab !== 'findings') {
            setCurrentTab('directory');
          }
        }}
      />

      <div className="enterprise-body">
        <Sidebar
          currentTab={currentTab as NavigationTab}
          onSelectTab={(tab) => setCurrentTab(tab)}
          pendingApprovalsCount={pendingApprovalsCount}
          pendingTasksCount={pendingTasksCount}
          openRisksCount={openRisksCount}
        />

        <main className="enterprise-main">
          <div className="tprm-breadcrumbs">
            <div className="flex items-center gap-2">
              <span className="text-slate-400">Cadence Design Systems</span>
              <span>/</span>
              <span className="text-slate-400">OneTrust TPRM</span>
              <span>/</span>
              <span className="capitalize font-bold text-slate-900">{currentTab.replace('_', ' ')}</span>
            </div>
            <div className="flex items-center gap-2 text-xs">
              <span className="text-slate-500">Active Role:</span>
              <span className="badge badge-info">
                {currentUser.is_admin ? 'TPRM Administrator (Full Admin)' : `${currentUser.groups[0] || 'Reviewer'} (Edit)`}
              </span>
              <button
                type="button"
                onClick={() => setShowLoginPortal(true)}
                className="btn-link text-xs"
              >
                Switch Group / IAM Login
              </button>
            </div>
          </div>

          {currentTab === 'dashboard' && (
            <DashboardView
              onNavigate={(tab) => {
                if (tab === 'vendors' || tab === 'directory') setCurrentTab('directory');
                else if (tab === 'onboarding') setCurrentTab('onboarding');
                else if (tab === 'assessments') setCurrentTab('questionnaire');
                else if (tab === 'tasks') setCurrentTab('tasks');
                else if (tab === 'findings') setCurrentTab('findings');
              }}
            />
          )}

          {currentTab === 'directory' && (
            <VendorDirectoryView
              currentUser={currentUser}
              initialSearch={globalSearchQuery}
              onInitiateAssessment={(assessmentId) => {
                setActiveAssessmentId(assessmentId);
                setCurrentTab('questionnaire');
              }}
              onRefreshData={() => refreshMetrics(currentUser.email)}
            />
          )}

          {currentTab === 'onboarding' && (
            <OnboardingWizardView
              currentUser={currentUser}
              onComplete={() => {
                refreshMetrics(currentUser.email);
                setCurrentTab('directory');
              }}
            />
          )}

          {(currentTab === 'questionnaire' || currentTab === 'assessments') && (
            <QuestionnaireRunnerView
              currentUser={currentUser}
              initialAssessmentId={activeAssessmentId}
              onNavigateToVendor={() => setCurrentTab('directory')}
              onRefreshMetrics={() => refreshMetrics(currentUser.email)}
            />
          )}

          {currentTab === 'findings' && (
            <RiskFindingsView
              currentUser={currentUser}
              onRefreshMetrics={() => refreshMetrics(currentUser.email)}
            />
          )}

          {(currentTab === 'tasks' || currentTab === 'approvals') && (
            <TasksApprovalsView
              currentUser={currentUser}
              initialMode={currentTab === 'approvals' ? 'approvals' : 'my'}
              onNavigateToVendor={() => setCurrentTab('directory')}
              onNavigateToQuestionnaire={(id) => {
                setActiveAssessmentId(id);
                setCurrentTab('questionnaire');
              }}
              onRefreshMetrics={() => refreshMetrics(currentUser.email)}
            />
          )}

          {currentTab === 'reassessments' && (
            <ReassessmentsView
              currentUser={currentUser}
              onRefreshMetrics={() => refreshMetrics(currentUser.email)}
            />
          )}

          {currentTab === 'offboarding' && (
            <VendorDirectoryView
              currentUser={currentUser}
              initialStatusFilter="Offboarding"
              onInitiateAssessment={(assessmentId) => {
                setActiveAssessmentId(assessmentId);
                setCurrentTab('questionnaire');
              }}
              onRefreshData={() => refreshMetrics(currentUser.email)}
            />
          )}

          {currentTab === 'workflows' && <WorkflowsView currentUser={currentUser} />}

          {currentTab === 'organization' && (
            <OrganizationAdminView
              currentUser={currentUser}
              onSelectUser={(u) => {
                setCurrentUser(u);
                refreshMetrics(u.email);
              }}
            />
          )}

          {currentTab === 'reports' && (
            <DashboardView
              showExportPanel={true}
              onNavigate={(tab) => {
                if (tab === 'vendors' || tab === 'directory') setCurrentTab('directory');
                else setCurrentTab('findings');
              }}
            />
          )}

          {currentTab === 'audit' && <AuditLedgerView />}

          {currentTab === 'pii_guard' && (
            <div className="space-y-6">
              <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm flex items-center justify-between">
                <div>
                  <h2 className="text-lg font-bold text-slate-900">
                    Zero-Leakage PII Guard Pipeline Verification
                  </h2>
                  <p className="text-xs text-slate-500 mt-1">
                    Independent verification gate for unstructured onboarding attachments & documents.
                  </p>
                </div>
                <button
                  onClick={() => setCurrentTab('dashboard')}
                  className="btn btn-secondary"
                >
                  Return to TPRM Console
                </button>
              </div>

              <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm space-y-4">
                <div className="flex flex-wrap items-center gap-4">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold text-slate-600">SOURCE:</span>
                    <button
                      onClick={() => setInputMode('scenario')}
                      className={`btn btn-sm ${inputMode === 'scenario' ? 'btn-primary' : 'btn-secondary'}`}
                    >
                      Demo Fixture
                    </button>
                    <button
                      onClick={() => setInputMode('upload')}
                      className={`btn btn-sm ${inputMode === 'upload' ? 'btn-primary' : 'btn-secondary'}`}
                    >
                      Custom File
                    </button>
                  </div>

                  {inputMode === 'scenario' ? (
                    <select
                      value={selectedScenario}
                      onChange={(e) => setSelectedScenario(e.target.value)}
                      className="text-xs border border-slate-300 rounded px-3 py-1.5 bg-slate-50 min-w-[260px]"
                    >
                      {scenarios.map((s) => (
                        <option key={s.filename} value={s.filename}>
                          {s.filename} — {s.name}
                        </option>
                      ))}
                    </select>
                  ) : (
                    <input
                      type="file"
                      onChange={(e) => setUploadedFile(e.target.files?.[0] || null)}
                      className="text-xs"
                    />
                  )}

                  <label className="flex items-center gap-2 text-xs font-medium text-slate-700 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={simulateFailure}
                      onChange={(e) => setSimulateFailure(e.target.checked)}
                    />
                    <span>Simulate Fail-Closed Block</span>
                  </label>

                  <button
                    onClick={handleExecuteLegacyPipeline}
                    disabled={legacyProcessing}
                    className="ml-auto btn btn-primary"
                  >
                    <Play size={14} />
                    {legacyProcessing ? 'Processing Pipeline...' : 'Run PII Guard'}
                  </button>
                </div>

                {legacyError && (
                  <div className="p-3 text-xs bg-rose-50 border border-rose-200 text-rose-800 rounded">
                    {legacyError}
                  </div>
                )}
              </div>

              {legacyResult && (
                <div className="space-y-4">
                  <div className="flex gap-2 border-b border-slate-200 pb-2">
                    <button
                      onClick={() => setLegacyTab('stages')}
                      className={`btn btn-sm ${legacyTab === 'stages' ? 'btn-primary' : 'btn-secondary'}`}
                    >
                      Pipeline Stages
                    </button>
                    <button
                      onClick={() => setLegacyTab('comparison')}
                      className={`btn btn-sm ${legacyTab === 'comparison' ? 'btn-primary' : 'btn-secondary'}`}
                    >
                      Document Diff & Redactions
                    </button>
                    <button
                      onClick={() => setLegacyTab('assistant')}
                      className={`btn btn-sm ${legacyTab === 'assistant' ? 'btn-primary' : 'btn-secondary'}`}
                    >
                      Downstream Security Guard
                    </button>
                    <button
                      onClick={() => setLegacyTab('audit')}
                      className={`btn btn-sm ${legacyTab === 'audit' ? 'btn-primary' : 'btn-secondary'}`}
                    >
                      Audit Trail
                    </button>
                  </div>

                  {legacyTab === 'stages' && (
                    <PipelineStages
                      currentStage={legacyResult.current_stage}
                      workflowStatus={legacyResult.workflow_status}
                      stageHistory={legacyResult.stage_history}
                      totalDuration={legacyResult.duration_sec}
                    />
                  )}
                  {legacyTab === 'comparison' && (
                    <DocumentComparison
                      extractedText={legacyResult.extracted_text}
                      redactedText={legacyResult.redacted_text}
                      entities={legacyResult.entities}
                      releaseAllowed={legacyResult.release_allowed}
                      verificationStatus={legacyResult.verification_status}
                    />
                  )}
                  {legacyTab === 'assistant' && (
                    <AIAssistant documentId={legacyResult.document_id} />
                  )}
                  {legacyTab === 'audit' && (
                    <AuditLedger
                      documentId={legacyResult.document_id}
                      releaseAllowed={legacyResult.release_allowed}
                      sourceType={legacyResult.source_type}
                    />
                  )}
                </div>
              )}
            </div>
          )}
        </main>
      </div>
    </div>
  );
};
export default App;
