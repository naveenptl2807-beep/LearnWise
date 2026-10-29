import React from 'react';
import { Button } from '../common/Button';
import { DifficultyBadge, StatusBadge } from '../common/Badge';
import { ArrowLeftIcon, BookOpenIcon, CheckCircleIcon, AwardIcon } from '../common/Icons';

export function LearningHeader({
  session,
  activeCycleNumber,
  onSelectCycleNumber,
  activeTab,
  onSelectTab,
  onBack,
  hasResults,
}) {
  if (!session) return null;

  const cycles = session.cycles || [];
  const currentDifficulty = session.current_difficulty || 'Beginner';
  const isMastered = session.status === 'MASTERED';

  return (
    <div
      style={{
        backgroundColor: 'var(--bg-card)',
        borderRadius: 'var(--radius-lg)',
        border: '1px solid var(--border-subtle)',
        boxShadow: 'var(--shadow-card)',
        padding: '1.5rem 1.75rem',
        marginBottom: '2rem',
      }}
    >
      {/* Top Bar: Back & Status */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: '1rem',
          flexWrap: 'wrap',
          gap: '0.75rem',
        }}
      >
        <Button
          variant="ghost"
          size="sm"
          onClick={onBack}
          leftIcon={<ArrowLeftIcon size={16} />}
        >
          Exit to Dashboard
        </Button>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
          <DifficultyBadge difficulty={currentDifficulty} size="sm" />
          <StatusBadge status={session.status} size="sm" />
        </div>
      </div>

      {/* Topic Title */}
      <div style={{ marginBottom: '1.25rem' }}>
        <span
          style={{
            fontSize: '0.75rem',
            fontWeight: '700',
            textTransform: 'uppercase',
            letterSpacing: '0.06em',
            color: 'var(--color-accent)',
            display: 'block',
            marginBottom: '0.2rem',
          }}
        >
          Active Learning Curriculum
        </span>
        <h1
          style={{
            fontSize: '1.75rem',
            fontWeight: '700',
            color: 'var(--text-main)',
            letterSpacing: '-0.02em',
            lineHeight: 1.25,
          }}
        >
          {session.topic}
        </h1>
      </div>

      {/* Cycle Navigation Tabs (if multiple cycles exist) */}
      {cycles.length > 1 && (
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            paddingBottom: '1rem',
            marginBottom: '1rem',
            borderBottom: '1px solid var(--border-subtle)',
            overflowX: 'auto',
          }}
        >
          <span style={{ fontSize: '0.8rem', fontWeight: '600', color: 'var(--text-muted)', marginRight: '0.5rem' }}>
            Cycles:
          </span>
          {cycles.map((c) => {
            const isSelected = c.cycle_number === activeCycleNumber;
            const isSubmitted = c.status === 'SUBMITTED';
            return (
              <button
                key={c.cycle_number}
                type="button"
                onClick={() => onSelectCycleNumber(c.cycle_number)}
                style={{
                  padding: '0.35rem 0.85rem',
                  borderRadius: 'var(--radius-md)',
                  border: `1.5px solid ${isSelected ? 'var(--color-primary)' : 'var(--border-subtle)'}`,
                  backgroundColor: isSelected ? 'var(--bg-soft)' : 'transparent',
                  color: isSelected ? 'var(--color-primary)' : 'var(--text-secondary)',
                  fontWeight: isSelected ? '700' : '500',
                  fontSize: '0.82rem',
                  cursor: 'pointer',
                  transition: 'all 0.15s ease',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.4rem',
                }}
              >
                <span>Cycle {c.cycle_number}</span>
                {isSubmitted && (
                  <span style={{ fontSize: '0.72rem', opacity: 0.8 }}>
                    ({c.score_percentage !== null && c.score_percentage !== undefined ? `${c.score_percentage}%` : 'Done'})
                  </span>
                )}
              </button>
            );
          })}
        </div>
      )}

      {/* Workflow Tabs: Lesson vs Quiz vs Results */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem' }}>
        <button
          type="button"
          onClick={() => onSelectTab('lesson')}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '0.45rem',
            padding: '0.6rem 1.15rem',
            borderRadius: 'var(--radius-md)',
            border: `1.5px solid ${activeTab === 'lesson' ? 'var(--color-primary)' : 'transparent'}`,
            backgroundColor: activeTab === 'lesson' ? 'var(--bg-soft)' : 'transparent',
            color: activeTab === 'lesson' ? 'var(--color-primary)' : 'var(--text-secondary)',
            fontWeight: activeTab === 'lesson' ? '700' : '600',
            fontSize: '0.9rem',
            cursor: 'pointer',
            transition: 'all 0.15s ease',
          }}
        >
          <BookOpenIcon size={16} />
          <span>1. Lesson & Notes</span>
        </button>

        <button
          type="button"
          onClick={() => onSelectTab('quiz')}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '0.45rem',
            padding: '0.6rem 1.15rem',
            borderRadius: 'var(--radius-md)',
            border: `1.5px solid ${activeTab === 'quiz' ? 'var(--color-primary)' : 'transparent'}`,
            backgroundColor: activeTab === 'quiz' ? 'var(--bg-soft)' : 'transparent',
            color: activeTab === 'quiz' ? 'var(--color-primary)' : 'var(--text-secondary)',
            fontWeight: activeTab === 'quiz' ? '700' : '600',
            fontSize: '0.9rem',
            cursor: 'pointer',
            transition: 'all 0.15s ease',
          }}
        >
          <CheckCircleIcon size={16} />
          <span>2. Practice Quiz (12 MCQs)</span>
        </button>

        {hasResults && (
          <button
            type="button"
            onClick={() => onSelectTab('results')}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.45rem',
              padding: '0.6rem 1.15rem',
              borderRadius: 'var(--radius-md)',
              border: `1.5px solid ${activeTab === 'results' ? 'var(--color-primary)' : 'transparent'}`,
              backgroundColor: activeTab === 'results' ? 'var(--bg-soft)' : 'transparent',
              color: activeTab === 'results' ? 'var(--color-primary)' : 'var(--text-secondary)',
              fontWeight: activeTab === 'results' ? '700' : '600',
              fontSize: '0.9rem',
              cursor: 'pointer',
              transition: 'all 0.15s ease',
            }}
          >
            <AwardIcon size={16} />
            <span>3. Quiz Results & Progression</span>
          </button>
        )}
      </div>
    </div>
  );
}

