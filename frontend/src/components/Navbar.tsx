import React from 'react';
import { Shield, Lock, FileCheck, Activity } from 'lucide-react';

interface NavbarProps {
  backendHealthy: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({ backendHealthy }) => {
  return (
    <header className="glass-panel" style={{ margin: '16px 24px', padding: '14px 24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 16 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
          <div style={{
            background: 'linear-gradient(135deg, #06b6d4 0%, #3b82f6 100%)',
            padding: 10,
            borderRadius: 10,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 0 20px rgba(6, 182, 212, 0.4)'
          }}>
            <Shield size={26} color="#ffffff" />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <h1 style={{ fontSize: '1.25rem', fontWeight: 800, color: '#f8fafc', letterSpacing: '-0.02em' }}>
                PII GUARD
              </h1>
              <span className="badge badge-ip" style={{ fontSize: '0.7rem' }}>ENTERPRISE v1.0.0</span>
            </div>
            <p style={{ fontSize: '0.8rem', color: '#94a3b8', margin: 0 }}>
              Cadence Financial Group — Cyber Strategy & Automated Redaction Release Gate
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: 6,
            background: 'rgba(15, 23, 42, 0.6)',
            padding: '6px 12px',
            borderRadius: 8,
            border: '1px solid rgba(51, 65, 85, 0.5)',
            fontSize: '0.8rem',
            color: '#cbd5e1'
          }}>
            <Lock size={14} color="#06b6d4" />
            <span>Zero-Leakage Policy</span>
          </div>

          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: 6,
            background: 'rgba(15, 23, 42, 0.6)',
            padding: '6px 12px',
            borderRadius: 8,
            border: '1px solid rgba(51, 65, 85, 0.5)',
            fontSize: '0.8rem',
            color: '#cbd5e1'
          }}>
            <FileCheck size={14} color="#10b981" />
            <span>Dual-Key Release Gate</span>
          </div>

          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            background: backendHealthy ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)',
            border: `1px solid ${backendHealthy ? 'rgba(16, 185, 129, 0.4)' : 'rgba(239, 68, 68, 0.4)'}`,
            padding: '6px 14px',
            borderRadius: 20,
            fontSize: '0.75rem',
            fontWeight: 600,
            color: backendHealthy ? '#34d399' : '#f87171'
          }}>
            <span style={{
              width: 8,
              height: 8,
              borderRadius: '50%',
              background: backendHealthy ? '#10b981' : '#ef4444',
              boxShadow: backendHealthy ? '0 0 8px #10b981' : '0 0 8px #ef4444'
            }} />
            <Activity size={14} />
            <span>{backendHealthy ? 'BACKEND ONLINE' : 'DISCONNECTED'}</span>
          </div>
        </div>
      </div>
    </header>
  );
};
