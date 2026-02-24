import React, { useState } from 'react';
import { CompanyData, Domain } from '../types';

interface Step1Props {
  data: CompanyData;
  onChange: (data: Partial<CompanyData>) => void;
  onNext: () => void;
}

const Step1Company: React.FC<Step1Props> = ({ data, onChange, onNext }) => {
  const [newDomain, setNewDomain] = useState<Domain>({
    name: '',
    sub_domains: [],
    level: 'intermediate'
  });
  const [newSubDomain, setNewSubDomain] = useState('');

  // Major cities by EU country
  const citiesByCountry: Record<string, string[]> = {
    'Austria': ['Vienna', 'Graz', 'Linz', 'Salzburg', 'Innsbruck'],
    'Belgium': ['Brussels', 'Antwerp', 'Ghent', 'Charleroi', 'Liège'],
    'Bulgaria': ['Sofia', 'Plovdiv', 'Varna', 'Burgas', 'Ruse'],
    'Croatia': ['Zagreb', 'Split', 'Rijeka', 'Osijek', 'Zadar'],
    'Cyprus': ['Nicosia', 'Limassol', 'Larnaca', 'Famagusta', 'Paphos'],
    'Czech Republic': ['Prague', 'Brno', 'Ostrava', 'Plzen', 'Liberec'],
    'Denmark': ['Copenhagen', 'Aarhus', 'Odense', 'Aalborg', 'Esbjerg'],
    'Estonia': ['Tallinn', 'Tartu', 'Narva', 'Pärnu', 'Kohtla-Järve'],
    'Finland': ['Helsinki', 'Espoo', 'Tampere', 'Vantaa', 'Oulu'],
    'France': ['Paris', 'Marseille', 'Lyon', 'Toulouse', 'Nice', 'Nantes', 'Strasbourg', 'Montpellier', 'Bordeaux', 'Lille'],
    'Germany': ['Berlin', 'Hamburg', 'Munich', 'Cologne', 'Frankfurt', 'Stuttgart', 'Düsseldorf', 'Leipzig', 'Dortmund', 'Essen'],
    'Greece': ['Athens', 'Thessaloniki', 'Patras', 'Heraklion', 'Larissa'],
    'Hungary': ['Budapest', 'Debrecen', 'Szeged', 'Miskolc', 'Pécs'],
    'Ireland': ['Dublin', 'Cork', 'Limerick', 'Galway', 'Waterford'],
    'Italy': ['Rome', 'Milan', 'Naples', 'Turin', 'Palermo', 'Genoa', 'Bologna', 'Florence', 'Bari', 'Catania'],
    'Latvia': ['Riga', 'Daugavpils', 'Liepaja', 'Jelgava', 'Jurmala'],
    'Lithuania': ['Vilnius', 'Kaunas', 'Klaipeda', 'Siauliai', 'Panevezys'],
    'Luxembourg': ['Luxembourg City', 'Esch-sur-Alzette', 'Differdange', 'Dudelange', 'Ettelbruck'],
    'Malta': ['Valletta', 'Birkirkara', 'Mosta', 'Qormi', 'Sliema'],
    'Netherlands': ['Amsterdam', 'Rotterdam', 'The Hague', 'Utrecht', 'Eindhoven', 'Tilburg', 'Groningen', 'Almere', 'Breda', 'Nijmegen'],
    'Poland': ['Warsaw', 'Krakow', 'Lodz', 'Wroclaw', 'Poznan', 'Gdansk', 'Szczecin', 'Bydgoszcz', 'Lublin', 'Katowice'],
    'Portugal': ['Lisbon', 'Porto', 'Vila Nova de Gaia', 'Amadora', 'Braga'],
    'Romania': ['Bucharest', 'Cluj-Napoca', 'Timisoara', 'Iasi', 'Constanta'],
    'Slovakia': ['Bratislava', 'Kosice', 'Presov', 'Zilina', 'Nitra'],
    'Slovenia': ['Ljubljana', 'Maribor', 'Celje', 'Kranj', 'Velenje'],
    'Spain': ['Madrid', 'Barcelona', 'Valencia', 'Seville', 'Zaragoza', 'Malaga', 'Murcia', 'Palma', 'Las Palmas', 'Bilbao'],
    'Sweden': ['Stockholm', 'Gothenburg', 'Malmö', 'Uppsala', 'Västerås']
  };

  // Debug function to fill in sample data
  const fillDebugData = () => {
    onChange({
      companyName: 'RoboTech Solutions',
      orgType: 'SME',
      description: 'We are a robotics company specializing in AI-driven automation for industrial applications. Our expertise includes collaborative robots, machine vision systems, and autonomous navigation. We develop cutting-edge solutions for manufacturing, logistics, and service robotics sectors.',
      employees: 45,
      country: 'Germany',
      city: 'Munich',
      domains: [
        {
          name: 'Artificial Intelligence',
          sub_domains: ['Machine Learning', 'Computer Vision', 'Autonomous Systems'],
          level: 'advanced'
        },
        {
          name: 'Robotics',
          sub_domains: ['Industrial Robotics', 'Collaborative Robots', 'Autonomous Navigation'],
          level: 'expert'
        },
        {
          name: 'Manufacturing',
          sub_domains: ['Industry 4.0', 'Process Automation'],
          level: 'intermediate'
        }
      ]
    });
  };

  // Debug function to fill in sample data (SaaS / Market Research Tech)
  const fillDebugDataShopmetrics = () => {
    onChange({
      companyName: 'Shopmetrics Europe Ltd.',
      orgType: 'Other',
      description:
        'We provide an enterprise-class SaaS platform for mystery shopping, fieldwork, and market research providers worldwide. Our mission is to help clients improve business performance through service excellence using real-time, accurate data collection and AI-powered analytics. Our focus areas include Digital Transformation, CX (Customer Experience) Excellence, and automated fieldwork management.',
      employees: 47,
      country: 'Bulgaria',
      city: 'Varna',
      domains: [
        {
          name: 'Customer Experience (CX) Software',
          sub_domains: ['Cloud-based SaaS Platforms', 'Mystery Shopping Technology', 'Automated Workflow Services', 'Mobile Data Collection (Online/Offline)'],
          level: 'expert'
        },
        {
          name: 'Market Research Analytics',
          sub_domains: ['Quantitative & Qualitative Research', 'Business Intelligence (BI) & Reporting', 'AI-Powered Data Validation & Fraud Detection', 'Sentimetrics (Social Media Sentiment Analysis)'],
          level: 'expert'
        },
        {
          name: 'Service Excellence Consulting',
          sub_domains: ['Process Mapping & Re-engineering', 'Data Warehouse & Data Mart Solutions', 'Financial Impact Analysis & ROI Metrics'],
          level: 'advanced'
        }
      ]
    });
  };

  // Debug function to fill in sample data (Healthcare / AI Diagnostics)
  const fillDebugDataHealthAI = () => {
    onChange({
      companyName: 'MedVision AI',
      orgType: 'SME',
      description: 'We develop AI-powered medical imaging and diagnostic solutions for early disease detection. Our technology uses deep learning algorithms to analyze X-rays, MRIs, and CT scans with high accuracy, assisting radiologists and clinicians in making faster, more reliable diagnoses. We specialize in oncology screening, cardiovascular health monitoring, and neurological disorder detection.',
      employees: 32,
      country: 'Netherlands',
      city: 'Amsterdam',
      domains: [
        {
          name: 'Artificial Intelligence',
          sub_domains: ['Deep Learning', 'Medical Image Analysis', 'Neural Networks', 'Pattern Recognition'],
          level: 'expert'
        },
        {
          name: 'Healthcare Technology',
          sub_domains: ['Medical Imaging', 'Diagnostic Tools', 'Clinical Decision Support', 'Digital Health'],
          level: 'advanced'
        },
        {
          name: 'Biomedical Engineering',
          sub_domains: ['Medical Devices', 'Healthcare Software', 'Patient Monitoring Systems'],
          level: 'intermediate'
        }
      ]
    });
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onNext();
  };

  const isFormValid = 
    data.companyName && 
    data.description && 
    data.orgType && 
    data.employees > 0 && 
    data.country &&
    data.domains.length > 0;

  const addDomain = () => {
    if (newDomain.name.trim()) {
      onChange({ 
        domains: [...data.domains, { ...newDomain }] 
      });
      setNewDomain({ name: '', sub_domains: [], level: 'intermediate' });
    }
  };

  const removeDomain = (index: number) => {
    onChange({ 
      domains: data.domains.filter((_, i) => i !== index) 
    });
  };

  const addSubDomain = () => {
    if (newSubDomain.trim() && !newDomain.sub_domains.includes(newSubDomain.trim())) {
      setNewDomain({
        ...newDomain,
        sub_domains: [...newDomain.sub_domains, newSubDomain.trim()]
      });
      setNewSubDomain('');
    }
  };

  const removeSubDomain = (subDomain: string) => {
    setNewDomain({
      ...newDomain,
      sub_domains: newDomain.sub_domains.filter(sd => sd !== subDomain)
    });
  };

  return (
    <div>
      {/* Hero Section */}
      <div className="text-center mb-8">
        <div className="relative inline-flex items-center justify-center mb-4">
          {/* Soft rotating ring (slightly stronger) */}
          <div
            className="absolute -inset-4 rounded-full bg-gradient-to-r from-eu-blue/45 via-eu-yellow/35 to-eu-blue/45 blur-2xl opacity-80 animate-[spin_14s_linear_infinite]"
            aria-hidden="true"
          />

          {/* Secondary shimmer ring to add depth */}
          <div
            className="absolute -inset-2 rounded-full bg-gradient-to-r from-white/25 via-eu-yellow/15 to-white/25 blur-xl opacity-60 animate-[spin_22s_linear_infinite_reverse]"
            aria-hidden="true"
          />

          {/* Gentle floating glow */}
          <div
            className="absolute -inset-1 rounded-full bg-eu-blue/18 blur-lg opacity-90 animate-[float_5.5s_ease-in-out_infinite]"
            aria-hidden="true"
          />

          {/* Icon container (keeps your fade-in) */}
          <div className="relative inline-flex items-center justify-center p-3 bg-gradient-to-br from-primary/10 via-eu-yellow/5 to-primary/10 rounded-full opacity-0 animate-fade-in shadow-lg shadow-primary/20 border border-eu-yellow/20">
            {/* Animated glow ring */}
            <div className="absolute inset-0 rounded-full animate-ping-slow opacity-25 bg-gradient-to-r from-primary/20 to-eu-yellow/20"></div>
            
            {/* Shimmer effect overlay */}
            <div className="absolute inset-0 rounded-full overflow-hidden">
              <div className="absolute inset-0 bg-gradient-to-r from-transparent via-eu-yellow/20 to-transparent -translate-x-full animate-shimmer"></div>
            </div>

            <span className="material-icons text-primary text-3xl drop-shadow-[0_0_10px_rgba(255,204,0,0.4)] relative z-10">
              auto_awesome
            </span>
          </div>
        </div>

        <h1 className="text-4xl font-extrabold text-eu-blue dark:text-white mb-3 opacity-0 animate-fade-in-delay">
          EU Funding Matcher
        </h1>
        <p className="text-lg text-slate-600 dark:text-slate-400">
          Tell us about your organization to find matching grants using AI.
        </p>

        {/* Local keyframes to keep the animation self-contained */}
        <style>{`
          @keyframes float {
            0%, 100% { transform: translateY(0px); }
            50% { transform: translateY(-6px); }
          }
        `}</style>
      </div>

      <form onSubmit={handleSubmit} className="space-y-8">
        {/* Debug & Info Show Box */}
        <div className="bg-gradient-to-r from-primary/10 via-primary/5 to-eu-yellow/10 rounded-xl p-6 border border-primary/20 shadow-lg">
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 bg-primary/20 rounded-full flex items-center justify-center flex-shrink-0">
              <span className="material-icons text-primary text-2xl">lightbulb</span>
            </div>
            <div className="flex-1">
              <h3 className="font-bold text-slate-900 dark:text-white mb-2 flex items-center gap-2">
                <span>Welcome to EU Funding Matcher</span>
                <span className="px-2 py-0.5 bg-eu-yellow text-eu-blue text-xs font-bold rounded">BETA</span>
              </h3>
              <p className="text-sm text-slate-600 dark:text-slate-400 mb-4">
                This AI-powered tool analyzes your company profile and matches it with the latest EU funding opportunities. 
                Fill in your details below or use the debug button to see a sample robotics company profile.
              </p>
              <div className="flex flex-wrap gap-3">
                <button
                  type="button"
                  onClick={fillDebugData}
                  className="inline-flex items-center gap-2 px-4 py-2 bg-primary/10 text-primary rounded-lg font-medium hover:bg-primary hover:text-white transition-all border border-primary/30"
                >
                  <span className="material-icons text-sm">bug_report</span>
                  <span>Fill Debug Data (Robotics)</span>
                </button>
                <button
                  type="button"
                  onClick={fillDebugDataShopmetrics}
                  className="inline-flex items-center gap-2 px-4 py-2 bg-primary/10 text-primary rounded-lg font-medium hover:bg-primary hover:text-white transition-all border border-primary/30"
                >
                  <span className="material-icons text-sm">bug_report</span>
                  <span>Fill Debug Data (Shopmetrics)</span>
                </button>
                <button
                  type="button"
                  onClick={fillDebugDataHealthAI}
                  className="inline-flex items-center gap-2 px-4 py-2 bg-primary/10 text-primary rounded-lg font-medium hover:bg-primary hover:text-white transition-all border border-primary/30"
                >
                  <span className="material-icons text-sm">bug_report</span>
                  <span>Fill Debug Data (Health AI)</span>
                </button>
                <button
                  type="button"
                  onClick={() => {
                    onChange({
                      companyName: '',
                      orgType: '',
                      description: '',
                      employees: 0,
                      country: '',
                      city: '',
                      domains: []
                    });
                  }}
                  className="inline-flex items-center gap-2 px-4 py-2 bg-slate-100 text-slate-600 rounded-lg font-medium hover:bg-slate-200 transition-all border border-slate-300"
                >
                  <span className="material-icons text-sm">clear</span>
                  <span>Clear Form</span>
                </button>
              </div>
            </div>
          </div>
          
          {/* Feature Highlights */}
          <div className="mt-4 pt-4 border-t border-primary/10 grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="flex items-center gap-2 text-sm text-slate-600">
              <span className="material-icons text-primary text-lg">search</span>
              <span>AI-powered matching</span>
            </div>
            <div className="flex items-center gap-2 text-sm text-slate-600">
              <span className="material-icons text-primary text-lg">update</span>
              <span>Real-time EC data</span>
            </div>
            <div className="flex items-center gap-2 text-sm text-slate-600">
              <span className="material-icons text-primary text-lg">analytics</span>
              <span>Smart analysis</span>
            </div>
          </div>
        </div>

        {/* Section 1: Company Profile */}
        <div className="bg-white dark:bg-slate-900 rounded-xl shadow-xl shadow-primary/5 border border-slate-200 dark:border-slate-800 overflow-hidden">
          <div className="p-6 border-b border-slate-100 dark:border-slate-800 flex items-center gap-4 bg-slate-50/50 dark:bg-slate-800/50">
            <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center text-primary">
              <span className="material-icons">business</span>
            </div>
            <h2 className="text-lg font-bold text-slate-900 dark:text-white leading-none">Organization Details</h2>
          </div>
          
          <div className="p-6 space-y-6">
            {/* Company Name */}
            <div>
              <label className="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2" htmlFor="company-name">
                Company Name *
              </label>
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

            {/* Organization Type & Country */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2" htmlFor="org-type">
                  Organization Type *
                </label>
                <select 
                  required
                  className="w-full px-4 py-2.5 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent transition-all outline-none" 
                  id="org-type"
                  value={data.orgType}
                  onChange={(e) => onChange({ orgType: e.target.value })}
                >
                  <option value="">Select type</option>
                  <option value="SME">SME</option>
                  <option value="Large Enterprise">Large Enterprise</option>
                  <option value="NGO">NGO</option>
                  <option value="University">University</option>
                  <option value="Public Body">Public Body</option>
                  <option value="Other">Other</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2" htmlFor="country">
                  Country *
                </label>
                <select 
                  required
                  className="w-full px-4 py-2.5 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent transition-all outline-none" 
                  id="country"
                  value={data.country}
                  onChange={(e) => {
                    const newCountry = e.target.value;
                    onChange({ 
                      country: newCountry,
                      city: '' // Clear city when country changes
                    });
                  }}
                >
                  <option value="">Select country</option>
                  <option value="Austria">Austria</option>
                  <option value="Belgium">Belgium</option>
                  <option value="Bulgaria">Bulgaria</option>
                  <option value="Croatia">Croatia</option>
                  <option value="Cyprus">Cyprus</option>
                  <option value="Czech Republic">Czech Republic</option>
                  <option value="Denmark">Denmark</option>
                  <option value="Estonia">Estonia</option>
                  <option value="Finland">Finland</option>
                  <option value="France">France</option>
                  <option value="Germany">Germany</option>
                  <option value="Greece">Greece</option>
                  <option value="Hungary">Hungary</option>
                  <option value="Ireland">Ireland</option>
                  <option value="Italy">Italy</option>
                  <option value="Latvia">Latvia</option>
                  <option value="Lithuania">Lithuania</option>
                  <option value="Luxembourg">Luxembourg</option>
                  <option value="Malta">Malta</option>
                  <option value="Netherlands">Netherlands</option>
                  <option value="Poland">Poland</option>
                  <option value="Portugal">Portugal</option>
                  <option value="Romania">Romania</option>
                  <option value="Slovakia">Slovakia</option>
                  <option value="Slovenia">Slovenia</option>
                  <option value="Spain">Spain</option>
                  <option value="Sweden">Sweden</option>
                </select>
              </div>
            </div>

            {/* City & Employees */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2" htmlFor="city">
                  City
                </label>
                <select 
                  className="w-full px-4 py-2.5 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent transition-all outline-none disabled:opacity-50 disabled:cursor-not-allowed" 
                  id="city"
                  value={data.city}
                  onChange={(e) => onChange({ city: e.target.value })}
                  disabled={!data.country}
                >
                  <option value="">
                    {data.country ? 'Select city' : 'Select country first'}
                  </option>
                  {data.country && citiesByCountry[data.country]?.map((city) => (
                    <option key={city} value={city}>{city}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2" htmlFor="employees">
                  Number of Employees *
                </label>
                <input 
                  required
                  min="1"
                  className="w-full px-4 py-2.5 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent transition-all outline-none" 
                  id="employees" 
                  placeholder="e.g. 50" 
                  type="number"
                  value={data.employees || ''}
                  onChange={(e) => onChange({ employees: parseInt(e.target.value) || 0 })}
                />
              </div>
            </div>

            {/* Description */}
            <div>
              <label className="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2" htmlFor="description">
                Core Activities & Mission *
              </label>
              <textarea 
                required
                minLength={20}
                className="w-full px-4 py-2.5 bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent transition-all outline-none resize-none" 
                id="description" 
                placeholder="What does your company do? Mention your focus areas like Digital, Green Energy, Health, etc. for better AI matching." 
                rows={5}
                value={data.description}
                onChange={(e) => onChange({ description: e.target.value })}
              ></textarea>
              <p className="mt-2 text-xs text-slate-500">
                The more detail you provide about your mission, the more accurate the AI funding matches will be. Minimum 20 characters.
              </p>
            </div>
          </div>
        </div>

        {/* Section 2: Domains of Expertise */}
        <div className="bg-white dark:bg-slate-900 rounded-xl shadow-xl shadow-primary/5 border border-slate-200 dark:border-slate-800 overflow-hidden">
          <div className="p-6 border-b border-slate-100 dark:border-slate-800 flex items-center gap-4 bg-slate-50/50 dark:bg-slate-800/50">
            <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center text-primary">
              <span className="material-icons">psychology</span>
            </div>
            <h2 className="text-lg font-bold text-slate-900 dark:text-white leading-none">
              Domains of Expertise *
              <span className="text-sm font-normal text-slate-500 ml-2">(Add at least one)</span>
            </h2>
          </div>
          
          <div className="p-6 space-y-6">
            {/* Display existing domains */}
            {data.domains.length > 0 && (
              <div className="space-y-3">
                {data.domains.map((domain, index) => (
                  <div key={index} className="bg-slate-50 dark:bg-slate-800 p-4 rounded-lg border border-slate-200 dark:border-slate-700">
                    <div className="flex justify-between items-start mb-2">
                      <div>
                        <h4 className="font-semibold text-slate-900 dark:text-white">{domain.name}</h4>
                        <span className="text-xs px-2 py-1 bg-primary/10 text-primary rounded-full">
                          {domain.level}
                        </span>
                      </div>
                      <button
                        type="button"
                        onClick={() => removeDomain(index)}
                        className="text-red-500 hover:text-red-700"
                      >
                        <span className="material-icons text-sm">delete</span>
                      </button>
                    </div>
                    {domain.sub_domains.length > 0 && (
                      <div className="flex flex-wrap gap-2 mt-2">
                        {domain.sub_domains.map((sd, i) => (
                          <span key={i} className="text-xs px-2 py-1 bg-slate-200 dark:bg-slate-700 rounded-full">
                            {sd}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}

            {/* Add new domain form */}
            <div className="bg-slate-50 dark:bg-slate-800 p-4 rounded-lg border border-slate-200 dark:border-slate-700 space-y-4">
              <h4 className="font-semibold text-slate-700 dark:text-slate-300">Add Domain</h4>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">
                    Domain Name
                  </label>
                  <input
                    className="w-full px-3 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent transition-all outline-none text-sm"
                    placeholder="e.g. Artificial Intelligence"
                    value={newDomain.name}
                    onChange={(e) => setNewDomain({ ...newDomain, name: e.target.value })}
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">
                    Expertise Level
                  </label>
                  <select
                    className="w-full px-3 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent transition-all outline-none text-sm"
                    value={newDomain.level}
                    onChange={(e) => setNewDomain({ ...newDomain, level: e.target.value as Domain['level'] })}
                  >
                    <option value="beginner">Beginner</option>
                    <option value="intermediate">Intermediate</option>
                    <option value="advanced">Advanced</option>
                    <option value="expert">Expert</option>
                  </select>
                </div>
              </div>

              {/* Sub-domains */}
              <div>
                <label className="block text-xs font-semibold text-slate-600 dark:text-slate-400 mb-1">
                  Sub-domains / Specializations
                </label>
                <div className="flex gap-2 mb-2">
                  <input
                    className="flex-1 px-3 py-2 bg-white dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent transition-all outline-none text-sm"
                    placeholder="e.g. Machine Learning"
                    value={newSubDomain}
                    onChange={(e) => setNewSubDomain(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addSubDomain())}
                  />
                  <button
                    type="button"
                    onClick={addSubDomain}
                    className="px-4 py-2 bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-300 rounded-lg hover:bg-slate-300 dark:hover:bg-slate-600 transition-colors"
                  >
                    <span className="material-icons text-sm">add</span>
                  </button>
                </div>
                {newDomain.sub_domains.length > 0 && (
                  <div className="flex flex-wrap gap-2">
                    {newDomain.sub_domains.map((sd, i) => (
                      <span key={i} className="inline-flex items-center gap-1 text-xs px-2 py-1 bg-primary/10 text-primary rounded-full">
                        {sd}
                        <button
                          type="button"
                          onClick={() => removeSubDomain(sd)}
                          className="hover:text-primary/70"
                        >
                          <span className="material-icons text-xs">close</span>
                        </button>
                      </span>
                    ))}
                  </div>
                )}
              </div>

              <button
                type="button"
                onClick={addDomain}
                disabled={!newDomain.name.trim()}
                className="w-full py-2 bg-primary text-white rounded-lg font-medium disabled:bg-slate-300 disabled:cursor-not-allowed hover:bg-primary/90 transition-colors"
              >
                Add Domain
              </button>
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
        
        {!isFormValid && (
          <p className="text-center text-sm text-red-500">
            Please fill in all required fields (*) and add at least one domain
          </p>
        )}
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
