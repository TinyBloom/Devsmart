/**
 * DevSmart API Service
 */

import axios from 'axios';
import type { Project, LLMSettings, TestConnectionResult, AvailableModels, ProjectType, OnboardingTemplate, OnboardingData } from '../types';

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
});

interface CreateProjectRequest {
  name: string;
  description?: string;
  project_type?: ProjectType;
  source_path?: string;
  onboarding_data?: OnboardingData;
}

// 项目管理 API
export const projectApi = {
  async createProject(data: CreateProjectRequest): Promise<Project> {
    const response = await api.post('/projects', data);
    return response.data;
  },

  async getProjects(search?: string): Promise<Project[]> {
    const response = await api.get('/projects', { params: { search } });
    return response.data;
  },

  async getProject(name: string): Promise<Project> {
    const response = await api.get(`/projects/${name}`);
    return response.data;
  },

  async updateProject(name: string, data: Partial<Project>): Promise<Project> {
    const response = await api.put(`/projects/${name}`, data);
    return response.data;
  },

  async deleteProject(name: string): Promise<void> {
    await api.delete(`/projects/${name}`);
  },

  async getOnboardingTemplate(): Promise<OnboardingTemplate> {
    const response = await api.get('/projects/onboarding/template');
    return response.data;
  },

  async scanProject(name: string): Promise<any> {
    const response = await api.post(`/projects/${name}/scan`);
    return response.data;
  },

  async generateDeltaPrd(name: string, data: { conversation_history: any[]; previous_prd_path?: string }): Promise<any> {
    const response = await api.post(`/projects/${name}/delta-prd`, data);
    return response.data;
  },

  async getPrdHistory(name: string): Promise<any> {
    const response = await api.get(`/projects/${name}/prd-history`);
    return response.data;
  },
};

// LLM 设置 API
export const settingsApi = {
  async getSettings(): Promise<LLMSettings> {
    const response = await api.get('/settings');
    return response.data;
  },

  async updateSettings(settings: Partial<LLMSettings>): Promise<LLMSettings> {
    const response = await api.put('/settings', settings);
    return response.data;
  },

  async testConnection(): Promise<TestConnectionResult> {
    const response = await api.post('/settings/test');
    return response.data;
  },

  async getModels(provider: string): Promise<AvailableModels> {
    const response = await api.get(`/settings/models/${provider}`);
    return response.data;
  },
};

export default api;