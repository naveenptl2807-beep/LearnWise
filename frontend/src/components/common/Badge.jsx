import React from 'react';

export function Badge({
  children,
  type = 'default',
  size = 'md',
  className = '',
}) {
  const getBadgeStyle = () => {
    switch (type) {
      case 'beginner':
        return {
          backgroundColor: '#EBE5D8',
          color: '#524F43',
          border: '1px solid #DDD4C2',
        };
      case 'intermediate':
        return {
          backgroundColor: '#E8E1D0',
          color: '#585547',
          border: '1px solid #D6CCB8',
        };
      case 'advanced':
        return {
          backgroundColor: '#DFD8C8',
          color: '#46443A',
          border: '1px solid #CBC0AA',
        };
      case 'mastered':
        return {
          backgroundColor: 'var(--status-mastered-bg)',
          color: 'var(--status-mastered-text)',
          border: '1px solid #CAD6C2',
        };
      case 'in-progress':
        return {
          backgroundColor: 'var(--status-in-progress-bg)',
          color: 'var(--status-in-progress-text)',
          border: '1px solid #E2D7C3',
        };
      case 'error':
        return {
          backgroundColor: 'var(--status-error-bg)',
          color: 'var(--status-error-text)',
          border: '1px solid var(--status-error-border)',
        };
      default:
        return {
          backgroundColor: 'var(--bg-soft)',
          color: 'var(--text-secondary)',
          border: '1px solid var(--border-subtle)',
        };
    }
  };

  const sizeStyles = {
    sm: { padding: '0.15rem 0.5rem', fontSize: '0.75rem' },
    md: { padding: '0.25rem 0.65rem', fontSize: '0.8rem' },
  };

  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '0.35rem',
        borderRadius: '9999px',
        fontWeight: '600',
        lineHeight: 1.2,
        letterSpacing: '0.01em',
        ...sizeStyles[size],
        ...getBadgeStyle(),
      }}
      className={`badge-component ${className}`}
    >
      {children}
    </span>
  );
}

/**
 * Convenient helper for rendering difficulty tier badges
 */
export function DifficultyBadge({ difficulty, size = 'md' }) {
  const norm = (difficulty || '').toLowerCase();
  const typeMap = {
    beginner: 'beginner',
    intermediate: 'intermediate',
    advanced: 'advanced',
  };
  return (
    <Badge type={typeMap[norm] || 'default'} size={size}>
      {difficulty || 'Beginner'}
    </Badge>
  );
}

/**
 * Convenient helper for rendering session status badges
 */
export function StatusBadge({ status, size = 'md' }) {
  const isMastered = status === 'MASTERED';
  return (
    <Badge type={isMastered ? 'mastered' : 'in-progress'} size={size}>
      {isMastered ? 'Mastered' : 'In Progress'}
    </Badge>
  );
}

