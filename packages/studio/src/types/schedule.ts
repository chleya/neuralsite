/**
 * Schedule data type definitions
 * 施工调度数据类型定义
 */

// 设备类型
export type EquipmentType = 'excavator' | 'paver' | 'roller' | 'bulldozer' | 'loader' | 'truck';

// 设备状态
export type EquipmentStatus = 'idle' | 'working' | 'maintenance' | 'offline';

// 施工区域
export interface ConstructionZone {
  id: string;
  name: string;
  position: {
    x: number;
    y: number;
    z: number;
  };
  dimensions: {
    width: number;
    length: number;
    height: number;
  };
  progress: number; // 0-100
  startDate?: string;
  endDate?: string;
  assignedEquipment: string[]; // equipment IDs
}

// 设备位置点
export interface PositionPoint {
  timestamp: string;
  position: {
    x: number;
    y: number;
    z: number;
  };
  rotation?: {
    x: number;
    y: number;
    z: number;
  };
  speed?: number;
  heading?: number;
}

// 设备轨迹
export interface EquipmentTrajectory {
  equipmentId: string;
  points: PositionPoint[];
  startTime: string;
  endTime: string;
  totalDistance: number; // meters
  workingDuration: number; // minutes
  idleDuration: number; // minutes
}

// 机械设备
export interface Equipment {
  id: string;
  name: string;
  type: EquipmentType;
  status: EquipmentStatus;
  model?: string; // GLTF模型路径
  position: {
    x: number;
    y: number;
    z: number;
  };
  rotation?: {
    x: number;
    y: number;
    z: number;
  };
  currentZoneId?: string;
  operator?: string;
  lastUpdate: string;
  trajectory?: EquipmentTrajectory;
  metadata?: {
    brand?: string;
    modelNumber?: string;
    capacity?: number;
    fuelLevel?: number;
    hoursWorked?: number;
  };
}

// 施工任务
export interface ScheduleTask {
  id: string;
  name: string;
  description?: string;
  zoneId: string;
  equipmentIds: string[];
  status: 'pending' | 'in_progress' | 'completed' | 'cancelled';
  priority: 'low' | 'medium' | 'high' | 'urgent';
  plannedStartDate: string;
  plannedEndDate: string;
  actualStartDate?: string;
  actualEndDate?: string;
  progress: number; // 0-100
  assignedCrew?: string[];
  notes?: string;
}

// 调度计划
export interface Schedule {
  id: string;
  name: string;
  projectId: string;
  date: string;
  tasks: ScheduleTask[];
  equipment: Equipment[];
  zones: ConstructionZone[];
  createdAt: string;
  updatedAt: string;
  createdBy?: string;
}

// 时间轴相关类型
export interface TimelineMarker {
  time: string;
  type: 'start' | 'end' | 'milestone' | 'event';
  label: string;
  description?: string;
}

export interface TimelineState {
  currentTime: string;
  isPlaying: boolean;
  playbackSpeed: number; // 1x, 2x, 5x, 10x
  duration: number; // seconds
  progress: number; // 0-1
}

// 热力图相关类型
export interface HeatmapCell {
  x: number;
  y: number;
  z: number;
  intensity: number; // 0-1
  timestamp?: string;
  equipmentId?: string;
}

export interface ProgressHeatmapData {
  zoneId: string;
  cells: HeatmapCell[];
  minIntensity: number;
  maxIntensity: number;
  timestamp: string;
}

// 调度统计
export interface ScheduleStatistics {
  totalEquipment: number;
  activeEquipment: number;
  idleEquipment: number;
  maintenanceEquipment: number;
  totalTasks: number;
  completedTasks: number;
  inProgressTasks: number;
  overallProgress: number;
  zoneProgress: Record<string, number>;
}

// API响应类型
export interface ScheduleListResponse {
  schedules: Schedule[];
  total: number;
  page: number;
  pageSize: number;
}

export interface EquipmentListResponse {
  equipment: Equipment[];
  total: number;
}

export interface TrajectoryResponse {
  trajectory: EquipmentTrajectory;
  metadata: {
    startTime: string;
    endTime: string;
    pointCount: number;
    totalDistance: number;
  };
}

// 筛选参数
export interface ScheduleFilterParams {
  projectId?: string;
  date?: string;
  startDate?: string;
  endDate?: string;
  status?: string;
  equipmentType?: EquipmentType;
  zoneId?: string;
}
