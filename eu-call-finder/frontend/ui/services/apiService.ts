import { CompanyData, FundingCall } from '../types';

// In dev, prefer Vite proxy (relative URL) to avoid CORS/network issues.
// Override with VITE_API_URL (e.g. http://localhost:8000/api) when needed.
const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

// Helper: add a timeout so fetch doesn't hang forever and returns a clearer error.
const fetchWithTimeout = async (
  input: RequestInfo | URL,
  init?: RequestInit,
  timeoutMs = 120_000
) => {
  // If the caller already supplied an AbortSignal (e.g. the SSE stream cleanup controller),
  // do NOT add our own timeout abort controller. Otherwise we'd override the caller signal
  // and unintentionally abort long-running streaming requests.
  if (init?.signal) {
    return fetch(input, init);
  }

  const controller = new AbortController();
  const id = window.setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(input, {
      ...init,
      signal: controller.signal,
    });
    return response;
  } finally {
    window.clearTimeout(id);
  }
};

export interface SearchRequest {
  company: {
    name: string;
    description: string;
    type: string;
    employees: number;
    country: string;
    city?: string;
    domains: Array<{
      name: string;
      sub_domains: string[];
      level: string;
    }>;
  };
  keywords?: string[];
}

export interface SearchResponse {
  company_name: string;
  search_date: string;
  total_calls: number;
  calls: FundingCall[];
  summary: string;
}

export interface ProgressUpdate {
  agent: string;
  progress: number;
  message: string;
  status: string;
}

export type ProgressCallback = (update: ProgressUpdate) => void;

/**
 * Search for EU funding calls with real-time progress updates via SSE.
 * 
 * This function connects to the SSE endpoint and calls the progress callback
 * as each agent completes its work.
 */
export const searchFundingCallsStream = (
  companyData: CompanyData,
  onProgress: ProgressCallback,
  // The backend sends a full SearchResult-like object on `complete`.
  onComplete: (result: unknown) => void,
  onError: (error: string) => void
): (() => void) => {
  // Transform CompanyData to backend format
  const request: SearchRequest = {
    company: {
      name: companyData.companyName,
      description: companyData.description,
      type: companyData.orgType,
      employees: companyData.employees,
      country: companyData.country,
      city: companyData.city || undefined,
      domains: companyData.domains.map(d => ({
        name: d.name,
        sub_domains: d.sub_domains,
        level: d.level
      }))
    }
  };

  console.log('Connecting to SSE stream with POST...');
  
  const abortController = new AbortController();
  let isClosed = false;

  // Use fetch to connect to SSE endpoint
  fetchWithTimeout(`${API_BASE_URL}/search/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'text/event-stream',
    },
    body: JSON.stringify(request),
    // NOTE: For proper cleanup and to prevent duplicate re-runs (React StrictMode / remounts),
    // we DO pass a signal so we can abort the streaming request.
    signal: abortController.signal,
  }).then(async (response) => {
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    if (!response.body) {
      throw new Error('No response body');
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    // Read the stream
    while (true) {
      if (isClosed) {
        try { await reader.cancel(); } catch {}
        break;
      }

      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      
      // Process SSE messages (format: "event: xxx\ndata: yyy\n\n")
      const messages = buffer.split('\n\n');
      buffer = messages.pop() || ''; // Keep incomplete message in buffer

      for (const message of messages) {
        if (!message.trim()) continue;

        const lines = message.split('\n');
        let eventType = 'message';
        let data = '';

        for (const line of lines) {
          if (line.startsWith('event:')) {
            eventType = line.substring(6).trim();
          } else if (line.startsWith('data:')) {
            data = line.substring(5).trim();
          }
        }

        if (!data) continue;

        try {
          const parsed = JSON.parse(data);
          console.log(`[SSE] ${eventType}:`, parsed);
          
           switch (eventType) {
             case 'progress':
               if (!isClosed) onProgress(parsed as ProgressUpdate);
               break;
             case 'complete':
               console.log('[SSE] Complete! Result:', parsed);
               // Guard against double-complete in case of duplicate streams
               if (!isClosed) {
                 isClosed = true;
                 // Pass the entire result object, not just calls
                 onComplete(parsed);
                 abortController.abort();
               }
               break;
             case 'error':
               console.error('[SSE] Error:', parsed.error);
               if (!isClosed) {
                 isClosed = true;
                 onError(parsed.error || 'Unknown error');
                 abortController.abort();
               }
               break;
           }
} catch (e) {
          console.error('[SSE] Failed to parse:', data, e);
        }
      }
    }

    console.log('[SSE] Stream ended');
  }).catch((error) => {
    // React StrictMode / route changes / explicit cleanup will abort the request.
    // Treat that as a normal cancellation, not a user-facing error.
    if (error?.name === 'AbortError') {
      console.log('[SSE] Request aborted');
      return;
    }

    console.error('[SSE] Fetch error:', error);

    // If backend/proxy closes the stream or the network flakes, browsers often surface
    // this as a generic TypeError("Failed to fetch"). Provide a clearer message.
    const msg =
      (error && typeof error.message === 'string' && error.message) ||
      'Request timed out or was aborted';

    onError(msg);
  });

   // Return cleanup function
  return () => {
    if (isClosed) return;
    isClosed = true;
    console.log('[SSE] Aborting request...');
    abortController.abort();
  };
};
/**
 * Search for EU funding calls matching a company profile (non-streaming).
 * 
 * This function calls the backend API which runs the complete workflow:
 * - Validates company input
 * - Plans search strategy
 * - Scrapes EU Funding & Tenders Portal
 * - Analyzes and scores calls
 * - Returns ranked matches
 */
export const searchFundingCalls = async (
  companyData: CompanyData
): Promise<FundingCall[]> => {
  try {
    // Transform CompanyData to backend format - include all fields
    const request: SearchRequest = {
      company: {
        name: companyData.companyName,
        description: companyData.description,
        type: companyData.orgType,
        employees: companyData.employees,
        country: companyData.country,
        city: companyData.city || undefined,
        domains: companyData.domains.map(d => ({
          name: d.name,
          sub_domains: d.sub_domains,
          level: d.level
        }))
      }
    };

    console.log('Sending request to backend:', JSON.stringify(request, null, 2));

    const response = await fetchWithTimeout(`${API_BASE_URL}/search`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      console.error('Backend error:', errorData);
      throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
    }

    const data: SearchResponse = await response.json();
    console.log('Received response:', data);
    return data.calls;
  } catch (error) {
    console.error('Error searching funding calls:', error);
    throw error;
  }
};

/**
 * Health check for the backend API.
 */
export const checkApiHealth = async (): Promise<boolean> => {
  try {
    const response = await fetchWithTimeout(`${API_BASE_URL}/health`, undefined, 10_000);
    return response.ok;
  } catch {
    return false;
  }
};
