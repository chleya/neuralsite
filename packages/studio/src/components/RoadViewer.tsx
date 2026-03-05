import { useState, useEffect, useRef, useMemo } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { OrbitControls, Grid, Line, Text, Html } from '@react-three/drei'
import * as THREE from 'three'

// ==================== 类型定义 ====================
interface Coordinate {
  station: string
  x: number
  y: number
  z: number
  azimuth: number
}

interface RoadViewerProps {
  coordinates: Coordinate[]
  loading?: boolean
  showRoadSurface?: boolean
  showSlope?: boolean
  showDrainage?: boolean
  showCenterLine?: boolean
  roadWidth?: number
  laneCount?: number
}

// ==================== 工具函数 ====================
const transformCoord = (
  c: Coordinate, 
  baseX: number, 
  baseY: number
): THREE.Vector3 => {
  return new THREE.Vector3(
    (c.x - baseX) / 100,
    c.z / 10,
    (c.y - baseY) / 100
  )
}

// ==================== 道路中心线组件 ====================
function CenterLine({ coordinates }: { coordinates: Coordinate[] }) {
  const baseX = coordinates[0]?.x || 0
  const baseY = coordinates[0]?.y || 0
  
  const points = useMemo(() => 
    coordinates.map(c => transformCoord(c, baseX, baseY)),
    [coordinates, baseX, baseY]
  )

  if (points.length < 2) return null

  return (
    <group>
      <Line points={points} color="#00ff88" lineWidth={4} />
      
      {/* 起点 */}
      <mesh position={points[0].toArray()}>
        <sphereGeometry args={[0.8, 16, 16]} />
        <meshStandardMaterial color="#ff6b6b" emissive="#ff0000" emissiveIntensity={0.5} />
      </mesh>
      <Text 
        position={[points[0].x + 3, points[0].y + 3, points[0].z]} 
        fontSize={2} 
        color="white"
        anchorX="left"
      >
        起点 {coordinates[0]?.station}
      </Text>
      
      {/* 终点 */}
      <mesh position={points[points.length - 1].toArray()}>
        <sphereGeometry args={[0.8, 16, 16]} />
        <meshStandardMaterial color="#4ecdc4" emissive="#00ff88" emissiveIntensity={0.5} />
      </mesh>
      <Text 
        position={[points[points.length - 1].x + 3, points[points.length - 1].y + 3, points[points.length - 1].z]} 
        fontSize={2} 
        color="white"
        anchorX="left"
      >
        终点 {coordinates[coordinates.length - 1]?.station}
      </Text>
      
      {/* 里程桩标记 */}
      {coordinates.filter((_, i) => i % 10 === 0).map((c, i) => {
        const idx = i * 10
        if (idx >= coordinates.length) return null
        const pos = points[idx]
        return (
          <group key={idx} position={pos.toArray()}>
            <mesh>
              <cylinderGeometry args={[0.3, 0.3, 0.1, 8]} />
              <meshStandardMaterial color="#ffd93d" emissive="#ffaa00" emissiveIntensity={0.3} />
            </mesh>
            <Text position={[0, 1, 0]} fontSize={1.5} color="#ffd93d" anchorX="center">
              {c.station}
            </Text>
          </group>
        )
      })}
    </group>
  )
}

// ==================== 路面组件 ====================
function RoadSurface({ 
  coordinates, 
  width = 10,
  laneCount = 4 
}: { 
  coordinates: Coordinate[]
  width?: number
  laneCount?: number
}) {
  const baseX = coordinates[0]?.x || 0
  const baseY = coordinates[0]?.y || 0
  
  const geometry = useMemo(() => {
    const leftPoints: THREE.Vector3[] = []
    const rightPoints: THREE.Vector3[] = []
    
    coordinates.forEach(c => {
      const pos = transformCoord(c, baseX, baseY)
      const rad = ((c.azimuth || 0) + 90) * Math.PI / 180
      const halfW = width / 200
      
      leftPoints.push(new THREE.Vector3(
        pos.x + halfW * Math.cos(rad),
        pos.y + 0.01,
        pos.z + halfW * Math.sin(rad)
      ))
      rightPoints.push(new THREE.Vector3(
        pos.x - halfW * Math.cos(rad),
        pos.y + 0.01,
        pos.z - halfW * Math.sin(rad)
      ))
    })
    
    const vertices: number[] = []
    for (let i = 0; i < leftPoints.length - 1; i++) {
      vertices.push(
        leftPoints[i].x, leftPoints[i].y, leftPoints[i].z,
        rightPoints[i].x, rightPoints[i].y, rightPoints[i].z,
        leftPoints[i + 1].x, leftPoints[i + 1].y, leftPoints[i + 1].z,
        rightPoints[i].x, rightPoints[i].y, rightPoints[i].z,
        rightPoints[i + 1].x, rightPoints[i + 1].y, rightPoints[i + 1].z,
        leftPoints[i + 1].x, leftPoints[i + 1].y, leftPoints[i + 1].z
      )
    }
    
    const geo = new THREE.BufferGeometry()
    geo.setAttribute('position', new THREE.Float32BufferAttribute(vertices, 3))
    geo.computeVertexNormals()
    return geo
  }, [coordinates, baseX, baseY, width])

  const laneLines = useMemo(() => {
    const lines: THREE.Vector3[][] = []
    
    for (let l = 1; l < laneCount; l++) {
      const offset = (l - laneCount / 2) * (width / 100 / laneCount)
      const points: THREE.Vector3[] = []
      
      coordinates.forEach(c => {
        const pos = transformCoord(c, baseX, baseY)
        const rad = ((c.azimuth || 0) + 90) * Math.PI / 180
        points.push(new THREE.Vector3(
          pos.x + offset * Math.cos(rad) - offset * 0.1 * Math.sin(rad),
          pos.y + 0.02,
          pos.z + offset * Math.sin(rad) + offset * 0.1 * Math.cos(rad)
        ))
      })
      lines.push(points)
    }
    return lines
  }, [coordinates, baseX, baseY, width, laneCount])

  return (
    <group>
      {/* 路面 */}
      <mesh geometry={geometry}>
        <meshStandardMaterial 
          color="#2d3436" 
          side={THREE.DoubleSide}
          roughness={0.8}
        />
      </mesh>
      
      {/* 车道线 */}
      {laneLines.map((points, i) => (
        <Line 
          key={i} 
          points={points} 
          color={i === laneCount - 2 ? "#ffffff" : "#ffcc00"} 
          lineWidth={1} 
        />
      ))}
    </group>
  )
}

// ==================== 边坡组件 ====================
function Slope({ 
  coordinates, 
  roadWidth = 10,
  slopeRatio = 1.5 
}: { 
  coordinates: Coordinate[]
  roadWidth?: number
  slopeRatio?: number
}) {
  const baseX = coordinates[0]?.x || 0
  const baseY = coordinates[0]?.y || 0
  
  const slopeGeometry = useMemo(() => {
    const leftSlope: THREE.Vector3[] = []
    const rightSlope: THREE.Vector3[] = []
    
    coordinates.forEach(c => {
      const pos = transformCoord(c, baseX, baseY)
      const rad = ((c.azimuth || 0) + 90) * Math.PI / 180
      const halfW = roadWidth / 200
      const slopeH = halfW * slopeRatio
      
      leftSlope.push(new THREE.Vector3(
        pos.x + halfW * Math.cos(rad),
        pos.y,
        pos.z + halfW * Math.sin(rad)
      ))
      leftSlope.push(new THREE.Vector3(
        pos.x + (halfW + slopeH) * Math.cos(rad),
        pos.y - slopeH / 2,
        pos.z + (halfW + slopeH) * Math.sin(rad)
      ))
      
      rightSlope.push(new THREE.Vector3(
        pos.x - halfW * Math.cos(rad),
        pos.y,
        pos.z - halfW * Math.sin(rad)
      ))
      rightSlope.push(new THREE.Vector3(
        pos.x - (halfW + slopeH) * Math.cos(rad),
        pos.y - slopeH / 2,
        pos.z - (halfW + slopeH) * Math.sin(rad)
      ))
    })
    
    return { left: leftSlope, right: rightSlope }
  }, [coordinates, baseX, baseY, roadWidth, slopeRatio])

  return (
    <group>
      {coordinates.slice(0, -1).map((c, i) => {
        if (i % 5 !== 0) return null
        const pos = transformCoord(c, baseX, baseY)
        const rad = ((c.azimuth || 0) + 90) * Math.PI / 180
        const halfW = roadWidth / 200
        const slopeH = halfW * slopeRatio
        
        return (
          <group key={i}>
            <mesh position={[
              pos.x + (halfW + slopeH/2) * Math.cos(rad),
              pos.y - slopeH/4,
              pos.z + (halfW + slopeH/2) * Math.sin(rad)
            ]} rotation={[0, 0, Math.atan(slopeRatio)]}>
              <planeGeometry args={[slopeH * 0.7, 0.5]} />
              <meshStandardMaterial color="#6b8e23" side={THREE.DoubleSide} opacity={0.6} transparent />
            </mesh>
            <mesh position={[
              pos.x - (halfW + slopeH/2) * Math.cos(rad),
              pos.y - slopeH/4,
              pos.z - (halfW + slopeH/2) * Math.sin(rad)
            ]} rotation={[0, 0, -Math.atan(slopeRatio)]}>
              <planeGeometry args={[slopeH * 0.7, 0.5]} />
              <meshStandardMaterial color="#6b8e23" side={THREE.DoubleSide} opacity={0.6} transparent />
            </mesh>
          </group>
        )
      })}
    </group>
  )
}

// ==================== 排水沟组件 ====================
function Drainage({ 
  coordinates, 
  roadWidth = 10 
}: { 
  coordinates: Coordinate[]
  roadWidth?: number
}) {
  const baseX = coordinates[0]?.x || 0
  const baseY = coordinates[0]?.y || 0
  
  const drainagePoints = useMemo(() => {
    const leftDrain: THREE.Vector3[] = []
    const rightDrain: THREE.Vector3[] = []
    
    coordinates.forEach(c => {
      const pos = transformCoord(c, baseX, baseY)
      const rad = ((c.azimuth || 0) + 90) * Math.PI / 180
      const drainOffset = roadWidth / 200 + 1.5
      
      leftDrain.push(new THREE.Vector3(
        pos.x + drainOffset * Math.cos(rad),
        pos.y - 0.3,
        pos.z + drainOffset * Math.sin(rad)
      ))
      
      rightDrain.push(new THREE.Vector3(
        pos.x - drainOffset * Math.cos(rad),
        pos.y - 0.3,
        pos.z - drainOffset * Math.sin(rad)
      ))
    })
    
    return { left: leftDrain, right: rightDrain }
  }, [coordinates, baseX, baseY, roadWidth])

  return (
    <group>
      <Line points={drainagePoints.left} color="#4a90e2" lineWidth={3} />
      {drainagePoints.left.filter((_, i) => i % 10 === 0).map((p, i) => (
        <mesh key={`ld-${i}`} position={p.toArray()}>
          <boxGeometry args={[0.4, 0.2, 0.4]} />
          <meshStandardMaterial color="#4a90e2" />
        </mesh>
      ))}
      
      <Line points={drainagePoints.right} color="#4a90e2" lineWidth={3} />
      {drainagePoints.right.filter((_, i) => i % 10 === 0).map((p, i) => (
        <mesh key={`rd-${i}`} position={p.toArray()}>
          <boxGeometry args={[0.4, 0.2, 0.4]} />
          <meshStandardMaterial color="#4a90e2" />
        </mesh>
      ))}
    </group>
  )
}

// ==================== 护栏组件 ====================
function Guardrail({ 
  coordinates, 
  roadWidth = 10 
}: { 
  coordinates: Coordinate[]
  roadWidth?: number
}) {
  const baseX = coordinates[0]?.x || 0
  const baseY = coordinates[0]?.y || 0
  
  const posts = useMemo(() => {
    const leftPosts: THREE.Vector3[] = []
    const rightPosts: THREE.Vector3[] = []
    
    coordinates.forEach((c, i) => {
      if (i % 5 !== 0) return
      const pos = transformCoord(c, baseX, baseY)
      const rad = ((c.azimuth || 0) + 90) * Math.PI / 180
      const railOffset = roadWidth / 200 + 0.3
      
      leftPosts.push(new THREE.Vector3(
        pos.x + railOffset * Math.cos(rad),
        pos.y + 0.5,
        pos.z + railOffset * Math.sin(rad)
      ))
      
      rightPosts.push(new THREE.Vector3(
        pos.x - railOffset * Math.cos(rad),
        pos.y + 0.5,
        pos.z - railOffset * Math.sin(rad)
      ))
    })
    
    return { left: leftPosts, right: rightPosts }
  }, [coordinates, baseX, baseY, roadWidth])

  return (
    <group>
      {posts.left.map((p, i) => (
        <mesh key={`lp-${i}`} position={p.toArray()}>
          <cylinderGeometry args={[0.05, 0.05, 1, 8]} />
          <meshStandardMaterial color="#ffd700" metalness={0.8} roughness={0.2} />
        </mesh>
      ))}
      
      {posts.right.map((p, i) => (
        <mesh key={`rp-${i}`} position={p.toArray()}>
          <cylinderGeometry args={[0.05, 0.05, 1, 8]} />
          <meshStandardMaterial color="#ffd700" metalness={0.8} roughness={0.2} />
        </mesh>
      ))}
    </group>
  )
}

// ==================== 主场景 ====================
function Scene({ 
  coordinates, 
  loading,
  options 
}: { 
  coordinates: Coordinate[]
  loading?: boolean
  options: {
    showRoadSurface: boolean
    showSlope: boolean
    showDrainage: boolean
    showCenterLine: boolean
    roadWidth: number
    laneCount: number
  }
}) {
  return (
    <>
      <ambientLight intensity={0.4} />
      <directionalLight position={[50, 50, 25]} intensity={1} castShadow />
      <pointLight position={[0, 20, 0]} intensity={0.5} color="#4ecdc4" />
      
      <Grid 
        args={[300, 300]} 
        cellSize={5} 
        cellThickness={0.5} 
        sectionSize={20}
        sectionThickness={1}
        fadeDistance={200}
        infiniteGrid
        cellColor="#333"
        sectionColor="#555"
      />
      
      <axesHelper args={[15]} />
      
      {coordinates.length > 0 && options.showCenterLine && (
        <CenterLine coordinates={coordinates} />
      )}
      
      {coordinates.length > 0 && options.showRoadSurface && (
        <RoadSurface 
          coordinates={coordinates} 
          width={options.roadWidth}
          laneCount={options.laneCount}
        />
      )}
      
      {coordinates.length > 0 && options.showSlope && (
        <Slope 
          coordinates={coordinates} 
          roadWidth={options.roadWidth}
          slopeRatio={1.5}
        />
      )}
      
      {coordinates.length > 0 && options.showDrainage && (
        <Drainage 
          coordinates={coordinates} 
          roadWidth={options.roadWidth}
        />
      )}
      
      {coordinates.length > 0 && (
        <Guardrail 
          coordinates={coordinates} 
          roadWidth={options.roadWidth}
        />
      )}
      
      {loading && (
        <mesh position={[0, 10, 0]}>
          <boxGeometry args={[2, 2, 2]} />
          <meshStandardMaterial color="orange" />
        </mesh>
      )}
    </>
  )
}

// ==================== 主组件 ====================
export default function RoadViewer({ 
  coordinates: propCoordinates,
  loading = false,
  showRoadSurface = true,
  showSlope = true,
  showDrainage = true,
  showCenterLine = true,
  roadWidth = 20,
  laneCount = 4
}: RoadViewerProps) {
  const defaultCoordinates: Coordinate[] = useMemo(() => {
    const coords: Coordinate[] = []
    for (let i = 0; i < 100; i++) {
      coords.push({
        station: `K${Math.floor(i / 10) + 1}+${(i % 10) * 10}`,
        x: i * 10,
        y: i * 5,
        z: i * 0.5 + Math.sin(i * 0.1) * 2,
        azimuth: 45 + Math.sin(i * 0.05) * 10
      })
    }
    return coords
  }, [])

  const coordinates = propCoordinates.length > 0 ? propCoordinates : defaultCoordinates
  
  const [options, setOptions] = useState({
    showRoadSurface,
    showSlope,
    showDrainage,
    showCenterLine,
    roadWidth,
    laneCount
  })

  return (
    <div style={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* 控制面板 */}
      <div style={{
        padding: '12px 20px',
        background: '#1a1a2e',
        borderBottom: '1px solid #333',
        display: 'flex',
        gap: '20px',
        flexWrap: 'wrap',
        alignItems: 'center'
      }}>
        <h3 style={{ margin: 0, color: '#00ff88' }}>🛣️ 道路三维模型</h3>
        
        <label style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#ccc', fontSize: 14 }}>
          <input 
            type="checkbox" 
            checked={options.showCenterLine}
            onChange={(e) => setOptions(o => ({ ...o, showCenterLine: e.target.checked }))}
          />
          道路中心线
        </label>
        
        <label style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#ccc', fontSize: 14 }}>
          <input 
            type="checkbox" 
            checked={options.showRoadSurface}
            onChange={(e) => setOptions(o => ({ ...o, showRoadSurface: e.target.checked }))}
          />
          路面
        </label>
        
        <label style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#ccc', fontSize: 14 }}>
          <input 
            type="checkbox" 
            checked={options.showSlope}
            onChange={(e) => setOptions(o => ({ ...o, showSlope: e.target.checked }))}
          />
          边坡
        </label>
        
        <label style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#ccc', fontSize: 14 }}>
          <input 
            type="checkbox" 
            checked={options.showDrainage}
            onChange={(e) => setOptions(o => ({ ...o, showDrainage: e.target.checked }))}
          />
          排水沟
        </label>
        
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ color: '#ccc', fontSize: 14 }}>路宽:</span>
          <input 
            type="range" 
            min="10" 
            max="40" 
            value={options.roadWidth}
            onChange={(e) => setOptions(o => ({ ...o, roadWidth: Number(e.target.value) }))}
            style={{ width: 80 }}
          />
          <span style={{ color: '#00ff88', fontSize: 14, minWidth: 30 }}>{options.roadWidth}m</span>
        </div>
        
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ color: '#ccc', fontSize: 14 }}>车道:</span>
          <select 
            value={options.laneCount}
            onChange={(e) => setOptions(o => ({ ...o, laneCount: Number(e.target.value) }))}
            style={{ background: '#333', color: 'white', border: '1px solid #555', padding: '4px 8px', borderRadius: 4 }}
          >
            <option value={2}>2车道</option>
            <option value={4}>4车道</option>
            <option value={6}>6车道</option>
            <option value={8}>8车道</option>
          </select>
        </div>
      </div>
      
      {/* 3D画布 */}
      <div style={{ flex: 1 }}>
        <Canvas camera={{ position: [50, 50, 50], fov: 60 }} shadows>
          <color attach="background" args={['#0a0a15']} />
          <Scene coordinates={coordinates} loading={loading} options={options} />
          <OrbitControls 
            enableDamping 
            dampingFactor={0.05}
            minDistance={10}
            maxDistance={300}
          />
        </Canvas>
      </div>
      
      {/* 图例 */}
      <div style={{
        position: 'absolute',
        bottom: 20,
        left: 20,
        background: 'rgba(0,0,0,0.7)',
        padding: '12px 16px',
        borderRadius: 8,
        fontSize: 12,
        color: '#aaa'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', marginBottom: 6 }}>
          <span style={{ width: 20, height: 3, background: '#00ff88', marginRight: 8 }}></span>
          道路中心线
        </div>
        <div style={{ display: 'flex', alignItems: 'center', marginBottom: 6 }}>
          <span style={{ width: 20, height: 3, background: '#2d3436', marginRight: 8, border: '1px solid #555' }}></span>
          路面
        </div>
        <div style={{ display: 'flex', alignItems: 'center', marginBottom: 6 }}>
          <span style={{ width: 20, height: 3, background: '#6b8e23', marginRight: 8 }}></span>
          边坡
        </div>
        <div style={{ display: 'flex', alignItems: 'center', marginBottom: 6 }}>
          <span style={{ width: 20, height: 3, background: '#4a90e2', marginRight: 8 }}></span>
          排水沟
        </div>
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <span style={{ width: 3, height: 12, background: '#ffd700', marginRight: 8 }}></span>
          护栏
        </div>
      </div>
      
      {/* 统计信息 */}
      <div style={{
        position: 'absolute',
        top: 80,
        right: 20,
        background: 'rgba(0,0,0,0.7)',
        padding: '10px 15px',
        borderRadius: 8,
        fontSize: 12,
        color: '#00ff88'
      }}>
        <div>桩号点: {coordinates.length}</div>
        <div>道路长度: {((coordinates[coordinates.length-1]?.x - coordinates[0]?.x) / 1000 || 0).toFixed(2)} km</div>
        <div>高程范围: {coordinates.length > 0 ? `${Math.min(...coordinates.map(c => c.z)).toFixed(1)} ~ ${Math.max(...coordinates.map(c => c.z)).toFixed(1)} m` : '-'}</div>
      </div>
    </div>
  )
}
