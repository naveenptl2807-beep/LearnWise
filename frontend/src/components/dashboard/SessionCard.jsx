import React from 'react';
import { Card } from '../common/Card';
import { DifficultyBadge, StatusBadge } from '../common/Badge';
import { BookOpenIcon, ClockIcon, ArrowRightIcon } from '../common/Icons';

export function SessionCard({ session, onSelect }) {
  const formatDate = (isoString) => {
    if (!isoString) return 'Recently';
    try {
      const date = new Date(isoString);
      return date.toLocaleDateString(undefined, {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return isoString;
    }
  };

  return (
    <Card
      padding="1.25rem 1.5rem"
      hoverable
      onClick={() => onSelect && onSelect(session)}
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: '1rem',
        marginBottom: '0.85rem',
      }}
    >
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', marginBottom: '0.35rem', flexWrap: 'wrap' }}>
          <h4
            style={{
              fontSize: '1.05rem',
              fontWeight: '700',
              color: 'var(--text-main)',
              letterSpacing: '-0.01em',
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
            }}
          >
            {session.topic}
          </h4>
          <DifficultyBadge difficulty={session.current_difficulty} size="sm" />
          <StatusBadge status={session.status} size="sm" />
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.35rem' }}>
            <BookOpenIcon size={14} />
            <span>Cycle {session.current_cycle_number}</span>
          </span>
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.35rem' }}>
            <ClockIcon size={14} />
            <span>{formatDate(session.updated_at || session.created_at)}</span>
          </span>
        </div>
      </div>

      <div style={{ flexShrink: 0, color: 'var(--color-primary)' }}>
        <ArrowRightIcon size={18} />
      </div>
    </Card>
  );
}

