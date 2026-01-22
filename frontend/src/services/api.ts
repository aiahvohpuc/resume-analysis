/** API Service for Resume Analysis Backend */

import type {
  NewResumeAnalysisResponse,
  ResumeAnalysisRequest,
  ResumeAnalysisResponse,
  ResumeParseResponse,
  SkillAnalysisResponse,
} from '../types/api';

const API_BASE_URL = import.meta.env.VITE_API_URL || '';

class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

async function fetchApi<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new ApiError(
      response.status,
      errorData.detail || `HTTP Error: ${response.status}`
    );
  }

  return response.json();
}

export const api = {
  /** Analyze resume and get AI feedback (legacy v1) */
  analyzeResume: (request: ResumeAnalysisRequest): Promise<ResumeAnalysisResponse> =>
    fetchApi('/api/feedback/resume', {
      method: 'POST',
      body: JSON.stringify(request),
    }),

  /** Analyze resume and get AI feedback (v2 - redesigned) */
  analyzeResumeV2: (request: ResumeAnalysisRequest): Promise<NewResumeAnalysisResponse> =>
    fetchApi('/api/feedback/resume/v2', {
      method: 'POST',
      body: JSON.stringify(request),
    }),

  /** Extract and analyze skills from text */
  analyzeSkills: (
    text: string,
    requirements?: string[]
  ): Promise<SkillAnalysisResponse> =>
    fetchApi('/api/analyze/skills', {
      method: 'POST',
      body: JSON.stringify({ text, requirements }),
    }),

  /** Parse resume text and extract structure */
  parseResume: (
    text: string,
    jobRequirements?: string[]
  ): Promise<ResumeParseResponse> =>
    fetchApi('/api/analyze/resume', {
      method: 'POST',
      body: JSON.stringify({ text, job_requirements: jobRequirements }),
    }),

  /** List available organizations */
  getOrganizations: (): Promise<string[]> =>
    fetchApi('/api/organizations'),

  /** Get organization details */
  getOrganization: (code: string): Promise<Record<string, unknown>> =>
    fetchApi(`/api/organizations/${code}`),

  /** Health check */
  healthCheck: (): Promise<{ status: string; version: string }> =>
    fetchApi('/health'),

  /** Upload PDF and extract text */
  uploadPdf: async (file: File): Promise<{ text: string }> => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE_URL}/api/upload/pdf`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new ApiError(
        response.status,
        errorData.detail || `HTTP Error: ${response.status}`
      );
    }

    return response.json();
  },
};

export { ApiError };
