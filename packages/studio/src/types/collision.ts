/**
 * Collision Data Types
 * 碰撞检测数据类型定义
 */

// 碰撞类型枚举
export type CollisionType = 
  | 'component_collision'    // 构件碰撞
  | 'clearance_violation'     // 净空不足
  | 'overlap'                // 重叠
  | 'proximity'              // 临近（警告）
  | 'penetration'           // 穿透

// 碰撞严重程度
export type CollisionSeverity = 
  | 'critical'   // 严重 - 必须处理
  | 'major'      // 重要 - 需要关注
  | 'minor'      // 轻微 - 建议检查
  | 'warning'    // 警告 - 提示信息

// 碰撞状态
export type CollisionStatus = 
  | 'detected'   // 已检测
  | 'confirmed'  // 已确认
  | 'resolved'   // 已解决
  | 'ignored'    // 已忽略

// LOD精度级别
export type CollisionLOD = 0 | 1 | 2

// 碰撞详细信息
export interface CollisionPoint {
  id: string
  project_id: string
  route_id?: string
  station?: number
  station_display?: string
  
  // 碰撞位置 (3D坐标)
  x: number
  y: number
  z: number
  
  // 碰撞类型
  collision_type: CollisionType
  
  // 严重程度
  severity: CollisionSeverity
  
  // 状态
  status: CollisionStatus
  
  // 关联的构件
  component_a_id?: string
  component_a_name?: string
  component_b_id?: string
  component_b_name?: string
  
  // 碰撞距离
  distance?: number
  overlap_distance?: number
  
  // LOD级别
  lod_level: CollisionLOD
  
  // 描述
  description?: string
  suggestion?: string
  
  // 时间戳
  detected_at: string
  confirmed_at?: string
  resolved_at?: string
  
  // 原始数据
  raw_data?: Record<string, unknown>
  
  // 同步状态
  sync_status: 'pending' | 'synced' | 'conflict' | 'failed'
  local_id?: string
  
  // 元数据
  created_at: string
  updated_at: string
}

// 碰撞列表查询参数
export interface CollisionListParams {
  project_id?: string
  route_id?: string
  station?: number
  collision_type?: CollisionType
  severity?: CollisionSeverity
  status?: CollisionStatus
  lod_level?: CollisionLOD
  page?: number
  limit?: number
  search?: string
}

// 碰撞列表响应
export interface CollisionListResponse {
  collisions: CollisionPoint[]
  total: number
  page: number
  limit: number
}

// 碰撞创建请求
export interface CollisionCreate {
  project_id: string
  route_id?: string
  station?: number
  station_display?: string
  x: number
  y: number
  z: number
  collision_type: CollisionType
  severity?: CollisionSeverity
  component_a_id?: string
  component_a_name?: string
  component_b_id?: string
  component_b_name?: string
  distance?: number
  overlap_distance?: number
  lod_level?: CollisionLOD
  description?: string
  suggestion?: string
  local_id?: string
}

// 碰撞更新请求
export interface CollisionUpdate {
  status?: CollisionStatus
  severity?: CollisionSeverity
  description?: string
  suggestion?: string
  confirmed_at?: string
  resolved_at?: string
}

// 碰撞统计
export interface CollisionStatistics {
  total: number
  by_type: Record<CollisionType, number>
  by_severity: Record<CollisionSeverity, number>
  by_status: Record<CollisionStatus, number>
  by_lod: Record<CollisionLOD, number>
}

// 碰撞检测结果 (来自API)
export interface CollisionDetectionResult {
  collision_id: string
  lod_level: CollisionLOD
  status: 'COLLISION' | 'NO_COLLISION' | 'UNCERTAIN'
  distance?: {
    min?: number
    max?: number
    average?: number
    total?: number
  }
  penetration_depth?: number
  affected_components?: string[]
  metadata?: Record<string, unknown>
}

// 碰撞批量操作
export interface CollisionBatchOperation {
  ids: string[]
  operation: 'resolve' | 'ignore' | 'confirm' | 'delete'
  note?: string
}

// 碰撞导出数据
export interface CollisionExport {
  collisions: CollisionPoint[]
  exported_at: string
  project_id: string
  filter_params?: CollisionListParams
}
