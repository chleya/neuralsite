/**
 * CollisionViewer - 碰撞3D可视化组件
 * 使用react-three-fiber渲染碰撞点3D场景
 */

import { useState, useEffect, useCallback, useMemo, Suspense } from 'react'
import { Canvas } from '@react-three/fiber'
import * as THREE from 'three'
import {
  CollisionPoint,
  CollisionStatistics,
  CollisionListParams,
} from '../../types/collision'
import CollisionMarker from './CollisionMarker'
import CollisionPanel from './CollisionPanel'
import SceneSetup, { EnhancedOrbitControls } from './SceneSetup'

// ============================================================================
// Types
// ============================================================================

export interface CollisionViewerProps {
  /** 碰撞数据列表 */
  collisions: CollisionPoint[]
  /** 统计数据 */
  statistics?: CollisionStatistics
  /** 查询参数 */
  params?: CollisionListParams
  /** 是否加载中 */
  loading?: boolean
  /** 选中的碰撞ID */
  selectedId?: string | null
  /** 场景背景色 */
  backgroundColor?: string
  /** 是否显示面板 */
  showPanel?: boolean
  /** 面板宽度 */
  panelWidth?: number
  /** 点击碰撞回调 */
  onSelect?: (collision: CollisionPoint | null) => void
  /** 查看详情回调 */
  onViewDetail?: (collision: CollisionPoint) => void
  /** 状态变更回调 */
  onStatusChange?: (ids: string[], status: 'detected' | 'confirmed' | 'resolved' | 'ignored') => void
  /** 刷新回调 */
  onRefresh?: () => void
  /** 相机位置 */
  cameraPosition?: [number, number, number]
  /** 相机目标点 */
  cameraTarget?: [number, number, number]
  /** 自定义样式类名 */
  className?: string
}

// ============================================================================
// Loading Component
// ============================================================================

function LoadingFallback() {
  return (
    <mesh>
      <boxGeometry args={[1, 1, 1]} />
      <meshBasicMaterial color="#4488ff" wireframe />
    </mesh>
  )
}

// ============================================================================
// Camera Controller
// ============================================================================

function CameraController({
  target,
  position,
}: {
  target?: [number, number, number]
  position?: [number, number, number]
}) {
  return (
    <EnhancedOrbitControls
      target={target || [0, 0, 0]}
      minDistance={1}
      maxDistance={500}
      enableDamping
      dampingFactor={0.05}
    />
  )
}

// ============================================================================
// Collision Scene Component
// ============================================================================

function CollisionScene({
  collisions,
  selectedId,
  onSelect,
  onHover,
  showLabels = true,
}: {
  collisions: CollisionPoint[]
  selectedId?: string | null
  onSelect?: (collision: CollisionPoint) => void
  onHover?: (collision: CollisionPoint | null) => void
  showLabels?: boolean
}) {
  // 计算场景中心点
  const centerPoint = useMemo(() => {
    if (collisions.length === 0) return [0, 0, 0] as [number, number, number]
    
    const sum = collisions.reduce(
      (acc, c) => [acc[0] + c.x, acc[1] + c.y, acc[2] + c.z],
      [0, 0, 0]
    )
    return [
      sum[0] / collisions.length,
      sum[1] / collisions.length,
      sum[2] / collisions.length,
    ] as [number, number, number]
  }, [collisions])
  
  return (
    <>
      {/* Scene Setup */}
      <SceneSetup
        environment
        environmentPreset="city"
        shadows
        grid
        gridSize={100}
        gridDivisions={50}
        gridColor="#333333"
        backgroundColor="#0a0a15"
        cameraPosition={[20, 20, 30]}
        cameraFov={50}
        controls={false}
        ambientIntensity={0.6}
        directionalIntensity={1}
      />
      
      {/* Camera Controls */}
      <CameraController target={centerPoint} />
      
      {/* Ambient light boost */}
      <ambientLight intensity={0.5} />
      <directionalLight position={[20, 30, 10]} intensity={1} castShadow />
      <pointLight position={[-10, 10, -10]} intensity={0.3} color="#4ecdc4" />
      
      {/* Collision Markers */}
      <Suspense fallback={<LoadingFallback />}>
        {collisions.map((collision) => (
          <CollisionMarker
            key={collision.id}
            collision={collision}
            selected={collision.id === selectedId}
            showLabel={showLabels}
            showDetail={collision.id === selectedId}
            size={0.4}
            animated
            onClick={onSelect}
            onHover={onHover}
          />
        ))}
      </Suspense>
      
      {/* Axes Helper */}
      <axesHelper args={[5]} />
    </>
  )
}

// ============================================================================
// Detail Modal Component
// ============================================================================

function DetailModal({
  collision,
  open,
  onClose,
}: {
  collision: CollisionPoint | null
  open: boolean
  onClose: () => void
}) {
  if (!open || !collision) return null
  
  const severityColors: Record<string, string> = {
    critical: '#ff3333',
    major: '#ff8800',
    minor: '#ffcc00',
    warning: '#4488ff',
  }
  
  const severityLabels: Record<string, string> = {
    critical: '严重',
    major: '重要',
    minor: '轻微',
    warning: '警告',
  }
  
  const statusLabels: Record<string, string> = {
    detected: '已检测',
    confirmed: '已确认',
    resolved: '已解决',
    ignored: '已忽略',
  }
  
  const typeLabels: Record<string, string> = {
    component_collision: '构件碰撞',
    clearance_violation: '净空不足',
    overlap: '重叠',
    proximity: '临近',
    penetration: '穿透',
  }
  
  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        background: 'rgba(0,0,0,0.7)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 1000,
      }}
      onClick={onClose}
    >
      <div
        style={{
          background: '#1a1a2e',
          borderRadius: '16px',
          width: '90%',
          maxWidth: '500px',
          maxHeight: '80vh',
          overflow: 'auto',
          border: '1px solid rgba(255,255,255,0.1)',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div
          style={{
            padding: '20px',
            borderBottom: '1px solid rgba(255,255,255,0.1)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <h3 style={{ margin: 0, color: 'white', fontSize: '18px' }}>碰撞详情</h3>
          <button
            onClick={onClose}
            style={{
              background: 'none',
              border: 'none',
              color: '#888',
              fontSize: '24px',
              cursor: 'pointer',
              padding: '0',
              lineHeight: 1,
            }}
          >
            ×
          </button>
        </div>
        
        {/* Content */}
        <div style={{ padding: '20px' }}>
          {/* Status Badge */}
          <div style={{ display: 'flex', gap: '8px', marginBottom: '20px' }}>
            <span
              style={{
                padding: '4px 12px',
                borderRadius: '4px',
                fontSize: '12px',
                fontWeight: 600,
                background: severityColors[collision.severity],
                color: 'white',
              }}
            >
              {severityLabels[collision.severity]}
            </span>
            <span
              style={{
                padding: '4px 12px',
                borderRadius: '4px',
                fontSize: '12px',
                background: 'rgba(68,136,255,0.2)',
                color: '#4488ff',
              }}
            >
              {statusLabels[collision.status]}
            </span>
            <span
              style={{
                padding: '4px 12px',
                borderRadius: '4px',
                fontSize: '12px',
                background: 'rgba(255,255,255,0.1)',
                color: '#888',
              }}
            >
              {typeLabels[collision.collision_type]}
            </span>
          </div>
          
          {/* Info Grid */}
          <div style={{ display: 'grid', gap: '12px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: '#888' }}>桩号:</span>
              <span style={{ color: 'white' }}>{collision.station_display || '-'}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: '#888' }}>X坐标:</span>
              <span style={{ color: 'white' }}>{collision.x.toFixed(3)}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: '#888' }}>Y坐标:</span>
              <span style={{ color: 'white' }}>{collision.y.toFixed(3)}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: '#888' }}>Z坐标:</span>
              <span style={{ color: 'white' }}>{collision.z.toFixed(3)}</span>
            </div>
            {collision.distance !== undefined && (
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: '#888' }}>碰撞距离:</span>
                <span style={{ color: '#ff6666' }}>{collision.distance.toFixed(3)} m</span>
              </div>
            )}
            {collision.overlap_distance !== undefined && (
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: '#888' }}>重叠距离:</span>
                <span style={{ color: '#ff6666' }}>{collision.overlap_distance.toFixed(3)} m</span>
              </div>
            )}
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: '#888' }}>LOD精度:</span>
              <span style={{ color: 'white' }}>LOD{collision.lod_level}</span>
            </div>
            {collision.component_a_name && (
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: '#888' }}>构件A:</span>
                <span style={{ color: 'white' }}>{collision.component_a_name}</span>
              </div>
            )}
            {collision.component_b_name && (
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: '#888' }}>构件B:</span>
                <span style={{ color: 'white' }}>{collision.component_b_name}</span>
              </div>
            )}
          </div>
          
          {/* Description */}
          {collision.description && (
            <div style={{ marginTop: '20px' }}>
              <div style={{ color: '#888', marginBottom: '8px' }}>描述:</div>
              <div style={{ color: '#ccc', fontSize: '13px', lineHeight: 1.6 }}>
                {collision.description}
              </div>
            </div>
          )}
          
          {/* Suggestion */}
          {collision.suggestion && (
            <div style={{ marginTop: '20px' }}>
              <div style={{ color: '#888', marginBottom: '8px' }}>处理建议:</div>
              <div style={{ color: '#4ecdc4', fontSize: '13px', lineHeight: 1.6 }}>
                {collision.suggestion}
              </div>
            </div>
          )}
          
          {/* Timestamps */}
          <div style={{ marginTop: '20px', paddingTop: '20px', borderTop: '1px solid rgba(255,255,255,0.1)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: '#666' }}>
              <span>检测时间:</span>
              <span>{new Date(collision.detected_at).toLocaleString('zh-CN')}</span>
            </div>
            {collision.confirmed_at && (
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: '#666', marginTop: '4px' }}>
                <span>确认时间:</span>
                <span>{new Date(collision.confirmed_at).toLocaleString('zh-CN')}</span>
              </div>
            )}
            {collision.resolved_at && (
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: '#666', marginTop: '4px' }}>
                <span>解决时间:</span>
                <span>{new Date(collision.resolved_at).toLocaleString('zh-CN')}</span>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

// ============================================================================
// Main CollisionViewer Component
// ============================================================================

export default function CollisionViewer({
  collisions,
  statistics,
  params,
  loading = false,
  selectedId,
  backgroundColor = '#0a0a15',
  showPanel = true,
  panelWidth = 360,
  onSelect,
  onViewDetail,
  onStatusChange,
  onRefresh,
  cameraPosition,
  cameraTarget,
  className,
}: CollisionViewerProps) {
  const [hoveredCollision, setHoveredCollision] = useState<CollisionPoint | null>(null)
  const [detailCollision, setDetailCollision] = useState<CollisionPoint | null>(null)
  const [showLabels, setShowLabels] = useState(true)
  
  // 选中的碰撞对象
  const selectedCollision = useMemo(() => {
    if (!selectedId) return null
    return collisions.find((c) => c.id === selectedId) || null
  }, [collisions, selectedId])
  
  // 处理碰撞点击
  const handleCollisionSelect = useCallback(
    (collision: CollisionPoint) => {
      onSelect?.(collision.id === selectedId ? null : collision)
    },
    [onSelect, selectedId]
  )
  
  // 处理碰撞悬浮
  const handleCollisionHover = useCallback((collision: CollisionPoint | null) => {
    setHoveredCollision(collision)
  }, [])
  
  // 处理查看详情
  const handleViewDetail = useCallback(
    (collision: CollisionPoint) => {
      setDetailCollision(collision)
      onViewDetail?.(collision)
    },
    [onViewDetail]
  )
  
  // 跳转到指定碰撞
  const handleNavigateToCollision = useCallback(
    (collision: CollisionPoint) => {
      onSelect?.(collision)
    },
    [onSelect]
  )
  
  return (
    <div
      className={className}
      style={{
        display: 'flex',
        height: '100%',
        width: '100%',
        position: 'relative',
        background: backgroundColor,
        borderRadius: '12px',
        overflow: 'hidden',
      }}
    >
      {/* 3D Canvas */}
      <div
        style={{
          flex: 1,
          position: 'relative',
        }}
      >
        <Canvas
          camera={{
            position: cameraPosition || [20, 20, 30],
            fov: 50,
            near: 0.1,
            far: 1000,
          }}
          shadows
          style={{ background: backgroundColor }}
        >
          <CollisionScene
            collisions={collisions}
            selectedId={selectedId}
            onSelect={handleCollisionSelect}
            onHover={handleCollisionHover}
            showLabels={showLabels}
          />
        </Canvas>
        
        {/* Floating Controls */}
        <div
          style={{
            position: 'absolute',
            top: '16px',
            left: '16px',
            display: 'flex',
            flexDirection: 'column',
            gap: '8px',
          }}
        >
          <button
            onClick={() => setShowLabels(!showLabels)}
            style={{
              padding: '8px 12px',
              background: showLabels ? 'rgba(68, 136, 255, 0.8)' : 'rgba(30, 30, 50, 0.8)',
              border: '1px solid rgba(255,255,255,0.2)',
              borderRadius: '6px',
              color: 'white',
              fontSize: '12px',
              cursor: 'pointer',
            }}
          >
            {showLabels ? '隐藏标签' : '显示标签'}
          </button>
        </div>
        
        {/* Stats Overlay */}
        <div
          style={{
            position: 'absolute',
            bottom: '16px',
            left: '16px',
            background: 'rgba(20, 20, 35, 0.9)',
            border: '1px solid rgba(255,255,255,0.1)',
            borderRadius: '8px',
            padding: '12px 16px',
            display: 'flex',
            gap: '16px',
            fontSize: '12px',
          }}
        >
          <div>
            <span style={{ color: '#888' }}>总数: </span>
            <span style={{ color: 'white', fontWeight: 600 }}>{collisions.length}</span>
          </div>
          <div>
            <span style={{ color: '#888' }}>严重: </span>
            <span style={{ color: '#ff3333', fontWeight: 600 }}>
              {collisions.filter((c) => c.severity === 'critical').length}
            </span>
          </div>
          <div>
            <span style={{ color: '#888' }}>重要: </span>
            <span style={{ color: '#ff8800', fontWeight: 600 }}>
              {collisions.filter((c) => c.severity === 'major').length}
            </span>
          </div>
        </div>
        
        {/* Hovered Info */}
        {hoveredCollision && !selectedId && (
          <div
            style={{
              position: 'absolute',
              top: '16px',
              right: showPanel ? panelWidth + 16 : 16,
              background: 'rgba(20, 20, 35, 0.95)',
              border: '1px solid rgba(255,255,255,0.1)',
              borderRadius: '8px',
              padding: '12px 16px',
              maxWidth: '300px',
            }}
          >
            <div style={{ fontSize: '13px', color: 'white', fontWeight: 600, marginBottom: '4px' }}>
              {hoveredCollision.station_display || '碰撞点'}
            </div>
            <div style={{ fontSize: '11px', color: '#888' }}>
              {hoveredCollision.collision_type} | LOD{hoveredCollision.lod_level}
            </div>
            {hoveredCollision.distance !== undefined && (
              <div style={{ fontSize: '12px', color: '#ff6666', marginTop: '4px' }}>
                距离: {hoveredCollision.distance.toFixed(3)}m
              </div>
            )}
          </div>
        )}
      </div>
      
      {/* Side Panel */}
      {showPanel && (
        <div
          style={{
            width: panelWidth,
            height: '100%',
            borderLeft: '1px solid rgba(255,255,255,0.1)',
          }}
        >
          <CollisionPanel
            collisions={collisions}
            statistics={statistics}
            selectedId={selectedId}
            loading={loading}
            onSelect={handleNavigateToCollision}
            onViewDetail={handleViewDetail}
            onStatusChange={onStatusChange}
            onRefresh={onRefresh}
          />
        </div>
      )}
      
      {/* Detail Modal */}
      <DetailModal
        collision={detailCollision}
        open={!!detailCollision}
        onClose={() => setDetailCollision(null)}
      />
    </div>
  )
}

// Export types
export type { CollisionViewerProps }
