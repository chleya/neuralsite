import React, { createContext, useContext, useReducer, ReactNode } from 'react'
import { Coordinate, PhotoItem, ModelInfo } from '../services/api'

// ============== 状态类型 ==============
interface AppState {
  // 路由参数
  routeId: string
  designSpeed: number
  
  // 坐标数据
  coordinates: Coordinate[]
  selectedStation: string | null
  
  // 照片数据
  photos: PhotoItem[]
  selectedPhoto: PhotoItem | null
  
  // 模型数据
  models: ModelInfo[]
  currentModel: ModelInfo | null
  
  // UI状态
  loading: boolean
  error: string | null
  
  // 知识图谱
  kgAnswer: string | null
}

// ============== Action 类型 ==============
type AppAction =
  | { type: 'SET_ROUTE_ID'; payload: string }
  | { type: 'SET_DESIGN_SPEED'; payload: number }
  | { type: 'SET_COORDINATES'; payload: Coordinate[] }
  | { type: 'SET_SELECTED_STATION'; payload: string | null }
  | { type: 'SET_PHOTOS'; payload: PhotoItem[] }
  | { type: 'SET_SELECTED_PHOTO'; payload: PhotoItem | null }
  | { type: 'SET_MODELS'; payload: ModelInfo[] }
  | { type: 'SET_CURRENT_MODEL'; payload: ModelInfo | null }
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_ERROR'; payload: string | null }
  | { type: 'SET_KG_ANSWER'; payload: string | null }
  | { type: 'CLEAR_ERROR' }

// ============== 初始状态 ==============
const initialState: AppState = {
  routeId: 'demo',
  designSpeed: 80,
  coordinates: [],
  selectedStation: null,
  photos: [],
  selectedPhoto: null,
  models: [],
  currentModel: null,
  loading: false,
  error: null,
  kgAnswer: null
}

// ============== Reducer ==============
function appReducer(state: AppState, action: AppAction): AppState {
  switch (action.type) {
    case 'SET_ROUTE_ID':
      return { ...state, routeId: action.payload }
    case 'SET_DESIGN_SPEED':
      return { ...state, designSpeed: action.payload }
    case 'SET_COORDINATES':
      return { ...state, coordinates: action.payload }
    case 'SET_SELECTED_STATION':
      return { ...state, selectedStation: action.payload }
    case 'SET_PHOTOS':
      return { ...state, photos: action.payload }
    case 'SET_SELECTED_PHOTO':
      return { ...state, selectedPhoto: action.payload }
    case 'SET_MODELS':
      return { ...state, models: action.payload }
    case 'SET_CURRENT_MODEL':
      return { ...state, currentModel: action.payload }
    case 'SET_LOADING':
      return { ...state, loading: action.payload }
    case 'SET_ERROR':
      return { ...state, error: action.payload }
    case 'SET_KG_ANSWER':
      return { ...state, kgAnswer: action.payload }
    case 'CLEAR_ERROR':
      return { ...state, error: null }
    default:
      return state
  }
}

// ============== Context ==============
interface AppContextType {
  state: AppState
  dispatch: React.Dispatch<AppAction>
}

const AppContext = createContext<AppContextType | undefined>(undefined)

// ============== Provider ==============
export function AppProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(appReducer, initialState)
  
  return (
    <AppContext.Provider value={{ state, dispatch }}>
      {children}
    </AppContext.Provider>
  )
}

// ============== Hook ==============
export function useApp() {
  const context = useContext(AppContext)
  if (context === undefined) {
    throw new Error('useApp must be used within an AppProvider')
  }
  return context
}

export default AppContext
