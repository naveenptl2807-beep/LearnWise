import React, { useEffect, useState } from 'react';
import { BRANDING } from '../../config/branding';
import {
  AcademicCapIcon,
  GridIcon,
  ClockIcon,
  CheckCircleIcon,
  AlertCircleIcon,
  CloseIcon,
} from '../common/Icons';
import { checkHealth } from '../../services/api';

export function Sidebar({
  currentView,
  onNavigate,
  isMobileOpen,
  onCloseMobile,
}) {
  const [apiStatus, setApiStatus] = useState('checking'); // 'checking' | 'healthy' | 'offline'

  useEffect(() => {
    let isMounted = true;
    checkHealth()
      .then(() => {
        if (isMounted) setApiStatus('healthy');
      })
      .catch(() => {
        if (isMounted) setApiStatus('offline');
      });

    return () => {
      isMounted = false;
    };
  }, []);

  const navItems = [
    {
      id: 'dashboard',
      label: BRANDING.links.dashboard,
      icon: <GridIcon size={18} />,
    },
    {
      id: 'history',
      label: BRANDING.links.history,
      icon: <ClockIcon size={18} />,
    },
  ];

  const handleNavClick = (id) => {
    onNavigate(id);
    if (onCloseMobile) onCloseMobile();
  };

  return (
    <>
      {/* Mobile Backdrop */}
      {isMobileOpen && (
        <div
          onClick={onCloseMobile}
          style={{
            position: 'fixed',
            inset: 0,
            backgroundColor: 'rgba(52, 54, 47, 0.4)',
            zIndex: 40,
            backdropFilter: 'blur(2px)',
          }}
        />
      )}

      <aside
        style={{
          width: 'var(--sidebar-width)',
          backgroundColor: 'var(--bg-card)',
          borderRight: '1px solid var(--border-subtle)',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          padding: '1.75rem 1.25rem',
          position: 'sticky',
          top: 0,
          height: '100vh',
          zIndex: 50,
          transition: 'transform 0.25s ease',
          ...(isMobileOpen
            ? {
                position: 'fixed',
                left: 0,
                transform: 'translateX(0)',
                boxShadow: 'var(--shadow-elevated)',
              }
            : {}),
        }}
        className={`sidebar-nav ${isMobileOpen ? 'mobile-open' : ''}`}
      >
        <div>
          {/* Brand Header */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              marginBottom: '2.25rem',
              paddingLeft: '0.5rem',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <div
                style={{
                  width: '38px',
                  height: '38px',
                  borderRadius: 'var(--radius-md)',
                  backgroundColor: 'var(--color-primary)',
                  color: '#FFFDFA',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  boxShadow: '0 2px 6px rgba(107, 112, 92, 0.25)',
                }}
              >
                <AcademicCapIcon size={22} />
              </div>
              <div>
                <h1
                  style={{
                    fontSize: '1.2rem',
                    fontWeight: '700',
                    color: 'var(--text-main)',
                    letterSpacing: '-0.02em',
                    lineHeight: 1.15,
                  }}
                >
                  {BRANDING.name}
                </h1>
                <span
                  style={{
                    fontSize: '0.72rem',
                    color: 'var(--color-accent)',
                    fontWeight: '600',
                    textTransform: 'uppercase',
                    letterSpacing: '0.05em',
                  }}
                >
                  {BRANDING.creatorBadge}
                </span>
              </div>
            </div>

            {/* Mobile Close Button */}
            {isMobileOpen && (
              <button
                type="button"
                onClick={onCloseMobile}
                style={{
                  background: 'none',
                  border: 'none',
                  cursor: 'pointer',
                  color: 'var(--text-secondary)',
                  padding: '4px',
                }}
              >
                <CloseIcon size={20} />
              </button>
            )}
          </div>

          {/* Navigation Links */}
          <nav style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
            <div
              style={{
                fontSize: '0.72rem',
                textTransform: 'uppercase',
                letterSpacing: '0.08em',
                color: 'var(--text-muted)',
                fontWeight: '700',
                padding: '0 0.75rem 0.5rem',
              }}
            >
              Main Menu
            </div>
            {navItems.map((item) => {
              const isActive = currentView === item.id;
              return (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => handleNavClick(item.id)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.75rem',
                    width: '100%',
                    padding: '0.75rem 0.85rem',
                    borderRadius: 'var(--radius-md)',
                    border: 'none',
                    backgroundColor: isActive ? 'var(--bg-soft)' : 'transparent',
                    color: isActive ? 'var(--color-primary)' : 'var(--text-secondary)',
                    fontWeight: isActive ? '700' : '500',
                    fontSize: '0.92rem',
                    cursor: 'pointer',
                    textAlign: 'left',
                    transition: 'all 0.15s ease',
                  }}
                >
                  <span style={{ color: isActive ? 'var(--color-primary)' : 'var(--text-muted)' }}>
                    {item.icon}
                  </span>
                  <span>{item.label}</span>
                </button>
              );
            })}
          </nav>
        </div>

        {/* System & Connection Status */}
        <div
          style={{
            padding: '1rem',
            backgroundColor: 'var(--bg-main)',
            borderRadius: 'var(--radius-md)',
            border: '1px solid var(--border-subtle)',
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              marginBottom: '0.35rem',
            }}
          >
            <span style={{ fontSize: '0.75rem', fontWeight: '600', color: 'var(--text-secondary)' }}>
              Backend API
            </span>
            <span
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '0.3rem',
                fontSize: '0.72rem',
                fontWeight: '600',
                color:
                  apiStatus === 'healthy'
                    ? 'var(--status-mastered-text)'
                    : apiStatus === 'offline'
                    ? 'var(--status-error-text)'
                    : 'var(--text-muted)',
              }}
            >
              {apiStatus === 'healthy' && <CheckCircleIcon size={12} />}
              {apiStatus === 'offline' && <AlertCircleIcon size={12} />}
              {apiStatus === 'healthy'
                ? 'Online'
                : apiStatus === 'offline'
                ? 'Offline'
                : 'Connecting...'}
            </span>
          </div>
          <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
            FastAPI + SQLite Engine
          </div>
        </div>
      </aside>
    </>
  );
}

