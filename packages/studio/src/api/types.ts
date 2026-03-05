// NeuralSite API Types
// Based on backend P0 models

export type UserRole = 'admin' | 'manager' | 'engineer' | 'worker';

export type IssueType = 'quality' | 'safety' | 'progress';

export type IssueSeverity = 'critical' | 'major' | 'minor';

export type IssueStatus = 'open' | 'in_progress' | 'resolved' | 'closed';

export type SyncStatus = 'pending' | 'synced' | 'conflict' | 'failed';

// ==================== User Types ====================

export interface User {
  user_id: string;
  username: string;
  real_name?: string;
  role: UserRole;
  phone?: string;
  is_active: boolean;
  project_id?: string;
  created_at: string;
  updated_at: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface RegisterRequest {
  username: string;
  password: string;
  real_name?: string;
  role?: UserRole;
  phone?: string;
  project_id?: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user_id: string;
  username: string;
  role: string;
  real_name?: string;
}

// ==================== Photo Types ====================

export interface Photo {
  photo_id: string;
  project_id: string;
  file_path: string;
  file_hash?: string;
  file_size?: number;
  mime_type?: string;
  captured_at: string;
  captured_by?: string;
  latitude?: number;
  longitude?: number;
  gps_accuracy?: number;
  station?: number;
  station_display?: string;
  ai_classification?: Record<string, unknown>;
  is_verified: boolean;
  verified_by?: string;
  verified_at?: string;
  entity_id?: string;
  entity_type?: string;
  description?: string;
  tags?: string[];
  sync_status: SyncStatus;
  local_id?: string;
  created_at: string;
  updated_at: string;
}

export interface PhotoCreate {
  project_id: string;
  file_path: string;
  captured_at: string;
  latitude?: number;
  longitude?: number;
  station?: number;
  station_display?: string;
  description?: string;
  tags?: string[];
  file_hash?: string;
  file_size?: number;
  mime_type?: string;
  captured_by?: string;
  gps_accuracy?: number;
  entity_id?: string;
  entity_type?: string;
  local_id?: string;
}

export interface PhotoUpdate {
  station?: number;
  station_display?: string;
  description?: string;
  tags?: string[];
  is_verified?: boolean;
  verified_by?: string;
}

export interface PhotoListParams {
  project_id?: string;
  station?: number;
  station_display?: string;
  captured_by?: string;
  is_verified?: boolean;
  sync_status?: SyncStatus;
  page?: number;
  limit?: number;
  search?: string;
}

export interface PhotoListResponse {
  photos: Photo[];
  total: number;
  page: number;
  limit: number;
}

// ==================== Issue Types ====================

export interface Issue {
  issue_id: string;
  project_id: string;
  issue_type: IssueType;
  title: string;
  description?: string;
  severity: IssueSeverity;
  station?: number;
  station_display?: string;
  latitude?: number;
  longitude?: number;
  location_description?: string;
  photo_ids: string[];
  status: IssueStatus;
  reported_by?: string;
  reported_at: string;
  assigned_to?: string;
  assigned_at?: string;
  resolved_by?: string;
  resolved_at?: string;
  resolution_note?: string;
  deadline?: string;
  ai_screening?: Record<string, unknown>;
  sync_status: SyncStatus;
  local_id?: string;
  created_at: string;
  updated_at: string;
}

export interface IssueCreate {
  project_id: string;
  issue_type: IssueType;
  title: string;
  description?: string;
  severity?: IssueSeverity;
  station?: number;
  station_display?: string;
  latitude?: number;
  longitude?: number;
  location_description?: string;
  photo_ids?: string[];
  reported_by?: string;
  assigned_to?: string;
  deadline?: string;
  local_id?: string;
}

export interface IssueUpdate {
  title?: string;
  description?: string;
  severity?: IssueSeverity;
  status?: IssueStatus;
  assigned_to?: string;
  resolved_by?: string;
  resolution_note?: string;
  deadline?: string;
  photo_ids?: string[];
}

export interface IssueListParams {
  project_id?: string;
  issue_type?: IssueType;
  severity?: IssueSeverity;
  status?: IssueStatus;
  reported_by?: string;
  assigned_to?: string;
  station?: number;
  page?: number;
  limit?: number;
  search?: string;
}

export interface IssueListResponse {
  issues: Issue[];
  total: number;
  page: number;
  limit: number;
}

// ==================== API Common Types ====================

export interface ApiError {
  message: string;
  code?: string;
  details?: Record<string, unknown>;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  limit: number;
}

export interface ApiResponse<T> {
  data: T;
  message?: string;
}

// ==================== Station Types ====================

export interface Station {
  station_id: string;
  project_id: string;
  route_id: string;
  station: number;
  station_display: string;
  x: number;
  y: number;
  z: number;
  azimuth: number;
  horizontal_elem?: string;
  vertical_elem?: string;
  mileage?: number;
  description?: string;
  sync_status: SyncStatus;
  local_id?: string;
  created_at: string;
  updated_at: string;
}

export interface StationCreate {
  project_id: string;
  route_id: string;
  station: number;
  station_display: string;
  x: number;
  y: number;
  z: number;
  azimuth: number;
  horizontal_elem?: string;
  vertical_elem?: string;
  mileage?: number;
  description?: string;
  local_id?: string;
}

export interface StationUpdate {
  station?: number;
  station_display?: string;
  x?: number;
  y?: number;
  z?: number;
  azimuth?: number;
  horizontal_elem?: string;
  vertical_elem?: string;
  mileage?: number;
  description?: string;
}

export interface StationListParams {
  project_id?: string;
  route_id?: string;
  station?: number;
  page?: number;
  limit?: number;
  search?: string;
}

export interface StationListResponse {
  stations: Station[];
  total: number;
  page: number;
  limit: number;
}

// ==================== CrossSection Types ====================

export interface CrossSection {
  cs_id: string;
  project_id: string;
  route_id: string;
  station: number;
  station_display: string;
  cs_type: 'left' | 'right' | 'center' | 'full';
  mileage?: number;
  // 断面点数据
  points: CrossSectionPoint[];
  // 原始JSON数据（用于导入导出）
  raw_data?: Record<string, unknown>;
  description?: string;
  sync_status: SyncStatus;
  local_id?: string;
  created_at: string;
  updated_at: string;
}

export interface CrossSectionPoint {
  offset: number;     // 距中桩偏移量 (m)
  elevation: number;  // 高程 (m)
  description?: string;
}

export interface CrossSectionCreate {
  project_id: string;
  route_id: string;
  station: number;
  station_display: string;
  cs_type: 'left' | 'right' | 'center' | 'full';
  mileage?: number;
  points: CrossSectionPoint[];
  raw_data?: Record<string, unknown>;
  description?: string;
  local_id?: string;
}

export interface CrossSectionUpdate {
  station?: number;
  station_display?: string;
  cs_type?: 'left' | 'right' | 'center' | 'full';
  mileage?: number;
  points?: CrossSectionPoint[];
  raw_data?: Record<string, unknown>;
  description?: string;
}

export interface CrossSectionListParams {
  project_id?: string;
  route_id?: string;
  station?: number;
  cs_type?: 'left' | 'right' | 'center' | 'full';
  page?: number;
  limit?: number;
  search?: string;
}

export interface CrossSectionListResponse {
  cross_sections: CrossSection[];
  total: number;
  page: number;
  limit: number;
}

// ==================== Project Types ====================

export interface Project {
  project_id: string;
  name: string;
  code?: string;
  route_id?: string;
  description?: string;
  start_station?: number;
  end_station?: number;
  total_length?: number;
  created_by?: string;
  created_at: string;
  updated_at: string;
}

export interface ProjectListParams {
  page?: number;
  limit?: number;
  search?: string;
}

export interface ProjectListResponse {
  projects: Project[];
  total: number;
  page: number;
  limit: number;
}

// ==================== Route Types ====================

export interface Route {
  route_id: string;
  name: string;
  code?: string;
  project_id?: string;
  total_length?: number;
  start_station?: number;
  end_station?: number;
  created_at: string;
  updated_at: string;
}

export interface RouteListParams {
  project_id?: string;
  page?: number;
  limit?: number;
  search?: string;
}

export interface RouteListResponse {
  routes: Route[];
  total: number;
  page: number;
  limit: number;
}
