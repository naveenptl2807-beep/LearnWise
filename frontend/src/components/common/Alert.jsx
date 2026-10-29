import React from 'react';
import { AlertCircleIcon, CloseIcon } from './Icons';

export function Alert({
  type = 'error',
  title = '',
  message,
  onClose,
  action,
  className = '',
}) {
  const isError = type === 'error';

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'flex-start',
        gap: '0.85rem',
        padding: '1rem 1.25rem',
        borderRadius: 'var(--radius-md)',
        backgroundColor: isError ? 'var(--status-error-bg)' : 'var(--bg-soft)',
        color: isError ? 'var(--status-error-text)' : 'var(--text-main)',
        border: `1px solid ${isError ? 'var(--status-error-border)' : 'var(--border-subtle)'}`,
        fontSize: '0.92rem',
        lineHeight: 1.5,
        margin: '1rem 0',
      }}
      className={`alert-component ${className}`}
    >
      <div style={{ flexShrink: 0, marginTop: '2px' }}>
        <AlertCircleIcon size={18} />
      </div>
      <div style={{ flex: 1 }}>
        {title && <div style={{ fontWeight: '600', marginBottom: '0.2rem' }}>{title}</div>}
        <div>{message}</div>
        {action && <div style={{ marginTop: '0.5rem' }}>{action}</div>}
      </div>
      {onClose && (
        <button
          onClick={onClose}
          type="button"
          style={{
            background: 'none',
            border: 'none',
            cursor: 'pointer',
            padding: '2px',
            color: 'inherit',
            opacity: 0.7,
          }}
          aria-label="Close notification"
        >
          <CloseIcon size={16} />
        </button>
      )}
    </div>
  );
}

