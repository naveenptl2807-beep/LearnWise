import React, { useState } from 'react';
import { Sidebar } from './components/layout/Sidebar';
import { Header } from './components/layout/Header';
import { DashboardPage } from './pages/DashboardPage';
import { HistoryPage } from './pages/HistoryPage';
import { LearningPage } from './pages/LearningPage';

export function App() {
  const [currentView, setCurrentView] = useState('dashboard'); // 'dashboard' | 'history' | 'learning'
  const [activeSessionId, setActiveSessionId] = useState(null);
  const [activeSessionData, setActiveSessionData] = useState(null);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  const handleStartLearning = (sessionData) => {
    if (!sessionData) return;
    setActiveSessionId(sessionData.session_id);
    setActiveSessionData(sessionData);
    setCurrentView('learning');
  };

  const handleExitLearning = () => {
    setActiveSessionId(null);
    setActiveSessionData(null);
    setCurrentView('dashboard');
  };

  return (
    <div className="app-container">
      {/* Navigation Sidebar */}
      <Sidebar
        currentView={currentView}
        onNavigate={(view) => {
          if (currentView === 'learning') {
            setActiveSessionId(null);
            setActiveSessionData(null);
          }
          setCurrentView(view);
        }}
        isMobileOpen={isMobileMenuOpen}
        onCloseMobile={() => setIsMobileMenuOpen(false)}
      />

      {/* Main Content Area */}
      <div className="main-content-wrapper">
        <Header onOpenMobileMenu={() => setIsMobileMenuOpen(true)} />

        <main className="page-content">
          {currentView === 'dashboard' && (
            <DashboardPage
              onNavigateHistory={() => setCurrentView('history')}
              onStartLearning={handleStartLearning}
            />
          )}

          {currentView === 'history' && (
            <HistoryPage
              onNavigateDashboard={() => setCurrentView('dashboard')}
              onStartLearning={handleStartLearning}
            />
          )}

          {currentView === 'learning' && (
            <LearningPage
              sessionId={activeSessionId}
              initialSessionData={activeSessionData}
              onBack={handleExitLearning}
            />
          )}
        </main>
      </div>

      {/* Responsive Styles Injection */}
      <style>{`
        @media (max-width: 900px) {
          .sidebar-nav {
            position: fixed !important;
            transform: translateX(-100%);
          }
          .sidebar-nav.mobile-open {
            transform: translateX(0) !important;
          }
          .mobile-hamburger {
            display: block !important;
          }
          .header-user-meta {
            display: none !important;
          }
        }
      `}</style>
    </div>
  );
}

export default App;
