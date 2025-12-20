import axios, { AxiosError } from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '';

// Custom error class for API errors
export class ApiError extends Error {
  status: number;
  data: unknown;
  retryAfter?: number;

  constructor(message: string, status: number, data?: unknown, retryAfter?: number) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
    this.retryAfter = retryAfter;
  }
}

export const api = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 second timeout
});

// Request interceptor for adding request ID
api.interceptors.request.use((config) => {
  config.headers['X-Request-ID'] = `web-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  return config;
});

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response) {
      const status = error.response.status;
      const data = error.response.data as Record<string, unknown>;
      const retryAfter = error.response.headers['retry-after']
        ? parseInt(error.response.headers['retry-after'] as string, 10)
        : undefined;

      let message = 'An error occurred';

      if (status === 429) {
        message = 'Too many requests. Please wait and try again.';
      } else if (status === 400) {
        message = (data?.detail as string) || 'Invalid request';
      } else if (status === 500) {
        message = 'Server error. Please try again later.';
      } else if (status === 503) {
        message = 'Service temporarily unavailable';
      }

      throw new ApiError(message, status, data, retryAfter);
    } else if (error.request) {
      throw new ApiError('Network error. Please check your connection.', 0);
    } else {
      throw new ApiError(error.message || 'An unexpected error occurred', 0);
    }
  }
);

// Types
export interface Citation {
  document_name: string;
  borough: string;
  section: string | null;
  page_number: number | null;
  paragraph: string;
  relevance_score: number;
  chunk_id: string;
}

export interface SuggestedQuestion {
  question: string;
  category?: string;
}

export interface ChatResponse {
  session_id: string;
  message: string;
  citations: Citation[];
  suggested_questions: SuggestedQuestion[];
  detected_borough: string | null;
  detected_location: string | null;
  query_count: number;
  requires_email: boolean;
  processing_time_ms: number;
}

export interface ChatRequest {
  message: string;
  session_id?: string;
  borough?: string;
  include_sources?: boolean;
  stream?: boolean;
}

export interface LeadRequest {
  email: string;
  name?: string;
  phone?: string;
  postcode?: string;
  project_type?: string;
  session_id?: string;
  marketing_consent?: boolean;
}

export interface LeadResponse {
  success: boolean;
  lead_id: string | null;
  message: string;
  remaining_free_queries?: number;
}

export interface Borough {
  name: string;
  description: string;
}

export interface Topic {
  name: string;
  description: string;
  example_questions: string[];
}

// API functions
export async function sendChatMessage(request: ChatRequest): Promise<ChatResponse> {
  const response = await api.post<ChatResponse>('/chat/query', request);
  return response.data;
}

export async function captureLead(request: LeadRequest): Promise<LeadResponse> {
  const response = await api.post<LeadResponse>('/leads/capture', request);
  return response.data;
}

export async function getBoroughs(): Promise<{ boroughs: Borough[] }> {
  const response = await api.get<{ boroughs: Borough[] }>('/chat/boroughs');
  return response.data;
}

export async function getTopics(): Promise<{ topics: Topic[] }> {
  const response = await api.get<{ topics: Topic[] }>('/chat/topics');
  return response.data;
}

export async function submitFeedback(
  queryId: string,
  feedback: 'positive' | 'negative',
  comment?: string
): Promise<{ success: boolean; message: string }> {
  const response = await api.post('/chat/feedback', {
    query_id: queryId,
    feedback,
    comment,
  });
  return response.data;
}

export async function checkEmail(
  email: string
): Promise<{ exists: boolean; query_count: number; remaining_free_queries: number }> {
  const response = await api.post('/leads/check-email', null, {
    params: { email },
  });
  return response.data;
}
