import { useState, useEffect, useRef } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { OrbitControls, Grid, Text, Html } from '@react-three/drei'
import * as THREE from 'three'

interface Component {
  id: string
  position: [number, number, number]
  size: [number, number, number]
  color: string
  isCollision?: boolean
}

interface CollisionResult {
  lod0?: { status: string; distance: any }
  lod1?: { status: string; distance: any }
  lod2?: { status: string; distance: any }
}

// 碰撞的两个方块
function CollisionBox({ component, showLabel = true }: { component: Component; showLabel?: boolean }) {
  const meshRef = useRef<THREE.Mesh>(null)
  
  useFrame((state) => {
    if (meshRef.current && component.isCollision) {
      // 碰撞时闪烁
      const t = state.clock.getElapsedTime()
      const scale = 1 + Math.sin(t * 10) * 0.05
      meshRef.current.scale.setScalar(scale)
    }
  })
  
  const [x, y, z] = component.position
  const [w, h, d] = component.size
  
  return (
    <group position={[x, y, z]}>
      <mesh ref={meshRef}>
        <boxGeometry args={[w, h, d]} />
        <meshStandardMaterial 
          color={component.isCollision ? "#ff3333" : component.color} 
          transparent 
          opacity={0.8}
          emissive={component.isCollision ? "#ff0000" : "#000000"}
          emissiveIntensity={component.isCollision ? 0.5 : 0}
        />
      </mesh>
      
      {/* 边框 */}
      <lineSegments>
        <edgesGeometry args={[new THREE.BoxGeometry(w, h, d)]} />
        <lineBasicMaterial color={component.isCollision ? "#ff0000" : "#ffffff"} />
      </lineSegments>
      
      {/* 标签 */}
      {showLabel && (
        <Html position={[0, h/2 + 0.5, 0]} center>
          <div style={{
            background: component.isCollision ? 'rgba(255,0,0,0.9)' : 'rgba(0,100,200,0.9)',
            color: 'white',
            padding: '4px 8px',
            borderRadius: '4px',
            fontSize: '12px',
            whiteSpace: 'nowrap'
          }}>
            {component.id}
            <br/>
            Size: {w}x{h}x{d}
          </div>
        </Html>
      )}
    </group>
  )
}

// 碰撞连线
function CollisionLine({ comp1, comp2, detected }: { 
  comp1: Component; 
  comp2: Component; 
  detected: boolean 
}) {
  if (!detected) return null
  
  const p1 = new THREE.Vector3(...comp1.position)
  const p2 = new THREE.Vector3(...comp2.position)
  const mid = p1.clone().add(p2).multiplyScalar(0.5)
  
  // 计算方向
  const dir = p2.clone().sub(p1)
  const length = dir.length()
  dir.normalize()
  
  return (
    <group>
      {/* 连接线 */}
      <Line 
        start={p1.toArray()} 
        end={p2.toArray()} 
        color="#ff0000" 
        lineWidth={3}
        dashed
      />
      
      {/* 距离标签 */}
      <Html position={mid.toArray()}>
        <div style={{
          background: 'rgba(255,0,0,0.9)',
          color: 'white',
          padding: '4px 8px',
          borderRadius: '4px',
          fontSize: '11px',
          whiteSpace: 'nowrap'
        }}>
          距离: {length.toFixed(3)}m
        </div>
      </Html>
    </group>
  )
}

// 简单线条组件
function Line({ start, end, color, lineWidth, dashed }: {
  start: number[]
  end: number[]
  color: string
  lineWidth: number
  dashed?: boolean
}) {
  const points = [
    new THREE.Vector3(...start),
    new THREE.Vector3(...end)
  ]
  
  return (
    <line>
      <bufferGeometry>
        <bufferAttribute
          attach="attributes-position"
          count={2}
          array={new Float32Array([...start, ...end])}
          itemSize={3}
        />
      </bufferGeometry>
      <lineBasicMaterial color={color} linewidth={lineWidth} />
    </line>
  )
}

// 主场景
function Scene({ components, collisionResult }: { 
  components: Component[]
  collisionResult: CollisionResult | null
}) {
  const hasCollision = collisionResult?.lod1?.status === 'COLLISION'
  
  return (
    <>
      {/* 灯光 */}
      <ambientLight intensity={0.4} />
      <directionalLight position={[20, 20, 10]} intensity={1} />
      <pointLight position={[0, 10, 0]} intensity={0.5} color="#4ecdc4" />
      
      {/* 地面 */}
      <Grid args={[50, 50]} cellSize={1} cellThickness={0.5} sectionSize={5} />
      
      {/* 组件 */}
      {components.map((comp) => (
        <CollisionBox 
          key={comp.id} 
          component={{
            ...comp,
            isCollision: hasCollision
          }} 
        />
      ))}
      
      {/* 碰撞连接线 */}
      {collisionResult && hasCollision && components.length >= 2 && (
        <CollisionLine 
          comp1={components[0]} 
          comp2={components[1]} 
          detected={true}
        />
      )}
      
      {/* 坐标轴 */}
      <axesHelper args={[5]} />
      
      {/* 控制器 */}
      <OrbitControls />
    </>
  )
}

export default function CollisionViewer() {
  const [components, setComponents] = useState<Component[]>([
    { id: 'col-001', position: [0, 0.5, 0], size: [1, 1, 1], color: '#4a90e2' },
    { id: 'col-002', position: [0.5, 0.3, 0.2], size: [1, 1, 1], color: '#4a90e2' }
  ])
  
  const [collisionResult, setCollisionResult] = useState<CollisionResult | null>(null)
  const [selectedLOD, setSelectedLOD] = useState(1)
  const [loading, setLoading] = useState(false)
  
  // 测试碰撞检测
  const testCollision = async () => {
    setLoading(true)
    
    try {
      const response = await fetch('http://localhost:8000/api/v1/engineering/demo/collision-test', {
        method: 'POST'
      })
      const data = await response.json()
      setCollisionResult(data.results)
      
      // 更新组件位置显示
      setComponents([
        { 
          id: 'col-001', 
          position: [0, 0.5, 0], 
          size: [1, 1, 1], 
          color: '#4a90e2' 
        },
        { 
          id: 'col-002', 
          position: [0.5, 0.3, 0.2], 
          size: [1, 1, 1], 
          color: '#4a90e2' 
        }
      ])
      
    } catch (error) {
      console.error('API调用失败:', error)
    }
    
    setLoading(false)
  }
  
  useEffect(() => {
    testCollision()
  }, [])
  
  const currentResult = selectedLOD === 0 ? collisionResult?.lod0 : 
                        selectedLOD === 1 ? collisionResult?.lod1 : 
                        collisionResult?.lod2
  
  return (
    <div style={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* 控制面板 */}
      <div style={{
        padding: '15px',
        background: '#1a1a2e',
        borderBottom: '1px solid #333',
        display: 'flex',
        alignItems: 'center',
        gap: '20px'
      }}>
        <h3 style={{ margin: 0, color: '#00ff88' }}>碰撞检测演示</h3>
        
        <div style={{ display: 'flex', gap: '10px' }}>
          {[0, 1, 2].map(lod => (
            <button
              key={lod}
              onClick={() => setSelectedLOD(lod)}
              style={{
                padding: '8px 16px',
                background: selectedLOD === lod ? '#667eea' : '#333',
                border: 'none',
                borderRadius: '6px',
                color: 'white',
                cursor: 'pointer'
              }}
            >
              LOD{lod}
            </button>
          ))}
        </div>
        
        <button
          onClick={testCollision}
          disabled={loading}
          style={{
            padding: '8px 20px',
            background: loading ? '#666' : 'linear-gradient(135deg, #667eea, #764ba2)',
            border: 'none',
            borderRadius: '6px',
            color: 'white',
            cursor: loading ? 'not-allowed' : 'pointer'
          }}
        >
          {loading ? '检测中...' : '重新检测'}
        </button>
        
        {currentResult && (
          <div style={{
            padding: '8px 16px',
            background: currentResult.status === 'COLLISION' ? 'rgba(255,0,0,0.2)' : 'rgba(0,255,0,0.2)',
            borderRadius: '6px',
            border: `1px solid ${currentResult.status === 'COLLISION' ? '#ff3333' : '#00ff88'}`,
            color: currentResult.status === 'COLLISION' ? '#ff3333' : '#00ff88'
          }}>
            状态: {currentResult.status === 'COLLISION' ? '⚠️ 碰撞' : '✓ 无碰撞'}
            {currentResult.distance && (
              <span style={{ marginLeft: '10px' }}>
                距离: {currentResult.distance.total?.toFixed(3)}m
              </span>
            )}
          </div>
        )}
      </div>
      
      {/* 3D画布 */}
      <div style={{ flex: 1 }}>
        <Canvas camera={{ position: [5, 5, 8], fov: 50 }}>
          <color attach="background" args={['#0a0a15']} />
          <Scene components={components} collisionResult={collisionResult} />
        </Canvas>
      </div>
      
      {/* 说明 */}
      <div style={{
        padding: '10px 15px',
        background: '#1a1a2e',
        borderTop: '1px solid #333',
        fontSize: '12px',
        color: '#888'
      }}>
        <strong>LOD精度说明：</strong>
        LOD0 = 米级 (1.0m容差) | 
        LOD1 = 分米级 (0.1m容差) | 
        LOD2 = 厘米级 (0.01m容差)
      </div>
    </div>
  )
}
