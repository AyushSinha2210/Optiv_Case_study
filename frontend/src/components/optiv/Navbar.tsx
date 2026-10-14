import React from 'react';
import {
  ShieldCheck,
  Moon,
  Sun,
  ArrowLeftRight,
  FileCheck2,
  AlertOctagon,
  Sparkles,
} from 'lucide-react';
import type { ProcessResponse } from '../../types';

interface NavbarProps {
  theme: 'light' | 'dark';
  onToggleTheme: () => void;
  currentView: string;
  activeDocument?: ProcessResponse | null;
  isProcessing?: boolean;
  onTogglePlatform: () => void;
  activePlatform: 'pii_workspace' | 'tprm';
}

export const Navbar: React.FC<NavbarProps> = ({
  theme,
  onToggleTheme,
  currentView,
  activeDocument,
  isProcessing = false,
  onTogglePlatform,
  activePlatform,
}) => {
  // Compute display name of current view
  const viewTitle = currentView.replace(/_/g, ' ');

  return (
    <header className="optiv-header">
      {/* Left: Brand Identity & Breadcrumb */}
      <div className="optiv-header-left">
        <div className="optiv-brand-group">
          <div className="optiv-logo-badge">
            <ShieldCheck size={18} color="#ffffff" strokeWidth={2.5} />
          </div>
          <div className="optiv-brand-text">
            <div className="optiv-brand-title">
              <span>OPTIV</span>
              <span className="optiv-workspace-pill">PRIVACY WORKSPACE</span>
            </div>
            <div className="optiv-brand-sub">Cadence Financial Group & Optiv Security</div>
          </div>
        </div>

        <div className="optiv-header-divider" />

        {/* Breadcrumb Context */}
        <div className="optiv-breadcrumb">
          <span className="optiv-breadcrumb-root">Workspace</span>
          <span className="optiv-breadcrumb-sep">/</span>
          <span className="optiv-breadcrumb-active">{viewTitle}</span>
        </div>
      </div>

      {/* Center: Dynamic Active Document & Gate Telemetry */}
      <div className="optiv-header-center">
        {isProcessing ? (
          <div className="optiv-status-pill processing">
            <span className="pulsing-dot" />
            <span>Scanning In Progress</span>
          </div>
        ) : activeDocument ? (
          <div className={`optiv-status-pill ${activeDocument.release_allowed ? 'passed' : 'blocked'}`}>
            {activeDocument.release_allowed ? (
              <FileCheck2 size={14} className="text-emerald" />
            ) : (
              <AlertOctagon size={14} className="text-rose" />
            )}
            <span className="optiv-status-docname">
              Doc: {activeDocument.document_id.slice(0, 16)}...
            </span>
            <span className="optiv-status-dot">•</span>
            <span className="optiv-status-verdict">
              {activeDocument.release_allowed ? 'Zero-Leakage PASS' : 'Gate BLOCKED'}
            </span>
          </div>
        ) : (
          <div className="optiv-status-pill idle">
            <span className="optiv-idle-dot" />
            <span>Zero-Leakage Fail-Closed Gate Active</span>
          </div>
        )}
      </div>

      {/* Right: Controls & Active Operator Badge */}
      <div className="optiv-header-right">
        {/* Switch Platform Mode (OPTIV vs TPRM) */}
        <button
          onClick={onTogglePlatform}
          className="optiv-btn-header"
          title="Toggle between OPTIV Document Privacy and TPRM Risk Governance"
        >
          <ArrowLeftRight size={14} />
          <span>Switch to {activePlatform === 'pii_workspace' ? 'TPRM Platform' : 'OPTIV Privacy'}</span>
        </button>

        {/* Theme Selector */}
        <button
          onClick={onToggleTheme}
          className="optiv-btn-header icon-only"
          title={`Switch to ${theme === 'dark' ? 'Light' : 'Dark'} theme`}
          aria-label="Toggle Theme"
        >
          {theme === 'dark' ? <Sun size={15} color="#fbbf24" /> : <Moon size={15} color="#64748b" />}
        </button>

        {/* Clean System Session Indicator - No account switching or predefined accounts */}
        <div className="optiv-session-badge" title="Active Security & Privacy Operator Session">
          <Sparkles size={13} color="var(--tprm-cyan)" />
          <span>Authorized Operator</span>
        </div>
      </div>
    </header>
  );
};
