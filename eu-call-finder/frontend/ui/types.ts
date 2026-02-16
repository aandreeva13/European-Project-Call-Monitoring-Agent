
export interface CompanyData {
  companyName: string;
  website: string;
  orgType: string;
  description: string;
  employees: string;
  country: string;
}

export interface FundingCall {
  id: string;
  title: string;
  description: string;
  deadline: string;
  budget: string;
  matchScore: number;
  tags: string[];
}
