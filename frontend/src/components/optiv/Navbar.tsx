import React from 'react';
import { ShieldCheck, Moon, Sun, LogOut, User, ArrowLeftRight } from 'lucide-react';
import type { UserProfile } from '../../types';

interface NavbarProps {
  currentUser: UserProfile;
  theme: 'light' | 'dark';
  onToggleTheme: () => void;
  onSwitchPersona: (email: string) => void;
  onLogout: () => void;
  currentView: string;
  isProcessing?: boolean;
  onTogglePlatform: () => void;
  activePlatform: 'pii_workspace' | 'tprm';
}

export const Navbar: React.FC<NavbarProps> = ({
  currentUser,
  theme,
  onToggleTheme,
  onSwitchPersona,
  onLogout,
  currentView,
  isProcessing = false,
  onTogglePlatform,
  activePlatform,
}) => {
  return (
    <header className="optiv-header">
      {/* Brand Identity */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div
            style={{
              background: 'linear-gradient(135deg, #0ea5e9 0%, #6366f1 100%)',
              padding: '6px 8px',
              borderRadius: 8,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <ShieldCheck size={20} color="#ffffff" />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span style={{ fontWeight: 800, fontSize: '1rem', letterSpacing: '-0.02em', color: 'var(--tprm-text-primary)' }}>
                OPTIV
              </span>
              <span className="badge badge-info" style={{ fontSize: '0.65rem', padding: '2px 6px' }}>
                PRIVACY WORKSPACE
              </span>
            </div>
            <div style={{ fontSize: '0.7rem', color: 'var(--tprm-text-muted)', lineHeight: 1 }}>
              Cadence Financial Group & Optiv Security
            </div>
          </div>
        </div>

        <div style={{ height: 24, width: 1, backgroundColor: 'var(--tprm-border)' }} />

        {/* Workspace Context */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: '0.85rem' }}>
          <span style={{ color: 'var(--tprm-text-muted)' }}>Workspace</span>
          <span style={{ color: 'var(--tprm-border-strong)' }}>/</span>
          <span style={{ fontWeight: 600, color: 'var(--tprm-text-primary)', textTransform: 'capitalize' }}>
            {currentView.replace(/_/g, ' ')}
          </span>
        </div>
      </div>

      {/* Center Processing Status */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        {isProcessing ? (
          <div className="badge badge-warning" style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.75rem' }}>
            <span className="pulsing-dot" />
            <span>Multi-Stage Scanning In Progress</span>
          </div>
        ) : (
          <div className="badge badge-success" style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: '0.75rem' }}>
            <span style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--tprm-emerald)' }} />
            <span>Zero-Leakage Gate Active</span>
          </div>
        )}

        {/* Switch Platform Mode (OPTIV vs TPRM) */}
        <button
          onClick={onTogglePlatform}
          className="btn-secondary"
          style={{ fontSize: '0.75rem', padding: '5px 12px', display: 'flex', alignItems: 'center', gap: 6 }}
          title="Toggle between OPTIV Document Privacy and TPRM Risk Governance"
        >
          <ArrowLeftRight size={14} />
          <span>Switch to {activePlatform === 'pii_workspace' ? 'TPRM Platform' : 'OPTIV Privacy'}</span>
        </button>
      </div>

      {/* Right Controls */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        {/* Theme Selector */}
        <button
          onClick={onToggleTheme}
          className="btn-secondary"
          style={{ padding: '6px 10px', borderRadius: 8 }}
          title={`Switch to ${theme === 'dark' ? 'Light' : 'Dark'} theme`}
        >
          {theme === 'dark' ? <Sun size={16} color="#fbbf24" /> : <Moon size={16} color="#64748b" />}
        </button>

        {/* User Persona Selector */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              padding: '4px 10px',
              borderRadius: 8,
              backgroundColor: 'var(--tprm-surface-subtle)',
              border: '1px solid var(--tprm-border)',
              fontSize: '0.8rem',
            }}
          >
            <User size={14} color="var(--tprm-indigo)" />
            <select
              value={currentUser.email}
              onChange={(e) => onSwitchPersona(e.target.value)}
              style={{
                background: 'transparent',
                border: 'none',
                color: 'var(--tprm-text-primary)',
                fontSize: '0.8rem',
                fontWeight: 600,
                cursor: 'pointer',
                outline: 'none',
              }}
            >
              <option value="admin@cadence.com">Daniela Figueroa (Compliance Officer)</option>
              <option value="analyst@cadence.com">Marcus Vance (Privacy Analyst)</option>
              <option value="auditor@cadence.com">Sarah Chen (Control Auditor)</option>
            </select>
          </div>

          <button
            onClick={onLogout}
            className="btn-secondary"
            style={{ padding: '6px 10px', color: 'var(--tprm-rose)' }}
            title="Sign out"
          >
            <LogOut size={15} />
          </button>
        </div>
      </div>
    </header>
  );
};
