// Route 3D - 公路路线三维可视化
// 基于 React Three Fiber

import { useState, useRef, useMemo } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { OrbitControls, Text, PerspectiveCamera, Line, Html } from '@react-three/drei'
import * as THREE from 'three'

// 路线点
interface RoutePoint {
  id: string
  station: number  // 桩号 (km)
  name: string
  elevation: number  // 海拔 (m)
  type: 'start' | 'end' | 'station' | 'bridge' | 'tunnel' | 'landmark'
}

// 示例路线数据 - 高速公路
const routePoints: RoutePoint[] = [
  { id: '1', station: 0, name: '起点', elevation: 120, type: 'start' },
  { id: '2', station: 2.5, name: 'K2+500', elevation: 125, type: 'station' },
  { id: '3', station: 5.0, name: 'K5+000 大桥', elevation: 130, type: 'bridge' },
  { id: '4', station: 7.5, name: 'K7+500', elevation: 145, type: 'station' },
  { id: '5', station: 10.0, name: 'K10+000 隧道', elevation: 280, type: 'tunnel' },
  { id: '6', station: 12.5, name: 'K12+500', elevation: 265, type: 'station' },
  { id: '7', station: 15.0, name: 'K15+000', elevation: 240, type: 'station' },
  { id: '8', station: 17.5, name: 'K17+500 特大', elevation: 220, type: 'bridge' },
  { id: '9', station: 20.0, name: 'K20+000', elevation: 195, type: 'station' },
  { id: '10', station: 25.0, name: '终点', elevation: 180, type: 'end' },
]

// 路线类型图标
const typeIcons: Record<string, string> = {
  start: '🚗',
  end: '🏁',
  station: '📍',
  bridge: '🌉',
  tunnel: '🚇',
  landmark: '🏛️',
}

const typeColors: Record<string, string> = {
  start: '#28a745',
  end: '#dc3545',
  station: '#667eea',
  bridge: '#ffc107',
  tunnel: '#764ba2',
  landmark: '#17a2b8',
}

// 生成路线曲线
function generateRouteCurve(points: RoutePoint[]): THREE.Vector3[] {
  const curve: THREE.Vector3[] = []
  const scale = 2 // 横向缩放
  const heightScale = 0.5 // 高度缩放
  
  for (let i = 0; i <= 100; i++) {
    const t = i / 100
    const totalLength = points[points.length - 1].station - points[0].station
    const currentStation = points[0].station + t * totalLength
    
    // 找到当前点所在区间
    let p1 = points[0]
    let p2 = points[1]
    for (let j = 0; j < points.length - 1; j++) {
      if (currentStation >= points[j].station && currentStation <= points[j + 1].station) {
        p1 = points[j]
        p2 = points[j + 1]
        break
      }
    }
    
    // 线性插值
    const localT = (currentStation - p1.station) / (p2.station - p1.station)
    const x = currentStation * scale
    const y = (p1.elevation + localT * (p2.elevation - p1.elevation)) * heightScale
    const z = 0
    
    curve.push(new THREE.Vector3(x, y, z))
  }
  
  return curve
}

// 路线曲线组件
function RouteCurve({ curve, color }: { curve: THREE.Vector3[]; color: string }) {
  return (
    <Line
      points={curve}
      color={color}
      lineWidth={3}
    />
  )
}

// 路线点标记
function RouteMarker({ point, selected, onClick }: { 
  point: RoutePoint
  selected: boolean
  onClick: () => void
}) {
  const meshRef = useRef<THREE.Mesh>(null)
  const scale = 2
  const heightScale = 0.5
  
  useFrame(() => {
    if (meshRef.current && selected) {
      meshRef.current.scale.setScalar(1 + Math.sin(Date.now() / 300) * 0.2)
    }
  })
  
  const position: [number, number, number] = [
    point.station * scale,
    point.elevation * heightScale,
    0
  ]
  
  return (
    <group position={position}>
      <mesh ref={meshRef} onClick={onClick}>
        <sphereGeometry args={[selected ? 0.4 : 0.3, 16, 16]} />
        <meshStandardMaterial 
          color={selected ? '#fff' : typeColors[point.type]}
          emissive={typeColors[point.type]}
          emissiveIntensity={selected ? 0.5 : 0.2}
        />
      </mesh>
      <Text
        position={[0, 0.8, 0]}
        fontSize={0.4}
        color="white"
        anchorX="center"
        outlineWidth={0.02}
        outlineColor="#000"
      >
        {point.name}
      </Text>
    </group>
  )
}

// 地形截面
function TerrainProfile({ points }: { points: RoutePoint[] }) {
  const curve = useMemo(() => generateRouteCurve(points), [points])
  const scale = 2
  const heightScale = 0.5
  
  // 生成填充形状
  const shapePoints = useMemo(() => {
    const shape: THREE.Vector3[] = []
    // 底部
    shape.push(new THREE.Vector3(points[0].station * scale, 0, 0))
    // 沿路线
    curve.forEach(p => shape.push(p))
    // 右侧底部
    shape.push(new THREE.Vector3(points[points.length - 1].station * scale, 0, 0))
    return shape
  }, [curve, points])
  
  return (
    <mesh position={[0, 0, -1]}>
      <bufferGeometry>
        <bufferAttribute
          attach="attributes-position"
          count={shapePoints.length}
          array={new Float32Array(shapePoints.flatMap(p => [p.x, p.y, p.z]))}
          itemSize={3}
        />
      </bufferGeometry>
      <meshStandardMaterial 
        color="#2a2a4a" 
        side={THREE.DoubleSide}
        transparent
        opacity={0.8}
      />
    </mesh>
  )
}

// 网格地面
function Ground() {
  const scale = 2
  const length = 25
  
  return (
    <>
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[length * scale / 2, -1, 0]}>
        <planeGeometry args={[length * scale, 20]} />
        <meshStandardMaterial color="#0a0a1a" />
      </mesh>
      <gridHelper 
        args={[length * scale, length, 0x333333, 0x222222]} 
        position={[length * scale / 2, -0.99, 0]}
        rotation={[0, 0, Math.PI / 2]}
      />
    </>
  )
}

// 主场景
function RouteScene({ 
  points, 
  selectedId, 
  onSelect,
  showTerrain,
  showLabels 
}: { 
  points: RoutePoint[]
  selectedId: string | null
  onSelect: (id: string) => void
  showTerrain: boolean
  showLabels: boolean
}) {
  const curve = useMemo(() => generateRouteCurve(points), [points])
  
  return (
    <>
      <ambientLight intensity={0.6} />
      <directionalLight position={[20, 30, 20]} intensity={1} castShadow />
      <pointLight position={[10, 20, 10]} intensity={0.5} color="#ff6600" />
      
      {/* 路线曲线 */}
      <RouteCurve curve={curve} color="#667eea" />
      
      {/* 地形截面 */}
      {showTerrain && <TerrainProfile points={points} />}
      
      {/* 路线点 */}
      {points.map(point => (
        <RouteMarker 
          key={point.id}
          point={point}
          selected={selectedId === point.id}
          onClick={() => onSelect(point.id)}
        />
      ))}
      
      {/* 地面 */}
      <Ground />
      
      {/* 标注 */}
      {showLabels && points.map(point => (
        <Html key={`label-${point.id}`} position={[point.station * 2, point.elevation * 0.5 + 2, 0]}>
          <div style={{ 
            background: 'rgba(0,0,0,0.8)', 
            padding: '4px 8px', 
            borderRadius: '4px',
            fontSize: '12px',
            color: '#fff',
            whiteSpace: 'nowrap'
          }}>
            {typeIcons[point.type]} {point.name} ({point.elevation}m)
          </div>
        </Html>
      ))}
    </>
  )
}

// 主组件
export default function Route3DViewer() {
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [showTerrain, setShowTerrain] = useState(true)
  const [showLabels, setShowLabels] = useState(true)
  const [viewMode, setViewMode] = useState<'3d' | 'profile'>('3d')
  const [elevationScale, setElevationScale] = useState(0.5)
  
  const selectedPoint = routePoints.find(p => p.id === selectedId)
  
  // 统计数据
  const stats = useMemo(() => {
    const total = routePoints[routePoints.length - 1].station - routePoints[0].station
    const bridges = routePoints.filter(p => p.type === 'bridge').length
    const tunnels = routePoints.filter(p => p.type === 'tunnel').length
    const maxElev = Math.max(...routePoints.map(p => p.elevation))
    const minElev = Math.min(...routePoints.map(p => p.elevation))
    return { total, bridges, tunnels, maxElev, minElev }
  }, [])
  
  return (
    <div style={{ display: 'flex', height: 'calc(100vh - 150px)' }}>
      {/* 3D 视图 */}
      <div style={{ flex: 1, position: 'relative' }}>
        <Canvas shadows>
          <PerspectiveCamera makeDefault position={[15, 15, 25]} fov={50} />
          <OrbitControls enableDamping dampingFactor={0.05} />
          <RouteScene 
            points={routePoints}
            selectedId={selectedId}
            onSelect={setSelectedId}
            showTerrain={showTerrain}
            showLabels={showLabels}
          />
        </Canvas>
        
        {/* 工具栏 */}
        <div style={{
          position: 'absolute',
          top: 10,
          left: 10,
          display: 'flex',
          gap: '8px',
          flexWrap: 'wrap',
          maxWidth: '400px'
        }}>
          <button style={toolbarBtn} onClick={() => setShowTerrain(!showTerrain)}>
            {showTerrain ? '🌲 隐藏地形' : '🌲 显示地形'}
          </button>
          <button style={toolbarBtn} onClick={() => setShowLabels(!showLabels)}>
            {showLabels ? '🏷️ 隐藏标注' : '🏷️ 显示标注'}
          </button>
          <button style={toolbarBtn} onClick={() => setViewMode(viewMode === '3d' ? 'profile' : '3d')}>
            {viewMode === '3d' ? '📐 侧面图' : '🎯 3D视图'}
          </button>
        </div>
        
        {/* 图例 */}
        <div style={{
          position: 'absolute',
          top: 10,
          right: 10,
          background: 'rgba(0,0,0,0.8)',
          padding: '12px',
          borderRadius: '8px',
          fontSize: '12px'
        }}>
          <div style={{ marginBottom: '6px', fontWeight: 'bold' }}>图例</div>
          {Object.entries(typeIcons).map(([type, icon]) => (
            <div key={type} style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '4px' }}>
              <span>{icon}</span>
              <span style={{ color: typeColors[type] }}>{type}</span>
            </div>
          ))}
        </div>
      </div>
      
      {/* 右侧面板 */}
      <div style={{ 
        width: '320px', 
        background: '#1a1a2e', 
        padding: '16px',
        borderLeft: '1px solid #333',
        overflow: 'auto'
      }}>
        <h3 style={{ marginTop: 0 }}>路线三维视图</h3>
        
        {/* 路线统计 */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', marginBottom: '16px' }}>
          <div style={statCard}>
            <div style={{ fontSize: '20px', fontWeight: 'bold' }}>{stats.total} km</div>
            <div style={{ color: '#888', fontSize: '11px' }}>路线总长</div>
          </div>
          <div style={statCard}>
            <div style={{ fontSize: '20px', fontWeight: 'bold', color: '#ffc107' }}>{stats.bridges}</div>
            <div style={{ color: '#888', fontSize: '11px' }}>桥梁</div>
          </div>
          <div style={statCard}>
            <div style={{ fontSize: '20px', fontWeight: 'bold', color: '#764ba2' }}>{stats.tunnels}</div>
            <div style={{ color: '#888', fontSize: '11px' }}>隧道</div>
          </div>
          <div style={statCard}>
            <div style={{ fontSize: '20px', fontWeight: 'bold' }}>{stats.maxElev - stats.minElev}m</div>
            <div style={{ color: '#888', fontSize: '11px' }}>高差</div>
          </div>
        </div>
        
        {/* 高程控制 */}
        <div style={{ marginBottom: '16px' }}>
          <label style={{ display: 'block', marginBottom: '8px', fontSize: '13px' }}>
            高程缩放: {elevationScale}x
          </label>
          <input 
            type="range" 
            min="0.1" 
            max="2" 
            step="0.1"
            value={elevationScale}
            onChange={e => setElevationScale(Number(e.target.value))}
            style={{ width: '100%' }}
          />
        </div>
        
        {/* 桩点列表 */}
        <h4>桩点列表</h4>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', maxHeight: '300px', overflow: 'auto' }}>
          {routePoints.map(point => (
            <div 
              key={point.id}
              onClick={() => setSelectedId(point.id)}
              style={{
                padding: '10px',
                background: selectedId === point.id ? '#333' : '#252540',
                borderRadius: '6px',
                cursor: 'pointer',
                borderLeft: `3px solid ${typeColors[point.type]}`,
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center'
              }}
            >
              <div>
                <div style={{ fontWeight: 'bold' }}>{typeIcons[point.type]} {point.name}</div>
                <div style={{ fontSize: '12px', color: '#888' }}>
                  K{point.station.toFixed(1)}
                </div>
              </div>
              <div style={{ textAlign: 'right' }}>
                <div style={{ fontSize: '14px', color: typeColors[point.type] }}>{point.elevation}m</div>
              </div>
            </div>
          ))}
        </div>
        
        {/* 选中详情 */}
        {selectedPoint && (
          <div style={{ 
            marginTop: '16px', 
            padding: '12px', 
            background: '#252540', 
            borderRadius: '8px',
            border: `2px solid ${typeColors[selectedPoint.type]}`
          }}>
            <h4 style={{ marginTop: 0, marginBottom: '8px' }}>
              {typeIcons[selectedPoint.type]} {selectedPoint.name}
            </h4>
            <div style={{ fontSize: '13px', color: '#aaa' }}>
              <p>桩号: K{selectedPoint.station.toFixed(1)}</p>
              <p>海拔: {selectedPoint.elevation}m</p>
              <p>类型: {selectedPoint.type}</p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

const toolbarBtn = {
  padding: '8px 12px',
  background: 'rgba(0,0,0,0.7)',
  color: 'white',
  border: 'none',
  borderRadius: '4px',
  cursor: 'pointer',
  fontSize: '12px'
}

const statCard = {
  background: '#252540',
  padding: '10px',
  borderRadius: '6px',
  textAlign: 'center' as const
}
