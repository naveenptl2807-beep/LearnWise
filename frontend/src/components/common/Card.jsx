import React from 'react';

export function Card({
  children,
  className = '',
  style = {},
  onClick,
  hoverable = false,
  padding = '1.5rem',
}) {
  return (
    <div
      onClick={onClick}
      style={{
        backgroundColor: 'var(--bg-card)',
        borderRadius: 'var(--radius-lg)',
        border: '1px solid var(--border-subtle)',
        boxShadow: 'var(--shadow-card)',
        padding,
        transition: 'all 0.2s ease',
        cursor: onClick ? 'pointer' : 'default',
        ...(hoverable && {
          ':hover': {
            borderColor: 'var(--border-strong)',
            boxShadow: 'var(--shadow-elevated)',
          },
        }),
        ...style,
      }}
      className={`card-component ${className}`}
    >
      {children}
    </div>
  );
}

