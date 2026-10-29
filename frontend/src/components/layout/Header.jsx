import React from 'react';
import { MenuIcon, AcademicCapIcon } from '../common/Icons';

export function Header({ onOpenMobileMenu }) {
  return (
    <header
      style={{
        height: 'var(--header-height)',
        backgroundColor: 'var(--bg-card)',
        borderBottom: '1px solid var(--border-subtle)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 2rem',
        position: 'sticky',
        top: 0,
        zIndex: 30,
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
        {/* Mobile Hamburger */}
        <button
          type="button"
          onClick={onOpenMobileMenu}
          style={{
            display: 'none',
            background: 'none',
            border: 'none',
            cursor: 'pointer',
            color: 'var(--text-main)',
            padding: '4px',
          }}
          className="mobile-hamburger"
          aria-label="Open navigation menu"
        >
          <MenuIcon size={22} />
        </button>

        <div>
          <h2
            style={{
              fontSize: '1.05rem',
              fontWeight: '700',
              color: 'var(--text-main)',
              letterSpacing: '-0.01em',
            }}
          >
            Welcome back, Scholar
          </h2>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
            Generate adaptive lessons and test your mastery
          </p>
        </div>
      </div>

      {/* User Avatar Placeholder */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'flex-end',
          }}
          className="header-user-meta"
        >
          <span style={{ fontSize: '0.85rem', fontWeight: '600', color: 'var(--text-main)' }}>
            Student Learner
          </span>
          <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
            Active Session
          </span>
        </div>
        <div
          style={{
            width: '38px',
            height: '38px',
            borderRadius: '50%',
            backgroundColor: 'var(--bg-soft)',
            border: '1.5px solid var(--border-subtle)',
            color: 'var(--color-primary)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontWeight: '700',
            fontSize: '0.85rem',
          }}
          title="Student Profile"
        >
          SL
        </div>
      </div>
    </header>
  );
}

