import axios, { AxiosInstance } from 'axios'

// API 配置
const API_BASE_URL = (import.meta as any).env?.VITE_API_BASE_URL || 'http://localhost:8000'

// 创建 axios 实例
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
apiClient.interceptors.request.use(
  (config) => {
    // 可以在这里添加认证token
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
apiClient.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    console.error('API Error:', error.message)
    return Promise.reject(error)
  }
)

// ============== API 接口 ==============

// 1. 桩号查询
export interface StationQueryParams {
  station: string
  route_id?: string
}

export interface StationInfo {
  station: string
  x: number
  y: number
  z: number
  azimuth: number
  horizontal_elem?: string
  vertical_elem?: string
}

export const queryStation = async (params: StationQueryParams): Promise<StationInfo> => {
  const response = await apiClient.post('/api/v1/calculate/station', params)
  return response.data
}

// 2. 范围计算坐标
export interface RangeParams {
  route_id: string
  start: number
  end: number
  interval: number
}

export interface Coordinate {
  station: string
  x: number
  y: number
  z: number
  azimuth: number
}

export const calculateRange = async (params: RangeParams): Promise<Coordinate[]> => {
  const response = await apiClient.post('/api/v1/calculate/range', params)
  return response.data?.data || []
}

// 3. 照片查询
export interface PhotoQueryParams {
  route_id?: string
  station?: string
  start_station?: string
  end_station?: string
  limit?: number
}

export interface PhotoItem {
  id: string
  url: string
  thumbnail: string
  station: string
  capture_time: string
  type: string
}

export const queryPhotos = async (params: PhotoQueryParams): Promise<PhotoItem[]> => {
  const response = await apiClient.post('/api/v1/media/photos', params)
  return response.data || []
}

// 4. 空间数据查询
export interface SpatialQueryParams {
  lon: number
  lat: number
  radius?: number
}

export interface SpatialFeature {
  id: string
  type: string
  properties: Record<string, any>
  geometry: {
    type: string
    coordinates: number[] | number[][]
  }
}

export const spatialQuery = async (params: SpatialQueryParams): Promise<SpatialFeature[]> => {
  const response = await apiClient.post('/api/v1/spatial/query', params)
  return response.data || []
}

// 5. 知识图谱问答
export interface KGQueryParams {
  question: string
  top_k?: number
}

export interface KGAnswer {
  answer: string
  entities: Array<{ id: string; name: string; type: string }>
  relations: Array<{ source: string; target: string; relation: string }>
}

export const kgQuery = async (params: KGQueryParams): Promise<KGAnswer> => {
  const response = await apiClient.post('/api/v1/kg/query', params)
  return response.data
}

// 6. 碰撞检测
export interface CollisionParams {
  components: Array<{
    id: string
    position: [number, number, number]
    size: [number, number, number]
  }>
  lod?: number
}

export interface CollisionResult {
  lod0?: { status: string; distance: any }
  lod1?: { status: string; distance: any }
  lod2?: { status: string; distance: any }
}

export const collisionCheck = async (params: CollisionParams): Promise<CollisionResult> => {
  const response = await apiClient.post('/api/v1/engineering/collision', params)
  return response as any
}

// 7. 模型列表
export interface ModelInfo {
  id: string
  name: string
  type: string
  station_range: [string, string]
  created_at: string
}

export const listModels = async (): Promise<ModelInfo[]> => {
  const response = await apiClient.get('/api/v1/models')
  return response.data || []
}

// 8. 模型详情
export const getModelDetail = async (modelId: string): Promise<any> => {
  const response = await apiClient.get(`/api/v1/models/${modelId}`)
  return response.data
}

export default apiClient
