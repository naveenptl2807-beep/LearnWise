import React, { useState } from 'react';
import { TopicInputCard } from '../components/dashboard/TopicInputCard';
import { FeatureCards } from '../components/dashboard/FeatureCards';
import { RecentSessions } from '../components/dashboard/RecentSessions';
import { SessionModal } from '../components/dashboard/SessionModal';
import { getSession } from '../services/api';

export function DashboardPage({ onNavigateHistory, onStartLearning }) {
  const [activeModalData, setActiveModalData] = useState(null);
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  const handleSessionCreated = (newSessionData) => {
    // Open modal preview for newly generated session with action to enter learning
    setActiveModalData(newSessionData);
    // Trigger history refresh
    setRefreshTrigger((prev) => prev + 1);
  };

  const handleSelectRecentSession = async (sessionSummary) => {
    try {
      // Fetch full details of the clicked session
      const fullDetails = await getSession(sessionSummary.session_id);
      setActiveModalData(fullDetails);
    } catch {
      // Fallback to summary representation if detail call fails
      setActiveModalData(sessionSummary);
    }
  };

  return (
    <div className="dashboard-page">
      {/* Hero / Topic Input Card */}
      <TopicInputCard onSessionCreated={handleSessionCreated} />

      {/* Feature Highlights Cards */}
      <FeatureCards />

      {/* Recent Sessions List & Empty State */}
      <RecentSessions
        onSelectSession={handleSelectRecentSession}
        onViewAllHistory={onNavigateHistory}
        refreshTrigger={refreshTrigger}
      />

      {/* Session Preview Modal */}
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
