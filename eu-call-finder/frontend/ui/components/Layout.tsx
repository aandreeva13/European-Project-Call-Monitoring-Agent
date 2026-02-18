
import React, { useEffect, useMemo, useState } from 'react';

interface LayoutProps {
  children: React.ReactNode;
  step: number;
  totalSteps: number;
  historySessions?: Array<{ id: string; createdAt: number; company: { companyName: string }; result?: any }>;
  onSelectHistory?: (company: any, result?: any, sessionId?: string) => void;
  onClearHistory?: () => void;
}

const Layout: React.FC<LayoutProps> = ({ children, step, totalSteps, historySessions = [], onSelectHistory, onClearHistory }) => {
  const [isHistoryOpen, setIsHistoryOpen] = useState(false);

  const historyTitle = useMemo(() => {
    if (historySessions.length === 0) return 'History';
    return `History (${historySessions.length})`;
  }, [historySessions.length]);

  const clearHistory = () => {
    if (onClearHistory) onClearHistory();
  };

  return (
    <div className="min-h-screen flex flex-col font-display bg-background-light dark:bg-background-dark">
      {/* Header */}
      <nav className="w-full border-b border-primary/10 bg-white dark:bg-background-dark/50 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="bg-primary p-1.5 rounded-lg">
              <span className="material-icons text-white text-xl">account_balance</span>
            </div>
            <span className="font-bold text-xl tracking-tight text-eu-blue dark:text-white">
              EuroFund <span className="text-primary">Finder</span>
            </span>
          </div>
          <div className="flex items-center gap-4 relative">
            <div className="text-xs font-medium px-3 py-1 bg-primary/10 text-primary rounded-full uppercase tracking-wider">
              Step {step} of {totalSteps}
            </div>

            {/* History toggle */}
            <button
              type="button"
              aria-label={historyTitle}
              title={historyTitle}
              onClick={() => setIsHistoryOpen((v) => !v)}
              className="text-slate-500 hover:text-primary transition-colors"
            >
              <span className="material-icons">history</span>
            </button>

            {/* History panel (closed by default) */}
            {isHistoryOpen && (
              <div
                role="dialog"
                aria-label="History"
                className="absolute right-0 top-12 w-80 max-w-[90vw] bg-white dark:bg-background-dark border border-slate-200 dark:border-slate-800 rounded-xl shadow-xl overflow-hidden"
              >
                <div className="flex items-center justify-between px-4 py-3 border-b border-slate-100 dark:border-slate-800">
                  <div className="text-sm font-semibold text-slate-800 dark:text-slate-100">{historyTitle}</div>
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

                <div className="max-h-80 overflow-auto">
                  {historySessions.length === 0 ? (
                    <div className="px-4 py-4 text-sm text-slate-500">No history yet.</div>
                  ) : (
                    <ul className="divide-y divide-slate-100 dark:divide-slate-800">
                      {historySessions.map((s) => (
                        <li key={s.id} className="px-4 py-0">
                          <button
                            type="button"
                             onClick={() => {
                              // Use the session data directly from props
                              if (s.company && onSelectHistory) {
                                onSelectHistory(s.company, s.result, s.id);
                              }
                              setIsHistoryOpen(false);
                            }}
                            className="w-full text-left px-4 py-3 hover:bg-slate-50 dark:hover:bg-slate-900/40 transition-colors"
                          >
                            <div className="flex items-center justify-between">
                              <div className="text-sm text-slate-800 dark:text-slate-100 font-medium truncate pr-3">
                                {s.company?.companyName || 'Unnamed company'}
                              </div>
                              <div className="text-xs text-slate-500 whitespace-nowrap">
                                {new Date(s.createdAt).toLocaleString()}
                              </div>
                            </div>
                          </button>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
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
        
        <div className="max-w-3xl mx-auto px-4 pt-12 pb-24 relative z-10">
          {children}
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-white dark:bg-background-dark/80 border-t border-slate-100 dark:border-slate-800 py-6">
        <div className="max-w-7xl mx-auto px-4 text-center">
          <p className="text-xs text-slate-500 dark:text-slate-500">
            © 2024 EuroFund Finder. All project data is synced daily from the Funding & Tenders portal.
          </p>
        </div>
      </footer>
    </div>
  );
};

export default Layout;
