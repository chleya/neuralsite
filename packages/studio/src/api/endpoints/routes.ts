// NeuralSite Routes API Endpoints

import apiClient from '../client';
import { Route, RouteListParams, RouteListResponse } from '../types';

export const routesApi = {
  /**
   * List routes with pagination
   * GET /api/v1/routes
   */
  list: async (params?: RouteListParams): Promise<RouteListResponse> => {
    return apiClient.get<RouteListResponse>('/routes', params);
  },

  /**
   * Get a single route by ID
   * GET /api/v1/routes/:id
   */
  get: async (routeId: string): Promise<Route> => {
    return apiClient.get<Route>(`/routes/${routeId}`);
  },

  /**
   * Create a new route
   * POST /api/v1/routes
   */
  create: async (data: Partial<Route>): Promise<Route> => {
    return apiClient.post<Route>('/routes', data);
  },

  /**
   * Update a route
   * PUT /api/v1/routes/:id
   */
  update: async (routeId: string, data: Partial<Route>): Promise<Route> => {
    return apiClient.put<Route>(`/routes/${routeId}`, data);
  },

  /**
   * Delete a route
   * DELETE /api/v1/routes/:id
   */
  delete: async (routeId: string): Promise<void> => {
    return apiClient.delete<void>(`/routes/${routeId}`);
  },

  /**
   * Get routes by project
   * GET /api/v1/routes/by-project
   */
  getByProject: async (projectId: string): Promise<RouteListResponse> => {
    return apiClient.get<RouteListResponse>('/routes/by-project', { project_id: projectId });
  },
};

export default routesApi;
