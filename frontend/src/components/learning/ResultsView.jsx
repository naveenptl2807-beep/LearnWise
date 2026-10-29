import React from 'react';
import { Card } from '../common/Card';
import { Button } from '../common/Button';
import { Alert } from '../common/Alert';
import { DifficultyBadge, StatusBadge } from '../common/Badge';
import {
  AwardIcon,
  CheckCircleIcon,
  CloseIcon,
  TrophyIcon,
  ArrowRightIcon,
  RefreshIcon,
  BookOpenIcon,
} from '../common/Icons';

export function ResultsView({
  submissionResults,
  cycle,
  session,
  onGenerateNextCycle,
  isGeneratingNext,
  nextCycleError,
  onClearNextCycleError,
  onReturnDashboard,
}) {
  // If we just submitted, submissionResults has detailed results & next_step
  // If resuming a previously submitted cycle, fall back to cycle.score_percentage
  const score = submissionResults?.score_percentage ?? cycle?.score_percentage ?? 0;
  const correctCount = submissionResults?.correct_count ?? Math.round((score / 100) * 12);
  const totalQuestions = submissionResults?.total_questions ?? 12;
  const isMastered = submissionResults?.is_mastered ?? session?.is_mastered ?? (session?.status === 'MASTERED');
  const nextDifficulty = submissionResults?.next_difficulty ?? session?.current_difficulty ?? 'Beginner';
  const feedback = submissionResults?.feedback ?? (
    isMastered
      ? `Topic '${session?.topic}' is fully mastered! Perfect score on Advanced difficulty.`
      : `You scored ${score}% (${correctCount}/12). Ready to proceed to the next cycle.`
  );
  const resultsList = submissionResults?.results || null;
  const submittedAnswers = cycle?.submitted_answers || null;

  return (
    <div className="results-view">
      {/* Primary Score & Feedback Card */}
      <Card
        padding="2.25rem"
        style={{
          marginBottom: '2rem',
          border: isMastered ? '2px solid #CAD6C2' : '1.5px solid var(--border-subtle)',
          backgroundColor: isMastered ? 'var(--status-mastered-bg)' : 'var(--bg-card)',
        }}
      >
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: '1.25rem',
            marginBottom: '1.5rem',
            borderBottom: `1px solid ${isMastered ? '#CAD6C2' : 'var(--border-subtle)'}`,
            paddingBottom: '1.25rem',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
            <div
              style={{
                width: '48px',
                height: '48px',
                borderRadius: '50%',
                backgroundColor: isMastered ? '#485E40' : 'var(--color-primary)',
                color: '#FFFDFA',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              {isMastered ? <TrophyIcon size={26} /> : <AwardIcon size={26} />}
            </div>

            <div>
              <div style={{ fontSize: '0.8rem', fontWeight: '700', textTransform: 'uppercase', letterSpacing: '0.05em', color: isMastered ? '#485E40' : 'var(--color-primary)' }}>
                {isMastered ? 'Topic Mastery Achieved' : `Cycle #${cycle?.cycle_number} Evaluation`}
              </div>
              <h2 style={{ fontSize: '1.65rem', fontWeight: '700', color: 'var(--text-main)', letterSpacing: '-0.02em' }}>
                {score}% Score ({correctCount} / {totalQuestions} Correct)
              </h2>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <DifficultyBadge difficulty={cycle?.difficulty_level} size="md" />
            <StatusBadge status={isMastered ? 'MASTERED' : 'SUBMITTED'} size="md" />
          </div>
        </div>

        {/* Feedback Message */}
        <p
          style={{
            fontSize: '1.02rem',
            lineHeight: 1.6,
            color: 'var(--text-main)',
            marginBottom: '1.5rem',
          }}
        >
          {feedback}
        </p>

        {/* Adaptive Progression Direction */}
        {!isMastered && (
          <div
            style={{
              padding: '1rem 1.25rem',
              borderRadius: 'var(--radius-md)',
              backgroundColor: 'var(--bg-main)',
              border: '1px solid var(--border-subtle)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              flexWrap: 'wrap',
              gap: '0.75rem',
            }}
          >
            <div>
              <div style={{ fontSize: '0.75rem', fontWeight: '700', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                Next Recommended Difficulty
              </div>
              <div style={{ fontSize: '1rem', fontWeight: '700', color: 'var(--color-primary)' }}>
                {nextDifficulty} Difficulty
              </div>
            </div>

            <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
              Cycle {session?.current_cycle_number ? session.current_cycle_number + 1 : 2} is ready to be generated.
            </div>
          </div>
        )}
      </Card>

      {/* Error Banner when Next Cycle Generation Fails */}
      {nextCycleError && (
        <Alert
          type="error"
          title="Next Cycle Generation Failed"
          message={nextCycleError}
          action={
            <Button
              size="sm"
              variant="outline"
              onClick={onGenerateNextCycle}
              isLoading={isGeneratingNext}
            >
              Retry Generating Cycle
            </Button>
          }
          onClose={onClearNextCycleError}
        />
      )}

      {/* Next Cycle Call to Action Card */}
      <Card
        padding="1.75rem 2rem"
        style={{
          marginBottom: '2.5rem',
          backgroundColor: 'var(--bg-card)',
          border: '1.5px solid var(--border-subtle)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '1rem',
        }}
      >
        <div>
          <h4 style={{ fontSize: '1.2rem', fontWeight: '700', color: 'var(--text-main)' }}>
            {isMastered ? 'Curriculum Complete' : 'Ready for the next learning cycle?'}
          </h4>
          <p style={{ fontSize: '0.88rem', color: 'var(--text-secondary)', marginTop: '0.2rem' }}>
            {isMastered
              ? 'You have fully mastered this topic! You can review past cycles or start a new topic.'
              : `Advance to Cycle ${(session?.current_cycle_number || 1) + 1} at ${nextDifficulty} difficulty.`}
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <Button variant="outline" size="md" onClick={onReturnDashboard}>
            Dashboard
          </Button>

          {!isMastered && (
            <Button
              variant="primary"
              size="lg"
              onClick={onGenerateNextCycle}
              isLoading={isGeneratingNext}
              disabled={isGeneratingNext}
              rightIcon={<ArrowRightIcon size={18} />}
            >
              Generate Next Cycle
            </Button>
          )}
        </div>
      </Card>

      {/* Question-by-Question Review (Available when submissionResults.results is present) */}
      {resultsList && resultsList.length > 0 && (
        <section style={{ marginBottom: '3rem' }}>
          <h3
            style={{
              fontSize: '1.3rem',
              fontWeight: '700',
              color: 'var(--text-main)',
              marginBottom: '1rem',
              letterSpacing: '-0.01em',
            }}
          >
            Question-by-Question Review
          </h3>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            {resultsList.map((res, idx) => {
              const isCorrect = res.is_correct;
              return (
                <Card
                  key={idx}
                  padding="1.5rem 1.75rem"
                  style={{
                    border: `1.5px solid ${isCorrect ? '#CAD6C2' : 'var(--status-error-border)'}`,
                    backgroundColor: isCorrect ? '#FCFDFB' : 'var(--bg-card)',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '1rem', marginBottom: '0.85rem' }}>
                    <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.75rem' }}>
                      <span
                        style={{
                          width: '28px',
                          height: '28px',
                          borderRadius: '50%',
                          backgroundColor: isCorrect ? '#485E40' : '#8E3A3A',
                          color: '#FFFDFA',
                          fontSize: '0.8rem',
                          fontWeight: '700',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          flexShrink: 0,
                          marginTop: '2px',
                        }}
                      >
                        {idx + 1}
                      </span>
                      <h4 style={{ fontSize: '1rem', fontWeight: '600', color: 'var(--text-main)', lineHeight: 1.5 }}>
                        {res.question}
                      </h4>
                    </div>

                    <span
                      style={{
                        padding: '0.2rem 0.6rem',
                        borderRadius: '9999px',
                        fontSize: '0.75rem',
                        fontWeight: '700',
                        backgroundColor: isCorrect ? 'var(--status-mastered-bg)' : 'var(--status-error-bg)',
                        color: isCorrect ? 'var(--status-mastered-text)' : 'var(--status-error-text)',
                        border: `1px solid ${isCorrect ? '#CAD6C2' : 'var(--status-error-border)'}`,
                        flexShrink: 0,
                      }}
                    >
                      {isCorrect ? 'Correct' : 'Incorrect'}
                    </span>
                  </div>

                  <div style={{ paddingLeft: '2.5rem', display: 'flex', flexDirection: 'column', gap: '0.4rem', fontSize: '0.9rem' }}>
                    <div>
                      <span style={{ color: 'var(--text-muted)', marginRight: '0.5rem' }}>Your Answer:</span>
                      <strong style={{ color: isCorrect ? 'var(--status-mastered-text)' : 'var(--status-error-text)' }}>
                        {res.selected_option}
                      </strong>
                    </div>

                    {!isCorrect && (
                      <div>
                        <span style={{ color: 'var(--text-muted)', marginRight: '0.5rem' }}>Correct Answer:</span>
                        <strong style={{ color: 'var(--status-mastered-text)' }}>
                          {res.correct_answer}
                        </strong>
                      </div>
                    )}
                  </div>
                </Card>
              );
            })}
          </div>
        </section>
      )}

      {/* Resumed Cycle: Render user's submitted answers if resultsList not in state */}
      {!resultsList && submittedAnswers && cycle?.quiz && (
        <section style={{ marginBottom: '3rem' }}>
          <h3 style={{ fontSize: '1.25rem', fontWeight: '700', color: 'var(--text-main)', marginBottom: '1rem' }}>
            Submitted Answers for Cycle #{cycle.cycle_number}
          </h3>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {cycle.quiz.map((q, idx) => (
              <Card key={idx} padding="1.25rem 1.5rem">
                <div style={{ fontSize: '0.95rem', fontWeight: '600', color: 'var(--text-main)', marginBottom: '0.5rem' }}>
                  {idx + 1}. {q.question}
                </div>
                <div style={{ fontSize: '0.88rem', color: 'var(--text-secondary)' }}>
                  Selected Answer: <strong style={{ color: 'var(--color-primary)' }}>{submittedAnswers[idx] || 'Not recorded'}</strong>
                </div>
              </Card>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}

