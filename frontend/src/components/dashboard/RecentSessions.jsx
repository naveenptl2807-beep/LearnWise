import React, { useEffect, useState } from 'react';
import { Card } from '../common/Card';
import { Button } from '../common/Button';
import { Alert } from '../common/Alert';
import { Spinner } from '../common/Spinner';
import { BookOpenIcon, RefreshIcon, ArrowRightIcon } from '../common/Icons';
import { SessionCard } from './SessionCard';
import { getSessions } from '../../services/api';

export function RecentSessions({ onSelectSession, onViewAllHistory, refreshTrigger }) {
  const [sessions, setSessions] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchHistory = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await getSessions();
      // Server returns list of sessions, sort descending by created_at or updated_at
      const sorted = Array.isArray(data)
        ? [...data].sort((a, b) => new Date(b.updated_at || b.created_at) - new Date(a.updated_at || a.created_at))
        : [];
      setSessions(sorted);
    } catch (err) {
      setError(err.message || 'Could not load learning history.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, [refreshTrigger]);

  const recentSessions = sessions.slice(0, 5);

  return (
    <section style={{ marginBottom: '3rem' }}>
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: '1.25rem',
        }}
      >
        <div>
          <h3
            style={{
              fontSize: '1.3rem',
              fontWeight: '700',
              color: 'var(--text-main)',
              letterSpacing: '-0.01em',
            }}
          >
            Recent Learning Sessions
          </h3>
          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
            Pick up where you left off or review past progress
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Button
            variant="ghost"
            size="sm"
            onClick={fetchHistory}
            disabled={isLoading}
            leftIcon={<RefreshIcon size={14} />}
            title="Refresh sessions list"
          >
            Refresh
          </Button>

          {sessions.length > 5 && (
            <Button
              variant="outline"
              size="sm"
              onClick={onViewAllHistory}
              rightIcon={<ArrowRightIcon size={14} />}
            >
              View All ({sessions.length})
            </Button>
          )}
        </div>
      </div>

      {/* Loading State */}
      {isLoading && (
        <Card padding="3rem" style={{ textAlign: 'center', color: 'var(--text-secondary)' }}>
          <Spinner size={28} />
          <div style={{ marginTop: '0.85rem', fontSize: '0.92rem', fontWeight: '500' }}>
            Retrieving saved sessions...
          </div>
        </Card>
      )}

      {/* Error State */}
      {!isLoading && error && (
        <Alert
          type="error"
          title="History Synchronization Error"
          message={error}
          action={
            <Button size="sm" variant="outline" onClick={fetchHistory}>
              Try Again
            </Button>
          }
        />
      )}

      {/* Empty State */}
      {!isLoading && !error && sessions.length === 0 && (
        <Card
          padding="3.5rem 2rem"
          style={{
            textAlign: 'center',
            backgroundColor: 'var(--bg-card)',
            border: '1.5px dashed var(--border-subtle)',
          }}
        >
          <div
            style={{
              width: '54px',
              height: '54px',
              borderRadius: '50%',
              backgroundColor: 'var(--bg-soft)',
              color: 'var(--color-primary)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              margin: '0 auto 1.25rem',
            }}
          >
            <BookOpenIcon size={26} />
          </div>
          <h4
            style={{
              fontSize: '1.15rem',
              fontWeight: '700',
              color: 'var(--text-main)',
              marginBottom: '0.4rem',
            }}
          >
            No learning sessions yet
          </h4>
          <p
            style={{
              color: 'var(--text-secondary)',
              fontSize: '0.9rem',
              maxWidth: '440px',
              margin: '0 auto 1.5rem',
              lineHeight: 1.5,
            }}
          >
            Enter a topic in the curriculum generator above and click &quot;Start learning&quot; to begin your first adaptive cycle.
          </p>
        </Card>
      )}

      {/* Populated Sessions List */}
      {!isLoading && !error && sessions.length > 0 && (
        <div>
          {recentSessions.map((s) => (
            <SessionCard key={s.session_id} session={s} onSelect={onSelectSession} />
          ))}
        </div>
      )}
    </section>
  );
}

