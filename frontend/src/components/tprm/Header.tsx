import React, { useState } from 'react';
import {
  Shield,
  Search,
  Bell,
  Building2,
  ChevronDown,
  CheckCircle2,
} from 'lucide-react';
import type { UserProfile, NotificationItem } from '../../types';

interface HeaderProps {
  currentUser: UserProfile;
  onSwitchUser: (email: string) => void;
  notifications: NotificationItem[];
  onMarkNotificationRead: (id: string) => void;
  onSearch: (query: string) => void;
}

const AVAILABLE_PERSONAS = [
  { email: 'daniela.figueroa@cadence.com', name: 'Daniela Figueroa', role: 'VRM Admin / Legal / Finance' },
  { email: 'bridgett.gatewood@cadence.com', name: 'Bridgett Gatewood', role: 'VRM Admin' },
  { email: 'tamika.oliver@cadence.com', name: 'Tamika Oliver', role: 'VRM Edit / Compliance' },
  { email: 'chris.ott@cadence.com', name: 'Chris Ott', role: 'VRM Edit / Security' },
  { email: 'shimane.smith@cadence.com', name: 'Shimane Smith', role: 'VRM Edit / Legal' },
  { email: 'chris.schmitz@cadence.com', name: 'Chris Schmitz', role: 'VRM Edit / Procurement' },
  { email: 'rob.tilney@cadence.com', name: 'Rob Tilney', role: 'VRM Edit / IT' },
  { email: 'dayo.seton@cadence.com', name: 'Dayo Seton', role: 'Privacy Reviewer' },
  { email: 'security@apexcloud.com', name: 'Apex Cloud Contact', role: 'Vendor Respondent (PVC)' },
];

export const Header: React.FC<HeaderProps> = ({
  currentUser,
  onSwitchUser,
  notifications,
  onMarkNotificationRead,
  onSearch,
}) => {
  const [showUserDropdown, setShowUserDropdown] = useState(false);
  const [showNotifDropdown, setShowNotifDropdown] = useState(false);

  const unreadCount = notifications.filter((n) => !n.is_read).length;

  return (
    <header className="enterprise-header">
      {/* Brand & Organization */}
      <div className="header-brand">
        <div className="logo-badge">
          <Shield className="logo-icon" size={20} />
        </div>
        <div className="brand-text">
          <div className="brand-title">CADENCE TPRM</div>
          <div className="brand-subtitle">OneTrust Architecture • Integrated Risk Management</div>
        </div>
        <div className="org-context-pill">
          <Building2 size={13} className="text-cyan" />
          <span>Cadence Financial Group</span>
        </div>
      </div>

      {/* Global Search */}
      <div className="header-search-bar">
        <Search size={15} className="search-icon" />
        <input
          type="text"
          placeholder="Search third parties, questionnaires, contracts, risk controls (QRC_*)..."
          onChange={(e) => onSearch(e.target.value)}
        />
      </div>

      {/* Action Controls */}
      <div className="header-actions">
        {/* Notifications Popover */}
        <div className="dropdown-container">
          <button
            className={`icon-button ${unreadCount > 0 ? 'has-badge' : ''}`}
            onClick={() => {
              setShowNotifDropdown(!showNotifDropdown);
              setShowUserDropdown(false);
            }}
            title="Notifications & SLA Reminders"
          >
            <Bell size={18} />
            {unreadCount > 0 && <span className="notification-badge">{unreadCount}</span>}
          </button>

          {showNotifDropdown && (
            <div className="popover-menu notifications-menu">
              <div className="popover-header">
                <span>In-App Notifications & SLA Alerts</span>
                <span className="badge badge-info">{unreadCount} Unread</span>
              </div>
              <div className="popover-list">
                {notifications.length === 0 ? (
                  <div className="popover-empty">No notifications yet.</div>
                ) : (
                  notifications.map((n) => (
                    <div
                      key={n.id}
                      className={`notification-item ${n.is_read ? 'read' : 'unread'}`}
                      onClick={() => onMarkNotificationRead(n.id)}
                    >
                      <div className="notif-header">
                        <span className="notif-subject">{n.subject}</span>
                        <span className="notif-time">{new Date(n.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                      </div>
                      <div className="notif-body">{n.body}</div>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
        </div>

        {/* Persona Switcher */}
        <div className="dropdown-container">
          <button
            className="user-profile-button"
            onClick={() => {
              setShowUserDropdown(!showUserDropdown);
              setShowNotifDropdown(false);
            }}
          >
            <div className="user-avatar">
              {currentUser.full_name.charAt(0)}
            </div>
            <div className="user-info-text">
              <span className="user-name">{currentUser.full_name}</span>
              <span className="user-role-badge">
                {currentUser.is_admin ? 'TPRM ADMIN' : currentUser.groups[0] || 'User'}
              </span>
            </div>
            <ChevronDown size={14} />
          </button>

          {showUserDropdown && (
            <div className="popover-menu persona-menu">
              <div className="popover-header">
                <span>Switch Enterprise Persona (Testing RBAC)</span>
              </div>
              <div className="popover-list">
                {AVAILABLE_PERSONAS.map((p) => (
                  <div
                    key={p.email}
                    className={`persona-item ${p.email === currentUser.email ? 'selected' : ''}`}
                    onClick={() => {
                      onSwitchUser(p.email);
                      setShowUserDropdown(false);
                    }}
                  >
                    <div className="persona-info">
                      <div className="persona-name">{p.name}</div>
                      <div className="persona-role">{p.role}</div>
                      <div className="persona-email">{p.email}</div>
                    </div>
                    {p.email === currentUser.email && <CheckCircle2 size={16} className="text-cyan" />}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};
