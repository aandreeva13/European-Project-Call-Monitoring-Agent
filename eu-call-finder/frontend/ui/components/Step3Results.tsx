
import React, { useEffect, useState } from 'react';
import { CompanyData, FundingCall } from '../types';
import { getFundingMatches } from '../services/geminiService';

interface Step3Props {
  company: CompanyData;
  onReset: () => void;
}

const Step3Results: React.FC<Step3Props> = ({ company, onReset }) => {
  const [loading, setLoading] = useState(true);
  const [results, setResults] = useState<FundingCall[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchResults = async () => {
      try {
        setLoading(true);
        const matches = await getFundingMatches(company);
        setResults(matches);
      } catch (err) {
        setError("Failed to fetch funding matches. Please try again.");
      } finally {
        setLoading(false);
      }
    };

    fetchResults();
  }, [company]);

  if (loading) {
    return (
      <div className="text-center py-24">
        <div className="mb-8 relative inline-block">
          <div className="w-20 h-20 border-4 border-primary/20 border-t-primary rounded-full animate-spin"></div>
          <span className="material-icons absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 text-primary text-3xl">auto_awesome</span>
        </div>
        <h2 className="text-2xl font-bold mb-4">Analyzing Opportunities...</h2>
        <p className="text-slate-500 max-w-sm mx-auto">
          Our AI is scanning the latest EU funding calls to find the best matches for {company.companyName}.
        </p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-24">
        <div className="inline-flex items-center justify-center p-4 bg-red-100 rounded-full mb-6">
          <span className="material-icons text-red-600 text-4xl">error_outline</span>
        </div>
        <h2 className="text-2xl font-bold mb-2">Something went wrong</h2>
        <p className="text-slate-500 mb-8">{error}</p>
        <button 
          onClick={onReset}
          className="bg-primary text-white px-6 py-2 rounded-lg font-bold"
        >
          Try Again
        </button>
      </div>
    );
  }

  return (
    <div>
      <div className="text-center mb-10">
        <div className="inline-flex items-center justify-center p-2 mb-4 bg-green-500/10 rounded-full">
          <span className="material-icons text-green-500 text-3xl">verified</span>
        </div>
        <h1 className="text-4xl font-extrabold text-eu-blue dark:text-white mb-3">Your Matches Found</h1>
        <p className="text-lg text-slate-600 dark:text-slate-400">
          We found {results.length} highly relevant funding opportunities for your profile.
        </p>
      </div>

      <div className="space-y-6">
        {results.map((call) => (
          <div key={call.id} className="bg-white dark:bg-slate-900 rounded-xl shadow-md border border-slate-200 dark:border-slate-800 overflow-hidden hover:shadow-xl transition-shadow">
            <div className="p-6">
              <div className="flex justify-between items-start mb-4">
                <div className="flex-grow">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="px-2 py-0.5 bg-primary/10 text-primary text-[10px] font-bold rounded uppercase tracking-wider">
                      Match Score: {call.matchScore}%
                    </span>
                    <span className="text-xs text-slate-400 font-medium">ID: {call.id}</span>
                  </div>
                  <h3 className="text-xl font-bold text-slate-900 dark:text-white group-hover:text-primary transition-colors">
                    {call.title}
                  </h3>
                </div>
                <div className="text-right">
                  <div className="text-primary font-bold">{call.budget}</div>
                  <div className="text-[10px] text-slate-400 uppercase font-bold tracking-tight">Estimated Budget</div>
                </div>
              </div>
              
              <p className="text-slate-600 dark:text-slate-400 text-sm mb-6 leading-relaxed">
                {call.description}
              </p>

              <div className="flex flex-wrap gap-2 mb-6">
                {call.tags.map(tag => (
                  <span key={tag} className="px-2.5 py-1 bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 text-xs font-semibold rounded-full">
                    #{tag}
                  </span>
                ))}
              </div>

              <div className="flex items-center justify-between pt-6 border-t border-slate-50 dark:border-slate-800">
                <div className="flex items-center gap-2 text-red-500">
                  <span className="material-icons text-sm">event</span>
                  <span className="text-xs font-bold uppercase tracking-wider">Deadline: {call.deadline}</span>
                </div>
                <button className="flex items-center gap-2 text-primary font-bold hover:underline">
                  View full details
                  <span className="material-icons text-sm">open_in_new</span>
                </button>
              </div>
            </div>
          </div>
        ))}

        <div className="pt-10 flex flex-col items-center gap-4">
          <button 
            onClick={onReset}
            className="text-slate-500 hover:text-primary font-semibold flex items-center gap-2 transition-colors"
          >
            <span className="material-icons text-lg">refresh</span>
            Start a new search
          </button>
        </div>
      </div>
    </div>
  );
};

export default Step3Results;
