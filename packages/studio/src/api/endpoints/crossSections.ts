// NeuralSite CrossSections API Endpoints

import apiClient from '../client';
import { 
  CrossSection, 
  CrossSectionCreate, 
  CrossSectionUpdate, 
  CrossSectionListParams, 
  CrossSectionListResponse 
} from '../types';

export const crossSectionsApi = {
  /**
   * List cross sections with filters and pagination
   * GET /api/v1/cross-sections
   */
  list: async (params?: CrossSectionListParams): Promise<CrossSectionListResponse> => {
    return apiClient.get<CrossSectionListResponse>('/cross-sections', params);
  },

  /**
   * Get a single cross section by ID
   * GET /api/v1/cross-sections/:id
   */
  get: async (csId: string): Promise<CrossSection> => {
    return apiClient.get<CrossSection>(`/cross-sections/${csId}`);
  },

  /**
   * Get cross section by station number
   * GET /api/v1/cross-sections/by-station
   */
  getByStation: async (station: number, routeId?: string): Promise<CrossSection> => {
    return apiClient.get<CrossSection>('/cross-sections/by-station', { station, route_id: routeId });
  },

  /**
   * Create a new cross section
   * POST /api/v1/cross-sections
   */
  create: async (data: CrossSectionCreate): Promise<CrossSection> => {
    return apiClient.post<CrossSection>('/cross-sections', data);
  },

  /**
   * Batch create cross sections
   * POST /api/v1/cross-sections/batch
   */
  createBatch: async (crossSections: CrossSectionCreate[]): Promise<CrossSection[]> => {
    return apiClient.post<CrossSection[]>('/cross-sections/batch', { cross_sections: crossSections });
  },

  /**
   * Update a cross section
   * PUT /api/v1/cross-sections/:id
   */
  update: async (csId: string, data: CrossSectionUpdate): Promise<CrossSection> => {
    return apiClient.put<CrossSection>(`/cross-sections/${csId}`, data);
  },

  /**
   * Delete a cross section
   * DELETE /api/v1/cross-sections/:id
   */
  delete: async (csId: string): Promise<void> => {
    return apiClient.delete<void>(`/cross-sections/${csId}`);
  },

  /**
   * Import cross sections from data
   * POST /api/v1/cross-sections/import
   */
  import: async (data: CrossSectionCreate[]): Promise<{ success: number; failed: number; errors: string[] }> => {
    return apiClient.post<{ success: number; failed: number; errors: string[] }>('/cross-sections/import', { cross_sections: data });
  },

  /**
   * Export cross sections to data
   * GET /api/v1/cross-sections/export
   */
  export: async (params?: CrossSectionListParams): Promise<CrossSection[]> => {
    return apiClient.get<CrossSection[]>('/cross-sections/export', params);
  },
};

export default crossSectionsApi;
