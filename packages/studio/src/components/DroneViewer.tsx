import { useState, useRef, useMemo } from 'react'
import { Canvas, useFrame, ThreeEvent } from '@react-three/fiber'
import { OrbitControls, Html, Text } from '@react-three/drei'
import * as THREE from 'three'

// ==================== 类型定义 ====================
interface OrthoImage {
  id: string
  name: string
  url: string
  bounds: {
    north: number
    south: number
    east: number
    west: number
  }
  resolution: number
  captureTime?: string
}

interface DronePoint {
  id: string
  position: [number, number, number]
  type: 'takeoff' | 'landing' | 'waypoint' | 'photo'
  label?: string
  altitude?: number
}

interface FlightPath {
  id: string
  name: string
  points: [number, number, number][]
  color?: string
}

interface DroneViewerProps {
  images?: OrthoImage[]
  points?: DronePoint[]
  paths?: FlightPath[]
  loading?: boolean
  onImageSelect?: (image: OrthoImage) => void
}

// ==================== 地形表面组件 ====================
function TerrainSurface({ 
  images,
  onImageClick 
}: { 
  images: OrthoImage[]
  onImageClick?: (img: OrthoImage) => void
}) {
  const geometry = useMemo(() => {
    const geo = new THREE.PlaneGeometry(100, 100, 50, 50)
    const positions = geo.attributes.position.array as Float32Array
    
    for (let i = 0; i < positions.length; i += 3) {
      const x = positions[i]
      const y = positions[i + 1]
      positions[i + 2] = Math.sin(x * 0.1) * Math.cos(y * 0.1) * 3 +
                       Math.sin(x * 0.3 + y * 0.2) * 1.5
    }
    
    geo.computeVertexNormals()
    return geo
  }, [])

  const material = useMemo(() => {
    return new THREE.MeshStandardMaterial({
      color: '#3d5a45',
      roughness: 0.9,
      metalness: 0.1,
      side: THREE.DoubleSide,
    })
  }, [])

  return (
    <group>
      <mesh 
        geometry={geometry} 
        material={material}
        rotation={[-Math.PI / 2, 0, 0]}
        receiveShadow
      />
      
      <gridHelper args={[100, 20, '#2a4035', '#1a2a25']} position={[0, 0.01, 0]} />
      
      {images[0] && (
        <mesh 
          rotation={[-Math.PI / 2, 0, 0]} 
          position={[0, 0.05, 0]}
          onClick={(e) => {
            e.stopPropagation()
            onImageClick?.(images[0])
          }}
        >
          <planeGeometry args={[80, 80]} />
          <meshStandardMaterial 
            color="#ffffff"
            transparent
            opacity={0.3}
            depthWrite={false}
          />
        </mesh>
      )}
    </group>
  )
}

// ==================== 飞行点标记 ====================
function DroneMarker({ 
  point, 
  onClick 
}: { 
  point: DronePoint
  onClick?: (p: DronePoint) => void
}) {
  const [hovered, setHovered] = useState(false)
  
  const colors = {
    takeoff: '#2ecc71',
    landing: '#e74c3c',
    waypoint: '#3498db',
    photo: '#f39c12'
  }
  
  const icons = {
    takeoff: '🛫',
    landing: '🛬',
    waypoint: '📍',
    photo: '📷'
  }

  return (
    <group position={point.position}>
      <mesh
        onClick={(e) => {
          e.stopPropagation()
          onClick?.(point)
        }}
        onPointerOver={() => setHovered(true)}
        onPointerOut={() => setHovered(false)}
      >
        <sphereGeometry args={[0.8, 16, 16]} />
        <meshStandardMaterial 
          color={colors[point.type]}
          emissive={colors[point.type]}
          emissiveIntensity={hovered ? 0.8 : 0.4}
        />
      </mesh>
      
      {point.altitude !== undefined && (
        <Text
          position={[1.5, 1, 0]}
          fontSize={1.2}
          color={colors[point.type]}
          anchorX="left"
        >
          {point.altitude}m
        </Text>
      )}
      
      {hovered && (
        <Html position={[0, 2, 0]} center>
          <div style={{
            background: 'rgba(0,0,0,0.8)',
            padding: '6px 10px',
            borderRadius: 4,
            color: 'white',
            fontSize: 12,
            whiteSpace: 'nowrap',
            border: `1px solid ${colors[point.type]}`
          }}>
            <div>{icons[point.type]} {point.label || point.type}</div>
          </div>
        </Html>
      )}
    </group>
  )
}

// ==================== 飞行路径线 ====================
function FlightPathLine({ 
  path,
}: { 
  path: FlightPath
}) {
  const points = useMemo(() => 
    path.points.map(p => new THREE.Vector3(...p)),
    [path.points]
  )

  return (
    <group>
      <line>
        <bufferGeometry>
          <bufferAttribute
            attach="attributes-position"
            count={points.length}
            array={new Float32Array(points.flatMap(p => [p.x, p.y, p.z]))}
            itemSize={3}
          />
        </bufferGeometry>
        <lineDashedMaterial 
          color={path.color || '#00ff88'} 
          dashSize={1} 
          gapSize={0.5}
        />
      </line>
      
      {points.map((p, i) => {
        if (i >= points.length - 1) return null
        const next = points[i + 1]
        const dir = next.clone().sub(p).normalize()
        const mid = p.clone().add(next).multiplyScalar(0.5)
        
        return (
          <mesh 
            key={i} 
            position={mid.toArray()}
            rotation={[0, Math.atan2(dir.x, dir.z), 0]}
          >
            <coneGeometry args={[0.3, 1, 8]} />
            <meshStandardMaterial color={path.color || '#00ff88'} />
          </mesh>
        )
      })}
    </group>
  )
}

// ==================== 无人机模型 ====================
function DroneModel({ 
  position,
}: { 
  position: [number, number, number]
}) {
  const droneRef = useRef<THREE.Group>(null)
  
  useFrame((state) => {
    if (droneRef.current) {
      droneRef.current.position.y = position[1] + Math.sin(state.clock.getElapsedTime() * 2) * 0.1
    }
  })

  return (
    <group ref={droneRef} position={position}>
      <mesh>
        <boxGeometry args={[1.5, 0.3, 1.5]} />
        <meshStandardMaterial color="#2c3e50" metalness={0.6} roughness={0.3} />
      </mesh>
      
      {[[-1, 0.2, -1], [1, 0.2, -1], [-1, 0.2, 1], [1, 0.2, 1]].map((pos, i) => (
        <group key={i} position={pos as [number, number, number]}>
          <mesh>
            <cylinderGeometry args={[0.8, 0.8, 0.05, 32]} />
            <meshStandardMaterial color="#ecf0f1" transparent opacity={0.6} />
          </mesh>
        </group>
      ))}
      
      <mesh position={[0, -0.3, 0.5]}>
        <boxGeometry args={[0.3, 0.3, 0.4]} />
        <meshStandardMaterial color="#1a1a1a" />
      </mesh>
      
      <pointLight position={[0, 0, 0]} intensity={0.5} color="#00ff00" distance={5} />
    </group>
  )
}

// ==================== 图像信息面板 ====================
function ImageInfoPanel({ 
  image, 
  onClose 
}: { 
  image: OrthoImage | null
  onClose: () => void
}) {
  if (!image) return null
  
  return (
    <div style={{
      position: 'absolute',
      top: 80,
      right: 20,
      width: 300,
      background: 'rgba(26, 26, 46, 0.95)',
      borderRadius: 8,
      border: '1px solid #444',
      overflow: 'hidden'
    }}>
      <div style={{
        padding: '12px 16px',
        background: '#2a2a4a',
        borderBottom: '1px solid #444',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <span style={{ color: '#00ff88', fontWeight: 'bold' }}>{image.name}</span>
        <button
          onClick={onClose}
          style={{
            background: 'transparent',
            border: 'none',
            color: '#888',
            cursor: 'pointer',
            fontSize: 18
          }}
        >
          ×
        </button>
      </div>
      
      <div style={{ padding: 12, fontSize: 13, color: '#ccc' }}>
        <div style={{ marginBottom: 8 }}>
          <span style={{ color: '#888' }}>分辨率: </span>
          {image.resolution} m/pixel
        </div>
        
        <div style={{ marginBottom: 8 }}>
          <span style={{ color: '#888' }}>拍摄时间: </span>
          {image.captureTime || '-'}
        </div>
        
        <div style={{ marginBottom: 8 }}>
          <span style={{ color: '#888' }}>范围: </span>
        </div>
        <div style={{ 
          padding: 8, 
          background: '#1a1a2e', 
          borderRadius: 4,
          fontSize: 11,
          fontFamily: 'monospace'
        }}>
          N: {image.bounds.north.toFixed(6)}<br/>
          S: {image.bounds.south.toFixed(6)}<br/>
          E: {image.bounds.east.toFixed(6)}<br/>
          W: {image.bounds.west.toFixed(6)}
        </div>
      </div>
    </div>
  )
}

// ==================== 飞行统计 ====================
function FlightStats({ 
  points, 
  paths 
}: { 
  points: DronePoint[]
  paths: FlightPath[]
}) {
  const totalDistance = useMemo(() => {
    if (!paths.length) return 0
    let dist = 0
    paths.forEach(path => {
      for (let i = 0; i < path.points.length - 1; i++) {
        const p1 = new THREE.Vector3(...path.points[i])
        const p2 = new THREE.Vector3(...path.points[i + 1])
        dist += p1.distanceTo(p2)
      }
    })
    return dist
  }, [paths])

  const maxAltitude = useMemo(() => {
    if (!points.length) return 0
    return Math.max(...points.map(p => p.position[2] || 0))
  }, [points])

  return (
    <div style={{
      position: 'absolute',
      top: 80,
      left: 20,
      background: 'rgba(0,0,0,0.7)',
      padding: '12px 16px',
      borderRadius: 8,
      fontSize: 12,
      color: '#00ff88'
    }}>
      <div style={{ fontWeight: 'bold', marginBottom: 8, color: '#fff' }}>🚁 航飞概览</div>
      <div>航点数量: {points.length}</div>
      <div>航线数量: {paths.length}</div>
      <div>航线总长: {totalDistance.toFixed(1)} m</div>
      <div>最高海拔: {maxAltitude.toFixed(1)} m</div>
    </div>
  )
}

// ==================== 图例 ====================
function Legend() {
  const items = [
    { color: '#2ecc71', label: '起飞点', icon: '🛫' },
    { color: '#e74c3c', label: '降落点', icon: '🛬' },
    { color: '#3498db', label: '航点', icon: '📍' },
    { color: '#f39c12', label: '拍照点', icon: '📷' }
  ]
  
  return (
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
      <div style={{ fontWeight: 'bold', marginBottom: 8, color: '#fff' }}>航点类型</div>
      {items.map(item => (
        <div key={item.label} style={{ display: 'flex', alignItems: 'center', marginBottom: 4 }}>
          <span style={{ 
            width: 12, 
            height: 12, 
            background: item.color, 
            borderRadius: '50%',
            marginRight: 8 
          }}></span>
          {item.icon} {item.label}
        </div>
      ))}
    </div>
  )
}

// ==================== 主组件 ====================
export default function DroneViewer({ 
  images: propImages,
  points: propPoints,
  paths: propPaths,
  loading = false,
  onImageSelect 
}: DroneViewerProps) {
  const defaultImages: OrthoImage[] = [
    {
      id: 'img-1',
      name: 'K0+000 ~ K1+000 正射影像',
      url: '/ortho/demo.jpg',
      bounds: { north: 30.01, south: 30.00, east: 120.01, west: 120.00 },
      resolution: 0.05,
      captureTime: '2024-10-15 10:30:00'
    }
  ]

  const defaultPoints: DronePoint[] = [
    { id: 'pt-1', position: [-20, 30, 0], type: 'takeoff', label: '起飞点', altitude: 0 },
    { id: 'pt-2', position: [-10, 50, 0], type: 'waypoint', label: '航点1', altitude: 50 },
    { id: 'pt-3', position: [0, 80, 0], type: 'photo', label: '拍照点1', altitude: 80 },
    { id: 'pt-4', position: [10, 80, 0], type: 'waypoint', label: '航点2', altitude: 80 },
    { id: 'pt-5', position: [20, 80, 0], type: 'photo', label: '拍照点2', altitude: 80 },
    { id: 'pt-6', position: [30, 60, 0], type: 'waypoint', label: '航点3', altitude: 60 },
    { id: 'pt-7', position: [40, 0, 0], type: 'landing', label: '降落点', altitude: 0 }
  ]

  const defaultPaths: FlightPath[] = [
    {
      id: 'path-1',
      name: '主航线',
      points: defaultPoints.map(p => [p.position[0], p.position[1], p.position[2]] as [number, number, number]),
      color: '#00ff88'
    }
  ]

  const images = propImages || defaultImages
  const points = propPoints || defaultPoints
  const paths = propPaths || defaultPaths
  
  const [selectedImage, setSelectedImage] = useState<OrthoImage | null>(null)
  const [showTerrain, setShowTerrain] = useState(true)
  const [showPaths, setShowPaths] = useState(true)
  const [showPoints, setShowPoints] = useState(true)
  const [showDrone, setShowDrone] = useState(true)

  const handleImageClick = (img: OrthoImage) => {
    setSelectedImage(img)
    onImageSelect?.(img)
  }

  const handlePointClick = (point: DronePoint) => {
    console.log('点击航点:', point)
  }

  return (
    <div style={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* 控制面板 */}
      <div style={{
        padding: '12px 20px',
        background: '#1a1a2e',
        borderBottom: '1px solid #333',
        display: 'flex',
        gap: '20px',
        alignItems: 'center',
        flexWrap: 'wrap'
      }}>
        <h3 style={{ margin: 0, color: '#00ff88' }}>🚁 无人机航拍集成</h3>
        
        <label style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#ccc', fontSize: 14 }}>
          <input 
            type="checkbox" 
            checked={showTerrain}
            onChange={(e) => setShowTerrain(e.target.checked)}
          />
          地形
        </label>
        
        <label style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#ccc', fontSize: 14 }}>
          <input 
            type="checkbox" 
            checked={showPaths}
            onChange={(e) => setShowPaths(e.target.checked)}
          />
          航线
        </label>
        
        <label style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#ccc', fontSize: 14 }}>
          <input 
            type="checkbox" 
            checked={showPoints}
            onChange={(e) => setShowPoints(e.target.checked)}
          />
          航点
        </label>
        
        <label style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#ccc', fontSize: 14 }}>
          <input 
            type="checkbox" 
            checked={showDrone}
            onChange={(e) => setShowDrone(e.target.checked)}
          />
          无人机
        </label>
        
        <div style={{ marginLeft: 'auto', color: '#888', fontSize: 13 }}>
          {loading ? '加载中...' : `${images.length} 幅影像 / ${points.length} 个航点`}
        </div>
      </div>
      
      {/* 3D画布 */}
      <div style={{ flex: 1, position: 'relative' }}>
        <Canvas camera={{ position: [50, 40, 50], fov: 60 }} shadows>
          <color attach="background" args={['#0a0a15']} />
          
          <ambientLight intensity={0.5} />
          <directionalLight position={[30, 50, 20]} intensity={1} castShadow />
          <hemisphereLight args={['#87ceeb', '#3d5a45', 0.5]} />
          
          {showTerrain && (
            <TerrainSurface images={images} onImageClick={handleImageClick} />
          )}
          
          {showPaths && paths.map(path => (
            <FlightPathLine key={path.id} path={path} />
          ))}
          
          {showPoints && points.map(point => (
            <DroneMarker 
              key={point.id} 
              point={point}
              onClick={handlePointClick}
            />
          ))}
          
          {showDrone && points.length > 0 && (
            <DroneModel 
              position={points[0]?.position || [0, 20, 0]}
            />
          )}
          
          <axesHelper args={[10]} />
          
          <OrbitControls 
            enableDamping 
            dampingFactor={0.05}
            minDistance={10}
            maxDistance={150}
          />
        </Canvas>
        
        <Legend />
        <FlightStats points={points} paths={paths} />
        <ImageInfoPanel image={selectedImage} onClose={() => setSelectedImage(null)} />
      </div>
    </div>
  )
}
