import React, { useState, useEffect } from 'react';
import { Save, CheckCircle } from 'lucide-react';
import type { UserProfile, SystemSettings } from '../../types';

interface SettingsViewProps {
  currentUser?: UserProfile;
}

export const SettingsView: React.FC<SettingsViewProps> = () => {
  const [settings, setSettings] = useState<SystemSettings | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [savedMessage, setSavedMessage] = useState<string | null>(null);

  useEffect(() => {
    fetch('/api/settings')
      .then((res) => res.json())
      .then((data) => setSettings(data))
      .catch((err) => console.warn('Failed to load settings', err))
      .finally(() => setLoading(false));
  }, []);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!settings) return;
    try {
      const res = await fetch('/api/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settings),
      });
      if (res.ok) {
        setSavedMessage('Settings successfully persisted to server.');
        setTimeout(() => setSavedMessage(null), 3000);
      }
    } catch (err) {
      console.error('Error saving settings', err);
    }
  };

  if (loading || !settings) {
    return <div className="optiv-card">Loading system configuration...</div>;
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      {/* Header */}
      <div className="optiv-card">
        <h2 style={{ fontSize: '1.25rem', fontWeight: 700, margin: 0, color: 'var(--tprm-text-primary)' }}>
          Governance Policy & System Threshold Configuration
        </h2>
        <p style={{ fontSize: '0.8rem', color: 'var(--tprm-text-muted)', margin: '4px 0 0' }}>
          Configurable detection sensitivities, release gating barriers, and audit retention policies.
        </p>
      </div>

      {savedMessage && (
        <div style={{ padding: '10px 16px', borderRadius: 6, backgroundColor: 'rgba(16, 185, 129, 0.1)', border: '1px solid var(--tprm-emerald)', color: 'var(--tprm-emerald)', fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: 8 }}>
          <CheckCircle size={16} />
          <span>{savedMessage}</span>
        </div>
      )}

      <form onSubmit={handleSave} className="optiv-card" style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 16 }}>
          {/* Zero Leakage Mandate */}
          <div style={{ padding: 14, borderRadius: 8, backgroundColor: 'var(--tprm-surface-subtle)', border: '1px solid var(--tprm-border)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
              <label style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--tprm-text-primary)' }}>
                Zero-Leakage Mandate
              </label>
              <input
                type="checkbox"
                checked={settings.zero_leakage_mandate}
                onChange={(e) => setSettings({ ...settings, zero_leakage_mandate: e.target.checked })}
              />
            </div>
            <p style={{ fontSize: '0.725rem', color: 'var(--tprm-text-muted)', margin: 0 }}>
              Enforces strict fail-closed gating: unverified documents cannot be egressed to downstream models.
            </p>
          </div>

          {/* Minimum Structure Score */}
          <div style={{ padding: 14, borderRadius: 8, backgroundColor: 'var(--tprm-surface-subtle)', border: '1px solid var(--tprm-border)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
              <label style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--tprm-text-primary)' }}>
                Structure Score Threshold
              </label>
              <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700 }}>
                {(settings.minimum_structure_score * 100).toFixed(0)}%
              </span>
            </div>
            <input
              type="range"
              min="0.5"
              max="0.95"
              step="0.05"
              value={settings.minimum_structure_score}
              onChange={(e) => setSettings({ ...settings, minimum_structure_score: parseFloat(e.target.value) })}
              style={{ width: '100%', marginBottom: 6 }}
            />
            <p style={{ fontSize: '0.725rem', color: 'var(--tprm-text-muted)', margin: 0 }}>
              Minimum layout retention ratio (Optiv Case Study requires no less than 80%).
            </p>
          </div>

          {/* Detector Confidence Threshold */}
          <div style={{ padding: 14, borderRadius: 8, backgroundColor: 'var(--tprm-surface-subtle)', border: '1px solid var(--tprm-border)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
              <label style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--tprm-text-primary)' }}>
                Detector Confidence Threshold
              </label>
              <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700 }}>
                {(settings.confidence_threshold * 100).toFixed(0)}%
              </span>
            </div>
            <input
              type="range"
              min="0.3"
              max="0.9"
              step="0.05"
              value={settings.confidence_threshold}
              onChange={(e) => setSettings({ ...settings, confidence_threshold: parseFloat(e.target.value) })}
              style={{ width: '100%', marginBottom: 6 }}
            />
            <p style={{ fontSize: '0.725rem', color: 'var(--tprm-text-muted)', margin: 0 }}>
              Spans below this threshold are flagged for manual review or conservative redaction.
            </p>
          </div>

          {/* OCR Confidence Threshold */}
          <div style={{ padding: 14, borderRadius: 8, backgroundColor: 'var(--tprm-surface-subtle)', border: '1px solid var(--tprm-border)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
              <label style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--tprm-text-primary)' }}>
                OCR Confidence Threshold
              </label>
              <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700 }}>
                {settings.ocr_confidence_threshold.toFixed(0)}%
              </span>
            </div>
            <input
              type="range"
              min="40"
              max="80"
              step="5"
              value={settings.ocr_confidence_threshold}
              onChange={(e) => setSettings({ ...settings, ocr_confidence_threshold: parseFloat(e.target.value) })}
              style={{ width: '100%', marginBottom: 6 }}
            />
            <p style={{ fontSize: '0.725rem', color: 'var(--tprm-text-muted)', margin: 0 }}>
              Trigger image enhancement preprocessing when OCR confidence dips below this mark.
            </p>
          </div>
        </div>

        {/* AI Explanation Mode */}
        <div style={{ padding: 14, borderRadius: 8, backgroundColor: 'var(--tprm-surface-subtle)', border: '1px solid var(--tprm-border)' }}>
          <label style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--tprm-text-primary)', display: 'block', marginBottom: 6 }}>
            AI Explanation Agent Engine Mode:
          </label>
          <select
            value={settings.ai_explanation_mode}
            onChange={(e) => setSettings({ ...settings, ai_explanation_mode: e.target.value })}
            style={{
              padding: '8px 12px',
              borderRadius: 6,
              border: '1px solid var(--tprm-border)',
              backgroundColor: 'var(--tprm-surface)',
              color: 'var(--tprm-text-primary)',
              fontSize: '0.85rem',
              width: '100%',
              maxWidth: 400,
            }}
          >
            <option value="DETERMINISTIC_EVIDENCE_GROUNDED">
              Deterministic Evidence-Grounded Engine (No External Cloud API Key Required)
            </option>
            <option value="HYBRID_LLM_EVALUATION">
              Hybrid LLM Assistant (Sanitized Telemetry Only)
            </option>
          </select>
        </div>

        {/* Supported Formats Display */}
        <div style={{ padding: 14, borderRadius: 8, backgroundColor: 'var(--tprm-surface-subtle)', border: '1px solid var(--tprm-border)' }}>
          <label style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--tprm-text-primary)', display: 'block', marginBottom: 6 }}>
            Registered Document Formats:
          </label>
          <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
            {settings.supported_formats.map((fmt) => (
              <span key={fmt} className="badge badge-generic" style={{ fontWeight: 600 }}>
                {fmt.toUpperCase()}
              </span>
            ))}
          </div>
        </div>

        <button
          type="submit"
          className="btn-primary"
          style={{ alignSelf: 'flex-start', padding: '8px 18px', display: 'flex', alignItems: 'center', gap: 8 }}
        >
          <Save size={15} />
          <span>Save Governance Policies</span>
        </button>
      </form>
    </div>
  );
};
