import React, { useState } from 'react';
import { Card } from '../common/Card';
import { Button } from '../common/Button';
import { Alert } from '../common/Alert';
import { SparklesIcon, ArrowRightIcon } from '../common/Icons';
import { createSession } from '../../services/api';

const DIFFICULTIES = [
  {
    id: 'Beginner',
    label: 'Beginner',
    description: 'Foundations & Core Concepts',
  },
  {
    id: 'Intermediate',
    label: 'Intermediate',
    description: 'Practical Application & Architecture',
  },
  {
    id: 'Advanced',
    label: 'Advanced',
    description: 'Deep Internals & Edge Cases',
  },
];

export function TopicInputCard({ onSessionCreated }) {
  const [topic, setTopic] = useState('');
  const [difficulty, setDifficulty] = useState('Beginner');
  const [isLoading, setIsLoading] = useState(false);
  const [validationError, setValidationError] = useState('');
  const [apiError, setApiError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setValidationError('');
    setApiError(null);

    const cleanTopic = topic.trim();
    if (!cleanTopic) {
      setValidationError('Please enter a learning topic to begin.');
      return;
    }
    if (cleanTopic.length > 255) {
      setValidationError('Topic name is too long (maximum 255 characters).');
      return;
    }

    setIsLoading(true);
    try {
      const response = await createSession({
        topic: cleanTopic,
        initial_difficulty: difficulty,
      });
      // Reset input on success
      setTopic('');
      if (onSessionCreated) {
        onSessionCreated(response);
      }
    } catch (err) {
      setApiError(err.message || 'Failed to start learning session. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Card padding="2rem" style={{ marginBottom: '2.5rem', border: '1.5px solid var(--border-subtle)' }}>
      <div style={{ marginBottom: '1.5rem' }}>
        <div style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem', color: 'var(--color-primary)', fontWeight: '700', fontSize: '0.82rem', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.35rem' }}>
          <SparklesIcon size={16} />
          <span>Adaptive Curriculum Generator</span>
        </div>
        <h2 style={{ fontSize: '1.65rem', fontWeight: '700', color: 'var(--text-main)', letterSpacing: '-0.02em', lineHeight: 1.25 }}>
          What would you like to master today?
        </h2>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem', marginTop: '0.4rem' }}>
          Enter any subject or skill. Our AI tutor will generate an adaptive lesson, concise revision notes, and a 12-question diagnostic quiz tailored to your level.
        </p>
      </div>

      <form onSubmit={handleSubmit}>
        {/* Topic Input Field */}
        <div style={{ marginBottom: '1.5rem' }}>
          <label
            htmlFor="topic-input"
            style={{
              display: 'block',
              fontSize: '0.85rem',
              fontWeight: '600',
              color: 'var(--text-main)',
              marginBottom: '0.5rem',
            }}
          >
            Learning Topic
          </label>
          <input
            id="topic-input"
            type="text"
            value={topic}
            onChange={(e) => {
              setTopic(e.target.value);
              if (validationError) setValidationError('');
            }}
            placeholder="e.g. Binary Search Trees, Rust Ownership, System Design, Quantum Computing..."
            disabled={isLoading}
            style={{
              width: '100%',
              padding: '0.85rem 1.15rem',
              borderRadius: 'var(--radius-md)',
              border: `1.5px solid ${validationError ? 'var(--status-error-border)' : 'var(--border-subtle)'}`,
              backgroundColor: '#FFFFFF',
              color: 'var(--text-main)',
              fontSize: '1rem',
              outline: 'none',
              transition: 'border-color 0.15s ease',
            }}
            onFocus={(e) => (e.target.style.borderColor = 'var(--color-primary)')}
            onBlur={(e) => (e.target.style.borderColor = validationError ? 'var(--status-error-border)' : 'var(--border-subtle)')}
          />
          {validationError && (
            <div style={{ color: 'var(--status-error-text)', fontSize: '0.82rem', marginTop: '0.35rem', fontWeight: '500' }}>
              {validationError}
            </div>
          )}
        </div>

        {/* Difficulty Selection */}
        <div style={{ marginBottom: '1.75rem' }}>
          <label
            style={{
              display: 'block',
              fontSize: '0.85rem',
              fontWeight: '600',
              color: 'var(--text-main)',
              marginBottom: '0.65rem',
            }}
          >
            Target Starting Difficulty
          </label>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
              gap: '0.85rem',
            }}
          >
            {DIFFICULTIES.map((tier) => {
              const isSelected = difficulty === tier.id;
              return (
                <button
                  key={tier.id}
                  type="button"
                  disabled={isLoading}
                  onClick={() => setDifficulty(tier.id)}
                  style={{
                    padding: '0.85rem 1rem',
                    borderRadius: 'var(--radius-md)',
                    border: `1.5px solid ${isSelected ? 'var(--color-primary)' : 'var(--border-subtle)'}`,
                    backgroundColor: isSelected ? 'var(--bg-soft)' : 'var(--bg-card)',
                    textAlign: 'left',
                    cursor: isLoading ? 'not-allowed' : 'pointer',
                    transition: 'all 0.18s ease',
                  }}
                >
                  <div
                    style={{
                      fontWeight: '700',
                      fontSize: '0.95rem',
                      color: isSelected ? 'var(--color-primary)' : 'var(--text-main)',
                      marginBottom: '0.2rem',
                    }}
                  >
                    {tier.label}
                  </div>
                  <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', lineHeight: 1.35 }}>
                    {tier.description}
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Error Display */}
        {apiError && (
          <Alert
            type="error"
            title="Session Generation Error"
            message={apiError}
            onClose={() => setApiError(null)}
          />
        )}

        {/* Action Button */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-start' }}>
          <Button
            type="submit"
            size="lg"
            variant="primary"
            isLoading={isLoading}
            disabled={isLoading || !topic.trim()}
            rightIcon={<ArrowRightIcon size={18} />}
          >
            Start learning
          </Button>
        </div>
      </form>
    </Card>
  );
}

