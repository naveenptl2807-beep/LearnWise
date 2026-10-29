import React, { useEffect, useState } from 'react';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Alert } from '../components/common/Alert';
import { Spinner } from '../components/common/Spinner';
import { SessionCard } from '../components/dashboard/SessionCard';
import { SessionModal } from '../components/dashboard/SessionModal';
import { BookOpenIcon, RefreshIcon, ClockIcon } from '../components/common/Icons';
import { getSessions, getSession } from '../services/api';

export function HistoryPage({ onNavigateDashboard, onStartLearning }) {
  const [sessions, setSessions] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [difficultyFilter, setDifficultyFilter] = useState('ALL');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [activeModalData, setActiveModalData] = useState(null);

  const fetchAllSessions = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await getSessions();
      const sorted = Array.isArray(data)
        ? [...data].sort((a, b) => new Date(b.updated_at || b.created_at) - new Date(a.updated_at || a.created_at))
        : [];
      setSessions(sorted);
    } catch (err) {
      setError(err.message || 'Unable to retrieve learning history.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchAllSessions();
  }, []);

  const handleSelectSession = async (sessionSummary) => {
    try {
      const fullDetails = await getSession(sessionSummary.session_id);
      setActiveModalData(fullDetails);
    } catch {
      setActiveModalData(sessionSummary);
    }
  };

  // Filtered Sessions
  const filteredSessions = sessions.filter((s) => {
    const matchesSearch = s.topic.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesDifficulty = difficultyFilter === 'ALL' || s.current_difficulty === difficultyFilter;
    const matchesStatus = statusFilter === 'ALL' || s.status === statusFilter;
    return matchesSearch && matchesDifficulty && matchesStatus;
  });

  return (
    <div className="history-page">
      {/* Header */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: '2rem',
          flexWrap: 'wrap',
          gap: '1rem',
        }}
      >
        <div>
          <div style={{ display: 'inline-flex', alignItems: 'center', gap: '0.4rem', color: 'var(--color-primary)', fontWeight: '700', fontSize: '0.82rem', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.25rem' }}>
            <ClockIcon size={16} />
            <span>Persistent Learning Ledger</span>
          </div>
          <h2 style={{ fontSize: '1.65rem', fontWeight: '700', color: 'var(--text-main)', letterSpacing: '-0.02em' }}>
            All Learning Sessions
          </h2>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
            Browse and resume all previously generated adaptive curricula
          </p>
        </div>

        <Button
          variant="outline"
          size="sm"
          onClick={fetchAllSessions}
          disabled={isLoading}
          leftIcon={<RefreshIcon size={14} />}
        >
          Refresh History
        </Button>
      </div>

      {/* Filter and Search Bar */}
      <Card padding="1.25rem 1.5rem" style={{ marginBottom: '1.75rem' }}>
        <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
          {/* Search Input */}
          <div style={{ flex: 2, minWidth: '220px' }}>
            <input
              type="text"
              placeholder="Search by topic name..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{
                width: '100%',
                padding: '0.65rem 0.95rem',
                borderRadius: 'var(--radius-md)',
                border: '1px solid var(--border-subtle)',
                backgroundColor: '#FFFFFF',
                color: 'var(--text-main)',
                fontSize: '0.9rem',
                outline: 'none',
              }}
            />
          </div>

          {/* Difficulty Filter */}
          <div style={{ flex: 1, minWidth: '140px' }}>
            <select
              value={difficultyFilter}
              onChange={(e) => setDifficultyFilter(e.target.value)}
              style={{
                width: '100%',
                padding: '0.65rem 0.95rem',
                borderRadius: 'var(--radius-md)',
                border: '1px solid var(--border-subtle)',
                backgroundColor: '#FFFFFF',
                color: 'var(--text-main)',
                fontSize: '0.9rem',
                outline: 'none',
                cursor: 'pointer',
              }}
            >
              <option value="ALL">All Difficulties</option>
              <option value="Beginner">Beginner</option>
              <option value="Intermediate">Intermediate</option>
              <option value="Advanced">Advanced</option>
            </select>
          </div>

          {/* Status Filter */}
          <div style={{ flex: 1, minWidth: '140px' }}>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              style={{
                width: '100%',
                padding: '0.65rem 0.95rem',
                borderRadius: 'var(--radius-md)',
                border: '1px solid var(--border-subtle)',
                backgroundColor: '#FFFFFF',
                color: 'var(--text-main)',
                fontSize: '0.9rem',
                outline: 'none',
                cursor: 'pointer',
              }}
            >
              <option value="ALL">All Statuses</option>
              <option value="IN_PROGRESS">In Progress</option>
              <option value="MASTERED">Mastered</option>
            </select>
          </div>
        </div>
      </Card>

      {/* Loading */}
      {isLoading && (
        <Card padding="3rem" style={{ textAlign: 'center', color: 'var(--text-secondary)' }}>
          <Spinner size={28} />
          <div style={{ marginTop: '0.85rem', fontSize: '0.92rem', fontWeight: '500' }}>
            Loading session history...
          </div>
        </Card>
      )}

      {/* Error */}
      {!isLoading && error && (
        <Alert
          type="error"
          title="Error Loading Sessions"
          message={error}
          action={
            <Button size="sm" variant="outline" onClick={fetchAllSessions}>
              Retry
            </Button>
          }
        />
      )}

      {/* Empty State */}
      {!isLoading && !error && filteredSessions.length === 0 && (
        <Card
          padding="3.5rem 2rem"
          style={{
            textAlign: 'center',
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
          <h4 style={{ fontSize: '1.15rem', fontWeight: '700', color: 'var(--text-main)', marginBottom: '0.4rem' }}>
            {sessions.length === 0 ? 'No learning history yet' : 'No matching sessions found'}
          </h4>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', maxWidth: '420px', margin: '0 auto 1.5rem', lineHeight: 1.5 }}>
            {sessions.length === 0
              ? 'Start your first adaptive curriculum from the dashboard to see your progress recorded here.'
              : 'Try clearing your search query or filter options to see other sessions.'}
          </p>
          {sessions.length === 0 && (
            <Button variant="primary" size="md" onClick={onNavigateDashboard}>
              Go to Dashboard
            </Button>
          )}
        </Card>
      )}

      {/* Session List */}
      {!isLoading && !error && filteredSessions.length > 0 && (
        <div>
          {filteredSessions.map((s) => (
            <SessionCard key={s.session_id} session={s} onSelect={handleSelectSession} />
          ))}
        </div>
      )}

      {/* Modal */}
      {activeModalData && (
        <SessionModal
          sessionData={activeModalData}
          onClose={() => setActiveModalData(null)}
          onStartLearning={onStartLearning}
        />
      )}
    </div>
  );
}

