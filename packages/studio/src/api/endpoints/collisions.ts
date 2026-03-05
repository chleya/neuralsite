/**
 * Collisions API Endpoints
 * 碰撞数据API接口
 */

import apiClient from '../client'
import {
  CollisionPoint,
  CollisionListParams,
  CollisionListResponse,
  CollisionCreate,
  CollisionUpdate,
  CollisionStatistics,
  CollisionDetectionResult,
  CollisionBatchOperation,
  CollisionExport,
  CollisionLOD,
} from '../../types/collision'

export const collisionsApi = {
  /**
   * List collisions with filters and pagination
   * GET /api/v1/collisions
   */
  list: async (params?: CollisionListParams): Promise<CollisionListResponse> => {
    return apiClient.get<CollisionListResponse>('/collisions', params)
  },

  /**
   * Get a single collision by ID
   * GET /api/v1/collisions/:id
   */
  get: async (collisionId: string): Promise<CollisionPoint> => {
    return apiClient.get<CollisionPoint>(`/collisions/${collisionId}`)
  },

  /**
   * Get collisions by project
   * GET /api/v1/collisions/by-project/:projectId
   */
  getByProject: async (
    projectId: string,
    params?: Partial<CollisionListParams>
  ): Promise<CollisionListResponse> => {
    return apiClient.get<CollisionListResponse>(`/collisions/by-project/${projectId}`, params)
  },

  /**
   * Get collisions by route
   * GET /api/v1/collisions/by-route/:routeId
   */
  getByRoute: async (
    routeId: string,
    params?: Partial<CollisionListParams>
  ): Promise<CollisionListResponse> => {
    return apiClient.get<CollisionListResponse>(`/collisions/by-route/${routeId}`, params)
  },

  /**
   * Get collisions by station range
   * GET /api/v1/collisions/by-station
   */
  getByStationRange: async (
    projectId: string,
    startStation: number,
    endStation: number,
    params?: Partial<CollisionListParams>
  ): Promise<CollisionListResponse> => {
    return apiClient.get<CollisionListResponse>('/collisions/by-station', {
      project_id: projectId,
      station_min: startStation,
      station_max: endStation,
      ...params,
    })
  },

  /**
   * Get collision statistics
   * GET /api/v1/collisions/statistics/:projectId
   */
  getStatistics: async (
    projectId: string,
    routeId?: string
  ): Promise<CollisionStatistics> => {
    return apiClient.get<CollisionStatistics>(`/collisions/statistics/${projectId}`, {
      route_id: routeId,
    })
  },

  /**
   * Create a new collision
   * POST /api/v1/collisions
   */
  create: async (data: CollisionCreate): Promise<CollisionPoint> => {
    return apiClient.post<CollisionPoint>('/collisions', data)
  },

  /**
   * Batch create collisions
   * POST /api/v1/collisions/batch
   */
  createBatch: async (collisions: CollisionCreate[]): Promise<CollisionPoint[]> => {
    return apiClient.post<CollisionPoint[]>('/collisions/batch', { collisions })
  },

  /**
   * Update a collision
   * PUT /api/v1/collisions/:id
   */
  update: async (collisionId: string, data: CollisionUpdate): Promise<CollisionPoint> => {
    return apiClient.put<CollisionPoint>(`/collisions/${collisionId}`, data)
  },

  /**
   * Batch update collisions
   * PUT /api/v1/collisions/batch
   */
  updateBatch: async (operation: CollisionBatchOperation): Promise<CollisionPoint[]> => {
    return apiClient.put<CollisionPoint[]>('/collisions/batch', operation)
  },

  /**
   * Delete a collision
   * DELETE /api/v1/collisions/:id
   */
  delete: async (collisionId: string): Promise<void> => {
    return apiClient.delete<void>(`/collisions/${collisionId}`)
  },

  /**
   * Batch delete collisions
   * DELETE /api/v1/collisions/batch
   */
  deleteBatch: async (ids: string[]): Promise<void> => {
    return apiClient.delete<void>('/collisions/batch', { ids })
  },

  /**
   * Run collision detection
   * POST /api/v1/collisions/detect
   */
  detect: async (
    projectId: string,
    routeId?: string,
    lodLevel?: CollisionLOD,
    componentIds?: string[]
  ): Promise<CollisionDetectionResult[]> => {
    return apiClient.post<CollisionDetectionResult[]>('/collisions/detect', {
      project_id: projectId,
      route_id: routeId,
      lod_level: lodLevel,
      component_ids: componentIds,
    })
  },

  /**
   * Run collision detection on specific components
   * POST /api/v1/collisions/detect/components
   */
  detectComponents: async (
    componentAId: string,
    componentBId: string,
    lodLevel?: CollisionLOD
  ): Promise<CollisionDetectionResult> => {
    return apiClient.post<CollisionDetectionResult>('/collisions/detect/components', {
      component_a_id: componentAId,
      component_b_id: componentBId,
      lod_level: lodLevel,
    })
  },

  /**
   * Export collisions
   * GET /api/v1/collisions/export
   */
  export: async (
    projectId: string,
    params?: Partial<CollisionListParams>
  ): Promise<CollisionExport> => {
    return apiClient.get<CollisionExport>('/collisions/export', {
      project_id: projectId,
      ...params,
    })
  },

  /**
   * Import collisions
   * POST /api/v1/collisions/import
   */
  import: async (
    collisions: CollisionCreate[]
  ): Promise<{ success: number; failed: number; errors: string[] }> => {
    return apiClient.post<{ success: number; failed: number; errors: string[] }>(
      '/collisions/import',
      { collisions }
    )
  },

  /**
   * Resolve multiple collisions
   * POST /api/v1/collisions/resolve
   */
  resolve: async (
    ids: string[],
    note?: string
  ): Promise<CollisionPoint[]> => {
    return apiClient.post<CollisionPoint[]>('/collisions/resolve', {
      ids,
      note,
    })
  },

  /**
   * Confirm multiple collisions
   * POST /api/v1/collisions/confirm
   */
  confirm: async (ids: string[]): Promise<CollisionPoint[]> => {
    return apiClient.post<CollisionPoint[]>('/collisions/confirm', { ids })
  },

  /**
   * Ignore multiple collisions
   * POST /api/v1/collisions/ignore
   */
  ignore: async (ids: string[]): Promise<CollisionPoint[]> => {
    return apiClient.post<CollisionPoint[]>('/collisions/ignore', { ids })
  },
}

export default collisionsApi
