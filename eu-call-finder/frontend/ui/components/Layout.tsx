
import React from 'react';

interface LayoutProps {
  children: React.ReactNode;
  step: number;
  totalSteps: number;
}

const Layout: React.FC<LayoutProps> = ({ children, step, totalSteps }) => {
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
          <div className="flex items-center gap-4">
            <div className="text-xs font-medium px-3 py-1 bg-primary/10 text-primary rounded-full uppercase tracking-wider">
              Step {step} of {totalSteps}
            </div>
            <button className="text-slate-500 hover:text-primary transition-colors">
              <span className="material-icons">help_outline</span>
            </button>
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
