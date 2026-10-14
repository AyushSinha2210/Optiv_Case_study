import React, { useState, useEffect, useMemo, useRef, useCallback } from 'react';
import {
  Upload,
  Play,
  Layers,
  Eye,
  FileCheck2,
  Lock,
  Download,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Clock,
  ShieldAlert,
  HelpCircle,
  ArrowRightLeft,
  RefreshCw,
  Shield,
} from 'lucide-react';
import type {
  ProcessResponse,
  ScenarioFixture,
  UserProfile,
} from '../../types';
import { PageHeader } from './PageHeader';

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
  const [showRevealModal, setShowRevealModal] = useState<boolean>(false);
  const [syncScroll, setSyncScroll] = useState<boolean>(true);

  // Scroll synchronization refs
  const originalPaneRef = useRef<HTMLDivElement>(null);
  const processedPaneRef = useRef<HTMLDivElement>(null);
  const isSyncingScroll = useRef<boolean>(false);

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

  // Synchronized scrolling handlers
  const handleOriginalScroll = useCallback(() => {
    if (!syncScroll || isSyncingScroll.current) return;
    isSyncingScroll.current = true;
    if (originalPaneRef.current && processedPaneRef.current) {
      const orig = originalPaneRef.current;
      const proc = processedPaneRef.current;
      const scrollPercentage = orig.scrollTop / (orig.scrollHeight - orig.clientHeight || 1);
      proc.scrollTop = scrollPercentage * (proc.scrollHeight - proc.clientHeight);
    }
    setTimeout(() => {
      isSyncingScroll.current = false;
    }, 20);
  }, [syncScroll]);

  const handleProcessedScroll = useCallback(() => {
    if (!syncScroll || isSyncingScroll.current) return;
    isSyncingScroll.current = true;
    if (originalPaneRef.current && processedPaneRef.current) {
      const orig = originalPaneRef.current;
      const proc = processedPaneRef.current;
      const scrollPercentage = proc.scrollTop / (proc.scrollHeight - proc.clientHeight || 1);
      orig.scrollTop = scrollPercentage * (orig.scrollHeight - orig.clientHeight);
    }
    setTimeout(() => {
      isSyncingScroll.current = false;
    }, 20);
  }, [syncScroll]);

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

  // Memoized entities and categories
  const entities = useMemo(() => result?.entities || [], [result?.entities]);

  const categories = useMemo(() => {
    return Array.from(new Set(entities.map((e) => e.type.toUpperCase())));
  }, [entities]);

  const filteredEntities = useMemo(() => {
    if (categoryFilter === 'ALL') return entities;
    return entities.filter((e) => e.type.toUpperCase() === categoryFilter.toUpperCase());
  }, [entities, categoryFilter]);

  // Memoized highlighted original text elements
  const highlightedOriginalElements = useMemo(() => {
    if (!result?.extracted_text) return null;
    const text = result.extracted_text;

    if (entities.length === 0) {
      return <pre style={{ whiteSpace: 'pre-wrap', margin: 0, fontFamily: 'var(--font-mono)', fontSize: '0.825rem' }}>{text}</pre>;
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
            opacity: isMatchingFilter ? 1 : 0.35,
            backgroundColor: isSelected ? 'rgba(239, 68, 68, 0.4)' : undefined,
            transition: 'background-color 0.15s ease',
          }}
          title={`${ent.type} [${ent.start}, ${ent.end}) | Click to inspect`}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              setSelectedEntityIndex(i);
            }
          }}
        >
          {showOriginalValues ? val : `[${ent.type}]`}
        </span>
      );
      lastIndex = ent.end;
    });

    if (lastIndex < text.length) {
      elements.push(text.slice(lastIndex));
    }

    return (
      <pre style={{ whiteSpace: 'pre-wrap', margin: 0, fontFamily: 'var(--font-mono)', fontSize: '0.825rem', lineHeight: 1.6 }}>
        {elements}
      </pre>
    );
  }, [result?.extracted_text, entities, selectedEntityIndex, categoryFilter, showOriginalValues]);

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
      {/* Standardized Page Header */}
      <PageHeader
        title="Document Comparison & Redaction Workspace"
        description="Inspect immutable original inputs side-by-side with policy-sanitized outputs, evaluate detected PII spans, and verify layout retention."
        actions={
          <div style={{ display: 'flex', gap: 8 }}>
            <button
              onClick={() => onOpenAssistant(result?.document_id || '')}
              className="btn-secondary"
              title="Open AI Privacy Copilot for this document"
            >
              <HelpCircle size={14} color="var(--tprm-indigo)" />
              <span>Ask Copilot</span>
            </button>
            <button
              onClick={handleExecutePipeline}
              className="btn-primary"
              disabled={processing}
              title="Run PII Privacy Pipeline on selected document"
            >
              {processing ? (
                <>
                  <RefreshCw size={14} className="animate-spin" />
                  <span>Scanning...</span>
                </>
              ) : (
                <>
                  <Play size={14} />
                  <span>Run Privacy Engine</span>
                </>
              )}
            </button>
          </div>
        }
      />

      {/* Document Selection & Ingestion Bar */}
      <div className="optiv-card" style={{ padding: '16px 20px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14, flexWrap: 'wrap', gap: 10 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <div style={{ padding: 8, borderRadius: 8, backgroundColor: 'var(--tprm-indigo-light)' }}>
              <Upload size={18} color="var(--tprm-indigo)" />
            </div>
            <div>
              <h3 style={{ fontSize: '0.95rem', fontWeight: 700, margin: 0, color: 'var(--tprm-text-primary)' }}>
                Document Ingestion & Execution Controller
              </h3>
              <p style={{ fontSize: '0.725rem', color: 'var(--tprm-text-muted)', margin: 0 }}>
                Supports PDF (PyMuPDF Vector), PPTX, PNG/JPEG, JSON, DOCX, and TXT (Max: 50MB)
              </p>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <button
              onClick={() => setInputMode('scenario')}
              className={`optiv-btn-header ${inputMode === 'scenario' ? 'active' : ''}`}
              style={{
                backgroundColor: inputMode === 'scenario' ? 'var(--tprm-indigo-light)' : 'transparent',
                color: inputMode === 'scenario' ? 'var(--tprm-indigo)' : 'inherit',
                borderColor: inputMode === 'scenario' ? 'rgba(99, 102, 241, 0.4)' : 'var(--tprm-border)',
              }}
            >
              Test Scenarios
            </button>
            <button
              onClick={() => setInputMode('upload')}
              className={`optiv-btn-header ${inputMode === 'upload' ? 'active' : ''}`}
              style={{
                backgroundColor: inputMode === 'upload' ? 'var(--tprm-indigo-light)' : 'transparent',
                color: inputMode === 'upload' ? 'var(--tprm-indigo)' : 'inherit',
                borderColor: inputMode === 'upload' ? 'rgba(99, 102, 241, 0.4)' : 'var(--tprm-border)',
              }}
            >
              Upload Document
            </button>
          </div>
        </div>

        {/* Input Configuration Row */}
        <div style={{ display: 'flex', gap: 12, alignItems: 'center', flexWrap: 'wrap' }}>
          {inputMode === 'scenario' ? (
            <div style={{ flex: 1, minWidth: 260 }}>
              <select
                className="optiv-select"
                style={{ width: '100%', height: 38 }}
                value={selectedScenario}
                onChange={(e) => setSelectedScenario(e.target.value)}
                disabled={processing}
                aria-label="Select Test Scenario"
              >
                {scenarios.map((s) => (
                  <option key={s.id || s.filename} value={s.filename}>
                    {s.name} ({s.filename} • {s.file_type.toUpperCase()})
                  </option>
                ))}
              </select>
            </div>
          ) : (
            <div style={{ flex: 1, minWidth: 260 }}>
              <input
                type="file"
                disabled={processing}
                onChange={(e) => {
                  if (e.target.files && e.target.files[0]) {
                    setUploadedFile(e.target.files[0]);
                  }
                }}
                className="optiv-input-search"
                style={{ width: '100%', height: 38, padding: '7px 10px', boxSizing: 'border-box' }}
                aria-label="Choose document file to upload"
              />
            </div>
          )}

          {/* Test Harness: Fail-Closed Simulation Checkbox */}
          <label
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              fontSize: '0.775rem',
              color: 'var(--tprm-text-secondary)',
              cursor: 'pointer',
              userSelect: 'none',
              padding: '6px 10px',
              borderRadius: 6,
              backgroundColor: 'var(--tprm-surface-subtle)',
              border: '1px solid var(--tprm-border)',
            }}
          >
            <input
              type="checkbox"
              checked={simulateFailure}
              onChange={(e) => setSimulateFailure(e.target.checked)}
              disabled={processing}
            />
            <span>Simulate Residual Failure (Tests Fail-Closed Gate)</span>
          </label>

          {/* Execution Button */}
          <button
            onClick={handleExecutePipeline}
            disabled={processing}
            className="btn-primary"
            style={{
              padding: '8px 20px',
              fontSize: '0.85rem',
              display: 'flex',
              alignItems: 'center',
              gap: 8,
            }}
          >
            {processing ? (
              <>
                <RefreshCw size={15} className="animate-spin" />
                <span>Executing Pipeline...</span>
              </>
            ) : (
              <>
                <Play size={15} />
                <span>Run Privacy Engine</span>
              </>
            )}
          </button>
        </div>

        {error && (
          <div
            style={{
              marginTop: 12,
              padding: '8px 12px',
              borderRadius: 6,
              backgroundColor: 'rgba(239, 68, 68, 0.1)',
              border: '1px solid var(--tprm-rose)',
              color: 'var(--tprm-rose)',
              fontSize: '0.8rem',
              display: 'flex',
              alignItems: 'center',
              gap: 8,
            }}
          >
            <AlertTriangle size={15} />
            <span>{error}</span>
          </div>
        )}
      </div>

      {/* 9-Stage Execution Telemetry Stepper */}
      {result && (
        <div className="optiv-card" style={{ padding: '14px 18px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <Layers size={16} color="var(--tprm-indigo)" />
              <span style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--tprm-text-primary)' }}>
                Stage-by-Stage Processing Telemetry
              </span>
            </div>
            <div style={{ fontSize: '0.75rem', color: 'var(--tprm-text-muted)' }}>
              Completed in <strong style={{ color: 'var(--tprm-text-primary)' }}>{result.duration_sec.toFixed(3)}s</strong>
            </div>
          </div>

          <div className="stage-stepper-grid">
            {[
              { id: 'RECEIVED', label: '1. Ingestion', status: 'completed' },
              { id: 'VALIDATED', label: '2. Validation', status: 'completed' },
              { id: 'EXTRACTED', label: '3. Extraction', status: result.extraction_status === 'SUCCESS' ? 'completed' : 'active' },
              { id: 'DETECTED', label: '4. Detection', status: result.detection_status === 'SUCCESS' ? 'completed' : 'active' },
              { id: 'CLASSIFIED', label: '5. Classifier', status: 'completed' },
              { id: 'REDACTED', label: '6. Redaction', status: result.redaction_status === 'SUCCESS' ? 'completed' : 'active' },
              { id: 'RESIDUAL_SCAN', label: '7. Residual Scan', status: result.verification_status === 'PASS' ? 'completed' : 'failed' },
              { id: 'VERIFIED', label: '8. Verification', status: result.verification_status === 'PASS' ? 'completed' : 'failed' },
              { id: 'RELEASED', label: '9. Release Gate', status: result.release_allowed ? 'completed' : 'blocked' },
            ].map((st, idx) => (
              <div key={idx} className={`stage-step-card ${st.status}`}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: '0.725rem', fontWeight: 600, color: 'var(--tprm-text-primary)' }}>
                    {st.label}
                  </span>
                  {st.status === 'completed' && <CheckCircle2 size={13} color="var(--tprm-emerald)" />}
                  {st.status === 'active' && <Clock size={13} color="var(--tprm-cyan)" />}
                  {(st.status === 'failed' || st.status === 'blocked') && <XCircle size={13} color="var(--tprm-rose)" />}
                </div>
                <div style={{ fontSize: '0.675rem', textTransform: 'uppercase', fontWeight: 700, color: st.status === 'completed' ? 'var(--tprm-emerald)' : st.status === 'failed' || st.status === 'blocked' ? 'var(--tprm-rose)' : 'var(--tprm-cyan)' }}>
                  {st.status}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Dual-Pane Document Diff Viewer */}
      {result && (
        <div className="optiv-card" style={{ padding: '16px 20px' }}>
          {/* Controls Bar Above Panes */}
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: 12,
              flexWrap: 'wrap',
              gap: 10,
            }}
          >
            {/* Category Filter Pills */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
              <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--tprm-text-muted)' }}>
                Filter PII:
              </span>
              <button
                onClick={() => setCategoryFilter('ALL')}
                className={`optiv-btn-header ${categoryFilter === 'ALL' ? 'active' : ''}`}
                style={{
                  height: 28,
                  fontSize: '0.725rem',
                  backgroundColor: categoryFilter === 'ALL' ? 'var(--tprm-indigo-light)' : 'transparent',
                  color: categoryFilter === 'ALL' ? 'var(--tprm-indigo)' : 'inherit',
                  borderColor: categoryFilter === 'ALL' ? 'rgba(99, 102, 241, 0.4)' : 'var(--tprm-border)',
                }}
              >
                All ({entities.length})
              </button>
              {categories.map((cat) => (
                <button
                  key={cat}
                  onClick={() => setCategoryFilter(cat)}
                  className={`optiv-btn-header ${categoryFilter === cat ? 'active' : ''}`}
                  style={{
                    height: 28,
                    fontSize: '0.725rem',
                    backgroundColor: categoryFilter === cat ? 'var(--tprm-indigo-light)' : 'transparent',
                    color: categoryFilter === cat ? 'var(--tprm-indigo)' : 'inherit',
                    borderColor: categoryFilter === cat ? 'rgba(99, 102, 241, 0.4)' : 'var(--tprm-border)',
                  }}
                >
                  {cat} ({entities.filter((e) => e.type.toUpperCase() === cat).length})
                </button>
              ))}
            </div>

            {/* View Actions */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              {/* Sync Scroll Toggle */}
              <button
                onClick={() => setSyncScroll(!syncScroll)}
                className={`optiv-btn-header ${syncScroll ? 'active' : ''}`}
                style={{
                  height: 28,
                  fontSize: '0.725rem',
                  backgroundColor: syncScroll ? 'rgba(6, 182, 212, 0.12)' : 'transparent',
                  color: syncScroll ? 'var(--tprm-cyan)' : 'inherit',
                  borderColor: syncScroll ? 'rgba(6, 182, 212, 0.3)' : 'var(--tprm-border)',
                }}
                title="Toggle synchronized scrolling between left and right panes"
              >
                <ArrowRightLeft size={12} />
                <span>Sync Scroll: {syncScroll ? 'ON' : 'OFF'}</span>
              </button>

              {/* Unmask toggle with authorization confirmation */}
              {currentUser.is_admin && (
                <button
                  onClick={() => {
                    if (!showOriginalValues) {
                      setShowRevealModal(true);
                    } else {
                      setShowOriginalValues(false);
                    }
                  }}
                  className="optiv-btn-header"
                  style={{
                    height: 28,
                    fontSize: '0.725rem',
                    color: showOriginalValues ? 'var(--tprm-rose)' : 'inherit',
                    borderColor: showOriginalValues ? 'rgba(239, 68, 68, 0.3)' : 'var(--tprm-border)',
                  }}
                  title="Restricted action: View unmasked sensitive spans on-screen"
                >
                  <Eye size={12} />
                  <span>{showOriginalValues ? 'Mask Sensitive Spans' : 'Reveal Spans (Authorized)'}</span>
                </button>
              )}

              {/* Explain Run Button */}
              <button
                onClick={() => onOpenAssistant(result.document_id)}
                className="optiv-btn-header"
                style={{ height: 28, fontSize: '0.725rem', backgroundColor: 'var(--tprm-indigo-light)', color: 'var(--tprm-indigo)', borderColor: 'rgba(99, 102, 241, 0.3)' }}
              >
                <HelpCircle size={12} />
                <span>Explain Run</span>
              </button>
            </div>
          </div>

          <div className="comparison-grid">
            {/* A. ORIGINAL INPUT PANE */}
            <div className="viewer-pane">
              <div className="viewer-pane-header">
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <Eye size={15} color="var(--tprm-indigo)" />
                  <span style={{ fontSize: '0.825rem', fontWeight: 700, color: 'var(--tprm-text-primary)' }}>
                    A. ORIGINAL INPUT (Immutable Source)
                  </span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <span className="badge badge-generic" style={{ fontSize: '0.675rem' }}>
                    {result.source_type?.toUpperCase() || 'FILE'}
                  </span>
                  <button
                    onClick={handleDownloadOriginal}
                    className="optiv-btn-header"
                    style={{ height: 26, fontSize: '0.7rem', padding: '0 8px' }}
                    title="Download unmodified original document"
                  >
                    <Download size={11} />
                    <span>Download Original</span>
                  </button>
                </div>
              </div>

              <div
                ref={originalPaneRef}
                onScroll={handleOriginalScroll}
                className="viewer-pane-content"
              >
                {highlightedOriginalElements || (
                  <div style={{ color: 'var(--tprm-text-muted)', padding: 24, textAlign: 'center' }}>
                    No document extracted yet. Run the pipeline above.
                  </div>
                )}
              </div>
            </div>

            {/* B. PROCESSED SANITIZED OUTPUT PANE */}
            <div className="viewer-pane">
              <div className="viewer-pane-header">
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <FileCheck2 size={15} color={result.release_allowed ? 'var(--tprm-emerald)' : 'var(--tprm-rose)'} />
                  <span style={{ fontSize: '0.825rem', fontWeight: 700, color: 'var(--tprm-text-primary)' }}>
                    B. PROCESSED OUTPUT (Sanitized Artifact)
                  </span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <span className={`badge ${result.release_allowed ? 'badge-success' : 'badge-danger'}`} style={{ fontSize: '0.675rem' }}>
                    {result.release_allowed ? 'RELEASE AUTHORIZED' : 'RELEASE WITHHELD'}
                  </span>
                  {result.release_allowed && (
                    <button
                      onClick={handleDownloadArtifact}
                      className="btn-primary"
                      style={{ fontSize: '0.7rem', padding: '3px 8px', display: 'flex', alignItems: 'center', gap: 4 }}
                      title="Download verified, sanitized artifact"
                    >
                      <Download size={11} />
                      <span>Download Sanitized</span>
                    </button>
                  )}
                </div>
              </div>

              <div
                ref={processedPaneRef}
                onScroll={handleProcessedScroll}
                className="viewer-pane-content"
              >
                {result.release_allowed && result.redacted_text ? (
                  <pre style={{ whiteSpace: 'pre-wrap', margin: 0, color: 'var(--tprm-text-primary)', fontFamily: 'var(--font-mono)', fontSize: '0.825rem', lineHeight: 1.6 }}>
                    {result.redacted_text}
                  </pre>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', gap: 14, textAlign: 'center', padding: 24 }}>
                    <div style={{ padding: 16, borderRadius: '50%', backgroundColor: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.3)' }}>
                      <Lock size={32} color="#ef4444" />
                    </div>
                    <div>
                      <h4 style={{ color: 'var(--tprm-rose)', fontSize: '0.95rem', margin: '0 0 6px', fontWeight: 700 }}>
                        Sanitized Document Egress Withheld
                      </h4>
                      <p style={{ fontSize: '0.775rem', color: 'var(--tprm-text-muted)', maxWidth: 380, margin: '0 auto', lineHeight: 1.5 }}>
                        Independent verification status evaluates to <strong style={{ color: 'var(--tprm-rose)' }}>{result.verification_status || 'FAIL'}</strong>. Under the fail-closed barrier, unverified artifacts are permanently blocked from egress.
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
        <div className="optiv-card" style={{ padding: '16px 20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14, flexWrap: 'wrap', gap: 10 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <ShieldAlert size={18} color="var(--tprm-indigo)" />
              <h4 style={{ fontSize: '0.95rem', fontWeight: 700, margin: 0, color: 'var(--tprm-text-primary)' }}>
                Detected PII Findings Inventory ({filteredEntities.length})
              </h4>
            </div>
            <div style={{ display: 'flex', gap: 8 }}>
              <button
                onClick={() => handleDownloadReport('json')}
                className="optiv-btn-header"
                style={{ height: 28, fontSize: '0.725rem' }}
              >
                Export JSON Report
              </button>
              <button
                onClick={() => handleDownloadReport('csv')}
                className="optiv-btn-header"
                style={{ height: 28, fontSize: '0.725rem' }}
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
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.825rem' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--tprm-border)', color: 'var(--tprm-text-muted)', textAlign: 'left', backgroundColor: 'var(--tprm-surface-subtle)' }}>
                    <th style={{ padding: '10px 12px' }}>Category</th>
                    <th style={{ padding: '10px 12px' }}>Span [Start, End)</th>
                    <th style={{ padding: '10px 12px' }}>Confidence</th>
                    <th style={{ padding: '10px 12px' }}>Sensitive Value</th>
                    <th style={{ padding: '10px 12px' }}>Masking Rule</th>
                    <th style={{ padding: '10px 12px' }}>Verification Status</th>
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
                        transition: 'background-color 0.15s ease',
                      }}
                      onClick={() => setSelectedEntityIndex(idx)}
                      onMouseEnter={(e) => {
                        if (selectedEntityIndex !== idx) e.currentTarget.style.backgroundColor = 'var(--tprm-surface-subtle)';
                      }}
                      onMouseLeave={(e) => {
                        if (selectedEntityIndex !== idx) e.currentTarget.style.backgroundColor = 'transparent';
                      }}
                    >
                      <td style={{ padding: '10px 12px' }}>
                        <span className={`badge ${getBadgeClass(ent.type)}`}>{ent.type}</span>
                      </td>
                      <td style={{ padding: '10px 12px', fontFamily: 'var(--font-mono)', fontSize: '0.75rem' }}>
                        [{ent.start}, {ent.end}) ({ent.end - ent.start} chars)
                      </td>
                      <td style={{ padding: '10px 12px' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                          <div style={{ width: 44, height: 5, backgroundColor: 'var(--tprm-border)', borderRadius: 3, overflow: 'hidden' }}>
                            <div style={{ width: `${ent.confidence * 100}%`, height: '100%', backgroundColor: ent.confidence >= 0.9 ? 'var(--tprm-emerald)' : '#f59e0b' }} />
                          </div>
                          <span style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)' }}>
                            {(ent.confidence * 100).toFixed(0)}%
                          </span>
                        </div>
                      </td>
                      <td style={{ padding: '10px 12px', fontFamily: 'var(--font-mono)', color: 'var(--tprm-rose)', fontWeight: 600 }}>
                        {showOriginalValues ? ent.value : '••••••••••••'}
                      </td>
                      <td style={{ padding: '10px 12px', fontFamily: 'var(--font-mono)', color: 'var(--tprm-emerald)' }}>
                        {ent.masked_value}
                      </td>
                      <td style={{ padding: '10px 12px' }}>
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

      {/* Confirmation Modal for Sensitive Spans Reveal */}
      {showRevealModal && (
        <div className="ai-drawer-overlay" onClick={() => setShowRevealModal(false)}>
          <div
            className="optiv-card"
            onClick={(e) => e.stopPropagation()}
            style={{
              width: 480,
              maxWidth: '90vw',
              margin: 'auto',
              padding: 24,
              boxShadow: 'var(--tprm-shadow-lg)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 }}>
              <div style={{ padding: 8, borderRadius: 8, backgroundColor: 'rgba(239, 68, 68, 0.1)', color: 'var(--tprm-rose)' }}>
                <Shield size={20} />
              </div>
              <h3 style={{ margin: 0, fontSize: '1rem', color: 'var(--tprm-text-primary)' }}>
                Authorized Unmasking Confirmation
              </h3>
            </div>

            <p style={{ fontSize: '0.8rem', color: 'var(--tprm-text-muted)', lineHeight: 1.5, margin: '0 0 16px' }}>
              You are requesting to reveal raw, unmasked PII spans on-screen. This action is restricted to authorized Compliance Officers under Cadence Data Governance Policy.
            </p>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10 }}>
              <button
                onClick={() => setShowRevealModal(false)}
                className="optiv-btn-header"
                style={{ height: 34, padding: '0 14px' }}
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  setShowOriginalValues(true);
                  setShowRevealModal(false);
                }}
                className="btn-primary"
                style={{ height: 34, padding: '0 16px', fontSize: '0.8rem', backgroundColor: 'var(--tprm-rose)', borderColor: 'var(--tprm-rose)' }}
              >
                Confirm &amp; Reveal Spans
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
