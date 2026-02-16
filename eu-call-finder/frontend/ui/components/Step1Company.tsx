
import React from 'react';
import { CompanyData } from '../types';

interface Step1Props {
  data: CompanyData;
  onChange: (data: Partial<CompanyData>) => void;
  onNext: () => void;
}

const Step1Company: React.FC<Step1Props> = ({ data, onChange, onNext }) => {
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onNext();
  };

  const isFormValid = data.companyName && data.description && data.orgType;

  return (
    <div>
      {/* Hero Section */}
      <div className="text-center mb-10">
        <div className="inline-flex items-center justify-center p-2 mb-4 bg-eu-blue/5 rounded-full">
          <span className="material-icons text-eu-blue text-3xl">auto_awesome</span>
        </div>
        <h1 className="text-4xl font-extrabold text-eu-blue dark:text-white mb-3">
          EU Funding Matcher
        </h1>
        <p className="text-lg text-slate-600 dark:text-slate-400">
          Tell us about your organization to find matching grants using AI.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-8">
        {/* Section 1: Company Profile */}
        <div className="bg-white dark:bg-slate-900 rounded-xl shadow-xl shadow-primary/5 border border-slate-200 dark:border-slate-800 overflow-hidden">
          <div className="p-6 border-b border-slate-100 dark:border-slate-800 flex items-center gap-4 bg-slate-50/50 dark:bg-slate-800/50">
            <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center text-primary">
              <span className="material-icons">business</span>
            </div>
            <h2 className="text-lg font-bold text-slate-900 dark:text-white leading-none">Organization Details</h2>
          </div>
          
          <div className="p-6 space-y-6">
            <div>
              <label className="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2" htmlFor="company-name">Company Name</label>
              <input 
                required
                className="w-full px-4 py-2.5 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent transition-all outline-none" 
                id="company-name" 
                placeholder="e.g. Innovatech Solutions Ltd." 
                type="text"
                value={data.companyName}
                onChange={(e) => onChange({ companyName: e.target.value })}
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2" htmlFor="org-type">Organization Type</label>
                <select 
                  className="w-full px-4 py-2.5 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent transition-all outline-none" 
                  id="org-type"
                  value={data.orgType}
                  onChange={(e) => onChange({ orgType: e.target.value })}
                >
                  <option value="">Select type</option>
                  <option value="sme">SME</option>
                  <option value="startup">Start-up</option>
                  <option value="ngo">NGO</option>
                  <option value="academic">Academic</option>
                  <option value="public">Public</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2" htmlFor="country">Country</label>
                <select 
                  className="w-full px-4 py-2.5 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent transition-all outline-none" 
                  id="country"
                  value={data.country}
                  onChange={(e) => onChange({ country: e.target.value })}
                >
                  <option value="BG">Bulgaria</option>
                  <option value="BE">Belgium</option>
                  <option value="DE">Germany</option>
                  <option value="FR">France</option>
                  <option value="IT">Italy</option>
                  <option value="ES">Spain</option>
                  <option value="PL">Poland</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2" htmlFor="description">Core Activities & Mission</label>
              <textarea 
                required
                className="w-full px-4 py-2.5 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent transition-all outline-none resize-none" 
                id="description" 
                placeholder="What does your company do? Mention your focus areas like Digital, Green Energy, Health, etc. for better AI matching." 
                rows={5}
                value={data.description}
                onChange={(e) => onChange({ description: e.target.value })}
              ></textarea>
              <p className="mt-2 text-xs text-slate-500">
                The more detail you provide about your mission, the more accurate the AI funding matches will be.
              </p>
            </div>
          </div>
        </div>

        <div className="flex justify-center pt-4">
          <button 
            disabled={!isFormValid}
            className={`w-full max-w-md py-4 rounded-xl font-bold shadow-lg flex items-center justify-center gap-3 transition-all transform hover:-translate-y-1 active:translate-y-0 ${
              isFormValid 
                ? 'bg-primary text-white shadow-primary/25 hover:bg-primary/90' 
                : 'bg-slate-200 text-slate-400 cursor-not-allowed shadow-none'
            }`}
            type="submit"
          >
            Find Grants for {data.companyName || 'your company'}
            <span className="material-icons">rocket_launch</span>
          </button>
        </div>
      </form>

      <div className="mt-12 flex items-center justify-center gap-6 opacity-40">
        <div className="flex items-center gap-2">
          <img alt="EU Flag" className="h-4 rounded-sm" src="https://upload.wikimedia.org/wikipedia/commons/b/b7/Flag_of_Europe.svg" />
          <span className="text-[10px] font-bold uppercase tracking-widest">EC Portal Data</span>
        </div>
        <div className="h-4 w-px bg-slate-300 dark:bg-slate-700"></div>
        <div className="flex items-center gap-2">
          <span className="material-icons text-xs">auto_awesome</span>
          <span className="text-[10px] font-bold uppercase tracking-widest">AI Powered</span>
        </div>
      </div>
    </div>
  );
};

export default Step1Company;
