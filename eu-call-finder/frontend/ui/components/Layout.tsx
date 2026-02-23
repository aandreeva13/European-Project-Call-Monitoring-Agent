
import React, { useEffect, useMemo, useRef, useState } from 'react';

interface LayoutProps {
  children: React.ReactNode;
  step: number;
  totalSteps: number;
  historySessions?: Array<{ id: string; createdAt: number; company: { companyName: string }; result?: any }>;
  onSelectHistory?: (company: any, result?: any, sessionId?: string) => void;
  onClearHistory?: () => void;
  onDeleteHistoryItem?: (sessionId: string) => void;
  onStartNewSearch?: () => void;
}

const Layout: React.FC<LayoutProps> = ({ children, step, totalSteps, historySessions = [], onSelectHistory, onClearHistory, onDeleteHistoryItem, onStartNewSearch }) => {
  const [isHistoryOpen, setIsHistoryOpen] = useState(false);
  const historyPanelRef = useRef<HTMLDivElement>(null);

  // Close history panel when clicking outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (
        isHistoryOpen &&
        historyPanelRef.current &&
        !historyPanelRef.current.contains(e.target as Node)
      ) {
        setIsHistoryOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isHistoryOpen]);

  const historyTitle = useMemo(() => {
    if (historySessions.length === 0) return 'History';
    return `History (${historySessions.length})`;
  }, [historySessions.length]);

  const clearHistory = () => {
    if (onClearHistory) onClearHistory();
  };

  return (
    <div className="min-h-screen flex flex-col font-display bg-background-light dark:bg-background-dark pt-16">
      {/* Header */}
      <nav className="w-full border-b border-primary/10 bg-white dark:bg-background-dark/50 backdrop-blur-md fixed top-0 left-0 right-0 z-40 overflow-visible">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between overflow-visible">
          <div className="flex items-center gap-2">
            <div className="bg-primary p-1.5 rounded-lg">
              <span className="material-icons text-white text-xl">account_balance</span>
            </div>
            <span className="font-bold text-xl tracking-tight text-eu-blue dark:text-white">
              EuroFund <span className="text-primary">Finder</span>
            </span>
          </div>
          <div className="flex items-center gap-4 relative overflow-visible">

            {/* History toggle */}
            <button
              type="button"
              aria-label={historyTitle}
              title={historyTitle}
              onClick={() => setIsHistoryOpen((v) => !v)}
              className="text-slate-500 hover:text-primary transition-colors inline-flex items-center justify-center h-10 w-10"
            >
              <span className="material-icons leading-none">history</span>
            </button>

            {/* History panel (closed by default) */}
            {isHistoryOpen && (
              <div
                ref={historyPanelRef}
                role="dialog"
                aria-label="History"
                className="fixed right-4 top-[calc(env(safe-area-inset-top)+64px+12px)] z-[1000] w-96 max-w-[92vw] bg-white dark:bg-background-dark border border-slate-200 dark:border-slate-800 rounded-2xl shadow-xl overflow-hidden max-h-[calc(100vh-env(safe-area-inset-top)-64px-24px)]"
              >
                {/* Header */}
                <div className="flex items-center justify-between px-5 py-4 border-b border-slate-100 dark:border-slate-800">
                  <div className="flex items-center gap-2">
                    <div className="text-sm font-semibold tracking-wide text-slate-600 dark:text-slate-300">
                      QUICK HISTORY
                    </div>
                    <span className="ml-1 inline-flex items-center rounded-full bg-eu-yellow/25 text-eu-yellow-dark dark:text-eu-yellow px-2 py-0.5 text-[11px] font-bold">
                      BETA
                    </span>
                  </div>

                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={clearHistory}
                      className="text-xs text-slate-500 hover:text-red-600 transition-colors"
                    >
                      Clear
                    </button>
                    <button
                      type="button"
                      aria-label="Close history"
                      onClick={() => setIsHistoryOpen(false)}
                      className="text-slate-500 hover:text-slate-800 dark:hover:text-slate-200 transition-colors"
                    >
                      <span className="material-icons text-base">close</span>
                    </button>
                  </div>
                </div>

                {/* List */}
                <div className="max-h-[520px] overflow-auto">
                  {historySessions.length === 0 ? (
                    <div className="px-5 py-6 text-sm text-slate-500">No history yet.</div>
                  ) : (
                    <ul className="divide-y divide-slate-100 dark:divide-slate-800">
                      {historySessions.map((s, idx) => {
                        const label = s.company?.companyName || 'Unnamed company';
                        const dateLabel = new Date(s.createdAt);

                        // Basic grouping labels similar to the screenshot
                        const now = new Date();
                        const diffMs = now.getTime() - dateLabel.getTime();
                        const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
                        const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

                        let relative = dateLabel.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' });
                        if (diffHours < 24) relative = `${Math.max(1, diffHours)} hour${diffHours === 1 ? '' : 's'} ago`;
                        else if (diffDays === 1) relative = 'Yesterday';
                        else if (diffDays < 7) relative = `${diffDays} days ago`;

                        const showGroup = idx === 0;

                        return (
                          <li key={s.id} className="px-5 py-5">
                            {showGroup && (
                              <div className="text-sm text-slate-400 dark:text-slate-500 mb-2">{relative}</div>
                            )}

                            <div className="flex items-start justify-between gap-3">
                              <div className="min-w-0">
                                <div className="text-[18px] leading-snug font-semibold text-slate-800 dark:text-slate-100">
                                  {label}
                                </div>
                              </div>
                              <button
                                type="button"
                                aria-label="Delete"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  if (onDeleteHistoryItem) {
                                    onDeleteHistoryItem(s.id);
                                  }
                                }}
                                className="text-slate-400 hover:text-red-600 dark:hover:text-red-400 transition-colors p-1 -mr-1"
                              >
                                <span className="material-icons text-base">delete</span>
                              </button>
                            </div>

                            <div className="mt-4 flex items-center gap-3">
                              <button
                                type="button"
                                disabled={!s.result}
                                onClick={() => {
                                  if (s.company && s.result && onSelectHistory) {
                                    onSelectHistory(s.company, s.result, s.id);
                                    setIsHistoryOpen(false);
                                  }
                                }}
                                className={`flex-1 inline-flex items-center justify-center rounded-xl font-semibold h-11 px-4 transition-colors ${
                                  s.result 
                                    ? 'bg-primary text-white hover:bg-primary/90' 
                                    : 'bg-slate-200 text-slate-400 cursor-not-allowed'
                                }`}
                              >
                                View Report
                              </button>
                              <button
                                type="button"
                                onClick={() => {
                                  if (s.company && onSelectHistory) {
                                    onSelectHistory(s.company, s.result, s.id);
                                    setIsHistoryOpen(false);
                                  }
                                }}
                                className="flex-1 inline-flex items-center justify-center rounded-xl border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-200 font-semibold h-11 px-4 hover:bg-slate-50 dark:hover:bg-slate-900/40 transition-colors"
                              >
                                <span className="material-icons text-base mr-2">refresh</span>
                                Re-run
                              </button>
                            </div>
                          </li>
                        );
                      })}
                    </ul>
                  )}
                </div>

                {/* Footer */}
                <button
                  type="button"
                  onClick={() => {
                    if (onStartNewSearch) {
                      onStartNewSearch();
                    }
                    setIsHistoryOpen(false);
                  }}
                  className="w-full border-t border-slate-100 dark:border-slate-800 px-5 py-4 text-primary font-semibold hover:bg-slate-50 dark:hover:bg-slate-900/40 transition-colors flex items-center justify-center gap-2"
                >
                  <span className="material-icons text-base">add_circle</span>
                  Start New Search
                </button>
              </div>
            )}
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="flex-grow relative overflow-hidden">
        {/* Background Decorations */}
        <div className="absolute inset-0 eu-stars-bg pointer-events-none"></div>
        <div className="absolute -top-24 -left-24 w-96 h-96 bg-primary/5 rounded-full blur-3xl"></div>
        <div className="absolute -bottom-24 -right-24 w-96 h-96 bg-eu-yellow/5 rounded-full blur-3xl"></div>
        
        <div className="max-w-7xl mx-auto px-4 pt-12 pb-24 relative">
          {children}
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-white dark:bg-background-dark/80 border-t border-slate-100 dark:border-slate-800 py-6">
        <div className="max-w-7xl mx-auto px-4 text-center">
          <p className="text-xs text-slate-500 dark:text-slate-500">
            © 2026 EuroFund Finder. All project data is synced daily from the Funding & Tenders portal.
          </p>
        </div>
      </footer>
    </div>
  );
};

export default Layout;
