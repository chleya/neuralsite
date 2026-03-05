// NeuralSite Issues API Endpoints

import apiClient from '../client';
import { Issue, IssueCreate, IssueUpdate, IssueListParams, IssueListResponse } from '../types';

export const issuesApi = {
  /**
   * List issues with filters and pagination
   * GET /api/v1/issues
   */
  list: async (params?: IssueListParams): Promise<IssueListResponse> => {
    return apiClient.get<IssueListResponse>('/issues', params);
  },

  /**
   * Get a single issue by ID
   * GET /api/v1/issues/:id
   */
  get: async (issueId: string): Promise<Issue> => {
    return apiClient.get<Issue>(`/issues/${issueId}`);
  },

  /**
   * Create a new issue
   * POST /api/v1/issues
   */
  create: async (data: IssueCreate): Promise<Issue> => {
    return apiClient.post<Issue>('/issues', data);
  },

  /**
   * Update an issue
   * PUT /api/v1/issues/:id
   */
  update: async (issueId: string, data: IssueUpdate): Promise<Issue> => {
    return apiClient.put<Issue>(`/issues/${issueId}`, data);
  },

  /**
   * Delete an issue
   * DELETE /api/v1/issues/:id
   */
  delete: async (issueId: string): Promise<void> => {
    return apiClient.delete<void>(`/issues/${issueId}`);
  },

  /**
   * Assign issue to a user
   * POST /api/v1/issues/:id/assign
   */
  assign: async (issueId: string, userId: string): Promise<Issue> => {
    return apiClient.post<Issue>(`/issues/${issueId}/assign`, { assigned_to: userId });
  },

  /**
   * Resolve an issue
   * POST /api/v1/issues/:id/resolve
   */
  resolve: async (issueId: string, resolutionNote?: string): Promise<Issue> => {
    return apiClient.post<Issue>(`/issues/${issueId}/resolve`, { resolution_note: resolutionNote });
  },

  /**
   * Close an issue
   * POST /api/v1/issues/:id/close
   */
  close: async (issueId: string): Promise<Issue> => {
    return apiClient.post<Issue>(`/issues/${issueId}/close`);
  },

  /**
   * Reopen an issue
   * POST /api/v1/issues/:id/reopen
   */
  reopen: async (issueId: string): Promise<Issue> => {
    return apiClient.post<Issue>(`/issues/${issueId}/reopen`);
  },

  /**
   * Add photos to an issue
   * POST /api/v1/issues/:id/photos
   */
  addPhotos: async (issueId: string, photoIds: string[]): Promise<Issue> => {
    return apiClient.post<Issue>(`/issues/${issueId}/photos`, { photo_ids: photoIds });
  },

  /**
   * Remove photos from an issue
   * DELETE /api/v1/issues/:id/photos
   */
  removePhotos: async (issueId: string, photoIds: string[]): Promise<Issue> => {
    return apiClient.delete<Issue>(`/issues/${issueId}/photos`, { data: { photo_ids: photoIds } });
  },

  /**
   * Get issues by station
   * GET /api/v1/issues/by-station
   */
  getByStation: async (station: number, projectId?: string): Promise<IssueListResponse> => {
    return apiClient.get<IssueListResponse>('/issues/by-station', { station, project_id: projectId });
  },

  /**
   * Get issue statistics
   * GET /api/v1/issues/stats
   */
  getStats: async (projectId?: string): Promise<{
    total: number;
    open: number;
    in_progress: number;
    resolved: number;
    closed: number;
    by_severity: Record<string, number>;
    by_type: Record<string, number>;
  }> => {
    return apiClient.get<{
      total: number;
      open: number;
      in_progress: number;
      resolved: number;
      closed: number;
      by_severity: Record<string, number>;
      by_type: Record<string, number>;
    }>('/issues/stats', { project_id: projectId });
  },
};

export default issuesApi;
