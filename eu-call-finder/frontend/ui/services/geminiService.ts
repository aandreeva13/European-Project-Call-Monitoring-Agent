
import { GoogleGenAI, Type } from "@google/genai";
import { CompanyData, FundingCall } from "../types";

const ai = new GoogleGenAI({ apiKey: process.env.API_KEY || '' });

export const getFundingMatches = async (
  company: CompanyData
): Promise<FundingCall[]> => {
  const prompt = `
    Based on the following company profile, find 3 relevant (simulated but realistic) EU funding calls from the Funding & Tenders portal (Horizon Europe, Digital Europe, etc.).
    
    Company Profile:
    - Name: ${company.companyName}
    - Type: ${company.orgType}
    - Description: ${company.description}
    - Country: ${company.country}
    - Employees: ${company.employees}

    Analyze the company's core activities and automatically determine the most suitable funding topics, budget ranges, and urgency levels.
    
    Return a list of opportunities that match this organization's profile.
  `;

  const response = await ai.models.generateContent({
    model: 'gemini-3-flash-preview',
    contents: prompt,
    config: {
      responseMimeType: "application/json",
      responseSchema: {
        type: Type.ARRAY,
        items: {
          type: Type.OBJECT,
          properties: {
            id: { type: Type.STRING },
            title: { type: Type.STRING },
            description: { type: Type.STRING },
            deadline: { type: Type.STRING },
            budget: { type: Type.STRING },
            matchScore: { type: Type.NUMBER },
            tags: { 
              type: Type.ARRAY,
              items: { type: Type.STRING }
            }
          },
          required: ["id", "title", "description", "deadline", "budget", "matchScore", "tags"]
        }
      }
    }
  });

  try {
    const results = JSON.parse(response.text || '[]');
    return results;
  } catch (e) {
    console.error("Failed to parse Gemini response", e);
    return [];
  }
};
