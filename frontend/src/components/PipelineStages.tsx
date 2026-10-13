import React from 'react';
import type { StageTransition } from '../types';
import { CheckCircle2, XCircle, Clock, ShieldAlert, ArrowRight, Layers, FileText } from 'lucide-react';

interface PipelineStagesProps {
  currentStage: string;
  workflowStatus: string;
  stageHistory: StageTransition[];
  totalDuration: number;
}

const LIFECYCLE_STAGES = [
  { name: 'RECEIVED', label: '1. Received', owner: 'M1: Ingestion' },
  { name: 'VALIDATED', label: '2. Validated', owner: 'M1: Validator' },
  { name: 'EXTRACTED', label: '3. Extracted', owner: 'M1: Extractor' },
  { name: 'DETECTED', label: '4. Detected', owner: 'M2: Detection' },
  { name: 'REDACTED', label: '5. Redacted', owner: 'M3: Redaction' },
  { name: 'VERIFIED', label: '6. Verified', owner: 'M3: Verifier' },
  { name: 'RELEASED', label: '7. Released', owner: 'M5: Release Gate' },
];

export const PipelineStages: React.FC<PipelineStagesProps> = ({
  currentStage,
  workflowStatus,
  stageHistory,
  totalDuration,
}) => {
  const getStageIndex = (stageName: string) => {
    return LIFECYCLE_STAGES.findIndex((s) => s.name === stageName);
  };

  const activeIndex = getStageIndex(currentStage);
  const isBlocked = workflowStatus === 'blocked';
  const isFailed = workflowStatus === 'failed';

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      {/* Visual Lifecycle Stepper */}
      <div className="glass-panel" style={{ padding: 24 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <Layers size={20} color="#06b6d4" />
            <h3 style={{ fontSize: '1.1rem', margin: 0 }}>7-Stage Architecture Lifecycle Stepper</h3>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: '0.85rem', color: '#94a3b8' }}>
            <Clock size={16} />
            <span>Cumulative Execution Duration: <strong>{totalDuration.toFixed(4)}s</strong></span>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: 12 }}>
          {LIFECYCLE_STAGES.map((stage, idx) => {
            const isCompleted = activeIndex > idx || (activeIndex === idx && workflowStatus === 'success');
            const isCurrent = activeIndex === idx;
            const isStageBlocked = isCurrent && isBlocked;
            const isStageFailed = isCurrent && isFailed;

            let bgColor = 'rgba(30, 41, 59, 0.4)';
            let borderColor = 'rgba(51, 65, 85, 0.5)';
            let statusIcon = <Clock size={16} color="#64748b" />;
            let textColor = '#64748b';

            if (isCompleted) {
              bgColor = 'rgba(16, 185, 129, 0.12)';
              borderColor = 'rgba(16, 185, 129, 0.4)';
              statusIcon = <CheckCircle2 size={16} color="#10b981" />;
              textColor = '#34d399';
            } else if (isStageBlocked) {
              bgColor = 'rgba(239, 68, 68, 0.15)';
              borderColor = '#ef4444';
              statusIcon = <ShieldAlert size={16} color="#ef4444" />;
              textColor = '#f87171';
            } else if (isStageFailed) {
              bgColor = 'rgba(239, 68, 68, 0.15)';
              borderColor = '#ef4444';
              statusIcon = <XCircle size={16} color="#ef4444" />;
              textColor = '#f87171';
            } else if (isCurrent) {
              bgColor = 'rgba(6, 182, 212, 0.15)';
              borderColor = '#06b6d4';
              statusIcon = <CheckCircle2 size={16} color="#06b6d4" />;
              textColor = '#38bdf8';
            }

            return (
              <div
                key={stage.name}
                style={{
                  background: bgColor,
                  border: `1px solid ${borderColor}`,
                  borderRadius: 10,
                  padding: '12px 14px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 6,
                  transition: 'all 0.2s ease',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: '0.75rem', fontWeight: 700, color: textColor }}>
                    STEP {idx + 1}
                  </span>
                  {statusIcon}
                </div>
                <div style={{ fontWeight: 600, fontSize: '0.9rem', color: '#f1f5f9' }}>
                  {stage.name}
                </div>
                <div style={{ fontSize: '0.7rem', color: '#94a3b8' }}>
                  {stage.owner}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Real-time Transition History Table */}
      <div className="glass-panel" style={{ padding: 24 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <FileText size={20} color="#3b82f6" />
            <h3 style={{ fontSize: '1.1rem', margin: 0 }}>Recorded Transition History (`stage_history`)</h3>
          </div>
          <span className="badge badge-ip">Monotonic State Machine</span>
        </div>

        {stageHistory.length === 0 ? (
          <p style={{ color: '#94a3b8', fontSize: '0.9rem' }}>No stage transitions recorded yet.</p>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.85rem' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--border-color)', color: '#94a3b8' }}>
                  <th style={{ padding: '10px 12px' }}>Step</th>
                  <th style={{ padding: '10px 12px' }}>Transition</th>
                  <th style={{ padding: '10px 12px' }}>Timestamp (UTC)</th>
                  <th style={{ padding: '10px 12px' }}>Stage Duration</th>
                  <th style={{ padding: '10px 12px' }}>State Machine Message</th>
                </tr>
              </thead>
              <tbody>
                {stageHistory.map((t) => (
                  <tr
                    key={t.step}
                    style={{
                      borderBottom: '1px solid rgba(51, 65, 85, 0.3)',
                      transition: 'background 0.15s ease',
                    }}
                  >
                    <td style={{ padding: '10px 12px', fontWeight: 600, color: '#06b6d4' }}>
                      #{t.step}
                    </td>
                    <td style={{ padding: '10px 12px', display: 'flex', alignItems: 'center', gap: 6 }}>
                      <span className="badge badge-generic">{t.from_stage}</span>
                      <ArrowRight size={14} color="#64748b" />
                      <span className={`badge ${
                        t.to_stage === 'RELEASED' ? 'badge-phone' :
                        t.to_stage === 'BLOCKED' || t.to_stage === 'FAILED' ? 'badge-gov' : 'badge-ip'
                      }`}>
                        {t.to_stage}
                      </span>
                    </td>
                    <td style={{ padding: '10px 12px', fontFamily: 'var(--font-mono)', color: '#cbd5e1' }}>
                      {new Date(t.timestamp).toLocaleTimeString([], { hour12: false })}.{new Date(t.timestamp).getMilliseconds().toString().padStart(3, '0')}
                    </td>
                    <td style={{ padding: '10px 12px', fontFamily: 'var(--font-mono)', color: '#f59e0b', fontWeight: 600 }}>
                      {t.duration_sec.toFixed(4)}s
                    </td>
                    <td style={{ padding: '10px 12px', color: '#94a3b8' }}>
                      {t.message}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
