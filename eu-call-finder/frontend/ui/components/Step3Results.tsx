import React, { useEffect, useState } from 'react';
import { CompanyData, SearchResult, FundingCard, CompanySummary, CompanyProfile } from '../types';
import { searchFundingCallsStream, ProgressUpdate } from '../services/apiService';

interface Step3Props {
  company: CompanyData;
  onReset: () => void;
  cachedResult?: SearchResult;
  onResultComplete?: (result: SearchResult) => void;
}

const AGENTS = [
  { name: 'Safety Guard', icon: 'security', color: 'text-green-500', bgColor: 'bg-green-500' },
  { name: 'Smart Planner', icon: 'psychology', color: 'text-purple-500', bgColor: 'bg-purple-500' },
  { name: 'Retriever', icon: 'web', color: 'text-orange-500', bgColor: 'bg-orange-500' },
  { name: 'Analyzer', icon: 'analytics', color: 'text-pink-500', bgColor: 'bg-pink-500' },
  { name: 'Reporter', icon: 'summarize', color: 'text-indigo-500', bgColor: 'bg-indigo-500' }
];

const Step3Results: React.FC<Step3Props> = ({ company, onReset, cachedResult, onResultComplete }) => {
  const [loading, setLoading] = useState(!cachedResult);
  const [result, setResult] = useState<SearchResult | null>(cachedResult || null);
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState<ProgressUpdate>({
    agent: 'Initializing',
    progress: 5,
    message: 'Starting workflow...',
    status: 'running'
  });
  const [completedAgents, setCompletedAgents] = useState<string[]>(cachedResult ? AGENTS.map(a => a.name) : []);
  const [selectedCard, setSelectedCard] = useState<FundingCard | null>(null);

  useEffect(() => {
    // If we have cached results, use them directly without searching
    // Check for valid SearchResult structure (must have company_profile)
    if (cachedResult && cachedResult.company_profile) {
      console.log('Using cached result:', cachedResult);
      setResult(cachedResult);
      setLoading(false);
      setCompletedAgents(AGENTS.map(a => a.name));
      return;
    }
    
    console.log('No cached result found, running search. cachedResult:', cachedResult);

    // Otherwise, run the search
    setLoading(true);
    setResult(null);
    setCompletedAgents([]);
    
    const cleanup = searchFundingCallsStream(
      company,
      (update) => {
        console.log('Progress update:', update);
        setProgress(update);
        
        // Track completed agents based on progress
        const currentProgress = update.progress;
        const newlyCompleted: string[] = [];
        
        if (currentProgress >= 15) newlyCompleted.push('Safety Guard');
        if (currentProgress >= 35) newlyCompleted.push('Smart Planner');
        if (currentProgress >= 55) newlyCompleted.push('Retriever');
        if (currentProgress >= 80) newlyCompleted.push('Analyzer');
        if (currentProgress >= 95) newlyCompleted.push('Reporter');
        
        setCompletedAgents(prev => {
          const combined = [...new Set([...prev, ...newlyCompleted])];
          return combined;
        });
      },
      (searchResult) => {
        console.log('Search complete:', searchResult);
        const typedResult = searchResult as unknown as SearchResult;
        setResult(typedResult);
        setLoading(false);
        setCompletedAgents(AGENTS.map(a => a.name));
        // Persist the result to the session
        if (onResultComplete) {
          onResultComplete(typedResult);
        }
      },
      (errorMsg) => {
        console.error('Search error:', errorMsg);
        setError(errorMsg);
        setLoading(false);
      }
    );

    return cleanup;
  }, [company, cachedResult, onResultComplete]);

  const getMatchColor = (percentage: number) => {
    if (percentage >= 80) return 'text-green-600 bg-green-50 border-green-200';
    if (percentage >= 60) return 'text-blue-600 bg-blue-50 border-blue-200';
    if (percentage >= 40) return 'text-yellow-600 bg-yellow-50 border-yellow-200';
    return 'text-red-600 bg-red-50 border-red-200';
  };

  const getProbabilityColor = (probability: string) => {
    switch (probability) {
      case 'high': return 'text-green-600 bg-green-100';
      case 'medium': return 'text-yellow-600 bg-yellow-100';
      case 'low': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const formatBudget = (budget: string) => {
    if (!budget || budget === 'N/A') return 'Budget N/A';

    const normalized = String(budget).replace(/\s+/g, ' ').trim();

    // Prefer big numbers from the text (e.g., "35 000 000") and format them.
    // The current UI bug (showing "€4") happens because we were matching small numbers first
    // (e.g., the "2027" year or "1" from "Showing 1–11").
    const matches = normalized.match(/\d[\d\s,.]*/g) || [];
    const parsed = matches
      .map(m => {
        // Keep digits only
        const digits = m.replace(/[^\d]/g, '');
        if (!digits) return null;
        const n = Number(digits);
        return Number.isFinite(n) ? n : null;
      })
      .filter((n): n is number => n !== null);

    // Filter out obvious non-budget numbers (years, indices)
    const candidates = parsed.filter(n => n >= 10000); // 10k+ is a reasonable "budget-ish" threshold

    if (candidates.length > 0) {
      const max = Math.max(...candidates);
      if (max >= 1_000_000_000) return `€${(max / 1_000_000_000).toFixed(1)}B`;
      if (max >= 1_000_000) return `€${(max / 1_000_000).toFixed(1)}M`;
      if (max >= 1_000) return `€${(max / 1_000).toFixed(0)}K`;
      return `€${max}`;
    }

    // If it's already formatted with currency markers, keep it.
    if (normalized.includes('€') || normalized.toLowerCase().includes('eur')) return normalized;

    return `€${normalized}`;
  };

  const parseBudgetTable = (budgetText: string) => {
    if (!budgetText || budgetText === 'N/A') return null;
    
    const lines = budgetText.split('\n').filter(line => line.trim());
    const entries: Array<{topic: string, budget: string, stage: string, opening: string, deadline: string, contribution: string, grants: string}> = [];
    
    // Look for lines that start with HORIZON (topic IDs)
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      if (line.includes('HORIZON-') && !line.includes('Budget') && !line.includes('Topic')) {
        // Found a topic line, next lines contain the data
        const topicMatch = line.match(/(HORIZON-[\w-]+)/);
        const topic = topicMatch ? topicMatch[1] : line.substring(0, 60);
        
        // Try to find budget info in this line or next lines
        let budget = 'N/A';
        let stage = 'N/A';
        let opening = 'N/A';
        let deadline = 'N/A';
        let contribution = 'N/A';
        let grants = 'N/A';
        
        // Look for numbers in this line
        const budgetMatch = line.match(/(\d[\d\s,]+\d|\d+)/);
        if (budgetMatch) {
          const amount = budgetMatch[1].replace(/\s/g, '');
          const num = parseInt(amount);
          if (num >= 1000000) {
            budget = `€${(num / 1000000).toFixed(1)}M`;
          } else if (num >= 1000) {
            budget = `€${(num / 1000).toFixed(0)}K`;
          } else {
            budget = `€${num}`;
          }
        }
        
        entries.push({topic, budget, stage, opening, deadline, contribution, grants});
      }
    }
    
    return entries.length > 0 ? entries : null;
  };

  if (loading) {
    const currentAgentName = progress.agent || 'Initializing';
    const currentProgress = progress.progress || 5;
    const currentMessage = progress.message || 'Processing...';
    
    const currentAgentConfig = AGENTS.find(a => a.name === currentAgentName) || {
      name: 'Initializing',
      icon: 'power_settings_new',
      color: 'text-blue-500',
      bgColor: 'bg-blue-500'
    };

    return (
      <div className="text-center py-24">
        <div className="mb-8 relative inline-block">
          <div className="w-24 h-24 border-4 border-primary/20 border-t-primary rounded-full animate-spin"></div>
          <span className={`material-icons absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 ${currentAgentConfig.color} text-4xl`}>
            {currentAgentConfig.icon}
          </span>
        </div>

        <h2 className="text-2xl font-bold mb-2">
          <span className={currentAgentConfig.color}>{currentAgentName}</span> is working
        </h2>

        <p className="text-slate-500 max-w-md mx-auto mb-6">
          {currentMessage}
        </p>

        <div className="max-w-md mx-auto mb-4">
          <div className="h-3 bg-slate-200 dark:bg-slate-700 rounded-full overflow-hidden">
            <div 
              className={`h-full ${currentAgentConfig.bgColor} transition-all duration-500 ease-out`}
              style={{ width: `${currentProgress}%` }}
            ></div>
          </div>
          <p className="text-sm text-slate-400 mt-2">{currentProgress}% complete</p>
        </div>

        <div className="flex justify-center items-center gap-2 mt-8">
          {AGENTS.map((agent, index) => {
            const isCompleted = completedAgents.includes(agent.name);
            const isCurrent = currentAgentName === agent.name;
            
            return (
              <React.Fragment key={agent.name}>
                <div className={`flex flex-col items-center transition-all duration-300 ${
                  isCurrent ? 'opacity-100 scale-110' : isCompleted ? 'opacity-100' : 'opacity-40'
                }`}>
                  <div className={`w-10 h-10 rounded-full flex items-center justify-center mb-1 ${
                    isCompleted 
                      ? 'bg-green-500 text-white' 
                      : isCurrent 
                        ? `${agent.bgColor} text-white ring-4 ring-offset-2 ring-offset-white dark:ring-offset-slate-900` 
                        : 'bg-slate-200 dark:bg-slate-700 text-slate-400'
                  }`}>
                    <span className="material-icons text-lg">
                      {isCompleted ? 'check' : agent.icon}
                    </span>
                  </div>
                  <span className={`text-[10px] font-bold ${isCurrent ? agent.color : 'text-slate-500'}`}>
                    {agent.name}
                  </span>
                </div>
                {index < AGENTS.length - 1 && (
                  <div className={`w-6 h-0.5 transition-all duration-500 ${
                    isCompleted ? 'bg-green-500' : 'bg-slate-300 dark:bg-slate-600'
                  }`}></div>
                )}
              </React.Fragment>
            );
          })}
        </div>

        <p className="mt-8 text-sm text-slate-400">
          Analyzing opportunities for <span className="font-semibold text-slate-600 dark:text-slate-300">{company.companyName}</span>
        </p>
      </div>
    );
  }

  if (error || !result) {
    return (
      <div className="text-center py-24">
        <div className="inline-flex items-center justify-center p-4 bg-red-100 rounded-full mb-6">
          <span className="material-icons text-red-600 text-4xl">error_outline</span>
        </div>
        <h2 className="text-2xl font-bold mb-2">Something went wrong</h2>
        <p className="text-slate-500 mb-8">{error || 'No results found'}</p>
        <button 
          onClick={onReset}
          className="bg-primary text-white px-6 py-2 rounded-lg font-bold"
        >
          Try Again
        </button>
      </div>
    );
  }

  const { company_profile, company_summary, overall_assessment, funding_cards, top_recommendations } = result || {};
  
  // Ensure all required data exists with defaults
  const safeCompanyProfile = company_profile || { name: 'Unknown', type: '', country: '', employees: 0, description: '', domains: [] };
  const safeCompanySummary = company_summary || { profile_overview: '', key_strengths: [], recommended_focus_areas: [] };
  const safeOverallAssessment = overall_assessment || { total_opportunities: 0, high_priority_count: 0, medium_priority_count: 0, low_priority_count: 0, summary_text: '', strategic_advice: '' };
  const safeFundingCards = funding_cards || [];
  const safeTopRecommendations = top_recommendations || [];

  return (
    <div className="max-w-7xl mx-auto">
      {/* Header */}
      <div className="text-center mb-8">
        <div className="inline-flex items-center justify-center p-2 mb-4 bg-green-500/10 rounded-full">
          <span className="material-icons text-green-500 text-3xl">verified</span>
        </div>
        <h1 className="text-4xl font-extrabold text-eu-blue dark:text-white mb-3">
          Your EU Funding Matches
        </h1>
        <p className="text-lg text-slate-600 dark:text-slate-400">
          We found <span className="font-bold text-primary">{safeOverallAssessment.total_opportunities}</span> funding opportunities for {safeCompanyProfile.name}
        </p>
      </div>

      <div className="grid grid-cols-1 gap-8">
        {/* Company Profile Card - Displayed First */}
        <div className="bg-white dark:bg-slate-900 rounded-xl shadow-lg border border-slate-200 dark:border-slate-800 p-8">
          <div className="flex items-center gap-4 mb-6">
            <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center">
              <span className="material-icons text-primary text-3xl">business</span>
            </div>
            <div>
              <h3 className="font-bold text-xl text-slate-900 dark:text-white">{safeCompanyProfile.name}</h3>
              <p className="text-base text-slate-500">{safeCompanyProfile.type} • {safeCompanyProfile.country} • {safeCompanyProfile.employees} employees</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {/* Left Column */}
            <div className="space-y-6">
              <div className="bg-slate-50 dark:bg-slate-800/50 p-5 rounded-lg">
                <h4 className="text-sm font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider mb-3 flex items-center gap-2">
                  <span className="material-icons text-primary text-base">info</span>
                  Company Overview
                </h4>
                <p className="text-base text-slate-700 dark:text-slate-300 leading-relaxed">
                  {safeCompanySummary.profile_overview || safeCompanyProfile.description}
                </p>
              </div>

              <div className="bg-slate-50 dark:bg-slate-800/50 p-5 rounded-lg">
                <h4 className="text-sm font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider mb-3 flex items-center gap-2">
                  <span className="material-icons text-primary text-base">stars</span>
                  Key Strengths
                </h4>
                <div className="flex flex-wrap gap-2">
                  {safeCompanySummary.key_strengths?.length > 0 ? (
                    safeCompanySummary.key_strengths.map((strength, i) => (
                      <span key={i} className="px-3 py-1.5 bg-primary/10 text-primary text-sm font-medium rounded-full">
                        {strength}
                      </span>
                    ))
                  ) : (
                    safeCompanyProfile.domains?.map((domain, i) => (
                      <span key={i} className="px-3 py-1.5 bg-primary/10 text-primary text-sm font-medium rounded-full">
                        {domain.name}
                      </span>
                    ))
                  )}
                </div>
              </div>
            </div>

            {/* Right Column */}
            <div className="space-y-6">
              <div className="bg-slate-50 dark:bg-slate-800/50 p-5 rounded-lg">
                <h4 className="text-sm font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider mb-3 flex items-center gap-2">
                  <span className="material-icons text-primary text-base">assessment</span>
                  Results Summary
                </h4>
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-green-100 dark:bg-green-900/30 p-4 rounded-lg text-center">
                    <div className="text-3xl font-bold text-green-700 dark:text-green-400">{safeOverallAssessment.high_priority_count}</div>
                    <div className="text-sm text-green-700 dark:text-green-400 font-medium mt-1">High Priority</div>
                  </div>
                  <div className="bg-blue-100 dark:bg-blue-900/30 p-4 rounded-lg text-center">
                    <div className="text-3xl font-bold text-blue-700 dark:text-blue-400">{safeOverallAssessment.medium_priority_count}</div>
                    <div className="text-sm text-blue-700 dark:text-blue-400 font-medium mt-1">Medium Priority</div>
                  </div>
                </div>
                <div className="mt-4 text-center">
                  <span className="text-2xl font-bold text-slate-800 dark:text-slate-200">{safeOverallAssessment.total_opportunities}</span>
                  <span className="text-slate-600 dark:text-slate-400 ml-2">Total Opportunities Found</span>
                </div>
              </div>

              <div className="bg-slate-50 dark:bg-slate-800/50 p-5 rounded-lg">
                <h4 className="text-sm font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider mb-3 flex items-center gap-2">
                  <span className="material-icons text-primary text-base">lightbulb</span>
                  Strategic Advice
                </h4>
                <p className="text-base text-slate-700 dark:text-slate-300 leading-relaxed italic">
                  {safeOverallAssessment.strategic_advice}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Funding Cards */}
        <div className="space-y-6">
          {/* Top Recommendations Banner */}
          {safeTopRecommendations.length > 0 && (
            <div className="bg-gradient-to-r from-primary/10 to-primary/5 rounded-xl p-6 border border-primary/20">
              <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-4 flex items-center gap-2">
                <span className="material-icons text-primary">star</span>
                Top Recommendations
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {safeTopRecommendations.slice(0, 3).map((rec, i) => (
                  <div key={i} className="bg-white dark:bg-slate-800 rounded-lg p-4 shadow-sm">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="w-6 h-6 bg-primary text-white rounded-full flex items-center justify-center text-xs font-bold">
                        {rec.priority_rank}
                      </span>
                      <span className={`px-2 py-0.5 rounded-full text-xs font-bold ${getProbabilityColor(rec.success_probability)}`}>
                        {rec.success_probability}
                      </span>
                    </div>
                    <div className="text-2xl font-bold text-slate-900 dark:text-white mb-1">
                      {rec.match_percentage}%
                    </div>
                    <div className="text-xs text-slate-500 line-clamp-2">
                      {rec.why_recommended}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Funding Cards Grid */}
          <div className="grid grid-cols-1 gap-6">
            {safeFundingCards.map((card) => (
              <div 
                key={card.id} 
                className="bg-white dark:bg-slate-900 rounded-xl shadow-lg border border-slate-200 dark:border-slate-800 overflow-hidden hover:shadow-xl transition-all cursor-pointer group"
                onClick={() => setSelectedCard(card)}
              >
                {/* Card Header */}
                <div className="p-6">
                  <div className="flex justify-between items-start mb-4">
                    <div className="flex-1 pr-4">
                      <div className="flex items-center gap-2 mb-2">
                        <span className={`px-3 py-1 rounded-full text-sm font-bold border ${getMatchColor(card.match_percentage)}`}>
                          {card.match_percentage}% Match
                        </span>
                        {card.eligibility_passed && (
                          <span className="px-2 py-1 bg-green-100 text-green-700 text-xs font-bold rounded-full">
                            Eligible
                          </span>
                        )}
                      </div>
                      <h3 className="text-lg font-bold text-slate-900 dark:text-white group-hover:text-primary transition-colors line-clamp-2">
                        {card.title}
                      </h3>
                      {card.programme && (
                        <p className="text-sm text-slate-500 mt-1">{card.programme}</p>
                      )}
                    </div>
                  </div>

                  {/* Budget & Deadline */}
                  <div className="flex gap-4 mb-4">
                    <div className="flex items-center gap-2 text-slate-600 dark:text-slate-400" title="Total indicative topic budget (may be split across multiple grants)">
                      <span className="material-icons text-sm">account_balance</span>
                      <span className="text-sm font-semibold">{formatBudget(card.budget)}</span>
                      <span className="text-xs text-slate-400">total</span>
                    </div>

                    {card.contribution && card.contribution !== 'N/A' && (
                      <div className="flex items-center gap-2 text-slate-600 dark:text-slate-400" title="Indicative EU contribution per project (more actionable than total)">
                        <span className="material-icons text-sm">paid</span>
                        <span className="text-sm font-semibold">{card.contribution}</span>
                        <span className="text-xs text-slate-400">per project</span>
                      </div>
                    )}

                    <div className="flex items-center gap-2 text-red-500">
                      <span className="material-icons text-sm">event</span>
                      <span className="text-sm font-semibold">{card.deadline}</span>
                    </div>
                  </div>

                  {/* Summary - Full Text */}
                  <div className="mb-4 p-4 bg-gradient-to-br from-slate-50 via-blue-50/30 to-indigo-50/20 dark:from-slate-800/50 dark:via-slate-800/30 dark:to-slate-800/20 rounded-2xl shadow-inner border border-slate-200/60 dark:border-slate-700/40">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="material-icons text-primary/60 text-sm">description</span>
                      <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Summary</span>
                    </div>
                    <p className="text-slate-700 dark:text-slate-300 text-sm leading-relaxed whitespace-pre-wrap">
                      {card.short_summary || card.description}
                    </p>
                  </div>

                  {/* Budget Info */}
                  {card.content?.budget_overview && (
                    <div className="mb-4 p-3 bg-slate-50 dark:bg-slate-800 rounded-lg">
                      <h4 className="text-xs font-bold text-slate-600 dark:text-slate-400 uppercase mb-2">Budget Overview</h4>
                      {(() => {
                        const budgetEntries = parseBudgetTable(card.content.budget_overview);
                        if (budgetEntries) {
                          return (
                            <div className="overflow-x-auto">
                              <table className="w-full text-xs">
                                <thead>
                                  <tr className="border-b border-slate-300 dark:border-slate-700">
                                    <th className="text-left py-1 px-2">Topic</th>
                                    <th className="text-right py-1 px-2">Budget</th>
                                  </tr>
                                </thead>
                                <tbody>
                                  {budgetEntries.slice(0, 3).map((entry, idx) => (
                                    <tr key={idx} className="border-b border-slate-200 dark:border-slate-800">
                                      <td className="py-1 px-2 text-slate-700 dark:text-slate-300 truncate max-w-[200px]">{entry.topic}</td>
                                      <td className="py-1 px-2 text-right font-semibold text-green-600">{entry.budget}</td>
                                    </tr>
                                  ))}
                                </tbody>
                              </table>
                            </div>
                          );
                        }
                        return <p className="text-xs text-slate-500">{card.content.budget_overview.substring(0, 200)}...</p>;
                      })()}
                    </div>
                  )}

                  {/* Tags */}
                  <div className="flex flex-wrap gap-2 mb-4">
                    {card.tags.slice(0, 4).map((tag, i) => (
                      <span key={i} className="px-2 py-1 bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 text-xs rounded-full">
                        #{tag}
                      </span>
                    ))}
                    {card.tags.length > 4 && (
                      <span className="px-2 py-1 text-slate-400 text-xs">+{card.tags.length - 4}</span>
                    )}
                  </div>

                  {/* Action Button */}
                  <button className="w-full py-2 bg-primary/10 text-primary font-semibold rounded-lg hover:bg-primary hover:text-white transition-all flex items-center justify-center gap-2">
                    <span>View Full Details</span>
                    <span className="material-icons text-sm">arrow_forward</span>
                  </button>
                </div>
              </div>
            ))}
          </div>

          {/* No Results */}
          {safeFundingCards.length === 0 && (
            <div className="text-center py-12 bg-slate-50 dark:bg-slate-800 rounded-xl">
              <span className="material-icons text-4xl text-slate-400 mb-4">search_off</span>
              <h3 className="text-lg font-bold text-slate-700 dark:text-slate-300 mb-2">No matches found</h3>
              <p className="text-slate-500">Try adjusting your company profile or search criteria.</p>
            </div>
          )}

          {/* Reset Button */}
          <div className="pt-6 flex justify-center">
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

      {/* Full Details Modal */}
      {selectedCard && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" onClick={() => setSelectedCard(null)}>
          <div className="bg-white dark:bg-slate-900 rounded-2xl shadow-2xl max-w-3xl w-full max-h-[90vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
            <div className="p-8">
              {/* Modal Header */}
              <div className="flex justify-between items-start mb-6">
                <div>
                  <div className="flex items-center gap-3 mb-2">
                    <span className={`px-3 py-1 rounded-full text-sm font-bold border ${getMatchColor(selectedCard.match_percentage)}`}>
                      {selectedCard.match_percentage}% Match
                    </span>
                    <span className={`px-2 py-1 rounded-full text-xs font-bold ${getProbabilityColor(selectedCard.success_probability)}`}>
                      {selectedCard.success_probability} success probability
                    </span>
                  </div>
                  <h2 className="text-2xl font-bold text-slate-900 dark:text-white">{selectedCard.title}</h2>
                  {selectedCard.programme && (
                    <p className="text-slate-500 mt-1">{selectedCard.programme}</p>
                  )}
                </div>
                <button 
                  onClick={() => setSelectedCard(null)}
                  className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-full transition-colors"
                >
                  <span className="material-icons">close</span>
                </button>
              </div>

              {/* Key Info */}
              <div className="grid grid-cols-2 gap-4 mb-6">
                <div className="bg-slate-50 dark:bg-slate-800 p-4 rounded-lg">
                  <div className="flex items-center gap-2 text-slate-500 mb-1">
                    <span className="material-icons text-sm">euro</span>
                    <span className="text-xs font-bold uppercase">Budget</span>
                  </div>
                  <div className="text-xl font-bold text-slate-900 dark:text-white">{formatBudget(selectedCard.budget)}</div>
                </div>
                <div className="bg-slate-50 dark:bg-slate-800 p-4 rounded-lg">
                  <div className="flex items-center gap-2 text-slate-500 mb-1">
                    <span className="material-icons text-sm">event</span>
                    <span className="text-xs font-bold uppercase">Deadline</span>
                  </div>
                  <div className="text-xl font-bold text-red-600">{selectedCard.deadline}</div>
                </div>
              </div>

              {/* Description */}
              <div className="mb-6">
                <h3 className="text-sm font-bold text-slate-900 dark:text-white uppercase tracking-wider mb-2">About This Opportunity</h3>
                <div className="text-slate-600 dark:text-slate-400 leading-relaxed whitespace-pre-wrap max-h-96 overflow-y-auto">
                  {selectedCard.content?.description || selectedCard.description || 'No detailed description available.'}
                </div>
              </div>

              {/* Full Budget Table */}
              {selectedCard.content?.budget_overview && (
                <div className="mb-6">
                  <h3 className="text-sm font-bold text-slate-900 dark:text-white uppercase tracking-wider mb-2">Budget Information</h3>
                  <div className="bg-slate-50 dark:bg-slate-800 p-4 rounded-lg overflow-x-auto">
                    {(() => {
                      const budgetEntries = parseBudgetTable(selectedCard.content.budget_overview);
                      if (budgetEntries && budgetEntries.length > 0) {
                        return (
                          <table className="w-full text-sm">
                            <thead>
                              <tr className="border-b-2 border-slate-300 dark:border-slate-700">
                                <th className="text-left py-2 px-3 font-bold text-slate-700 dark:text-slate-300">Topic</th>
                                <th className="text-right py-2 px-3 font-bold text-slate-700 dark:text-slate-300">Budget</th>
                                <th className="text-center py-2 px-3 font-bold text-slate-700 dark:text-slate-300">Stage</th>
                                <th className="text-center py-2 px-3 font-bold text-slate-700 dark:text-slate-300">Deadline</th>
                              </tr>
                            </thead>
                            <tbody>
                              {budgetEntries.map((entry, idx) => (
                                <tr key={idx} className="border-b border-slate-200 dark:border-slate-700">
                                  <td className="py-2 px-3 text-slate-700 dark:text-slate-300 max-w-[300px] truncate" title={entry.topic}>{entry.topic}</td>
                                  <td className="py-2 px-3 text-right font-semibold text-green-600">{entry.budget}</td>
                                  <td className="py-2 px-3 text-center text-slate-600">{entry.stage}</td>
                                  <td className="py-2 px-3 text-center text-slate-600">{entry.deadline}</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        );
                      }
                      return (
                        <pre className="text-xs text-slate-600 dark:text-slate-400 whitespace-pre-wrap">
                          {selectedCard.content.budget_overview}
                        </pre>
                      );
                    })()}
                  </div>
                </div>
              )}

              {/* Why Recommended */}
              <div className="mb-6">
                <h3 className="text-sm font-bold text-slate-900 dark:text-white uppercase tracking-wider mb-2">Why This Matches Your Profile</h3>
                <p className="text-slate-600 dark:text-slate-400 leading-relaxed">
                  {selectedCard.why_recommended}
                </p>
              </div>

              {/* Key Benefits */}
              {selectedCard.key_benefits.length > 0 && (
                <div className="mb-6">
                  <h3 className="text-sm font-bold text-slate-900 dark:text-white uppercase tracking-wider mb-2">Key Benefits</h3>
                  <ul className="space-y-2">
                    {selectedCard.key_benefits.map((benefit, i) => (
                      <li key={i} className="flex items-start gap-2">
                        <span className="material-icons text-green-500 text-sm mt-0.5">check_circle</span>
                        <span className="text-slate-600 dark:text-slate-400">{benefit}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Action Items */}
              {selectedCard.action_items.length > 0 && (
                <div className="mb-6">
                  <h3 className="text-sm font-bold text-slate-900 dark:text-white uppercase tracking-wider mb-2">Recommended Actions</h3>
                  <ul className="space-y-2">
                    {selectedCard.action_items.map((action, i) => (
                      <li key={i} className="flex items-start gap-2">
                        <span className="material-icons text-primary text-sm mt-0.5">arrow_right</span>
                        <span className="text-slate-600 dark:text-slate-400">{action}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Suggested Partners */}
              {selectedCard.suggested_partners.length > 0 && (
                <div className="mb-6">
                  <h3 className="text-sm font-bold text-slate-900 dark:text-white uppercase tracking-wider mb-2">Suggested Partners</h3>
                  <div className="flex flex-wrap gap-2">
                    {selectedCard.suggested_partners.map((partner, i) => (
                      <span key={i} className="px-3 py-1 bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 text-sm rounded-full">
                        {partner}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Tags */}
              <div className="mb-8">
                <h3 className="text-sm font-bold text-slate-900 dark:text-white uppercase tracking-wider mb-2">Tags</h3>
                <div className="flex flex-wrap gap-2">
                  {selectedCard.tags.map((tag, i) => (
                    <span key={i} className="px-3 py-1 bg-primary/10 text-primary text-sm rounded-full">
                      #{tag}
                    </span>
                  ))}
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex gap-4">
                {selectedCard.url && (
                  <a 
                    href={selectedCard.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex-1 py-3 bg-primary text-white font-bold rounded-lg hover:bg-primary/90 transition-all flex items-center justify-center gap-2"
                  >
                    <span>View Official Call</span>
                    <span className="material-icons text-sm">open_in_new</span>
                  </a>
                )}
                <button 
                  onClick={() => setSelectedCard(null)}
                  className="px-6 py-3 border border-slate-300 dark:border-slate-700 text-slate-700 dark:text-slate-300 font-bold rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800 transition-all"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Step3Results;
