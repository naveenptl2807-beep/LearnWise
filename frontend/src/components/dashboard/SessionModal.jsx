import React from 'react';
import { Button } from '../common/Button';
import { DifficultyBadge, StatusBadge } from '../common/Badge';
import { CloseIcon, BookOpenIcon, CheckCircleIcon, ArrowRightIcon } from '../common/Icons';

export function SessionModal({ sessionData, onClose, onStartLearning }) {
  if (!sessionData) return null;

  const {
    session_id,
    topic,
    current_difficulty,
    status,
    is_mastered,
    current_cycle_number,
    cycle,
    cycles,
  } = sessionData;

  // If newly created response, cycle is under `cycle`. If retrieved via getSession, cycles is an array.
  const activeCycle = cycle || (cycles && cycles[cycles.length - 1]);

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        backgroundColor: 'rgba(52, 54, 47, 0.45)',
        backdropFilter: 'blur(3px)',
        zIndex: 100,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '1.5rem',
      }}
      onClick={onClose}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        style={{
          width: '100%',
          maxWidth: '680px',
          maxHeight: '90vh',
          backgroundColor: 'var(--bg-card)',
          borderRadius: 'var(--radius-xl)',
          border: '1.5px solid var(--border-subtle)',
          boxShadow: 'var(--shadow-elevated)',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
          animation: 'fadeInModal 0.2s ease',
        }}
      >
        <style>{`
          @keyframes fadeInModal {
            from { opacity: 0; transform: scale(0.97); }
            to { opacity: 1; transform: scale(1); }
          }
        `}</style>

        {/* Modal Header */}
        <div
          style={{
            padding: '1.5rem 1.75rem',
            borderBottom: '1px solid var(--border-subtle)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            backgroundColor: 'var(--bg-main)',
          }}
        >
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '0.25rem' }}>
              <span style={{ fontSize: '0.75rem', fontWeight: '600', color: 'var(--text-muted)' }}>
                SESSION ID: {session_id}
              </span>
              <DifficultyBadge difficulty={current_difficulty} size="sm" />
              <StatusBadge status={status} size="sm" />
            </div>
            <h3
              style={{
                fontSize: '1.35rem',
                fontWeight: '700',
                color: 'var(--text-main)',
                letterSpacing: '-0.01em',
              }}
            >
              {topic}
            </h3>
          </div>

          <button
            type="button"
            onClick={onClose}
            style={{
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              color: 'var(--text-secondary)',
              padding: '6px',
              borderRadius: '50%',
            }}
            aria-label="Close modal"
          >
            <CloseIcon size={20} />
          </button>
        </div>

        {/* Modal Body */}
        <div style={{ padding: '1.75rem', overflowY: 'auto', flex: 1 }}>
          {activeCycle ? (
            <div>
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  fontSize: '0.85rem',
                  fontWeight: '700',
                  color: 'var(--color-primary)',
                  textTransform: 'uppercase',
                  letterSpacing: '0.04em',
                  marginBottom: '0.65rem',
                }}
              >
                <BookOpenIcon size={16} />
                <span>Learning Cycle #{activeCycle.cycle_number} Overview</span>
              </div>

              {/* Explanation Excerpt */}
              <div
                style={{
                  backgroundColor: 'var(--bg-main)',
                  padding: '1.15rem 1.25rem',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--border-subtle)',
                  marginBottom: '1.25rem',
                }}
              >
                <div style={{ fontSize: '0.8rem', fontWeight: '700', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '0.4rem' }}>
                  Lesson Explanation
                </div>
                <p style={{ fontSize: '0.92rem', color: 'var(--text-main)', lineHeight: 1.6 }}>
                  {activeCycle.explanation}
                </p>
              </div>

              {/* Revision Notes Preview */}
              {activeCycle.notes && activeCycle.notes.length > 0 && (
                <div style={{ marginBottom: '1.25rem' }}>
                  <div style={{ fontSize: '0.8rem', fontWeight: '700', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '0.5rem' }}>
                    Key Revision Notes ({activeCycle.notes.length})
                  </div>
                  <ul style={{ paddingLeft: '1.25rem', fontSize: '0.9rem', color: 'var(--text-main)', lineHeight: 1.55 }}>
                    {activeCycle.notes.map((note, idx) => (
                      <li key={idx} style={{ marginBottom: '0.35rem' }}>
                        {note}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Diagnostic Quiz Preview */}
              {activeCycle.quiz && (
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '0.9rem 1.25rem',
                    backgroundColor: 'var(--bg-soft)',
                    borderRadius: 'var(--radius-md)',
                    border: '1px solid var(--border-subtle)',
                    marginBottom: '1.25rem',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                    <div style={{ color: 'var(--color-primary)' }}>
                      <CheckCircleIcon size={20} />
                    </div>
                    <div>
                      <div style={{ fontWeight: '700', fontSize: '0.92rem', color: 'var(--text-main)' }}>
                        Diagnostic Practice Quiz
                      </div>
                      <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
                        Exactly {activeCycle.quiz.length} multiple-choice questions ready
                      </div>
                    </div>
                  </div>
                  <div style={{ fontSize: '0.82rem', fontWeight: '600', color: 'var(--color-primary)' }}>
                    {activeCycle.status === 'SUBMITTED' ? `Scored: ${activeCycle.score_percentage}%` : 'Unsubmitted'}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div style={{ textAlign: 'center', padding: '2rem 0', color: 'var(--text-secondary)' }}>
              No active learning cycle details available.
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div
          style={{
            padding: '1rem 1.75rem',
            borderTop: '1px solid var(--border-subtle)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'flex-end',
            gap: '0.75rem',
            backgroundColor: 'var(--bg-card)',
          }}
        >
          <Button variant="outline" size="md" onClick={onClose}>
            Close
          </Button>

          {onStartLearning && (
            <Button
              variant="primary"
              size="md"
              onClick={() => {
                onClose();
                onStartLearning(sessionData);
              }}
              rightIcon={<ArrowRightIcon size={16} />}
            >
              Enter Lesson & Quiz
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
