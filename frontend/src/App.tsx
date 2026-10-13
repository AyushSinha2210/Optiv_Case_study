import React, { useState, useEffect } from 'react';
import './tprm.css';
import { Header } from './components/tprm/Header';
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
  full_name: 'Daniela Figueroa',
  is_active: true,
  is_admin: true,
  groups: ['Vendor Risk Management', 'Legal', 'Finance'],
  group_roles: { 'Vendor Risk Management': 'Lead Reviewer / Administrator' },
};

export const App: React.FC = () => {
  const [currentUser, setCurrentUser] = useState<UserProfile>(DEFAULT_USER);
  const [currentTab, setCurrentTab] = useState<NavigationTab | 'pii_guard'>('dashboard');
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [activeAssessmentId, setActiveAssessmentId] = useState<string | null>(null);

  // Metrics for badges
  const [pendingApprovalsCount, setPendingApprovalsCount] = useState<number>(2);
  const [pendingTasksCount, setPendingTasksCount] = useState<number>(4);
  const [openRisksCount, setOpenRisksCount] = useState<number>(3);

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

  // Load notifications and metrics from backend
  const refreshMetrics = async () => {
    try {
      const summaryRes = await fetch('/api/tprm/v1/reports/summary');
      if (summaryRes.ok) {
        const summary = await summaryRes.json();
        setOpenRisksCount(summary.risk_findings?.high || 0);
        setPendingTasksCount(summary.sla_and_tasks?.pending_tasks || 0);
      }

      const tasksRes = await fetch('/api/tprm/v1/tasks');
      if (tasksRes.ok) {
        const tasksData = await tasksRes.json();
        const approvals = (tasksData.items || []).filter(
          (t: any) => t.task_type.includes('Approval') && t.status !== 'Completed'
        ).length;
        setPendingApprovalsCount(approvals);
      }
    } catch (err) {
      console.warn('Initial TPRM metrics fetch fallback', err);
    }
  };

  useEffect(() => {
    refreshMetrics();

    // Fetch initial notifications
    setNotifications([
      {
        id: 'notif_1',
        subject: 'SLA Warning: Apex Cloud Assessment Review',
        body: 'Apex Cloud Systems due diligence review is due in 24 hours under Table 13 SLA.',
        is_read: false,
        created_at: new Date(Date.now() - 3600000).toISOString(),
      },
      {
        id: 'notif_2',
        subject: 'Table 14 High Risk Triggered: QRC_001',
        body: 'Staffing Plus Inc flagged for unencrypted data in transit. Security mitigation required.',
        is_read: false,
        created_at: new Date(Date.now() - 7200000).toISOString(),
      },
    ]);

    // Fetch scenarios for legacy tab
    fetch('/api/scenarios')
      .then((res) => res.json())
      .then((data) => setScenarios(data.scenarios || []))
      .catch(() => {});
  }, []);

  const handleSwitchUser = async (email: string) => {
    try {
      const res = await fetch(`/api/tprm/v1/auth/me?email=${encodeURIComponent(email)}`);
      if (res.ok) {
        const user = await res.json();
        setCurrentUser(user);
      } else {
        // Fallback demo switch
        setCurrentUser({
          id: `usr_${email.split('@')[0]}`,
          email,
          full_name: email.split('@')[0].replace('.', ' ').toUpperCase(),
          is_active: true,
          is_admin: email.includes('daniela') || email.includes('bridgett'),
          groups: [email.includes('sec') ? 'Security' : email.includes('leg') ? 'Legal' : 'Vendor Risk Management'],
          group_roles: {},
        });
      }
    } catch (err) {
      console.error('Error switching user', err);
    }
  };

  const handleMarkNotificationRead = (id: string) => {
    setNotifications((prev) =>
      prev.map((n) => (n.id === id ? { ...n, is_read: true } : n))
    );
  };

  // Legacy pipeline execution
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

  return (
    <div className="enterprise-shell">
      {/* Enterprise Header */}
      <Header
        currentUser={currentUser}
        onSwitchUser={handleSwitchUser}
        notifications={notifications}
        onMarkNotificationRead={handleMarkNotificationRead}
        onSearch={(q) => {
          if (q) setCurrentTab('directory');
        }}
      />

      <div className="enterprise-body">
        {/* Hierarchical Sidebar */}
        <Sidebar
          currentTab={currentTab as NavigationTab}
          onSelectTab={(tab) => setCurrentTab(tab)}
          pendingApprovalsCount={pendingApprovalsCount}
          pendingTasksCount={pendingTasksCount}
          openRisksCount={openRisksCount}
        />

        {/* Main Content Viewport */}
        <main className="enterprise-main">
          {/* Breadcrumbs */}
          <div className="tprm-breadcrumbs">
            <span className="text-slate-400">Cadence TPRM</span>
            <span>/</span>
            <span className="capitalize">{currentTab.replace('_', ' ')}</span>
          </div>

          {/* Tab Route Rendering */}
          {currentTab === 'dashboard' && (
            <DashboardView
              onNavigate={(tab) => {
                if (tab === 'vendors') setCurrentTab('directory');
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
              onInitiateAssessment={(assessmentId) => {
                setActiveAssessmentId(assessmentId);
                setCurrentTab('questionnaire');
              }}
            />
          )}

          {currentTab === 'onboarding' && (
            <OnboardingWizardView
              currentUser={currentUser}
              onComplete={() => {
                refreshMetrics();
                setCurrentTab('directory');
              }}
            />
          )}

          {(currentTab === 'questionnaire' || currentTab === 'assessments') && (
            <QuestionnaireRunnerView
              currentUser={currentUser}
              initialAssessmentId={activeAssessmentId}
              onNavigateToVendor={() => setCurrentTab('directory')}
            />
          )}

          {currentTab === 'findings' && <RiskFindingsView />}

          {(currentTab === 'tasks' || currentTab === 'approvals') && (
            <TasksApprovalsView
              currentUser={currentUser}
              onNavigateToVendor={() => setCurrentTab('directory')}
              onNavigateToQuestionnaire={(id) => {
                setActiveAssessmentId(id);
                setCurrentTab('questionnaire');
              }}
            />
          )}

          {currentTab === 'reassessments' && <ReassessmentsView />}

          {currentTab === 'offboarding' && (
            <VendorDirectoryView currentUser={currentUser} />
          )}

          {currentTab === 'workflows' && <WorkflowsView />}

          {currentTab === 'organization' && (
            <OrganizationAdminView
              currentUser={currentUser}
              onSelectUser={(u) => setCurrentUser(u)}
            />
          )}

          {currentTab === 'reports' && (
            <DashboardView
              onNavigate={(tab) => {
                if (tab === 'vendors') setCurrentTab('directory');
                else setCurrentTab('findings');
              }}
            />
          )}

          {currentTab === 'audit' && <AuditLedgerView />}

          {/* Legacy PII Guard Verification Panel */}
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
                  className="px-3 py-1 text-xs font-semibold text-slate-700 bg-slate-100 hover:bg-slate-200 rounded border border-slate-300"
                >
                  Return to TPRM Console
                </button>
              </div>

              {/* Legacy Execution Bar */}
              <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm space-y-4">
                <div className="flex flex-wrap items-center gap-4">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold text-slate-600">SOURCE:</span>
                    <button
                      onClick={() => setInputMode('scenario')}
                      className={`px-3 py-1 text-xs font-semibold rounded ${
                        inputMode === 'scenario'
                          ? 'bg-indigo-600 text-white'
                          : 'bg-slate-100 text-slate-700'
                      }`}
                    >
                      Demo Fixture
                    </button>
                    <button
                      onClick={() => setInputMode('upload')}
                      className={`px-3 py-1 text-xs font-semibold rounded ${
                        inputMode === 'upload'
                          ? 'bg-indigo-600 text-white'
                          : 'bg-slate-100 text-slate-700'
                      }`}
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
                      className="rounded text-rose-600"
                    />
                    <span>Simulate Fail-Closed Block</span>
                  </label>

                  <button
                    onClick={handleExecuteLegacyPipeline}
                    disabled={legacyProcessing}
                    className="ml-auto inline-flex items-center gap-1.5 px-4 py-1.5 text-xs font-bold text-white bg-indigo-600 hover:bg-indigo-700 rounded shadow-xs disabled:opacity-50"
                  >
                    <Play className="w-3.5 h-3.5 fill-current" />
                    {legacyProcessing ? 'Processing Pipeline...' : 'Run PII Guard'}
                  </button>
                </div>

                {legacyError && (
                  <div className="p-3 text-xs bg-rose-50 border border-rose-200 text-rose-800 rounded">
                    {legacyError}
                  </div>
                )}
              </div>

              {/* Legacy Tabs */}
              {legacyResult && (
                <div className="space-y-4">
                  <div className="flex gap-2 border-b border-slate-200 pb-2">
                    <button
                      onClick={() => setLegacyTab('stages')}
                      className={`px-3 py-1 text-xs font-bold rounded ${
                        legacyTab === 'stages'
                          ? 'bg-indigo-600 text-white'
                          : 'text-slate-600 hover:bg-slate-100'
                      }`}
                    >
                      Pipeline Stages
                    </button>
                    <button
                      onClick={() => setLegacyTab('comparison')}
                      className={`px-3 py-1 text-xs font-bold rounded ${
                        legacyTab === 'comparison'
                          ? 'bg-indigo-600 text-white'
                          : 'text-slate-600 hover:bg-slate-100'
                      }`}
                    >
                      Document Diff & Redactions
                    </button>
                    <button
                      onClick={() => setLegacyTab('assistant')}
                      className={`px-3 py-1 text-xs font-bold rounded ${
                        legacyTab === 'assistant'
                          ? 'bg-indigo-600 text-white'
                          : 'text-slate-600 hover:bg-slate-100'
                      }`}
                    >
                      Downstream Security Guard
                    </button>
                    <button
                      onClick={() => setLegacyTab('audit')}
                      className={`px-3 py-1 text-xs font-bold rounded ${
                        legacyTab === 'audit'
                          ? 'bg-indigo-600 text-white'
                          : 'text-slate-600 hover:bg-slate-100'
                      }`}
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
