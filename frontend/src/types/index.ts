/**
 * DevSmart Frontend Types
 */

export type ProjectType = 'greenfield' | 'incremental';

export interface Project {
  id: string;
  name: string;
  description?: string;
  current_phase: string;
  prd_version: number;
  project_type: ProjectType;
  source_path?: string;
  created_at: string;
  updated_at: string;
}

export interface OnboardingOption {
  value: string;
  label: string;
  description: string;
}

export interface OnboardingSection {
  type: 'textarea' | 'select';
  label: string;
  placeholder?: string;
  required: boolean;
  max_length?: number;
  options?: OnboardingOption[];
}

export interface OnboardingTemplate {
  template_version: string;
  sections: Record<string, OnboardingSection>;
}

export interface OnboardingData {
  requirement_description: string;
  backend_tech: string;
  frontend_tech: string;
  database: string;
  deployment: string;
}

export interface LLMSettings {
  id: string;
  llm_provider: string;
  llm_model: string;
  api_key: string;
  base_url: string;
  temperature: number;
  max_tokens: number;
  streaming: boolean;
  created_at: string;
  updated_at: string;
}

export interface Conversation {
  id: string;
  project_id: string;
  phase: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  token_count: number;
  completeness_score?: number;
  created_at: string;
}

export interface TestConnectionResult {
  status: 'success' | 'error';
  message: string;
  provider: string;
  model: string;
  response_time?: number;
}

export interface AvailableModels {
  provider: string;
  models: string[];
}