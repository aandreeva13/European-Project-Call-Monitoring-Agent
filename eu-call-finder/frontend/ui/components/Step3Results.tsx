import React, { useEffect, useRef, useState } from 'react';
import { CompanyData, SearchResult, FundingCard, CompanySummary, CompanyProfile } from '../types';
import { searchFundingCallsStream, ProgressUpdate } from '../services/apiService';
import { exportProjectToPDF } from '../utils/pdfExport';
import { buildFundingDeadlineICS, downloadICS } from '../utils/ics';

interface LikedProject extends FundingCard {
  searchContext?: {
    companyName: string;
    sessionId?: string;
    searchedAt?: number;
  };
}

interface Step3Props {
  company: CompanyData;
  onReset: () => void;
  cachedResult?: SearchResult;
  onResultComplete?: (result: SearchResult) => void;
  likedProjects?: LikedProject[];
  onToggleLikedProject?: (project: FundingCard) => void;
  isProjectLiked?: (projectId: string) => boolean;
  showLikedOnly?: boolean;
}

const AGENTS = [
  { name: 'Safety Guard', icon: 'security', color: 'text-green-500', bgColor: 'bg-green-500' },
  { name: 'Smart Planner', icon: 'psychology', color: 'text-purple-500', bgColor: 'bg-purple-500' },
  { name: 'Retriever', icon: 'web', color: 'text-orange-500', bgColor: 'bg-orange-500' },
  { name: 'Analyzer', icon: 'analytics', color: 'text-pink-500', bgColor: 'bg-pink-500' },
  { name: 'Reporter', icon: 'summarize', color: 'text-indigo-500', bgColor: 'bg-indigo-500' }
];

const Step3Results: React.FC<Step3Props> = ({ company, onReset, cachedResult, onResultComplete, likedProjects = [], onToggleLikedProject, isProjectLiked, showLikedOnly = false }) => {
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
  const [sharedProjectId, setSharedProjectId] = useState<string | null>(null);
  const [copiedProjectId, setCopiedProjectId] = useState<string | null>(null);
  const hasStartedSearch = useRef(false);
  
  // Store onResultComplete in ref to avoid triggering useEffect when it changes
  const onResultCompleteRef = useRef(onResultComplete);
  onResultCompleteRef.current = onResultComplete;

  useEffect(() => {
    const readSharedProjectIdFromHash = () => {
      // Read shared project id from URL hash: #project=<id>
      try {
        const hash = window.location.hash || '';
        const m = hash.match(/(?:^|#|&)project=([^&]+)/);
        const pid = m ? decodeURIComponent(m[1]) : null;
        setSharedProjectId(pid);
      } catch {
        setSharedProjectId(null);
      }
    };

    // Read immediately on mount...
    readSharedProjectIdFromHash();
    // ...and keep it in sync when user pastes a share URL in the same tab.
    window.addEventListener('hashchange', readSharedProjectIdFromHash);

    // If showing liked projects only, don't run a search - just show the liked projects
    if (showLikedOnly) {
      console.log('Showing liked projects only, skipping search');
      setLoading(false);
      setCompletedAgents(AGENTS.map(a => a.name));
      return () => window.removeEventListener('hashchange', readSharedProjectIdFromHash);
    }

    // If a share link is opened (#project=<id>), do NOT force liked-only.
    // Instead, attempt to load the matching project from the user's cached sessions.
    // If found, show it via cachedResult; otherwise fall back to normal behavior.
    const hash = window.location.hash || '';
    const m = hash.match(/(?:^|#|&)project=([^&]+)/);
    const pid = m ? decodeURIComponent(m[1]) : null;
    if (pid) {
      setSharedProjectId(pid);

      try {
        const raw = localStorage.getItem('eurofundfinder:sessions:v1');
        if (raw) {
          const parsed = JSON.parse(raw);
          if (Array.isArray(parsed)) {
            for (const entry of parsed) {
              const cards = entry?.result?.funding_cards;
              if (Array.isArray(cards)) {
                const found = cards.find((c: any) => c?.id === pid);
                if (found) {
                  // Build a minimal SearchResult so the UI can render the single card.
                  const fallbackCompany = entry?.result?.company_profile || {
                    name: entry?.company?.companyName || company.companyName || 'Unknown',
                    type: entry?.company?.orgType || company.orgType || '',
                    country: entry?.company?.country || company.country || '',
                    city: entry?.company?.city || company.city || '',
                    employees: entry?.company?.employees || company.employees || 0,
                    description: entry?.company?.description || company.description || '',
                    domains: entry?.company?.domains || company.domains || [],
                  };

                  const minimalResult: any = {
                    company_profile: fallbackCompany,
                    company_summary: entry?.result?.company_summary || {
                      profile_overview: '',
                      key_strengths: [],
                      recommended_focus_areas: []
                    },
                    overall_assessment: entry?.result?.overall_assessment || {
                      total_opportunities: 1,
                      high_priority_count: 0,
                      medium_priority_count: 0,
                      low_priority_count: 0,
                      summary_text: '',
                      strategic_advice: ''
                    },
                    funding_cards: [found],
                    top_recommendations: []
                  };

                  setResult(minimalResult);
                  setLoading(false);
                  setCompletedAgents(AGENTS.map(a => a.name));
                  return () => window.removeEventListener('hashchange', readSharedProjectIdFromHash);
                }
              }
            }
          }
        }
      } catch {
        // ignore parsing errors; fallback to normal behavior
      }

      // No cached session contained this project id; show the normal landing/results behavior.
      setLoading(false);
      setCompletedAgents(AGENTS.map(a => a.name));
      return () => window.removeEventListener('hashchange', readSharedProjectIdFromHash);
    }

    // Prevent duplicate searches (React StrictMode double-mount)
    if (hasStartedSearch.current) {
      console.log('Search already started, skipping duplicate');
      return () => window.removeEventListener('hashchange', readSharedProjectIdFromHash);
    }

    // Set the flag immediately to prevent any race conditions
    hasStartedSearch.current = true;

    // If we have cached results, use them directly without searching
    // Check for valid SearchResult structure (must have company_profile)
    if (cachedResult && cachedResult.company_profile) {
      console.log('Using cached result:', cachedResult);
      setResult(cachedResult);
      setLoading(false);
      setCompletedAgents(AGENTS.map(a => a.name));
      return () => window.removeEventListener('hashchange', readSharedProjectIdFromHash);
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
        
        // Debug: Log first funding card details
        if (typedResult.funding_cards && typedResult.funding_cards.length > 0) {
          const firstCard = typedResult.funding_cards[0];
          console.log('[DEBUG] First funding card:', {
            id: firstCard.id,
            title: firstCard.title,
            hasProjectSummary: !!firstCard.project_summary,
            projectSummaryOverview: firstCard.project_summary?.overview?.substring(0, 100),
            whyRecommended: firstCard.why_recommended?.substring(0, 100),
            keyBenefitsCount: firstCard.key_benefits?.length,
            actionItemsCount: firstCard.action_items?.length,
          });
        }
        
        setResult(typedResult);
        setLoading(false);
        setCompletedAgents(AGENTS.map(a => a.name));
        // Persist the result to the session using ref to avoid re-triggering
        if (onResultCompleteRef.current) {
          onResultCompleteRef.current(typedResult);
        }
      },
      (errorMsg) => {
        console.error('Search error:', errorMsg);
        setError(errorMsg);
        setLoading(false);
      }
    );

    return () => {
      cleanup();
      // Reset the flag on unmount so future searches work
      hasStartedSearch.current = false;
    };
  }, [company, cachedResult, showLikedOnly]);

  const getMatchColor = (percentage: number) => {
    if (percentage >= 80) return 'text-green-700 bg-green-50 border-green-200';
    if (percentage >= 70) return 'text-blue-700 bg-blue-50 border-blue-200';
    if (percentage >= 60) return 'text-yellow-700 bg-yellow-50 border-yellow-200';
    return 'text-red-600 bg-red-50 border-red-200';
  };

  const getProbabilityColor = (probability: string) => {
    switch (probability) {
      case 'high': return 'text-green-700 bg-green-100';
      case 'medium': return 'text-blue-700 bg-blue-100';
      case 'low': return 'text-yellow-700 bg-yellow-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getRankColor = (matchPercentage: number) => {
    if (matchPercentage >= 80) return 'bg-green-400 hover:bg-green-500';
    if (matchPercentage >= 70) return 'bg-blue-400 hover:bg-blue-500';
    return 'bg-yellow-400 hover:bg-yellow-500';
  };

  const formatBudget = (budget: string) => {
    if (!budget || budget === 'N/A') return 'Budget N/A';

    const normalized = String(budget).replace(/\s+/g, ' ').trim();

    // Prefer big numbers from the text (e.g. "35 000 000") and format them.
    // The current UI bug (showing "€4") happens because we were matching small numbers first
    // (e.g. the "2027" year or "1" from "Showing 1–11").
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

  const parseObjectivesFromText = (text: string): { summary: string; objectives: string[] } => {
    if (!text) return { summary: '', objectives: [] };
    
    const sentences = text.match(/[^.!?]+[.!?]+/g) || [text];
    const summary = sentences.slice(0, 2).join(' ').trim();
    const remainingText = sentences.slice(2).join(' ');
    const objectives: string[] = [];
    
    const objectivePatterns = [
      /(?:aims?|objectives?|goals?|focus(?:es)?|seeks?|will)\s+(?:to\s+)?([^.,;]+)/gi,
      /(?:develop|create|establish|implement|support|enhance|improve)\s+([^.,;]+)/gi,
    ];
    
    objectivePatterns.forEach(pattern => {
      let match;
      while ((match = pattern.exec(remainingText)) !== null) {
        const objective = match[0].trim();
        if (objective.length > 10 && !objectives.includes(objective)) {
          objectives.push(objective);
        }
      }
    });
    
    if (objectives.length === 0 && remainingText.length > 20) {
      const chunks = remainingText.split(/[.!?]/).filter(s => s.trim().length > 15);
      objectives.push(...chunks.slice(0, 5).map(s => s.trim()));
    }
    
    return { summary, objectives: objectives.slice(0, 5) };
  };

  // Helper function to get icon based on partner type
  const getPartnerIcon = (partner: string): string => {
    const lowerPartner = partner.toLowerCase();
    if (lowerPartner.includes('universit') || lowerPartner.includes('academic') || lowerPartner.includes('college')) {
      return 'school';
    } else if (lowerPartner.includes('research') || lowerPartner.includes('institute') || lowerPartner.includes('fraunhofer') || lowerPartner.includes('max planck')) {
      return 'science';
    } else if (lowerPartner.includes('hospital') || lowerPartner.includes('medical') || lowerPartner.includes('clinic') || lowerPartner.includes('health')) {
      return 'local_hospital';
    } else if (lowerPartner.includes('sme') || lowerPartner.includes('startup') || lowerPartner.includes('small')) {
      return 'store';
    } else if (lowerPartner.includes('industry') || lowerPartner.includes('manufacturing') || lowerPartner.includes('factory')) {
      return 'factory';
    } else if (lowerPartner.includes('tech') || lowerPartner.includes('software') || lowerPartner.includes('it ') || lowerPartner.includes('digital')) {
      return 'computer';
    } else if (lowerPartner.includes('consult') || lowerPartner.includes('advisor')) {
      return 'support_agent';
    } else if (lowerPartner.includes('government') || lowerPartner.includes('public') || lowerPartner.includes('authority')) {
      return 'account_balance';
    } else if (lowerPartner.includes('ngo') || lowerPartner.includes('non-profit') || lowerPartner.includes('association')) {
      return 'volunteer_activism';
    } else {
      return 'business';
    }
  };

  const highlightTechnologiesAndStrengths = (text: string): React.ReactElement => {
    if (!text) return <span>{text}</span>;
    
    const techPatterns = [
      'artificial intelligence', 'AI', 'machine learning', 'ML', 'deep learning',
      'data analytics', 'big data', 'cloud computing', 'IoT', 'blockchain',
      'cybersecurity', 'renewable energy', 'sustainability', 'digital transformation',
      'research and development', 'R&D', 'innovation', 'technology',
      'software', 'hardware', 'automation', 'robotics', 'sensors',
      'algorithms', 'models', 'platforms', 'systems', 'infrastructure'
    ];
    
    const escapeRegExp = (string: string) => string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    const pattern = new RegExp(`\\b(${techPatterns.map(escapeRegExp).join('|')})\\b`, 'gi');
    
    const parts: Array<string | React.ReactElement> = [];
    let lastIndex = 0;
    let match;
    
    // Reset regex
    pattern.lastIndex = 0;
    
    while ((match = pattern.exec(text)) !== null) {
      // Add text before the match
      if (match.index > lastIndex) {
        parts.push(text.slice(lastIndex, match.index));
      }
      
      // Add the matched word as bold
      parts.push(
        <strong key={match.index} className="text-slate-800 dark:text-slate-200 font-semibold">
          {match[0]}
        </strong>
      );
      
      lastIndex = match.index + match[0].length;
    }
    
    // Add remaining text
    if (lastIndex < text.length) {
      parts.push(text.slice(lastIndex));
    }
    
    return <>{parts}</>;
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

        {/* Cancel Button */}
        <button
          onClick={() => {
            // Reset to stop the search and go back
            hasStartedSearch.current = false;
            setLoading(false);
            onReset();
          }}
          className="mt-6 px-4 py-2 bg-slate-100 text-slate-600 rounded-lg hover:bg-slate-200 transition-colors flex items-center gap-2 mx-auto"
        >
          <span className="material-icons text-sm">close</span>
          Cancel Search
        </button>
      </div>
    );
  }

  // Only show error state if there's an actual error, or if no result AND not showing liked projects
  if (error || (!result && !showLikedOnly)) {
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
  const safeCompanyProfile = company_profile || { name: 'Unknown', type: '', country: '', city: '', employees: 0, description: '', domains: [] };
  const safeCompanySummary = company_summary || { profile_overview: '', key_strengths: [], recommended_focus_areas: [] };
  const safeOverallAssessment = overall_assessment || { total_opportunities: 0, high_priority_count: 0, medium_priority_count: 0, low_priority_count: 0, summary_text: '', strategic_advice: '' };

  // UI filtering: do not show suggestions below 60% profile match.
  // Keeps the results page focused on relevant opportunities.
  const safeFundingCards = (funding_cards || []).filter(card => (card?.match_percentage ?? 0) >= 60);
  const safeTopRecommendations = (top_recommendations || []).filter(rec => (rec?.match_percentage ?? 0) >= 60);
  
  // When showing liked only, display ALL liked projects from all searches
  const displayCards = showLikedOnly ? likedProjects : safeFundingCards;

  // If a share link is opened (#project=<id>), only show that project (if present).
  const shareFilteredCards = sharedProjectId
    ? displayCards.filter(c => c.id === sharedProjectId)
    : displayCards;
  
  // Calculate counts based on ACTUAL displayed cards (not backend totals)
  const displayedTotal = shareFilteredCards.length;
  const displayedHigh = shareFilteredCards.filter(c => c.match_percentage >= 80).length;
  const displayedMedium = shareFilteredCards.filter(c => c.match_percentage >= 70 && c.match_percentage < 80).length;
  const displayedLow = shareFilteredCards.filter(c => c.match_percentage >= 60 && c.match_percentage < 70).length;

  return (
    <div className="max-w-7xl mx-auto">
      {/* Header */}
      <div className="text-center mb-8">
        <div className="inline-flex items-center justify-center p-2 mb-4 bg-green-500/10 rounded-full">
          <span className="material-icons text-green-500 text-3xl">{showLikedOnly ? 'star' : 'verified'}</span>
        </div>
        <h1 className="text-4xl font-extrabold text-eu-blue dark:text-white mb-3">
          {showLikedOnly ? 'Your Liked Projects' : 'Your EU Funding Matches'}
        </h1>
        <p className="text-lg text-slate-600 dark:text-slate-400">
          {showLikedOnly ? (
            <>You have <span className="font-bold text-primary">{displayedTotal}</span> liked projects</>
          ) : (
            <>We found <span className="font-bold text-primary">{displayedTotal}</span> funding opportunities for {safeCompanyProfile.name}</>
          )}
        </p>
      </div>

      <div className="grid grid-cols-1 gap-8">
        {/* Company Profile Card - Displayed First */}
        {!showLikedOnly && (
        <div className="bg-white dark:bg-slate-900 rounded-xl shadow-lg border border-slate-200 dark:border-slate-800 p-8">
          <div className="flex items-center gap-4 mb-6">
            <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center">
              <span className="material-icons text-primary text-3xl">business</span>
            </div>
            <div>
              <h3 className="font-bold text-xl text-slate-900 dark:text-white">{safeCompanyProfile.name}</h3>
              <p className="text-base text-slate-500">{safeCompanyProfile.type} • {safeCompanyProfile.city}{safeCompanyProfile.city && safeCompanyProfile.country ? ', ' : ''}{safeCompanyProfile.country} • {safeCompanyProfile.employees} employees</p>
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
                <div className="grid grid-cols-3 gap-3">
                  <div className="bg-green-100 dark:bg-green-900/30 p-3 rounded-lg text-center">
                    <div className="text-2xl font-bold text-green-700 dark:text-green-400">{displayedHigh}</div>
                    <div className="text-xs text-green-700 dark:text-green-400 font-medium mt-1">High Priority<br/>80%+</div>
                  </div>
                  <div className="bg-blue-100 dark:bg-blue-900/30 p-3 rounded-lg text-center">
                    <div className="text-2xl font-bold text-blue-700 dark:text-blue-400">{displayedMedium}</div>
                    <div className="text-xs text-blue-700 dark:text-blue-400 font-medium mt-1">Medium Priority<br/>70-79%</div>
                  </div>
                  <div className="bg-yellow-50 dark:bg-yellow-900/20 p-3 rounded-lg text-center border border-yellow-200 dark:border-yellow-800">
                    <div className="text-2xl font-bold text-yellow-700 dark:text-yellow-400">{displayedLow}</div>
                    <div className="text-xs text-yellow-700 dark:text-yellow-400 font-medium mt-1">Low Priority<br/>60-69%</div>
                  </div>
                </div>
                <div className="mt-4 text-center">
                  <span className="text-2xl font-bold text-slate-800 dark:text-slate-200">{displayedTotal}</span>
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
        )}

        {/* Funding Cards */}
        <div className="space-y-6">
          {/* Top Recommendations Banner - Hidden in liked-only mode */}
          {!showLikedOnly && safeTopRecommendations.length > 0 && (
            <div className="bg-gradient-to-r from-primary/10 to-primary/5 rounded-xl p-6 border border-primary/20">
              <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-4 flex items-center gap-2">
                <span className="material-icons text-primary">star</span>
                Top Recommendations
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {safeTopRecommendations.slice(0, 3).map((rec, i) => (
                  <div key={i} className="bg-white dark:bg-slate-800 rounded-lg p-5 shadow-sm hover:shadow-md transition-shadow">
                    <div className="flex items-center justify-between mb-3">
                      <span className={`w-8 h-8 text-white rounded-full flex items-center justify-center text-sm font-bold transition-colors ${getRankColor(rec.match_percentage)}`}>
                        {rec.priority_rank}
                      </span>
                      <span className={`px-2 py-1 rounded-full text-xs font-semibold ${getProbabilityColor(rec.success_probability)}`}>
                        {rec.success_probability} success
                      </span>
                    </div>

                    <div className="text-3xl font-bold text-slate-900 dark:text-white mb-2" title="Profile match based on your inputs and the call text. Not a funding success prediction.">
                      {rec.match_percentage}%
                      <span className="text-sm font-semibold text-slate-500 dark:text-slate-400 ml-2 align-middle">
                        Profile match
                      </span>
                    </div>

                    <div className="text-sm text-slate-600 dark:text-slate-400 leading-relaxed max-h-24 overflow-y-auto">
                      {rec.why_recommended}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Funding Cards Grid */}
          <div className="grid grid-cols-1 gap-6">
            {sharedProjectId && (
              <div className="p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-xl">
                <div className="flex items-center gap-2 text-blue-800 dark:text-blue-200 font-semibold">
                  <span className="material-icons text-sm">link</span>
                  Share link view
                </div>
                <div className="text-sm text-blue-700 dark:text-blue-300 mt-1">
                  Showing {shareFilteredCards.length} project(s) for id: <span className="font-mono">{sharedProjectId}</span>
                </div>
              </div>
            )}
            {shareFilteredCards.map((card) => (
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
                        <span
                          className={`px-3 py-1 rounded-full text-sm font-bold border ${getMatchColor(card.match_percentage)}`}
                          title="Profile match based on your inputs and the call text. Not a funding success prediction."
                        >
                          {card.match_percentage}% Profile match
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
                      {/* Search Context Badge - Only shown when viewing liked projects from all searches */}
                      {showLikedOnly && (card as LikedProject).searchContext && (
                        <div className="flex items-center gap-2 mt-2">
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-400 text-xs font-medium rounded-full">
                            <span className="material-icons text-xs">search</span>
                            Found for {(card as LikedProject).searchContext!.companyName}
                          </span>
                        </div>
                      )}
                    </div>
                    {/* Share Button */}
                    <button
                      type="button"
                      onClick={async (e) => {
                        e.stopPropagation();

                        const shareUrl = `${window.location.origin}${window.location.pathname}#project=${encodeURIComponent(card.id)}`;

                        try {
                          // Always copy to clipboard and show an inline confirmation.
                          if (navigator.clipboard?.writeText) {
                            await navigator.clipboard.writeText(shareUrl);
                          } else {
                            window.prompt('Copy this link:', shareUrl);
                          }

                          setCopiedProjectId(card.id);
                          window.setTimeout(() => {
                            setCopiedProjectId((prev) => (prev === card.id ? null : prev));
                          }, 1400);
                        } catch (err) {
                          console.warn('[share] failed', err);
                        }
                      }}
                      className={`p-1 transition-all hover:scale-110 ${
                        copiedProjectId === card.id
                          ? 'text-emerald-600'
                          : 'text-slate-400 hover:text-primary'
                      }`}
                      title={copiedProjectId === card.id ? 'Link copied' : 'Copy share link'}
                      aria-label={copiedProjectId === card.id ? 'Link copied' : 'Copy share link'}
                    >
                      <span className="material-icons text-[20px]">
                        {copiedProjectId === card.id ? 'done' : 'content_copy'}
                      </span>

                    </button>

                    {/* PDF Export Button */}
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        exportProjectToPDF(card, company.companyName);
                      }}
                      className="p-1 text-slate-400 hover:text-primary transition-all hover:scale-110"
                      title="Export to PDF"
                    >
                      <span className="material-icons text-[20px]">picture_as_pdf</span>
                    </button>

                    {/* Add to Calendar (.ics) */}
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        const { ics, filename } = buildFundingDeadlineICS(card);
                        downloadICS(filename, ics);
                      }}
                      className="p-1 text-slate-400 hover:text-primary transition-all hover:scale-110"
                      title="Add deadline to Google Calendar (.ics)"
                    >
                      <span className="material-icons text-[20px]">event_available</span>
                    </button>
                     
                    {/* Star Button */}
                    {onToggleLikedProject && isProjectLiked && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onToggleLikedProject(card);
                        }}
                        className={`p-1 transition-all hover:scale-110 ${
                          isProjectLiked(card.id)
                            ? 'text-yellow-500'
                            : 'text-slate-400 hover:text-yellow-500'
                        }`}
                        title={isProjectLiked(card.id) ? 'Remove from liked projects' : 'Add to liked projects'}
                      >
                        <span className="material-icons text-[20px]">
                          {isProjectLiked(card.id) ? 'star' : 'star_border'}
                        </span>
                      </button>
                    )}
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
                  <button 
                    className="w-full py-2 bg-primary/10 text-primary font-semibold rounded-lg hover:bg-primary hover:text-white transition-all flex items-center justify-center gap-2"
                  >
                    <span>View Full Details</span>
                    <span className="material-icons text-sm">arrow_forward</span>
                  </button>
                </div>
              </div>
            ))}
          </div>

          {/* No Results */}
          {shareFilteredCards.length === 0 && (
            <div className="text-center py-12 bg-slate-50 dark:bg-slate-800 rounded-xl">
              <span className="material-icons text-4xl text-slate-400 mb-4">search_off</span>
              <h3 className="text-lg font-bold text-slate-700 dark:text-slate-300 mb-2">
                {sharedProjectId ? 'Shared project not found in this session' : (showLikedOnly ? 'No liked projects yet' : 'No matches found')}
              </h3>
              <p className="text-slate-500">
                {sharedProjectId
                  ? 'This link points to a project id, but your browser does not have the matching results cached. Run a search again or open the project URL directly.'
                  : (showLikedOnly ? 'Star projects from your searches to see them here.' : 'Try adjusting your company profile or search criteria.')}
              </p>
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
          <div className="bg-white dark:bg-slate-900 rounded-2xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
            <div className="p-8">
              {/* Modal Header */}
              <div className="flex justify-between items-start mb-6">
                <div className="flex-1 pr-4">
                  <div className="flex items-center gap-3 mb-3">
                    <span className={`px-3 py-1 rounded-full text-sm font-bold border ${getMatchColor(selectedCard.match_percentage)}`}>
                      {selectedCard.match_percentage}% Match
                    </span>
                    {selectedCard.eligibility_passed && (
                      <span className="px-2 py-1 bg-green-100 text-green-700 text-xs font-bold rounded-full">
                        Eligible
                      </span>
                    )}
                  </div>
                  <h2 className="text-2xl font-bold text-slate-900 dark:text-white leading-tight">{selectedCard.title}</h2>
                  {selectedCard.programme && (
                    <p className="text-slate-500 mt-2 text-sm">{selectedCard.programme}</p>
                  )}
                </div>
                <button 
                  onClick={() => setSelectedCard(null)}
                  className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-full transition-colors"
                >
                  <span className="material-icons">close</span>
                </button>
              </div>

              {/* Summary Table - Budget & Deadline */}
              <div className="mb-8 bg-slate-50 dark:bg-slate-800 rounded-xl overflow-hidden border border-slate-200 dark:border-slate-700">
                <table className="w-full text-sm">
                  <thead className="bg-slate-100 dark:bg-slate-700">
                    <tr>
                      <th className="text-left py-3 px-4 font-bold text-slate-700 dark:text-slate-300 uppercase text-xs tracking-wider">Budget</th>
                      <th className="text-left py-3 px-4 font-bold text-slate-700 dark:text-slate-300 uppercase text-xs tracking-wider">Deadline</th>
                      <th className="text-left py-3 px-4 font-bold text-slate-700 dark:text-slate-300 uppercase text-xs tracking-wider">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr className="border-t border-slate-200 dark:border-slate-700">
                      <td className="py-4 px-4">
                        <div className="flex items-center gap-2">
                          <span className="text-xl font-bold text-slate-900 dark:text-white">{formatBudget(selectedCard.budget)}</span>
                        </div>
                        {selectedCard.contribution && selectedCard.contribution !== 'N/A' && (
                          <div className="text-xs text-slate-500 mt-1">{selectedCard.contribution} per project</div>
                        )}
                      </td>
                      <td className="py-4 px-4">
                        <div className="flex items-center gap-2">
                          <span className="material-icons text-red-500 text-lg">event</span>
                          <span className="text-lg font-bold text-red-600">{selectedCard.deadline}</span>
                        </div>
                      </td>
                      <td className="py-4 px-4">
                        <span className="inline-flex items-center gap-1 px-3 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 text-sm font-medium rounded-full">
                          <span className="material-icons text-sm">info</span>
                          {selectedCard.status || 'Open'}
                        </span>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>

              {/* About This Opportunity */}
              {(() => {
                const aboutText = selectedCard.project_summary?.overview || selectedCard.content?.description || selectedCard.description || selectedCard.short_summary || '';
                const { summary, objectives } = parseObjectivesFromText(aboutText);
                
                return (
                  <div className="mb-8">
                    <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-4 flex items-center gap-2">
                      <span className="material-icons text-primary">description</span>
                      About This Opportunity
                    </h3>
                    
                    {summary ? (
                      <div className="space-y-4">
                        <p className="text-slate-700 dark:text-slate-300 leading-relaxed text-base">
                          {summary}
                        </p>
                        
                        {objectives.length > 0 && (
                          <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4">
                            <h4 className="text-sm font-bold text-slate-700 dark:text-slate-300 mb-3 uppercase tracking-wider">Key Objectives</h4>
                            <ul className="space-y-2">
                              {objectives.map((objective, i) => (
                                <li key={i} className="flex items-start gap-2">
                                  <span className="material-icons text-primary text-sm mt-0.5">arrow_right</span>
                                  <span className="text-slate-700 dark:text-slate-300 capitalize">{objective}</span>
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    ) : (
                      <p className="text-slate-500 italic">No detailed description available.</p>
                    )}
                  </div>
                );
              })()}

              {/* Full Budget Table */}
              {selectedCard.content?.budget_overview && (
                <div className="mb-8">
                  <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-4 flex items-center gap-2">
                    <span className="material-icons text-primary">account_balance</span>
                    Budget Information
                  </h3>
                  <div className="bg-slate-50 dark:bg-slate-800 rounded-lg overflow-hidden border border-slate-200 dark:border-slate-700">
                    {(() => {
                      const budgetEntries = parseBudgetTable(selectedCard.content.budget_overview);
                      if (budgetEntries && budgetEntries.length > 0) {
                        return (
                          <table className="w-full text-sm">
                            <thead className="bg-slate-100 dark:bg-slate-700">
                              <tr>
                                <th className="text-left py-3 px-4 font-bold text-slate-700 dark:text-slate-300 uppercase text-xs tracking-wider">Topic</th>
                                <th className="text-right py-3 px-4 font-bold text-slate-700 dark:text-slate-300 uppercase text-xs tracking-wider">Budget</th>
                                <th className="text-center py-3 px-4 font-bold text-slate-700 dark:text-slate-300 uppercase text-xs tracking-wider">Stage</th>
                                <th className="text-center py-3 px-4 font-bold text-slate-700 dark:text-slate-300 uppercase text-xs tracking-wider">Deadline</th>
                              </tr>
                            </thead>
                            <tbody>
                              {budgetEntries.map((entry, idx) => (
                                <tr key={idx} className="border-t border-slate-200 dark:border-slate-700">
                                  <td className="py-3 px-4 text-slate-700 dark:text-slate-300 max-w-[300px] truncate" title={entry.topic}>{entry.topic}</td>
                                  <td className="py-3 px-4 text-right font-semibold text-green-600">{entry.budget}</td>
                                  <td className="py-3 px-4 text-center text-slate-600">{entry.stage}</td>
                                  <td className="py-3 px-4 text-center text-slate-600">{entry.deadline}</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        );
                      }
                      return (
                        <pre className="text-xs text-slate-600 dark:text-slate-400 whitespace-pre-wrap p-4">
                          {selectedCard.content.budget_overview}
                        </pre>
                      );
                    })()}
                  </div>
                </div>
              )}

              {/* Why This Matches Your Profile */}
              <div className="mb-8">
                <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-4 flex items-center gap-2">
                  <span className="material-icons text-primary">person_check</span>
                  Why This Matches Your Profile
                </h3>
                <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-5 border-l-4 border-green-500">
                  <p className="text-slate-700 dark:text-slate-300 leading-relaxed whitespace-pre-wrap">
                    {highlightTechnologiesAndStrengths(selectedCard.why_recommended)}
                  </p>
                </div>
              </div>

              {/* Key Benefits */}
              {selectedCard.key_benefits.length > 0 && (
                <div className="mb-8">
                  <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-4 flex items-center gap-2">
                    <span className="material-icons text-primary">stars</span>
                    Key Benefits
                  </h3>
                  <ul className="space-y-3">
                    {selectedCard.key_benefits.map((benefit, i) => (
                      <li key={i} className="flex items-start gap-3 bg-slate-50 dark:bg-slate-800 rounded-lg p-3">
                        <span className="material-icons text-green-500 text-lg">check_circle</span>
                        <span className="text-slate-700 dark:text-slate-300">{benefit}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Action Items */}
              {selectedCard.action_items.length > 0 && (
                <div className="mb-8">
                  <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-4 flex items-center gap-2">
                    <span className="material-icons text-primary">task_alt</span>
                    Recommended Actions
                  </h3>
                  <div className="space-y-3">
                    {selectedCard.action_items.map((action, i) => (
                      <div key={i} className="flex items-start gap-3 bg-amber-50 dark:bg-amber-900/20 rounded-lg p-4 border-l-4 border-amber-500">
                        <span className="material-icons text-amber-600 text-lg">arrow_forward</span>
                        <span className="text-slate-700 dark:text-slate-300 font-medium">{action}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Suggested Partners */}
              {selectedCard.suggested_partners.length > 0 && (
                <div className="mb-8">
                  <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-4 flex items-center gap-2">
                    <span className="material-icons text-primary">groups</span>
                    Suggested Partners
                  </h3>
                  <ul className="space-y-3">
                    {selectedCard.suggested_partners.map((partner, i) => (
                      <li key={i} className="flex items-start gap-3 rounded-lg p-3">
                        <span className="material-icons text-slate-400 text-lg mt-0.5">
                          {getPartnerIcon(partner)}
                        </span>
                        <span className="text-slate-700 dark:text-slate-300">{partner}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Tags */}
              {selectedCard.tags.length > 0 && (
                <div className="mb-8">
                  <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-4 flex items-center gap-2">
                    <span className="material-icons text-primary">label</span>
                    Tags
                  </h3>
                  <div className="flex flex-wrap gap-2">
                    {selectedCard.tags.map((tag, i) => (
                      <span key={i} className="px-3 py-1.5 bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 text-sm rounded-lg font-medium">
                        #{tag}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Action Buttons */}
              <div className="flex gap-4 pt-4 border-t border-slate-200 dark:border-slate-700">
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
                  className="px-8 py-3 border border-slate-300 dark:border-slate-700 text-slate-700 dark:text-slate-300 font-bold rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800 transition-all"
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
