export interface Domain {
  name: string;
  sub_domains: string[];
  level: 'beginner' | 'intermediate' | 'advanced' | 'expert';
}

export interface CompanyData {
  companyName: string;
  orgType: string;
  description: string;
  employees: number;
  country: string;
  city: string;
  domains: Domain[];
}

export interface FundingCard {
  id: string;
  title: string;
  programme: string;
  description: string;
  short_summary: string;
  project_summary?: {
    overview: string;
    company_fit_assessment: string;
    key_alignment_points: string[];
    potential_challenges: string[];
    recommendation: string;
  };
  match_percentage: number;
  relevance_score: number;
  eligibility_passed: boolean;
  budget: string;
  contribution?: string;
  deadline: string;
  url: string;
  status: string;
  tags: string[];
  why_recommended: string;
  key_benefits: string[];
  action_items: string[];
  success_probability: 'high' | 'medium' | 'low';
  domain_matches: Array<{
    domain: string;
    relevance: string;
  }>;
  suggested_partners: string[];
  content?: {
    description?: string;
    budget_overview?: string;
    destination?: string;
    conditions?: string;
  };
}

export interface CompanyProfile {
  name: string;
  type: string;
  country: string;
  employees: number;
  description: string;
  domains: Domain[];
}

export interface CompanySummary {
  profile_overview: string;
  key_strengths: string[];
  recommended_focus_areas: string[];
}

export interface OverallAssessment {
  total_opportunities: number;
  high_priority_count: number;
  medium_priority_count: number;
  low_priority_count: number;
  summary_text: string;
  strategic_advice: string;
}

export interface TopRecommendation {
  call_id: string;
  priority_rank: number;
  match_percentage: number;
  why_recommended: string;
  success_probability: 'high' | 'medium' | 'low';
}

export interface SearchResult {
  company_profile: CompanyProfile;
  company_summary: CompanySummary;
  overall_assessment: OverallAssessment;
  funding_cards: FundingCard[];
  top_recommendations: TopRecommendation[];
  total_calls: number;
  report_type: string;
  generated_at: string;
}

// Legacy interface for backward compatibility
export interface FundingCall {
  id: string;
  title: string;
  description: string;
  deadline: string;
  budget: string;
  matchScore: number;
  tags: string[];
  url?: string;
  status?: string;
  programme?: string;
  eligibilityPassed?: boolean;
  relevanceScore?: number;
  recommendation?: string;
}
