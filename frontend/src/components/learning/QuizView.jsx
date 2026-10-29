import React, { useState } from 'react';
import { Card } from '../common/Card';
import { Button } from '../common/Button';
import { Alert } from '../common/Alert';
import { CheckCircleIcon, ArrowRightIcon, AlertCircleIcon, AwardIcon } from '../common/Icons';

export function QuizView({
  cycle,
  selectedAnswers = {},
  onSelectAnswer,
  onSubmitQuiz,
  isSubmitting,
  submissionError,
  onClearError,
}) {
  const questions = cycle?.quiz || [];
  const totalQuestions = questions.length;

  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [validationWarning, setValidationWarning] = useState('');

  const answeredCount = Object.keys(selectedAnswers).filter((k) => !!selectedAnswers[k]).length;
  const isAllAnswered = totalQuestions > 0 && answeredCount === totalQuestions;

  const handleSelectOption = (questionIndex, option) => {
    if (isSubmitting) return;
    if (onSelectAnswer) {
      onSelectAnswer(questionIndex, option);
    }
    if (validationWarning) setValidationWarning('');
  };

  const handleAttemptSubmit = () => {
    if (!isAllAnswered) {
      const unansweredIndices = [];
      for (let i = 0; i < totalQuestions; i++) {
        if (!selectedAnswers[i]) unansweredIndices.push(i + 1);
      }
      setValidationWarning(
        `Please answer all 12 questions before submitting. Missing: Question(s) ${unansweredIndices.join(', ')}`
      );
      return;
    }
    setValidationWarning('');
    setShowConfirmModal(true);
  };

  const handleConfirmSubmit = () => {
    setShowConfirmModal(false);
    // Build array ordered 0..11
    const orderedAnswers = [];
    for (let i = 0; i < totalQuestions; i++) {
      orderedAnswers.push({
        question_index: i,
        selected_option: selectedAnswers[i],
      });
    }
    onSubmitQuiz(orderedAnswers);
  };

  return (
    <div className="quiz-view">
      {/* Quiz Progress & Navigation Bar */}
      <Card
        padding="1.25rem 1.75rem"
        style={{
          marginBottom: '2rem',
          backgroundColor: 'var(--bg-card)',
          position: 'sticky',
          top: 'calc(var(--header-height) + 0.5rem)',
          zIndex: 20,
          border: '1.5px solid var(--border-subtle)',
        }}
      >
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            gap: '1rem',
            marginBottom: '0.85rem',
          }}
        >
          <div>
            <div style={{ fontSize: '0.8rem', fontWeight: '700', color: 'var(--color-primary)', textTransform: 'uppercase' }}>
              Cycle #{cycle?.cycle_number} Assessment
            </div>
            <h3 style={{ fontSize: '1.25rem', fontWeight: '700', color: 'var(--text-main)', letterSpacing: '-0.01em' }}>
              Diagnostic Practice Quiz
            </h3>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
            <span
              style={{
                fontSize: '0.88rem',
                fontWeight: '600',
                color: isAllAnswered ? 'var(--status-mastered-text)' : 'var(--text-secondary)',
              }}
            >
              Answered: {answeredCount} / {totalQuestions}
            </span>

            <Button
              variant="primary"
              size="md"
              disabled={!isAllAnswered || isSubmitting}
              isLoading={isSubmitting}
              onClick={handleAttemptSubmit}
              rightIcon={<AwardIcon size={16} />}
            >
              Submit Quiz
            </Button>
          </div>
        </div>

        {/* Question Index Pills Bar */}
        <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap' }}>
          {questions.map((q, idx) => {
            const hasAnswered = !!selectedAnswers[idx];
            return (
              <a
                key={idx}
                href={`#question-${idx}`}
                style={{
                  width: '32px',
                  height: '32px',
                  borderRadius: 'var(--radius-sm)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '0.8rem',
                  fontWeight: '700',
                  textDecoration: 'none',
                  border: `1.5px solid ${hasAnswered ? 'var(--color-primary)' : 'var(--border-subtle)'}`,
                  backgroundColor: hasAnswered ? 'var(--color-primary)' : 'var(--bg-main)',
                  color: hasAnswered ? '#FFFDFA' : 'var(--text-secondary)',
                  transition: 'all 0.15s ease',
                }}
                title={`Jump to Question ${idx + 1} (${hasAnswered ? 'Answered' : 'Unanswered'})`}
              >
                {idx + 1}
              </a>
            );
          })}
        </div>
      </Card>

      {/* Warnings & Errors */}
      {validationWarning && (
        <Alert
          type="error"
          title="Incomplete Submission"
          message={validationWarning}
          onClose={() => setValidationWarning('')}
        />
      )}

      {submissionError && (
        <Alert
          type="error"
          title="Quiz Submission Error"
          message={submissionError}
          onClose={onClearError}
        />
      )}

      {/* 12 MCQ Questions List */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1.75rem', marginBottom: '2.5rem' }}>
        {questions.map((q, qIdx) => {
          const currentSelection = selectedAnswers[qIdx];
          return (
            <Card
              key={qIdx}
              id={`question-${qIdx}`}
              padding="1.75rem"
              style={{
                scrollMarginTop: '160px',
                border: currentSelection ? '1.5px solid var(--border-strong)' : '1px solid var(--border-subtle)',
              }}
            >
              {/* Question Header */}
              <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.85rem', marginBottom: '1.25rem' }}>
                <span
                  style={{
                    backgroundColor: currentSelection ? 'var(--color-primary)' : 'var(--bg-soft)',
                    color: currentSelection ? '#FFFDFA' : 'var(--color-primary)',
                    width: '30px',
                    height: '30px',
                    borderRadius: '50%',
                    fontSize: '0.85rem',
                    fontWeight: '700',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    flexShrink: 0,
                    marginTop: '2px',
                  }}
                >
                  {qIdx + 1}
                </span>

                <div style={{ flex: 1 }}>
                  <h4
                    style={{
                      fontSize: '1.05rem',
                      fontWeight: '600',
                      color: 'var(--text-main)',
                      lineHeight: 1.5,
                    }}
                  >
                    {q.question}
                  </h4>
                </div>
              </div>

              {/* 4 Choices */}
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
                  gap: '0.75rem',
                  paddingLeft: '2.75rem',
                }}
                className="quiz-options-grid"
              >
                {q.options.map((opt, optIdx) => {
                  const isChecked = currentSelection === opt;
                  const optionLetters = ['A', 'B', 'C', 'D'];
                  return (
                    <label
                      key={optIdx}
                      style={{
                        display: 'flex',
                        alignItems: 'flex-start',
                        gap: '0.65rem',
                        padding: '0.85rem 1rem',
                        borderRadius: 'var(--radius-md)',
                        border: `1.5px solid ${isChecked ? 'var(--color-primary)' : 'var(--border-subtle)'}`,
                        backgroundColor: isChecked ? 'var(--bg-soft)' : 'var(--bg-card)',
                        cursor: isSubmitting ? 'not-allowed' : 'pointer',
                        transition: 'all 0.15s ease',
                        userSelect: 'none',
                      }}
                    >
                      <input
                        type="radio"
                        name={`question-${qIdx}`}
                        value={opt}
                        checked={isChecked}
                        disabled={isSubmitting}
                        onChange={() => handleSelectOption(qIdx, opt)}
                        style={{
                          marginTop: '3px',
                          accentColor: 'var(--color-primary)',
                          cursor: 'pointer',
                        }}
                      />
                      <span style={{ fontSize: '0.9rem', color: isChecked ? 'var(--text-main)' : 'var(--text-secondary)', fontWeight: isChecked ? '600' : '400', lineHeight: 1.4 }}>
                        <strong style={{ marginRight: '0.35rem', color: 'var(--color-primary)' }}>
                          {optionLetters[optIdx]}.
                        </strong>
                        {opt}
                      </span>
                    </label>
                  );
                })}
              </div>
            </Card>
          );
        })}
      </div>

      {/* Bottom Submit Trigger */}
      <Card
        padding="1.75rem 2rem"
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          backgroundColor: 'var(--bg-soft)',
          border: '1.5px solid var(--border-subtle)',
          flexWrap: 'wrap',
          gap: '1rem',
        }}
      >
        <div>
          <h4 style={{ fontSize: '1.15rem', fontWeight: '700', color: 'var(--text-main)' }}>
            Completed all questions?
          </h4>
          <p style={{ fontSize: '0.88rem', color: 'var(--text-secondary)' }}>
            {isAllAnswered
              ? 'All 12 questions answered. Ready for server-side evaluation.'
              : `You have answered ${answeredCount} of ${totalQuestions} questions. Answer all 12 to submit.`}
          </p>
        </div>

        <Button
          variant="primary"
          size="lg"
          disabled={!isAllAnswered || isSubmitting}
          isLoading={isSubmitting}
          onClick={handleAttemptSubmit}
          rightIcon={<ArrowRightIcon size={18} />}
        >
          Submit for Grading
        </Button>
      </Card>

      {/* Final Submission Confirmation Dialog */}
      {showConfirmModal && (
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
          onClick={() => setShowConfirmModal(false)}
        >
          <div
            onClick={(e) => e.stopPropagation()}
            style={{
              width: '100%',
              maxWidth: '460px',
              backgroundColor: 'var(--bg-card)',
              borderRadius: 'var(--radius-lg)',
              border: '1.5px solid var(--border-subtle)',
              boxShadow: 'var(--shadow-elevated)',
              padding: '1.75rem',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.65rem', marginBottom: '0.75rem', color: 'var(--color-primary)' }}>
              <CheckCircleIcon size={22} />
              <h3 style={{ fontSize: '1.25rem', fontWeight: '700', color: 'var(--text-main)' }}>
                Confirm Quiz Submission
              </h3>
            </div>

            <p style={{ fontSize: '0.92rem', color: 'var(--text-secondary)', lineHeight: 1.55, marginBottom: '1.5rem' }}>
              You have selected answers for all 12 questions. Once submitted, your quiz will be evaluated against the server-side answer key and difficulty progression will be calculated.
            </p>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
              <Button
                variant="outline"
                size="md"
                onClick={() => setShowConfirmModal(false)}
                disabled={isSubmitting}
              >
                Review Answers
              </Button>
              <Button
                variant="primary"
                size="md"
                isLoading={isSubmitting}
                onClick={handleConfirmSubmit}
              >
                Yes, Submit Now
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

