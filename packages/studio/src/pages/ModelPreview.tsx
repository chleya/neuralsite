import { useState, useRef, Suspense } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { OrbitControls, Grid, Html, Line } from '@react-three/drei'
import * as THREE from 'three'

// 测试数据 - 模拟道路坐标
const generateTestCoords = () => {
  const coords = []
  for (let s = 0; s <= 2000; s += 50) {
    const x = s * Math.cos(Math.PI / 4)
    const y = s * Math.sin(Math.PI / 4)
    let z = 100
    if (s <= 500) {
      z = 100 + s * 20 / 1000
    } else if (s <= 700) {
      const ls = s - 500
      z = 110 + 20 * ls / 1000 - 35 * ls * ls / (200 * 1000)
    } else {
      z = 110 - 15 * (s - 500) / 1000
    }
    coords.push({
      station: `K${Math.floor(s / 1000)}+${(s % 1000).toString().padStart(3, '0')}`,
      x, y, z,
      azimuth: 45
    })
  }
  return coords
}

const testCoords = generateTestCoords()

// 道路中心线
function RoadCenterLine({ coordinates }: { coordinates: any[] }) {
  if (coordinates.length < 2) return null
  
  const baseX = coordinates[0].x
  const baseY = coordinates[0].y
  
  const points = coordinates.map(c => 
    new THREE.Vector3((c.x - baseX) / 50, c.z / 5, (c.y - baseY) / 50)
  )
  
  return (
    <group>
      <Line
        points={points}
        color="#00ff88"
        lineWidth={3}
      />
      {/* 起点 */}
      <mesh position={points[0].toArray()}>
        <sphereGeometry args={[0.3, 16, 16]} />
        <meshStandardMaterial color="#ff6b6b" emissive="#ff0000" emissiveIntensity={0.5} />
      </mesh>
      <Html position={[points[0].x + 1, points[0].y + 1, points[0].z]}>
        <div style={{ color: '#fff', fontSize: '12px', background: 'rgba(0,0,0,0.7)', padding: '2px 6px', borderRadius: '4px' }}>
          起点
        </div>
      </Html>
      {/* 终点 */}
      <mesh position={points[points.length - 1].toArray()}>
        <sphereGeometry args={[0.3, 16, 16]} />
        <meshStandardMaterial color="#4ecdc4" emissive="#00ff88" emissiveIntensity={0.5} />
      </mesh>
    </group>
  )
}

// 道路表面
function RoadSurface({ coordinates }: { coordinates: any[] }) {
  if (coordinates.length < 2) return null
  
  const baseX = coordinates[0].x
  const baseY = coordinates[0].y
  const width = 2
  
  const leftPoints: THREE.Vector3[] = []
  const rightPoints: THREE.Vector3[] = []
  
  coordinates.forEach(c => {
    const relX = (c.x - baseX) / 50
    const relY = c.z / 5
    const relZ = (c.y - baseY) / 50
    
    const rad = (c.azimuth || 45) * Math.PI / 180
    const halfW = width / 2
    
    const leftX = relX + halfW * Math.cos(rad + Math.PI / 2)
    const leftZ = relZ + halfW * Math.sin(rad + Math.PI / 2)
    
    const rightX = relX + halfW * Math.cos(rad - Math.PI / 2)
    const rightZ = relZ + halfW * Math.sin(rad - Math.PI / 2)
    
    leftPoints.push(new THREE.Vector3(leftX, relY, leftZ))
    rightPoints.push(new THREE.Vector3(rightX, relY, rightZ))
  })
  
  // 创建带状几何体
  const vertices: number[] = []
  for (let i = 0; i < leftPoints.length - 1; i++) {
    vertices.push(leftPoints[i].x, leftPoints[i].y, leftPoints[i].z)
    vertices.push(rightPoints[i].x, rightPoints[i].y, rightPoints[i].z)
    vertices.push(leftPoints[i + 1].x, leftPoints[i + 1].y, leftPoints[i + 1].z)
    
    vertices.push(rightPoints[i].x, rightPoints[i].y, rightPoints[i].z)
    vertices.push(rightPoints[i + 1].x, rightPoints[i + 1].y, rightPoints[i + 1].z)
    vertices.push(leftPoints[i + 1].x, leftPoints[i + 1].y, leftPoints[i + 1].z)
  }
  
  const geometry = new THREE.BufferGeometry()
  geometry.setAttribute('position', new THREE.Float32BufferAttribute(vertices, 3))
  geometry.computeVertexNormals()
  
  return (
    <mesh geometry={geometry}>
      <meshStandardMaterial 
        color="#3d5a80" 
        side={THREE.DoubleSide} 
        opacity={0.8} 
        transparent
      />
    </mesh>
  )
}

// 地形网格
function Terrain({ size = 80 }: { size?: number }) {
  return (
    <Grid
      args={[size, size]}
      cellSize={2}
      cellThickness={0.5}
      sectionSize={10}
      sectionThickness={1}
      fadeDistance={100}
      infiniteGrid
      cellColor="#333"
      sectionColor="#444"
      position={[0, 0, 0]}
    />
  )
}

// 动画标记点
function AnimatedMarker({ position, color = '#ff6b6b' }: { position: [number, number, number], color?: string }) {
  const meshRef = useRef<THREE.Mesh>(null)
  
  useFrame((state) => {
    if (meshRef.current) {
      const t = state.clock.getElapsedTime()
      meshRef.current.position.y = position[1] + Math.sin(t * 2) * 0.2
    }
  })
  
  return (
    <mesh ref={meshRef} position={position}>
      <coneGeometry args={[0.3, 0.8, 8]} />
      <meshStandardMaterial color={color} emissive={color} emissiveIntensity={0.5} />
    </mesh>
  )
}

// 主场景
function Scene({ coordinates, showTerrain }: { 
  coordinates: any[], 
  showTerrain: boolean
}) {
  return (
    <>
      <ambientLight intensity={0.4} />
      <directionalLight position={[20, 30, 10]} intensity={1} castShadow />
      <pointLight position={[0, 15, 0]} intensity={0.5} color="#4ecdc4" />
      
      {showTerrain && <Terrain />}
      
      <axesHelper args={[5]} />
      
      {coordinates.length > 0 && (
        <>
          <RoadCenterLine coordinates={coordinates} />
          <RoadSurface coordinates={coordinates} />
        </>
      )}
      
      <OrbitControls 
        enableDamping 
        dampingFactor={0.05}
        minDistance={5}
        maxDistance={100}
      />
    </>
  )
}

export default function ModelPreview() {
  const [coordinates] = useState(testCoords)
  const [showTerrain, setShowTerrain] = useState(true)
  const [selectedStation, setSelectedStation] = useState<string | null>(null)
  
  // 根据选中的桩号定位
  const focusStation = (station: string) => {
    setSelectedStation(station)
  }
  
  // 视图重置
  const resetView = () => {
    setSelectedStation(null)
  }

  return (
    <div className="model-preview">
      {/* 控制面板 */}
      <div className="control-panel">
        <h2>🎮 三维预览</h2>
        
        <div className="control-group">
          <label>
            <input 
              type="checkbox" 
              checked={showTerrain}
              onChange={(e) => setShowTerrain(e.target.checked)}
            />
            显示地形网格
          </label>
        </div>
        
        <div className="control-group">
          <button className="btn-action" onClick={resetView}>
            重置视图
          </button>
        </div>
        
        <div className="control-group">
          <h4>快速跳转</h4>
          <div className="station-buttons">
            {['K0+000', 'K0+500', 'K1+000', 'K1+500', 'K2+000'].map(station => (
              <button
                key={station}
                className={`station-btn ${selectedStation === station ? 'active' : ''}`}
                onClick={() => focusStation(station)}
              >
                {station}
              </button>
            ))}
          </div>
        </div>
        
        <div className="info">
          <p>🖱️ 鼠标左键: 旋转</p>
          <p>🖱️ 鼠标右键: 平移</p>
          <p>🖱️ 滚轮: 缩放</p>
        </div>
      </div>
      
      {/* 3D 画布 */}
      <div className="canvas-container">
        <Canvas
          camera={{ position: [30, 30, 30], fov: 60 }}
          shadows
        >
          <color attach="background" args={['#0a0a15']} />
          <Suspense fallback={null}>
            <Scene 
              coordinates={coordinates} 
              showTerrain={showTerrain}
            />
          </Suspense>
        </Canvas>
        
        {/* 图例 */}
        <div className="legend">
          <div className="legend-item">
            <span className="line"></span>
            道路中心线
          </div>
          <div className="legend-item">
            <span className="surface"></span>
            道路表面
          </div>
        </div>
        
        {/* 统计 */}
        <div className="stats">
          <span>点数: {coordinates.length}</span>
          <span>范围: K0+000 - K2+000</span>
        </div>
      </div>
      
      <style>{`
        .model-preview {
          display: flex;
          height: 100%;
        }
        
        .control-panel {
          width: 240px;
          background: #1a1a2e;
          padding: 20px;
          display: flex;
          flex-direction: column;
          gap: 16px;
          border-right: 1px solid #333;
        }
        
        .control-panel h2 {
          font-size: 18px;
          color: #00ff88;
          margin-bottom: 8px;
        }
        
        .control-group {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }
        
        .control-group h4 {
          font-size: 12px;
          color: #888;
          margin: 0;
        }
        
        .control-group label {
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 13px;
          color: #ccc;
          cursor: pointer;
        }
        
        .control-group input[type="checkbox"] {
          accent-color: #667eea;
        }
        
        .btn-action {
          padding: 8px 16px;
          background: #252540;
          border: 1px solid #444;
          border-radius: 6px;
          color: #fff;
          font-size: 13px;
          cursor: pointer;
          transition: all 0.2s;
        }
        
        .btn-action:hover {
          background: #333;
          border-color: #667eea;
        }
        
        .station-buttons {
          display: flex;
          flex-wrap: wrap;
          gap: 6px;
        }
        
        .station-btn {
          padding: 4px 10px;
          background: #252540;
          border: 1px solid #444;
          border-radius: 4px;
          color: #aaa;
          font-size: 11px;
          cursor: pointer;
        }
        
        .station-btn:hover, .station-btn.active {
          background: #667eea;
          border-color: #667eea;
          color: #fff;
        }
        
        .info {
          margin-top: auto;
          font-size: 11px;
          color: #666;
        }
        
        .info p {
          margin: 4px 0;
        }
        
        .canvas-container {
          flex: 1;
          position: relative;
        }
        
        .legend {
          position: absolute;
          bottom: 20px;
          left: 20px;
          background: rgba(0, 0, 0, 0.7);
          padding: 12px 16px;
          border-radius: 8px;
          font-size: 12px;
          color: #aaa;
        }
        
        .legend-item {
          display: flex;
          align-items: center;
          gap: 8px;
          margin: 4px 0;
        }
        
        .legend-item .line {
          width: 20px;
          height: 3px;
          background: #00ff88;
        }
        
        .legend-item .surface {
          width: 20px;
          height: 12px;
          background: #3d5a80;
          opacity: 0.8;
        }
        
        .stats {
          position: absolute;
          top: 20px;
          right: 20px;
          background: rgba(0, 0, 0, 0.7);
          padding: 10px 16px;
          border-radius: 8px;
          font-size: 12px;
          color: #00ff88;
          display: flex;
          gap: 16px;
        }
      `}</style>
    </div>
  )
}
