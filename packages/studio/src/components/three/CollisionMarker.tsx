/**
 * CollisionMarker - 单个碰撞标注组件
 * 使用react-three-fiber渲染3D碰撞点标记
 */

import { useRef, useState, useMemo } from 'react'
import { useFrame } from '@react-three/fiber'
import { Html } from '@react-three/drei'
import * as THREE from 'three'
import {
  CollisionPoint,
  CollisionSeverity,
  CollisionType,
} from '../../types/collision'

// ============================================================================
// Types
// ============================================================================

export interface CollisionMarkerProps {
  /** 碰撞点数据 */
  collision: CollisionPoint
  /** 是否被选中 */
  selected?: boolean
  /** 是否显示标签 */
  showLabel?: boolean
  /** 是否显示详细信息 */
  showDetail?: boolean
  /** 点击回调 */
  onClick?: (collision: CollisionPoint) => void
  /** 悬浮回调 */
  onHover?: (collision: CollisionPoint | null) => void
  /** 标记尺寸 */
  size?: number
  /** 是否启用动画 */
  animated?: boolean
}

// ============================================================================
// Severity Colors
// ============================================================================

const severityColors: Record<CollisionSeverity, string> = {
  critical: '#ff3333',   // 红色 - 严重
  major: '#ff8800',       // 橙色 - 重要
  minor: '#ffcc00',       // 黄色 - 轻微
  warning: '#4488ff',     // 蓝色 - 警告
}

const typeIcons: Record<CollisionType, string> = {
  component_collision: '⚠️',
  clearance_violation: '📏',
  overlap: '🔄',
  proximity: '📍',
  penetration: '🔨',
}

// ============================================================================
// Marker Sphere Component
// ============================================================================

function MarkerSphere({
  position,
  color,
  size,
  selected,
  animated,
  onClick,
  onPointerOver,
  onPointerOut,
}: {
  position: [number, number, number]
  color: string
  size: number
  selected?: boolean
  animated?: boolean
  onClick?: () => void
  onPointerOver?: () => void
  onPointerOut?: () => void
}) {
  const meshRef = useRef<THREE.Mesh>(null)
  const [hovered, setHovered] = useState(false)
  
  // 动画效果
  useFrame((state) => {
    if (meshRef.current && (animated || selected || hovered)) {
      const t = state.clock.getElapsedTime()
      // 脉冲动画
      const scale = 1 + Math.sin(t * 4) * 0.1
      meshRef.current.scale.setScalar(scale)
    }
  })
  
  const finalColor = useMemo(() => new THREE.Color(color), [color])
  const emissiveColor = useMemo(() => new THREE.Color(color), [color])
  
  return (
    <mesh
      ref={meshRef}
      position={position}
      onClick={(e) => {
        e.stopPropagation()
        onClick?.()
      }}
      onPointerOver={(e) => {
        e.stopPropagation()
        setHovered(true)
        onPointerOver?.()
        document.body.style.cursor = 'pointer'
      }}
      onPointerOut={(e) => {
        e.stopPropagation()
        setHovered(false)
        onPointerOut?.()
        document.body.style.cursor = 'auto'
      }}
    >
      <sphereGeometry args={[size, 32, 32]} />
      <meshStandardMaterial
        color={finalColor}
        emissive={emissiveColor}
        emissiveIntensity={selected || hovered ? 0.8 : 0.4}
        transparent
        opacity={0.9}
        roughness={0.3}
        metalness={0.5}
      />
      
      {/* 外圈光环 */}
      {(selected || hovered) && (
        <mesh scale={1.3}>
          <sphereGeometry args={[size, 32, 32]} />
          <meshBasicMaterial
            color={color}
            transparent
            opacity={0.3}
            side={THREE.BackSide}
          />
        </mesh>
      )}
    </mesh>
  )
}

// ============================================================================
// Collision Label Component
// ============================================================================

function CollisionLabel({
  collision,
  showDetail,
}: {
  collision: CollisionPoint
  showDetail?: boolean
}) {
  const severity = collision.severity
  const color = severityColors[severity]
  const icon = typeIcons[collision.collision_type]
  
  return (
    <Html
      position={[
        collision.x,
        collision.y + 1.5,
        collision.z,
      ]}
      center
      distanceFactor={10}
      style={{ pointerEvents: 'none' }}
    >
      <div
        style={{
          background: 'rgba(20, 20, 30, 0.95)',
          border: `2px solid ${color}`,
          borderRadius: '8px',
          padding: showDetail ? '12px' : '6px 10px',
          color: 'white',
          fontSize: showDetail ? '13px' : '11px',
          whiteSpace: 'nowrap',
          minWidth: '120px',
          boxShadow: `0 4px 20px rgba(0,0,0,0.5), 0 0 20px ${color}40`,
          transition: 'all 0.2s ease',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: showDetail ? '6px' : '0' }}>
          <span style={{ fontSize: '14px' }}>{icon}</span>
          <span style={{ fontWeight: 600, color }}>{severity.toUpperCase()}</span>
        </div>
        
        {showDetail && (
          <>
            <div style={{ fontSize: '11px', color: '#aaa', marginBottom: '4px' }}>
              {collision.station_display || `X:${collision.x.toFixed(1)} Y:${collision.y.toFixed(1)} Z:${collision.z.toFixed(1)}`}
            </div>
            {collision.distance !== undefined && (
              <div style={{ fontSize: '12px', color: '#ff6666' }}>
                距离: {collision.distance.toFixed(3)}m
              </div>
            )}
            {collision.description && (
              <div style={{ marginTop: '6px', fontSize: '11px', color: '#888' }}>
                {collision.description}
              </div>
            )}
          </>
        )}
      </div>
    </Html>
  )
}

// ============================================================================
// Main CollisionMarker Component
// ============================================================================

export default function CollisionMarker({
  collision,
  selected = false,
  showLabel = true,
  showDetail = false,
  onClick,
  onHover,
  size = 0.3,
  animated = true,
}: CollisionMarkerProps) {
  const [hovered, setHovered] = useState(false)
  
  const color = severityColors[collision.severity]
  const position: [number, number, number] = [
    collision.x,
    collision.y,
    collision.z,
  ]
  
  const handleClick = () => {
    onClick?.(collision)
  }
  
  const handlePointerOver = () => {
    setHovered(true)
    onHover?.(collision)
  }
  
  const handlePointerOut = () => {
    setHovered(false)
    onHover?.(null)
  }
  
  return (
    <group>
      {/* 碰撞点标记球 */}
      <MarkerSphere
        position={position}
        color={color}
        size={size}
        selected={selected || hovered}
        animated={animated}
        onClick={handleClick}
        onPointerOver={handlePointerOver}
        onPointerOut={handlePointerOut}
      />
      
      {/* 垂直指示线 */}
      {(selected || hovered) && (
        <line>
          <bufferGeometry>
            <bufferAttribute
              attach="attributes-position"
              count={2}
              array={new Float32Array([
                collision.x,
                collision.y,
                collision.z,
                collision.x,
                0,
                collision.z,
              ])}
              itemSize={3}
            />
          </bufferGeometry>
          <lineBasicMaterial color={color} transparent opacity={0.5} />
        </line>
      )}
      
      {/* 地面指示点 */}
      {(selected || hovered) && (
        <mesh position={[collision.x, 0.01, collision.z]} rotation={[-Math.PI / 2, 0, 0]}>
          <ringGeometry args={[size * 0.8, size * 1.2, 32]} />
          <meshBasicMaterial color={color} transparent opacity={0.3} side={THREE.DoubleSide} />
        </mesh>
      )}
      
      {/* 标签 */}
      {showLabel && (selected || hovered) && (
        <CollisionLabel collision={collision} showDetail={showDetail} />
      )}
    </group>
  )
}

// Export types
export type { CollisionMarkerProps }
