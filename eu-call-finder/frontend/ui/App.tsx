import React, { useEffect, useMemo, useState } from 'react';
import Layout from './components/Layout';
import Step1Company from './components/Step1Company';
import Step3Results from './components/Step3Results';
import { CompanyData } from './types';

const HISTORY_SESSIONS_KEY = 'eurofundfinder:sessions:v1';
const MAX_SESSIONS = 20;

type SessionEntry = {
  id: string;
  createdAt: number;
  company: CompanyData;
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
      }))
      .filter((x) => x.id && Number.isFinite(x.createdAt) && x.company && typeof x.company.companyName === 'string')
      .slice(0, MAX_SESSIONS);
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

  const handleCompanyChange = (updates: Partial<CompanyData>) => {
    setCompanyData(prev => ({ ...prev, ...updates }));
  };

  const [sessionsVersion, setSessionsVersion] = useState(0);

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
    } catch {
      // ignore
    }
  };

  const nextStep = () => {
    setCurrentStep(prev => Math.min(prev + 1, 2));
    persistSession();
  };

  const reset = () => {
    setCurrentStep(1);
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

  const selectSession = (company: CompanyData) => {
    setCompanyData(company);
    setCurrentStep(2);
  };

  const clearSessions = () => {
    try {
      localStorage.removeItem(HISTORY_SESSIONS_KEY);
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
        />
      )}
    </Layout>
  );
};

export default App;
