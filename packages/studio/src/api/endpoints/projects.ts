// NeuralSite Projects API Endpoints

import apiClient from '../client';
import { Project, ProjectListParams, ProjectListResponse } from '../types';

export const projectsApi = {
  /**
   * List projects with pagination
   * GET /api/v1/projects
   */
  list: async (params?: ProjectListParams): Promise<ProjectListResponse> => {
    return apiClient.get<ProjectListResponse>('/projects', params);
  },

  /**
   * Get a single project by ID
   * GET /api/v1/projects/:id
   */
  get: async (projectId: string): Promise<Project> => {
    return apiClient.get<Project>(`/projects/${projectId}`);
  },

  /**
   * Create a new project
   * POST /api/v1/projects
   */
  create: async (data: Partial<Project>): Promise<Project> => {
    return apiClient.post<Project>('/projects', data);
  },

  /**
   * Update a project
   * PUT /api/v1/projects/:id
   */
  update: async (projectId: string, data: Partial<Project>): Promise<Project> => {
    return apiClient.put<Project>(`/projects/${projectId}`, data);
  },

  /**
   * Delete a project
   * DELETE /api/v1/projects/:id
   */
  delete: async (projectId: string): Promise<void> => {
    return apiClient.delete<void>(`/projects/${projectId}`);
  },
};

export default projectsApi;
