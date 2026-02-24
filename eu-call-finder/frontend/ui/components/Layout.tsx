
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
  likedProjectsCount?: number;
  onShowLikedProjects?: () => void;
  showLikedOnly?: boolean;
  onShowAllProjects?: () => void;
}

const Layout: React.FC<LayoutProps> = ({ children, step, totalSteps, historySessions = [], onSelectHistory, onClearHistory, onDeleteHistoryItem, onStartNewSearch, likedProjectsCount = 0, onShowLikedProjects, showLikedOnly, onShowAllProjects }) => {
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
    return 'History';
  }, []);

  const clearHistory = () => {
    if (onClearHistory) onClearHistory();
  };

  return (
    <div className="min-h-screen flex flex-col font-display bg-background-light dark:bg-background-dark">
      {/* Left Sidebar - Transparent with blur */}
      <div className="fixed left-0 top-0 bottom-0 w-16 bg-white/5 dark:bg-slate-900/5 backdrop-blur-2xl z-50 flex flex-col">
        {/* History Toggle */}
        <button
          type="button"
          aria-label={isHistoryOpen ? 'Collapse history' : historyTitle}
          title={isHistoryOpen ? 'Collapse history' : historyTitle}
          onClick={() => setIsHistoryOpen((v) => !v)}
          className={`inline-flex items-center justify-center h-12 w-12 mx-auto mt-4 rounded-xl transition-colors ${
            isHistoryOpen
              ? 'text-slate-700 dark:text-slate-200 bg-slate-100/80 dark:bg-slate-800/80'
              : 'text-slate-500 hover:text-primary hover:bg-primary/10'
          }`}
        >
          <span className="material-icons leading-none">restore</span>
        </button>

        {/* Add Button - Below History */}
        <button
          type="button"
          aria-label="Start new search"
          title="Start new search"
          onClick={() => {
            if (onStartNewSearch) onStartNewSearch();
            setIsHistoryOpen(false);
          }}
          className="inline-flex items-center justify-center h-10 w-10 mx-auto mt-2 rounded-xl text-primary hover:bg-primary/10 transition-colors"
        >
          <span className="material-icons leading-none">add</span>
        </button>

        {/* Star Button - Liked Projects */}
        <button
          type="button"
          aria-label="Liked projects"
          title="Liked projects"
          onClick={() => {
            if (showLikedOnly) {
              if (onShowAllProjects) onShowAllProjects();
            } else {
              if (onShowLikedProjects) onShowLikedProjects();
            }
            setIsHistoryOpen(false);
          }}
          className={`inline-flex items-center justify-center h-10 w-10 mx-auto mt-2 rounded-xl transition-colors ${
            showLikedOnly 
              ? 'text-yellow-600 bg-yellow-400/20' 
              : likedProjectsCount > 0
                ? 'text-yellow-600 bg-yellow-400/20 hover:bg-yellow-400/30'
                : 'text-slate-500 hover:text-yellow-500 hover:bg-yellow-500/10'
          }`}
        >
          <span className="material-icons leading-none">{showLikedOnly || likedProjectsCount > 0 ? 'star' : 'star_border'}</span>
        </button>

        {/* Spacer */}
        <div className="flex-1"></div>
      </div>

      {/* Main Content Area - No header, full height */}
      <div className={`ml-16 min-h-screen flex-col ${isHistoryOpen ? 'blur-sm' : ''} transition-all duration-300`}>
        {/* Main Content */}
        <main className="flex-grow relative overflow-hidden">
          {/* Background Decorations */}
          <div className="absolute inset-0 eu-stars-bg pointer-events-none"></div>
          <div className="absolute -top-24 -left-24 w-96 h-96 bg-primary/5 rounded-full blur-3xl"></div>
          <div className="absolute -bottom-24 -right-24 w-96 h-96 bg-eu-yellow/5 rounded-full blur-3xl"></div>
          
          <div className="max-w-6xl mx-auto px-4 py-8 pb-24 relative">
            {children}
          </div>
        </main>

        {/* Footer */}
        <footer className="bg-white/30 dark:bg-slate-900/30 backdrop-blur-xl border-t border-white/20 dark:border-slate-700/30 py-6">
          <div className="max-w-7xl mx-auto px-4 text-center">
            <p className="text-xs text-slate-500 dark:text-slate-500">
              © 2026 EuroFund Finder. All project data is synced daily from the Funding & Tenders portal.
            </p>
          </div>
        </footer>
      </div>

      {/* History panel */}
      {isHistoryOpen && (
        <div
          ref={historyPanelRef}
          role="dialog"
          aria-label="History"
          className="fixed left-0 top-0 bottom-0 z-[60] w-80 bg-white/20 dark:bg-slate-900/20 backdrop-blur-xl border-r border-white/20 dark:border-slate-700/30 shadow-xl overflow-hidden flex flex-col"
        >
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-4 border-b border-white/20 dark:border-slate-700/30">
            <div className="flex items-center gap-2">
              <span className="material-icons text-slate-500">restore</span>
              <div className="text-sm font-semibold tracking-wide text-slate-600 dark:text-slate-300">
                HISTORY
              </div>
              <span className="inline-flex items-center rounded-full bg-eu-yellow/25 text-eu-yellow-dark dark:text-eu-yellow px-2 py-0.5 text-[11px] font-bold">
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
                className="p-1.5 text-slate-400 hover:text-slate-600 transition-colors"
              >
                <span className="material-icons text-lg">close</span>
              </button>
            </div>
          </div>

           {/* History list */}
           <div className="flex-1 overflow-y-auto">
             <div className="p-4">
               {historySessions.length === 0 ? (
                 <div className="text-center py-8 text-slate-400 text-sm">
                   <span className="material-icons text-3xl mb-2 block">history</span>
                   No history yet
                 </div>
               ) : (
                 <ul className="space-y-3">
                   {historySessions.map((s) => {
                     const label = s.company?.companyName || 'Untitled';
                     const date = new Date(s.createdAt).toLocaleDateString();
                     const time = new Date(s.createdAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                     
                     return (
                       <li
                         key={s.id}
                         className="bg-white/40 dark:bg-slate-800/40 backdrop-blur-sm rounded-xl p-4 cursor-pointer hover:bg-white/60 dark:hover:bg-slate-700/60 transition-colors border border-white/30 dark:border-slate-700/30"
                         onClick={() => {
                           if (s.company && s.result && onSelectHistory) {
                             onSelectHistory(s.company, s.result, s.id);
                             setIsHistoryOpen(false);
                           }
                         }}
                       >
                         <div className="flex items-center justify-between gap-3">
                           <div className="min-w-0 flex items-center gap-3">
                             <div className="inline-flex h-9 w-9 items-center justify-center rounded-xl bg-primary/10 text-primary">
                               <span className="material-icons text-[18px] leading-none">business</span>
                             </div>
                             <div className="min-w-0">
                               <div className="text-[16px] leading-snug font-semibold text-slate-800 dark:text-slate-100 truncate">
                                 {label}
                               </div>
                               <div className="text-xs text-slate-400">
                                 {date} • {time}
                               </div>
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
                             className="text-slate-400 hover:text-red-600 dark:hover:text-red-400 transition-colors p-1"
                           >
                             <span className="material-icons text-base">delete</span>
                           </button>
                         </div>

                         <div className="mt-3 flex items-center gap-2">
                           <button
                             type="button"
                             disabled={!s.result}
                             onClick={(e) => {
                               e.stopPropagation();
                               if (s.company && s.result && onSelectHistory) {
                                 onSelectHistory(s.company, s.result, s.id);
                                 setIsHistoryOpen(false);
                               }
                             }}
                             className={`flex-1 inline-flex items-center justify-center rounded-lg font-semibold h-9 text-sm transition-colors ${
                               s.result 
                                 ? 'bg-primary text-white hover:bg-primary/90' 
                                 : 'bg-slate-200 text-slate-400 cursor-not-allowed'
                             }`}
                           >
                             View Report
                           </button>
                         </div>
                       </li>
                     );
                   })}
                 </ul>
               )}
             </div>
           </div>

           {/* New Search Button - Fixed at bottom */}
           <div className="p-4 border-t border-white/20 dark:border-slate-700/30 bg-white/10 dark:bg-slate-900/10 backdrop-blur-xl">
             <button
               type="button"
               onClick={() => {
                 if (onStartNewSearch) onStartNewSearch();
                 setIsHistoryOpen(false);
               }}
               className="w-full py-3 bg-primary text-white font-semibold rounded-lg hover:bg-primary/90 transition-colors flex items-center justify-center gap-2"
             >
               <span className="material-icons">add</span>
               New Search
             </button>
           </div>
        </div>
      )}
    </div>
  );
};

export default Layout;
