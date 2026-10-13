import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { PipelineStages } from './components/PipelineStages';
import { DocumentComparison } from './components/DocumentComparison';
import { AIAssistant } from './components/AIAssistant';
import { AuditLedger } from './components/AuditLedger';
import type { ProcessResponse, ScenarioFixture } from './types';
import {
  CheckCircle,
  XCircle,
  Play,
  Upload,
  FileCode,
  Layers,
  Eye,
  Bot,
  ScrollText,
  AlertTriangle,
} from 'lucide-react';

export const App: React.FC = () => {
  const [backendHealthy, setBackendHealthy] = useState<boolean>(false);
  const [scenarios, setScenarios] = useState<ScenarioFixture[]>([]);
  const [selectedScenario, setSelectedScenario] = useState<string>('03_mixed_pii.txt');
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [inputMode, setInputMode] = useState<'scenario' | 'upload'>('scenario');
  const [simulateFailure, setSimulateFailure] = useState<boolean>(false);

  const [activeTab, setActiveTab] = useState<'stages' | 'comparison' | 'assistant' | 'audit'>('stages');
  const [processing, setProcessing] = useState<boolean>(false);
  const [result, setResult] = useState<ProcessResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Poll backend health and fetch scenarios on mount
  useEffect(() => {
    fetch('/api/health')
      .then((res) => {
        if (res.ok) setBackendHealthy(true);
      })
      .catch(() => setBackendHealthy(false));

    fetch('/api/scenarios')
      .then((res) => res.json())
      .then((data) => {
        setScenarios(data.scenarios || []);
      })
      .catch((err) => console.error('Failed to load scenarios', err));
  }, []);

  const handleExecutePipeline = async () => {
    setError(null);
    setProcessing(true);

    try {
      const formData = new FormData();
      formData.append('simulate_verification_failure', simulateFailure.toString());

      if (inputMode === 'scenario') {
        formData.append('scenario_filename', selectedScenario);
      } else {
        if (!uploadedFile) {
          setError('Please select a file to upload.');
          setProcessing(false);
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
      setResult(data);
    } catch (err: any) {
      setError(err.message || 'Error communicating with backend pipeline.');
    } finally {
      setProcessing(false);
    }
  };

  const selectedScenarioMeta = scenarios.find((s) => s.filename === selectedScenario);

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Navbar backendHealthy={backendHealthy} />

      <main style={{ flex: 1, padding: '0 24px 32px 24px', maxWidth: '1440px', width: '100%', margin: '0 auto' }}>
        {/* Top Control Card */}
        <section className="glass-panel" style={{ padding: 24, marginBottom: 24 }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: 24 }}>
            {/* Input Selection Column */}
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
                <span style={{ fontSize: '0.85rem', fontWeight: 600, color: '#94a3b8' }}>SOURCE:</span>
                <div style={{ display: 'flex', gap: 6, background: 'rgba(15, 23, 42, 0.6)', padding: 4, borderRadius: 8 }}>
                  <button
                    onClick={() => setInputMode('scenario')}
                    className={`btn-secondary ${inputMode === 'scenario' ? 'active' : ''}`}
                    style={{
                      padding: '6px 12px',
                      fontSize: '0.8rem',
                      background: inputMode === 'scenario' ? 'rgba(6, 182, 212, 0.25)' : 'transparent',
                      borderColor: inputMode === 'scenario' ? '#06b6d4' : 'transparent',
                      color: inputMode === 'scenario' ? '#fff' : '#94a3b8',
                    }}
                  >
                    <FileCode size={14} />
                    <span>Demo Scenarios</span>
                  </button>
                  <button
                    onClick={() => setInputMode('upload')}
                    className={`btn-secondary ${inputMode === 'upload' ? 'active' : ''}`}
                    style={{
                      padding: '6px 12px',
                      fontSize: '0.8rem',
                      background: inputMode === 'upload' ? 'rgba(6, 182, 212, 0.25)' : 'transparent',
                      borderColor: inputMode === 'upload' ? '#06b6d4' : 'transparent',
                      color: inputMode === 'upload' ? '#fff' : '#94a3b8',
                    }}
                  >
                    <Upload size={14} />
                    <span>Custom Upload</span>
                  </button>
                </div>
              </div>

              {inputMode === 'scenario' ? (
                <div>
                  <label style={{ display: 'block', fontSize: '0.8rem', color: '#94a3b8', marginBottom: 8, fontWeight: 500 }}>
                    Select Certified Synthetic Scenario:
                  </label>
                  <select
                    value={selectedScenario}
                    onChange={(e) => setSelectedScenario(e.target.value)}
                    style={{
                      width: '100%',
                      background: 'rgba(15, 23, 42, 0.8)',
                      border: '1px solid var(--border-color)',
                      borderRadius: 8,
                      padding: '10px 14px',
                      color: '#f8fafc',
                      fontSize: '0.875rem',
                      outline: 'none',
                    }}
                  >
                    {scenarios.map((sc) => (
                      <option key={sc.filename} value={sc.filename}>
                        {sc.filename} — {sc.description || sc.name}
                      </option>
                    ))}
                  </select>
                  {selectedScenarioMeta && (
                    <div style={{ marginTop: 10, fontSize: '0.75rem', color: '#94a3b8', lineHeight: 1.4 }}>
                      Expected Categories: {selectedScenarioMeta.expected_categories.join(', ') || 'None (Clean)'} | Expected Entities: {selectedScenarioMeta.expected_count}
                    </div>
                  )}
                </div>
              ) : (
                <div>
                  <label style={{ display: 'block', fontSize: '0.8rem', color: '#94a3b8', marginBottom: 8, fontWeight: 500 }}>
                    Upload File (.pdf, .docx, .pptx, .txt):
                  </label>
                  <input
                    type="file"
                    accept=".pdf,.docx,.pptx,.txt"
                    onChange={(e) => setUploadedFile(e.target.files?.[0] || null)}
                    style={{
                      width: '100%',
                      background: 'rgba(15, 23, 42, 0.8)',
                      border: '1px solid var(--border-color)',
                      borderRadius: 8,
                      padding: '8px 12px',
                      color: '#cbd5e1',
                      fontSize: '0.85rem',
                    }}
                  />
                  {uploadedFile && (
                    <div style={{ marginTop: 8, fontSize: '0.75rem', color: '#38bdf8' }}>
                      Selected: <strong>{uploadedFile.name}</strong> ({(uploadedFile.size / 1024).toFixed(1)} KB)
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Security Controls & Action Column */}
            <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between', gap: 16 }}>
              <div>
                <span style={{ fontSize: '0.85rem', fontWeight: 600, color: '#94a3b8', display: 'block', marginBottom: 12 }}>
                  FAIL-CLOSED SECURITY TESTING:
                </span>
                <label
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 12,
                    cursor: 'pointer',
                    background: 'rgba(15, 23, 42, 0.6)',
                    padding: '10px 16px',
                    borderRadius: 8,
                    border: simulateFailure ? '1px solid #ef4444' : '1px solid var(--border-color)',
                  }}
                >
                  <input
                    type="checkbox"
                    checked={simulateFailure}
                    onChange={(e) => setSimulateFailure(e.target.checked)}
                    style={{ width: 18, height: 18, accentColor: '#ef4444' }}
                  />
                  <div>
                    <div style={{ fontSize: '0.85rem', fontWeight: 600, color: simulateFailure ? '#f87171' : '#f8fafc' }}>
                      Simulate Verification Residual Leakage
                    </div>
                    <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>
                      Simulates finding residual PII in verification re-scan to prove download blocking.
                    </div>
                  </div>
                </label>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', alignItems: 'center', gap: 12 }}>
                <button
                  onClick={handleExecutePipeline}
                  disabled={processing}
                  className="btn-primary"
                  style={{ width: '100%', justifyContent: 'center', padding: '12px 24px', fontSize: '0.95rem' }}
                >
                  {processing ? (
                    <>
                      <div className="animate-pulse-glow" style={{ width: 14, height: 14, borderRadius: '50%', background: '#fff' }} />
                      <span>Executing Multi-Stage Pipeline...</span>
                    </>
                  ) : (
                    <>
                      <Play size={18} fill="#ffffff" />
                      <span>Execute Protection Pipeline</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>

          {error && (
            <div style={{ marginTop: 16, background: 'rgba(239, 68, 68, 0.15)', border: '1px solid #ef4444', borderRadius: 8, padding: '12px 16px', display: 'flex', alignItems: 'center', gap: 10, color: '#f87171', fontSize: '0.875rem' }}>
              <AlertTriangle size={18} />
              <span>{error}</span>
            </div>
          )}
        </section>

        {/* Results Presentation Section */}
        {result && (
          <section style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
            {/* Prominent Release Gate Status Banner */}
            <div
              className={`glass-panel ${result.workflow_status === 'success' && result.release_allowed ? 'glow-emerald' : 'glow-crimson'}`}
              style={{
                padding: '20px 28px',
                background: result.workflow_status === 'success' && result.release_allowed
                  ? 'linear-gradient(135deg, rgba(16, 185, 129, 0.15) 0%, rgba(6, 182, 212, 0.15) 100%)'
                  : 'linear-gradient(135deg, rgba(239, 68, 68, 0.2) 0%, rgba(185, 28, 28, 0.15) 100%)',
                border: `1px solid ${result.workflow_status === 'success' && result.release_allowed ? '#10b981' : '#ef4444'}`,
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                flexWrap: 'wrap',
                gap: 16,
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
                <div style={{
                  background: result.workflow_status === 'success' && result.release_allowed ? 'rgba(16, 185, 129, 0.25)' : 'rgba(239, 68, 68, 0.25)',
                  padding: 12,
                  borderRadius: '50%',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}>
                  {result.workflow_status === 'success' && result.release_allowed ? (
                    <CheckCircle size={32} color="#10b981" />
                  ) : (
                    <XCircle size={32} color="#ef4444" />
                  )}
                </div>
                <div>
                  <h2 style={{ fontSize: '1.3rem', margin: 0, color: '#fff' }}>
                    {result.workflow_status === 'success' && result.release_allowed
                      ? 'RELEASE AUTHORIZED — VERIFICATION PASS'
                      : 'RELEASE BLOCKED — DOWNLOAD STRICTLY WITHHELD'}
                  </h2>
                  <p style={{ margin: '4px 0 0 0', fontSize: '0.85rem', color: '#cbd5e1' }}>
                    {result.workflow_status === 'success' && result.release_allowed
                      ? 'All classified PII entities safely redacted. Autonomous re-scan found 0 residual leaks. Approved for downstream LLM ingress.'
                      : (result.safe_error || 'Residual PII or verification exception detected during post-redaction re-scan. Fail-closed gate engaged.')}
                  </p>
                </div>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <span className={`badge ${result.verification_status === 'PASS' ? 'badge-phone' : 'badge-gov'}`} style={{ padding: '6px 14px', fontSize: '0.8rem' }}>
                  GATE: {result.verification_status || 'UNKNOWN'}
                </span>
                <span className={`badge ${result.release_allowed ? 'badge-ip' : 'badge-generic'}`} style={{ padding: '6px 14px', fontSize: '0.8rem' }}>
                  RELEASE: {result.release_allowed ? 'TRUE' : 'FALSE'}
                </span>
              </div>
            </div>

            {/* High-Level Telemetry Cards */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: 14 }}>
              <div className="glass-panel" style={{ padding: '14px 18px' }}>
                <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginBottom: 4 }}>DOCUMENT ID</div>
                <div style={{ fontSize: '0.95rem', fontWeight: 700, fontFamily: 'var(--font-mono)', color: '#38bdf8' }}>
                  {result.document_id.slice(0, 12)}...
                </div>
              </div>

              <div className="glass-panel" style={{ padding: '14px 18px' }}>
                <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginBottom: 4 }}>FORMAT / PAGES</div>
                <div style={{ fontSize: '0.95rem', fontWeight: 700, color: '#f8fafc' }}>
                  {(result.source_type || 'TXT').toUpperCase()} ({result.pages_count}p)
                </div>
              </div>

              <div className="glass-panel" style={{ padding: '14px 18px' }}>
                <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginBottom: 4 }}>PII DETECTED</div>
                <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#f87171' }}>
                  {result.entities.length} spans
                </div>
              </div>

              <div className="glass-panel" style={{ padding: '14px 18px' }}>
                <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginBottom: 4 }}>MASKED APPLIED</div>
                <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#34d399' }}>
                  {result.redactions_applied} entities
                </div>
              </div>

              <div className="glass-panel" style={{ padding: '14px 18px' }}>
                <div style={{ fontSize: '0.75rem', color: '#94a3b8', marginBottom: 4 }}>TOTAL DURATION</div>
                <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#f59e0b', fontFamily: 'var(--font-mono)' }}>
                  {result.duration_sec.toFixed(4)}s
                </div>
              </div>
            </div>

            {/* Navigation Tabs */}
            <div className="nav-tabs" style={{ marginTop: 8 }}>
              <button
                onClick={() => setActiveTab('stages')}
                className={`nav-tab-btn ${activeTab === 'stages' ? 'active' : ''}`}
              >
                <Layers size={16} />
                <span>Live Execution Inspector (7 Stages)</span>
              </button>

              <button
                onClick={() => setActiveTab('comparison')}
                className={`nav-tab-btn ${activeTab === 'comparison' ? 'active' : ''}`}
              >
                <Eye size={16} />
                <span>Document Comparison & Entity Spans</span>
              </button>

              <button
                onClick={() => setActiveTab('assistant')}
                className={`nav-tab-btn ${activeTab === 'assistant' ? 'active' : ''}`}
              >
                <Bot size={16} />
                <span>AI Governance Assistant</span>
              </button>

              <button
                onClick={() => setActiveTab('audit')}
                className={`nav-tab-btn ${activeTab === 'audit' ? 'active' : ''}`}
              >
                <ScrollText size={16} />
                <span>Sanitized Audit & Formal Reports</span>
              </button>
            </div>

            {/* Tab Contents */}
            {activeTab === 'stages' && (
              <PipelineStages
                currentStage={result.current_stage}
                workflowStatus={result.workflow_status}
                stageHistory={result.stage_history}
                totalDuration={result.duration_sec}
              />
            )}

            {activeTab === 'comparison' && (
              <DocumentComparison
                extractedText={result.extracted_text}
                redactedText={result.redacted_text}
                entities={result.entities}
                releaseAllowed={result.release_allowed}
                verificationStatus={result.verification_status}
              />
            )}

            {activeTab === 'assistant' && (
              <AIAssistant documentId={result.document_id} />
            )}

            {activeTab === 'audit' && (
              <AuditLedger
                documentId={result.document_id}
                releaseAllowed={result.release_allowed}
                sourceType={result.source_type}
              />
            )}
          </section>
        )}
      </main>

      <footer style={{ borderTop: '1px solid var(--border-color)', padding: '16px 24px', textAlign: 'center', fontSize: '0.8rem', color: '#64748b' }}>
        Cadence Financial Group — Enterprise AI Governance & Automated Redaction Release Gate Pipeline | Zero-Leakage Mandate
      </footer>
    </div>
  );
};

export default App;

