import React from 'react';
import { Spinner } from './Spinner';

/**
 * Standardized Button component with multiple variants.
 * Palette:
 * - primary: muted olive (#6B705C)
 * - secondary: soft beige / sand
 * - outline: border with subtle hover
 * - ghost: minimal
 */
export function Button({
  children,
  variant = 'primary',
  size = 'md',
  isLoading = false,
  disabled = false,
  leftIcon = null,
  rightIcon = null,
  className = '',
  type = 'button',
  onClick,
  ...rest
}) {
  const baseStyles = {
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '0.5rem',
    fontWeight: '600',
    borderRadius: 'var(--radius-md)',
    cursor: disabled || isLoading ? 'not-allowed' : 'pointer',
    transition: 'all 0.18s ease',
    border: '1px solid transparent',
    outline: 'none',
    textDecoration: 'none',
    userSelect: 'none',
  };

  const sizeStyles = {
    sm: { padding: '0.4rem 0.85rem', fontSize: '0.85rem' },
    md: { padding: '0.65rem 1.25rem', fontSize: '0.95rem' },
    lg: { padding: '0.85rem 1.6rem', fontSize: '1.05rem' },
  };

  const variantStyles = {
    primary: {
      backgroundColor: disabled ? '#A9ACA0' : 'var(--color-primary)',
      color: '#FFFDFA',
      boxShadow: disabled ? 'none' : '0 2px 6px rgba(107, 112, 92, 0.25)',
    },
    secondary: {
      backgroundColor: 'var(--bg-soft)',
      color: 'var(--text-main)',
      borderColor: 'var(--border-subtle)',
    },
    outline: {
      backgroundColor: 'transparent',
      color: 'var(--color-primary)',
      borderColor: 'var(--border-subtle)',
    },
    ghost: {
      backgroundColor: 'transparent',
      color: 'var(--text-secondary)',
    },
  };

  return (
    <button
      type={type}
      disabled={disabled || isLoading}
      onClick={onClick}
      style={{
        ...baseStyles,
        ...sizeStyles[size],
        ...variantStyles[variant],
      }}
      className={`btn-component ${className}`}
      {...rest}
    >
      {isLoading ? <Spinner size={size === 'sm' ? 14 : 18} color="currentColor" /> : leftIcon}
      <span>{children}</span>
      {!isLoading && rightIcon}
    </button>
  );
}

