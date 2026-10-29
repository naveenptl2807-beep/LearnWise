import React, { useEffect, useState, useCallback } from 'react';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Alert } from '../components/common/Alert';
import { Spinner } from '../components/common/Spinner';
import { LearningHeader } from '../components/learning/LearningHeader';
import { LessonView } from '../components/learning/LessonView';
import { QuizView } from '../components/learning/QuizView';
import { ResultsView } from '../components/learning/ResultsView';
import { getSession, submitCycleQuiz, createNextCycle } from '../services/api';

// Module-scoped in-memory cache to preserve drafts when returning to the same active session
let cachedSessionId = null;
let cachedDrafts = {}; // { [cycleNumber]: { [questionIndex]: selectedOption } }

export function LearningPage({ sessionId, initialSessionData, onBack }) {
  const [session, setSession] = useState(null);
  const [isLoading, setIsLoading] = useState(!initialSessionData);
  const [loadError, setLoadError] = useState(null);

  const [activeCycleNumber, setActiveCycleNumber] = useState(1);
  const [activeTab, setActiveTab] = useState('lesson'); // 'lesson' | 'quiz' | 'results'

  // Quiz drafts state: { [cycleNumber]: { [questionIndex]: selectedOption } }
  const [quizDrafts, setQuizDrafts] = useState(() => {
    if (sessionId && sessionId === cachedSessionId) {
      return { ...cachedDrafts };
    }
    cachedSessionId = sessionId;
    cachedDrafts = {};
    return {};
  });

  useEffect(() => {
    if (sessionId && sessionId !== cachedSessionId) {
      cachedSessionId = sessionId;
      cachedDrafts = {};
      setQuizDrafts({});
    }
  }, [sessionId]);

  const handleSelectAnswer = useCallback((cycleNum, questionIndex, option) => {
    setQuizDrafts((prev) => {
      const cycleDrafts = prev[cycleNum] || {};
      const updatedCycleDrafts = {
        ...cycleDrafts,
        [questionIndex]: option,
      };
      const updated = {
        ...prev,
        [cycleNum]: updatedCycleDrafts,
      };
      cachedDrafts = updated;
      return updated;
    });
  }, []);

  // Submission & Next Cycle states
  const [submissionResults, setSubmissionResults] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submissionError, setSubmissionError] = useState(null);

  const [isGeneratingNext, setIsGeneratingNext] = useState(false);
  const [nextCycleError, setNextCycleError] = useState(null);

  // Initialize or fetch session
  const loadSession = useCallback(async () => {
    if (!sessionId) return;
    setIsLoading(true);
    setLoadError(null);
    try {
      const data = await getSession(sessionId);
      setSession(data);

      const latestCycleNum = data.current_cycle_number || 1;
      setActiveCycleNumber(latestCycleNum);

      // Determine default tab based on latest cycle status
      const latestCycle = data.cycles?.find((c) => c.cycle_number === latestCycleNum);
      if (latestCycle && latestCycle.status === 'SUBMITTED') {
        setActiveTab('results');
      } else {
        setActiveTab('lesson');
      }
    } catch (err) {
      setLoadError(err.message || 'Failed to load learning session.');
    } finally {
      setIsLoading(false);
    }
  }, [sessionId]);

  useEffect(() => {
    if (initialSessionData) {
      // Normalize initialSessionData (handle both Create response and Detail response shapes)
      const normalizedCycles = initialSessionData.cycles || (initialSessionData.cycle ? [initialSessionData.cycle] : []);
      const normalizedSession = {
        ...initialSessionData,
        cycles: normalizedCycles,
      };
      setSession(normalizedSession);
      const targetCycleNum = normalizedSession.current_cycle_number || 1;
      setActiveCycleNumber(targetCycleNum);
      const activeCycle = normalizedCycles.find((c) => c.cycle_number === targetCycleNum);
      if (activeCycle && activeCycle.status === 'SUBMITTED') {
        setActiveTab('results');
      } else {
        setActiveTab('lesson');
      }
      setIsLoading(false);
    } else {
      loadSession();
    }
  }, [initialSessionData, loadSession]);

  // Handle cycle selection
  const handleSelectCycle = (cycleNum) => {
    setActiveCycleNumber(cycleNum);
    const selectedCycle = session?.cycles?.find((c) => c.cycle_number === cycleNum);
    if (selectedCycle && selectedCycle.status === 'SUBMITTED') {
      setActiveTab('results');
    } else {
      setActiveTab('lesson');
    }
    setSubmissionResults(null);
    setSubmissionError(null);
  };

  // Submit Quiz Action
  const handleSubmitQuiz = async (orderedAnswers) => {
    if (!session || isSubmitting) return;

    setIsSubmitting(true);
    setSubmissionError(null);

    try {
      const response = await submitCycleQuiz(session.session_id, activeCycleNumber, orderedAnswers);
      setSubmissionResults(response);

      // Successfully submitted: clear/retire this cycle's draft
      setQuizDrafts((prev) => {
        const updated = { ...prev };
        delete updated[activeCycleNumber];
        cachedDrafts = updated;
        return updated;
      });

      // Update session in local state
      setSession((prev) => {
        if (!prev) return prev;
        const updatedCycles = (prev.cycles || []).map((c) => {
          if (c.cycle_number === activeCycleNumber) {
            return {
              ...c,
              status: 'SUBMITTED',
              score_percentage: response.score_percentage,
              submitted_answers: orderedAnswers.map((a) => a.selected_option),
            };
          }
          return c;
        });

        return {
          ...prev,
          status: response.is_mastered ? 'MASTERED' : prev.status,
          is_mastered: response.is_mastered,
          current_difficulty: response.next_difficulty,
          cycles: updatedCycles,
        };
      });

      // Switch to results tab
      setActiveTab('results');
    } catch (err) {
      setSubmissionError(err.message || 'Failed to submit quiz for grading.');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Generate Next Cycle Action
  const handleGenerateNextCycle = async () => {
    if (!session || isGeneratingNext) return;

    setIsGeneratingNext(true);
    setNextCycleError(null);

    try {
      const response = await createNextCycle(session.session_id);
      // response is SessionCreateResponse with new cycle
      const newCycle = response.cycle;

      setSession((prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          current_cycle_number: response.current_cycle_number,
          current_difficulty: response.current_difficulty,
          cycles: [...(prev.cycles || []), newCycle],
        };
      });

      // Transition to new cycle
      setActiveCycleNumber(response.current_cycle_number);
      setSubmissionResults(null);
      setActiveTab('lesson');
    } catch (err) {
      setNextCycleError(err.message || 'Failed to generate next learning cycle. Please try again.');
    } finally {
      setIsGeneratingNext(false);
    }
  };

  // Loading State
  if (isLoading) {
    return (
      <div style={{ maxWidth: '900px', margin: '3rem auto' }}>
        <Card padding="3.5rem" style={{ textAlign: 'center', color: 'var(--text-secondary)' }}>
          <Spinner size={32} />
          <div style={{ marginTop: '1rem', fontSize: '1rem', fontWeight: '600' }}>
            Loading adaptive curriculum...
          </div>
        </Card>
      </div>
    );
  }

  // Load Error State
  if (loadError || !session) {
    return (
      <div style={{ maxWidth: '900px', margin: '2rem auto' }}>
        <Alert
          type="error"
          title="Could Not Load Session"
          message={loadError || 'Session data could not be found.'}
          action={
            <div style={{ display: 'flex', gap: '0.75rem', marginTop: '0.5rem' }}>
              <Button size="sm" variant="outline" onClick={loadSession}>
                Retry Loading
              </Button>
              <Button size="sm" variant="ghost" onClick={onBack}>
                Return to Dashboard
              </Button>
            </div>
          }
        />
      </div>
    );
  }

  const currentCycle = session.cycles?.find((c) => c.cycle_number === activeCycleNumber) || session.cycles?.[0];
  const isCurrentCycleSubmitted = currentCycle?.status === 'SUBMITTED' || !!submissionResults;

  return (
    <div className="learning-page" style={{ maxWidth: '960px', margin: '0 auto', paddingBottom: '4rem' }}>
      {/* Top Header with Breadcrumbs, Tabs & Cycle Switcher */}
      <LearningHeader
        session={session}
        activeCycleNumber={activeCycleNumber}
        onSelectCycleNumber={handleSelectCycle}
        activeTab={activeTab}
        onSelectTab={(tab) => setActiveTab(tab)}
        onBack={onBack}
        hasResults={isCurrentCycleSubmitted}
      />

      {/* Tab 1: Lesson & Notes */}
      {activeTab === 'lesson' && (
        <LessonView
          cycle={currentCycle}
          onProceedToQuiz={() => setActiveTab('quiz')}
        />
      )}

      {/* Tab 2: Practice Quiz */}
      {activeTab === 'quiz' && (
        <QuizView
          key={activeCycleNumber}
          cycle={currentCycle}
          selectedAnswers={quizDrafts[activeCycleNumber] || {}}
          onSelectAnswer={(questionIndex, option) =>
            handleSelectAnswer(activeCycleNumber, questionIndex, option)
          }
          onSubmitQuiz={handleSubmitQuiz}
          isSubmitting={isSubmitting}
          submissionError={submissionError}
          onClearError={() => setSubmissionError(null)}
        />
      )}

      {/* Tab 3: Quiz Results & Progression */}
      {activeTab === 'results' && (
        <ResultsView
          submissionResults={submissionResults}
          cycle={currentCycle}
          session={session}
          onGenerateNextCycle={handleGenerateNextCycle}
          isGeneratingNext={isGeneratingNext}
          nextCycleError={nextCycleError}
          onClearNextCycleError={() => setNextCycleError(null)}
          onReturnDashboard={onBack}
        />
      )}
    </div>
  );
}

