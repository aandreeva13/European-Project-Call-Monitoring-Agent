import React, { useEffect, useMemo, useRef, useState } from 'react';
import Layout from './components/Layout';
import Step1Company from './components/Step1Company';
import Step3Results from './components/Step3Results';
import { CompanyData, SearchResult, FundingCard } from './types';

const HISTORY_SESSIONS_KEY = 'eurofundfinder:sessions:v1';
const LIKED_PROJECTS_KEY = 'eurofundfinder:liked:v1';
const MAX_SESSIONS = 20;

type SessionEntry = {
  id: string;
  createdAt: number;
  company: CompanyData;
  result?: SearchResult;
};

type LikedProject = FundingCard & {
  searchContext?: {
    companyName: string;
    sessionId?: string;
    searchedAt?: number;
  };
};

const readSessions = (): SessionEntry[] => {
  try {
    const raw = localStorage.getItem(HISTORY_SESSIONS_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    return parsed
      .filter((x) => x && typeof x === 'object')
      .map((x: any) => ({
        id: String(x.id ?? ''),
        createdAt: Number(x.createdAt ?? 0),
        company: x.company as CompanyData,
        result: x.result as SearchResult | undefined,
      }))
      .filter((x) => x.id && Number.isFinite(x.createdAt) && x.company && typeof x.company.companyName === 'string')
      .slice(0, MAX_SESSIONS);
  } catch {
    return [];
  }
};

const readLikedProjects = (): LikedProject[] => {
  try {
    const raw = localStorage.getItem(LIKED_PROJECTS_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    return parsed.filter((x) => x && typeof x === 'object' && x.id);
  } catch {
    return [];
  }
};

const App: React.FC = () => {
  const [currentStep, setCurrentStep] = useState(1);
  const [companyData, setCompanyData] = useState<CompanyData>({
    companyName: '',
    orgType: '',
    description: '',
    employees: 0,
    country: '',
    city: '',
    domains: []
  });
  const [cachedResult, setCachedResult] = useState<SearchResult | undefined>(undefined);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [likedProjects, setLikedProjects] = useState<LikedProject[]>([]);
  const [showLikedOnly, setShowLikedOnly] = useState(false);
  const [sessionsVersion, setSessionsVersion] = useState(0);

  // Deep links: if URL contains #project=<id>, jump directly to results step.
  // We do NOT force liked-only mode here because share links should work for any
  // project visible in results (not only liked projects).
  useEffect(() => {
    const syncFromHash = () => {
      try {
        const hash = window.location.hash || '';
        const m = hash.match(/(?:^|#|&)project=([^&]+)/);
        const pid = m ? decodeURIComponent(m[1]) : null;
        if (pid) {
          setCurrentStep(2);
        }
      } catch {
        // ignore
      }
    };

    syncFromHash();
    window.addEventListener('hashchange', syncFromHash);
    return () => window.removeEventListener('hashchange', syncFromHash);
  }, []);

  // Load liked projects on mount
  useEffect(() => {
    setLikedProjects(readLikedProjects());
  }, []);

  const handleCompanyChange = (updates: Partial<CompanyData>) => {
    setCompanyData(prev => ({ ...prev, ...updates }));
  };

  const sessions = useMemo((): SessionEntry[] => {
    return readSessions();
  }, [sessionsVersion]);

  useEffect(() => {
    const onStorage = (e: StorageEvent) => {
      if (e.key === HISTORY_SESSIONS_KEY) setSessionsVersion(v => v + 1);
    };
    window.addEventListener('storage', onStorage);
    return () => window.removeEventListener('storage', onStorage);
  }, []);

  const persistSession = () => {
    try {
      const entry: SessionEntry = {
        id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
        createdAt: Date.now(),
        company: companyData,
      };
      const next = [entry, ...sessions].slice(0, MAX_SESSIONS);
      localStorage.setItem(HISTORY_SESSIONS_KEY, JSON.stringify(next));
      setSessionsVersion(v => v + 1);
      setCurrentSessionId(entry.id);
    } catch {
      // ignore
    }
  };

  const toggleLikedProject = (project: FundingCard) => {
    try {
      const current = readLikedProjects();
      const isLiked = current.some(p => p.id === project.id);
      let next: LikedProject[];
      
      if (isLiked) {
        next = current.filter(p => p.id !== project.id);
      } else {
        // Add search context when liking a project
        const projectWithContext: LikedProject = {
          ...project,
          searchContext: {
            companyName: companyData.companyName || 'Unknown Company',
            sessionId: currentSessionId || undefined,
            searchedAt: Date.now()
          }
        };
        next = [projectWithContext, ...current];
      }
      
      localStorage.setItem(LIKED_PROJECTS_KEY, JSON.stringify(next));
      setLikedProjects(next);
    } catch (e) {
      console.warn('[likes] failed to toggle project', e);
    }
  };

  const isProjectLiked = (projectId: string): boolean => {
    return likedProjects.some(p => p.id === projectId);
  };

  const handleShowLikedProjects = () => {
    setShowLikedOnly(true);
    // Always go to step 2 when showing liked projects (needed when on step 1)
    if (currentStep === 1) {
      setCurrentStep(2);
    }
  };

  const handleShowAllProjects = () => {
    setShowLikedOnly(false);
  };

  const nextStep = () => {
    setCurrentStep(prev => Math.min(prev + 1, 2));
    setCachedResult(undefined); // Clear cached result for new search
    persistSession();
  };

  const reset = () => {
    setCurrentStep(1);
    setCachedResult(undefined);
    setShowLikedOnly(false);
    setCompanyData({
      companyName: '',
      orgType: '',
      description: '',
      employees: 0,
      country: '',
      city: '',
      domains: []
    });
  };

  const selectSession = (company: CompanyData, result?: SearchResult, sessionId?: string) => {
    setCompanyData(company);
    setCachedResult(result);
    setCurrentSessionId(sessionId || null);
    setShowLikedOnly(false);
    setCurrentStep(2);
  };

  // Use ref to always have latest currentSessionId without causing re-renders
  const currentSessionIdRef = useRef(currentSessionId);
  currentSessionIdRef.current = currentSessionId;

  const persistSessionResult = (result: SearchResult) => {
    try {
      const raw = localStorage.getItem(HISTORY_SESSIONS_KEY);
      if (!raw) return;
      const parsed = JSON.parse(raw);
      if (!Array.isArray(parsed)) return;
      
      // Find the session by ID using ref to get latest value
      const updated = parsed.map((entry: any) => {
        if (entry.id === currentSessionIdRef.current) {
          return { ...entry, result };
        }
        return entry;
      });
      
      localStorage.setItem(HISTORY_SESSIONS_KEY, JSON.stringify(updated));
      setSessionsVersion(v => v + 1);
    } catch {
      // ignore
    }
  };

  const clearSessions = () => {
    try {
      localStorage.removeItem(HISTORY_SESSIONS_KEY);
      setSessionsVersion(v => v + 1);
    } catch {
      // ignore
    }
  };

  const deleteSession = (sessionId: string) => {
    try {
      const raw = localStorage.getItem(HISTORY_SESSIONS_KEY);
      if (!raw) return;
      const parsed = JSON.parse(raw);
      if (!Array.isArray(parsed)) return;
      
      const filtered = parsed.filter((entry: any) => entry.id !== sessionId);
      localStorage.setItem(HISTORY_SESSIONS_KEY, JSON.stringify(filtered));
      setSessionsVersion(v => v + 1);
    } catch {
      // ignore
    }
  };

  return (
    <Layout
      step={currentStep}
      totalSteps={2}
      historySessions={sessions}
      onSelectHistory={selectSession}
      onClearHistory={clearSessions}
      onDeleteHistoryItem={deleteSession}
      onStartNewSearch={reset}
      likedProjectsCount={likedProjects.length}
      onShowLikedProjects={handleShowLikedProjects}
      showLikedOnly={showLikedOnly}
      onShowAllProjects={handleShowAllProjects}
    >
      {currentStep === 1 && (
        <Step1Company
          data={companyData}
          onChange={handleCompanyChange}
          onNext={nextStep}
        />
      )}
      {currentStep === 2 && (
        <Step3Results
          company={companyData}
          onReset={reset}
          cachedResult={cachedResult}
          onResultComplete={persistSessionResult}
          likedProjects={likedProjects}
          onToggleLikedProject={toggleLikedProject}
          isProjectLiked={isProjectLiked}
          showLikedOnly={showLikedOnly}
        />
      )}
    </Layout>
  );
};

export default App;
