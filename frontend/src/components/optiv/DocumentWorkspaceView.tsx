import React, { useState, useEffect } from 'react';
import {
  Upload,
  Play,
  Layers,
  Eye,
  Sparkles,
  Lock,
  Download,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Clock,
  ShieldAlert,
  Bot,
} from 'lucide-react';
import type {
  ProcessResponse,
  ScenarioFixture,
  UserProfile,
} from '../../types';

interface DocumentWorkspaceViewProps {
  currentUser: UserProfile;
  initialDocumentId?: string | null;
  initialEntityIndex?: number | null;
  activeDocument?: ProcessResponse | null;
  onDocumentChange?: (doc: ProcessResponse) => void;
  onOpenAssistant: (documentId: string) => void;
  scenarios: ScenarioFixture[];
}

export const DocumentWorkspaceView: React.FC<DocumentWorkspaceViewProps> = ({
  currentUser,
  initialDocumentId,
  initialEntityIndex,
  activeDocument,
  onDocumentChange,
  onOpenAssistant,
  scenarios,
}) => {
  const [inputMode, setInputMode] = useState<'scenario' | 'upload'>('scenario');
  const [selectedScenario, setSelectedScenario] = useState<string>('03_mixed_pii.txt');
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [simulateFailure, setSimulateFailure] = useState<boolean>(false);
  const [processing, setProcessing] = useState<boolean>(false);
  const [result, setResult] = useState<ProcessResponse | null>(activeDocument || null);
  const [error, setError] = useState<string | null>(null);

  // Inspection navigation
  const [selectedEntityIndex, setSelectedEntityIndex] = useState<number | null>(initialEntityIndex ?? null);
  const [categoryFilter, setCategoryFilter] = useState<string>('ALL');
  const [showOriginalValues, setShowOriginalValues] = useState<boolean>(false);

  // Sync activeDocument
  useEffect(() => {
    if (activeDocument) {
      setResult(activeDocument);
    }
  }, [activeDocument]);

  useEffect(() => {
    if (initialEntityIndex !== undefined && initialEntityIndex !== null) {
      setSelectedEntityIndex(initialEntityIndex);
    }
  }, [initialEntityIndex]);

  // Load initial document if supplied
  useEffect(() => {
    if (initialDocumentId && (!activeDocument || activeDocument.document_id !== initialDocumentId)) {
      fetch(`/api/runs/${initialDocumentId}`)
        .then((res) => {
          if (res.ok) return res.json();
          throw new Error('Not found');
        })
        .then((data: ProcessResponse) => {
          setResult(data);
          if (onDocumentChange) onDocumentChange(data);
        })
        .catch(() => {});
    }
  }, [initialDocumentId]);

  const handleExecutePipeline = async () => {
    setError(null);
    setProcessing(true);
    setSelectedEntityIndex(null);

    try {
      const formData = new FormData();
      formData.append('simulate_verification_failure', simulateFailure.toString());

      if (inputMode === 'scenario') {
        formData.append('scenario_filename', selectedScenario);
      } else {
        if (!uploadedFile) {
          setError('Please select a document file to upload.');
          setProcessing(false);
          return;
        }
        formData.append('file', uploadedFile);
      }

      const res = await fetch('/api/process', {
        method: 'POST',
        headers: {
          'X-User-Email': currentUser?.email || 'privacy@optiv.security',
        },
        body: formData,
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({ detail: 'Execution failed' }));
        throw new Error(errData.detail || 'Pipeline execution failed');
      }

      const data: ProcessResponse = await res.json();
      setResult(data);
      if (onDocumentChange) {
        onDocumentChange(data);
      }
    } catch (err: any) {
      setError(err.message || 'Error processing document');
    } finally {
      setProcessing(false);
    }
  };

  const handleDownloadArtifact = () => {
    if (!result?.document_id || !result.release_allowed) return;
    window.open(`/api/artifact/${result.document_id}`, '_blank');
  };

  const handleDownloadOriginal = () => {
    if (!result?.document_id) return;
    window.open(`/api/original/${result.document_id}`, '_blank');
  };

  const handleDownloadReport = (format: 'json' | 'csv' | 'summary') => {
    if (!result?.document_id) return;
    window.open(`/api/report/${result.document_id}?format=${format}`, '_blank');
  };

  // Filtered entities
  const entities = result?.entities || [];
  const filteredEntities = categoryFilter === 'ALL'
    ? entities
    : entities.filter((e) => e.type.toUpperCase() === categoryFilter.toUpperCase());
  const categories = Array.from(new Set(entities.map((e) => e.type.toUpperCase())));

  // Render highlighted original text
  const renderOriginalText = () => {
    if (!result?.extracted_text) {
      return (
        <div style={{ color: 'var(--tprm-text-muted)', padding: 24, textAlign: 'center' }}>
          No document extracted yet. Run the pipeline above.
        </div>
      );
    }

    const text = result.extracted_text;
    if (entities.length === 0) {
      return <pre style={{ whiteSpace: 'pre-wrap', margin: 0 }}>{text}</pre>;
    }

    const sorted = [...entities].sort((a, b) => a.start - b.start);
    const elements: React.ReactNode[] = [];
    let lastIndex = 0;

    sorted.forEach((ent, i) => {
      if (ent.start > lastIndex) {
        elements.push(text.slice(lastIndex, ent.start));
      }
      const val = text.slice(ent.start, ent.end);
      const isSelected = selectedEntityIndex === i;
      const isMatchingFilter = categoryFilter === 'ALL' || ent.type.toUpperCase() === categoryFilter.toUpperCase();

      elements.push(
        <span
          key={`span-${i}`}
          onClick={() => setSelectedEntityIndex(i)}
          className={`highlight-entity ${isSelected ? 'selected' : ''}`}
          style={{
            opacity: isMatchingFilter ? 1 : 0.4,
            backgroundColor: isSelected ? 'rgba(239, 68, 68, 0.4)' : undefined,
          }}
          title={`${ent.type} [${ent.start}, ${ent.end}) | Click to inspect`}
        >
          {showOriginalValues ? val : `[${ent.type}]`}
        </span>
      );
      lastIndex = ent.end;
    });

    if (lastIndex < text.length) {
      elements.push(text.slice(lastIndex));
    }

    return <pre style={{ whiteSpace: 'pre-wrap', margin: 0 }}>{elements}</pre>;
  };

  const getBadgeClass = (type: string) => {
    switch (type.toUpperCase()) {
      case 'EMAIL': return 'badge-email';
      case 'PHONE': return 'badge-phone';
      case 'GOVERNMENT_ID': return 'badge-gov';
      case 'FINANCIAL_IDENTIFIER': return 'badge-card';
      case 'EMPLOYEE_ID': return 'badge-emp';
      case 'IP_ADDRESS': return 'badge-ip';
      case 'PERSON': return 'badge-person';
      default: return 'badge-generic';
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      {/* Document Selection & Ingestion Bar */}
      <div className="optiv-card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <div style={{ padding: 8, borderRadius: 8, backgroundColor: 'var(--tprm-indigo-light)' }}>
              <Upload size={18} color="var(--tprm-indigo)" />
            </div>
            <div>
              <h3 style={{ fontSize: '1rem', fontWeight: 700, margin: 0, color: 'var(--tprm-text-primary)' }}>
                Document Ingestion & Execution Controller
              </h3>
              <p style={{ fontSize: '0.75rem', color: 'var(--tprm-text-muted)', margin: 0 }}>
                Supports PDF, PPTX (PowerPoint), PNG/JPEG (Images), JSON, DOCX, and TXT (Max: 50MB)
              </p>
            </div>
          </div>

          {/* Mode Switcher */}
          <div style={{ display: 'flex', gap: 6, backgroundColor: 'var(--tprm-surface-subtle)', padding: 4, borderRadius: 8 }}>
            <button
              onClick={() => setInputMode('scenario')}
              className={`btn-sm ${inputMode === 'scenario' ? 'btn-primary' : 'btn-secondary'}`}
              style={{ padding: '4px 12px', fontSize: '0.75rem' }}
            >
              Certified Scenario Fixtures
            </button>
            <button
              onClick={() => setInputMode('upload')}
              className={`btn-sm ${inputMode === 'upload' ? 'btn-primary' : 'btn-secondary'}`}
              style={{ padding: '4px 12px', fontSize: '0.75rem' }}
            >
              Custom File Upload
            </button>
          </div>
        </div>

        {/* File Picker Row */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 16, flexWrap: 'wrap' }}>
          {inputMode === 'scenario' ? (
            <div style={{ flex: 1, minWidth: 280 }}>
              <label style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--tprm-text-secondary)', display: 'block', marginBottom: 4 }}>
                Select Certified Test Fixture:
              </label>
              <select
                value={selectedScenario}
                onChange={(e) => setSelectedScenario(e.target.value)}
                className="w-full"
                style={{
                  padding: '8px 12px',
                  borderRadius: 6,
                  border: '1px solid var(--tprm-border)',
                  backgroundColor: 'var(--tprm-surface)',
                  color: 'var(--tprm-text-primary)',
                  fontSize: '0.85rem',
                }}
              >
                {scenarios.map((s) => (
                  <option key={s.id || s.filename} value={s.filename}>
                    {s.name} ({s.file_type.toUpperCase()} • {(s.size_bytes / 1024).toFixed(1)} KB)
                  </option>
                ))}
              </select>
            </div>
          ) : (
            <div style={{ flex: 1, minWidth: 280 }}>
              <label style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--tprm-text-secondary)', display: 'block', marginBottom: 4 }}>
                Choose Local File (.pdf, .pptx, .json, .png, .jpg, .docx, .txt):
              </label>
              <input
                type="file"
                onChange={(e) => setUploadedFile(e.target.files?.[0] || null)}
                accept=".pdf,.pptx,.docx,.txt,.json,.png,.jpg,.jpeg"
                style={{
                  padding: '6px 10px',
                  borderRadius: 6,
                  border: '1px solid var(--tprm-border)',
                  backgroundColor: 'var(--tprm-surface)',
                  color: 'var(--tprm-text-primary)',
                  fontSize: '0.85rem',
                  width: '100%',
                }}
              />
            </div>
          )}

          {/* Verification Barrier Simulation Option */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '8px 12px', borderRadius: 6, backgroundColor: 'var(--tprm-surface-subtle)', border: '1px solid var(--tprm-border)' }}>
            <input
              type="checkbox"
              id="sim-fail"
              checked={simulateFailure}
              onChange={(e) => setSimulateFailure(e.target.checked)}
              style={{ cursor: 'pointer' }}
            />
            <label htmlFor="sim-fail" style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--tprm-text-secondary)', cursor: 'pointer' }}>
              Simulate Residual Leakage / Verification Gate Block
            </label>
          </div>

          {/* Trigger Button */}
          <button
            onClick={handleExecutePipeline}
            disabled={processing}
            className="btn-primary"
            style={{ padding: '8px 18px', fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: 8 }}
          >
            <Play size={15} />
            <span>{processing ? 'Executing Multi-Stage Scan...' : 'Run Pipeline'}</span>
          </button>
        </div>

        {error && (
          <div style={{ marginTop: 14, padding: '10px 14px', borderRadius: 6, backgroundColor: 'rgba(239, 68, 68, 0.1)', border: '1px solid var(--tprm-rose)', color: 'var(--tprm-rose)', fontSize: '0.8rem', display: 'flex', alignItems: 'center', gap: 8 }}>
            <AlertTriangle size={16} />
            <span>{error}</span>
          </div>
        )}
      </div>

      {/* 9-Stage Observable Pipeline Stepper */}
      {result && (
        <div className="optiv-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <Layers size={18} color="var(--tprm-cyan)" />
              <h4 style={{ fontSize: '0.9rem', fontWeight: 700, margin: 0, color: 'var(--tprm-text-primary)' }}>
                Multi-Stage Scanning Pipeline Execution Telemetry
              </h4>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.75rem', color: 'var(--tprm-text-muted)' }}>
              <Clock size={14} />
              <span>Duration: <strong>{(result.duration_sec || 0).toFixed(4)}s</strong></span>
            </div>
          </div>

          <div className="stage-stepper-grid">
            {[
              { stage: 'RECEIVED', label: '1. Ingestion', code: 'Stage 1' },
              { stage: 'VALIDATED', label: '2. Inspection', code: 'Stage 2' },
              { stage: 'EXTRACTED', label: '3. Extraction & OCR', code: 'Stage 3' },
              { stage: 'DETECTED', label: '4. PII Detection', code: 'Stage 4' },
              { stage: 'REDACTED', label: '5. Policy & Masking', code: 'Stage 5-6' },
              { stage: 'VERIFIED', label: '6. Verification', code: 'Stage 7' },
              { stage: 'RELEASED', label: '7. Release Decision', code: 'Stage 8' },
            ].map((st) => {
              const hist = result.stage_history.find((h) => h.to_stage === st.stage);
              const isCurrent = result.current_stage === st.stage;
              const isCompleted = !!hist && (!isCurrent || result.workflow_status === 'success');
              const isBlocked = result.workflow_status === 'blocked' && st.stage === 'RELEASED';

              return (
                <div
                  key={st.stage}
                  className={`stage-step-card ${isBlocked ? 'blocked' : isCompleted ? 'completed' : isCurrent ? 'active' : ''}`}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: '0.65rem', fontWeight: 700, color: 'var(--tprm-text-muted)' }}>
                      {st.code}
                    </span>
                    {isBlocked ? (
                      <XCircle size={14} color="var(--tprm-rose)" />
                    ) : isCompleted ? (
                      <CheckCircle2 size={14} color="var(--tprm-emerald)" />
                    ) : (
                      <Clock size={14} color="var(--tprm-text-muted)" />
                    )}
                  </div>
                  <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--tprm-text-primary)' }}>
                    {st.label}
                  </div>
                  <div style={{ fontSize: '0.65rem', color: 'var(--tprm-text-muted)', fontFamily: 'var(--font-mono)' }}>
                    {hist ? `${hist.duration_sec.toFixed(3)}s` : 'Pending'}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Side-by-Side Document Comparison: ORIGINAL vs PROCESSED */}
      {result && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--tprm-text-secondary)' }}>
                Filter Entities by Category:
              </span>
              <button
                onClick={() => setCategoryFilter('ALL')}
                className={`btn-sm ${categoryFilter === 'ALL' ? 'btn-primary' : 'btn-secondary'}`}
                style={{ fontSize: '0.725rem', padding: '3px 8px' }}
              >
                All ({entities.length})
              </button>
              {categories.map((cat) => (
                <button
                  key={cat}
                  onClick={() => setCategoryFilter(cat)}
                  className={`badge ${getBadgeClass(cat)}`}
                  style={{
                    cursor: 'pointer',
                    fontSize: '0.725rem',
                    padding: '3px 8px',
                    border: categoryFilter === cat ? '1px solid var(--tprm-indigo)' : undefined,
                  }}
                >
                  {cat} ({entities.filter((e) => e.type.toUpperCase() === cat).length})
                </button>
              ))}
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              {/* Unmask toggle for authorized compliance officers */}
              {currentUser.is_admin && (
                <button
                  onClick={() => setShowOriginalValues(!showOriginalValues)}
                  className="btn-secondary"
                  style={{ fontSize: '0.75rem', padding: '4px 10px' }}
                >
                  {showOriginalValues ? 'Mask Sensitive Spans' : 'Reveal Sensitive Spans (Authorized)'}
                </button>
              )}

              {/* Ask Copilot Button */}
              <button
                onClick={() => onOpenAssistant(result.document_id)}
                className="btn-secondary"
                style={{ fontSize: '0.75rem', padding: '4px 10px', display: 'flex', alignItems: 'center', gap: 6 }}
              >
                <Bot size={14} color="var(--tprm-indigo)" />
                <span>Explain Run</span>
              </button>
            </div>
          </div>

          <div className="comparison-grid">
            {/* A. ORIGINAL INPUT PANE */}
            <div className="viewer-pane">
              <div className="viewer-pane-header">
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <Eye size={16} color="var(--tprm-indigo)" />
                  <span style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--tprm-text-primary)' }}>
                    A. ORIGINAL INPUT (Immutable Source)
                  </span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <span className="badge badge-generic" style={{ fontSize: '0.7rem' }}>
                    {result.source_type?.toUpperCase() || 'FILE'}
                  </span>
                  <button
                    onClick={handleDownloadOriginal}
                    className="btn-secondary"
                    style={{ fontSize: '0.7rem', padding: '2px 8px' }}
                    title="Download unmodified original document"
                  >
                    Download Original
                  </button>
                </div>
              </div>

              <div className="viewer-pane-content">
                {renderOriginalText()}
              </div>
            </div>

            {/* B. PROCESSED SANITIZED OUTPUT PANE */}
            <div className="viewer-pane">
              <div className="viewer-pane-header">
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <Sparkles size={16} color={result.release_allowed ? 'var(--tprm-emerald)' : 'var(--tprm-rose)'} />
                  <span style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--tprm-text-primary)' }}>
                    B. PROCESSED OUTPUT (Sanitized Artifact)
                  </span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <span className={`badge ${result.release_allowed ? 'badge-success' : 'badge-gov'}`} style={{ fontSize: '0.7rem' }}>
                    {result.release_allowed ? 'RELEASE AUTHORIZED' : 'RELEASE WITHHELD'}
                  </span>
                  {result.release_allowed && (
                    <button
                      onClick={handleDownloadArtifact}
                      className="btn-primary"
                      style={{ fontSize: '0.7rem', padding: '2px 8px', display: 'flex', alignItems: 'center', gap: 4 }}
                    >
                      <Download size={12} />
                      <span>Download Sanitized</span>
                    </button>
                  )}
                </div>
              </div>

              <div className="viewer-pane-content">
                {result.release_allowed && result.redacted_text ? (
                  <pre style={{ whiteSpace: 'pre-wrap', margin: 0, color: 'var(--tprm-text-primary)' }}>
                    {result.redacted_text}
                  </pre>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', gap: 14, textAlign: 'center', padding: 24 }}>
                    <div style={{ padding: 16, borderRadius: '50%', backgroundColor: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.3)' }}>
                      <Lock size={32} color="#ef4444" />
                    </div>
                    <div>
                      <h4 style={{ color: 'var(--tprm-rose)', fontSize: '0.95rem', margin: '0 0 6px' }}>
                        Sanitized Document Egress Withheld
                      </h4>
                      <p style={{ fontSize: '0.75rem', color: 'var(--tprm-text-muted)', maxWidth: 360, margin: '0 auto', lineHeight: 1.5 }}>
                        Independent verification status is <strong>{result.verification_status || 'FAIL'}</strong>. Under the fail-closed barrier, unverified artifacts cannot be egressed to downstream consumers.
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Classified PII Entity Spans Inventory */}
      {result && (
        <div className="optiv-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <ShieldAlert size={18} color="var(--tprm-indigo)" />
              <h4 style={{ fontSize: '0.95rem', fontWeight: 700, margin: 0, color: 'var(--tprm-text-primary)' }}>
                Detected PII Findings Inventory ({filteredEntities.length})
              </h4>
            </div>
            <div style={{ display: 'flex', gap: 8 }}>
              <button
                onClick={() => handleDownloadReport('json')}
                className="btn-secondary"
                style={{ fontSize: '0.75rem', padding: '4px 10px' }}
              >
                Export JSON Report
              </button>
              <button
                onClick={() => handleDownloadReport('csv')}
                className="btn-secondary"
                style={{ fontSize: '0.75rem', padding: '4px 10px' }}
              >
                Export CSV Matrix
              </button>
            </div>
          </div>

          {filteredEntities.length === 0 ? (
            <div style={{ padding: 24, textAlign: 'center', color: 'var(--tprm-text-muted)', fontSize: '0.85rem' }}>
              No PII entities detected matching current filter.
            </div>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--tprm-border)', color: 'var(--tprm-text-muted)', textAlign: 'left' }}>
                    <th style={{ padding: '8px 12px' }}>Category</th>
                    <th style={{ padding: '8px 12px' }}>Span [Start, End)</th>
                    <th style={{ padding: '8px 12px' }}>Confidence</th>
                    <th style={{ padding: '8px 12px' }}>Sensitive Value</th>
                    <th style={{ padding: '8px 12px' }}>Masking Rule</th>
                    <th style={{ padding: '8px 12px' }}>Verification Status</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredEntities.map((ent, idx) => (
                    <tr
                      key={idx}
                      style={{
                        borderBottom: '1px solid var(--tprm-border)',
                        backgroundColor: selectedEntityIndex === idx ? 'rgba(99, 102, 241, 0.08)' : undefined,
                        cursor: 'pointer',
                      }}
                      onClick={() => setSelectedEntityIndex(idx)}
                    >
                      <td style={{ padding: '8px 12px' }}>
                        <span className={`badge ${getBadgeClass(ent.type)}`}>{ent.type}</span>
                      </td>
                      <td style={{ padding: '8px 12px', fontFamily: 'var(--font-mono)', fontSize: '0.75rem' }}>
                        [{ent.start}, {ent.end}) ({ent.end - ent.start} chars)
                      </td>
                      <td style={{ padding: '8px 12px' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                          <div style={{ width: 48, height: 5, backgroundColor: 'var(--tprm-border)', borderRadius: 3, overflow: 'hidden' }}>
                            <div style={{ width: `${ent.confidence * 100}%`, height: '100%', backgroundColor: ent.confidence >= 0.9 ? 'var(--tprm-emerald)' : '#f59e0b' }} />
                          </div>
                          <span style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)' }}>
                            {(ent.confidence * 100).toFixed(0)}%
                          </span>
                        </div>
                      </td>
                      <td style={{ padding: '8px 12px', fontFamily: 'var(--font-mono)', color: 'var(--tprm-rose)', fontWeight: 600 }}>
                        {showOriginalValues ? ent.value : '••••••••••••'}
                      </td>
                      <td style={{ padding: '8px 12px', fontFamily: 'var(--font-mono)', color: 'var(--tprm-emerald)' }}>
                        {ent.masked_value}
                      </td>
                      <td style={{ padding: '8px 12px' }}>
                        <span className="badge badge-success" style={{ fontSize: '0.7rem' }}>
                          VERIFIED REMOVED
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
