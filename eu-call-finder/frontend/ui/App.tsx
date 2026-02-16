
import React, { useState } from 'react';
import Layout from './components/Layout';
import Step1Company from './components/Step1Company';
import Step3Results from './components/Step3Results';
import { CompanyData } from './types';

const App: React.FC = () => {
  const [currentStep, setCurrentStep] = useState(1);
  const [companyData, setCompanyData] = useState<CompanyData>({
    companyName: '',
    website: '',
    orgType: '',
    description: '',
    employees: '',
    country: 'BG'
  });

  const handleCompanyChange = (updates: Partial<CompanyData>) => {
    setCompanyData(prev => ({ ...prev, ...updates }));
  };

  const nextStep = () => setCurrentStep(prev => Math.min(prev + 1, 2));
  const reset = () => {
    setCurrentStep(1);
    setCompanyData({
      companyName: '',
      website: '',
      orgType: '',
      description: '',
      employees: '',
      country: 'BG'
    });
  };

  return (
    <Layout step={currentStep} totalSteps={2}>
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
