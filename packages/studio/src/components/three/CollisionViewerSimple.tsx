// Collision Detection 3D Viewer
// 基于 React Three Fiber

import { useState, useRef } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { OrbitControls, Grid, Html, PerspectiveCamera } from '@react-three/drei'
import * as THREE from 'three'

// 碰撞物体
interface CollisionObject {
  id: string
  name: string
  position: [number, number, number]
  size: [number, number, number]
  color: string
  hasCollision: boolean
}

// 初始碰撞数据
const initialObjects: CollisionObject[] = [
  { id: '1', name: '柱子A', position: [0, 1, 0], size: [1, 2, 1], color: '#667eea', hasCollision: false },
  { id: '2', name: '柱子B', position: [2, 1, 0], size: [1, 2, 1], color: '#764ba2', hasCollision: true },
  { id: '3', name: '横梁A', position: [1, 2.5, 0], size: [3, 0.5, 1], color: '#28a745', hasCollision: true },
  { id: '4', name: '设备A', position: [-2, 0.5, 1], size: [1, 1, 1], color: '#ffc107', hasCollision: false },
  { id: '5', name: '设备B', position: [-2, 0.5, -1], size: [1, 1, 1], color: '#dc3545', hasCollision: false },
]

// 碰撞框组件
function CollisionBox({ 
  object, 
  selected,
  onClick 
}: { 
  object: CollisionObject
  selected: boolean
  onClick: () => void
}) {
  const meshRef = useRef<THREE.Mesh>(null)
  
  useFrame((state) => {
    if (meshRef.current && object.hasCollision) {
      // 碰撞物体闪烁
      const t = state.clock.elapsedTime
      const scale = 1 + Math.sin(t * 3) * 0.05
      meshRef.current.scale.setScalar(scale)
    }
  })
  
  return (
    <mesh 
      ref={meshRef} 
      position={object.position}
      onClick={onClick}
    >
      <boxGeometry args={object.size} />
      <meshStandardMaterial 
        color={object.hasCollision ? '#ff0000' : object.color}
        transparent
        opacity={selected ? 1 : 0.8}
        wireframe={object.hasCollision}
      />
    </mesh>
  )
}

// 场景组件
function CollisionScene({ 
  objects, 
  selectedId, 
  onSelect 
}: { 
  objects: CollisionObject[]
  selectedId: string | null
  onSelect: (id: string) => void
}) {
  return (
    <>
      <ambientLight intensity={0.6} />
      <directionalLight position={[10, 15, 10]} intensity={1} castShadow />
      <pointLight position={[-5, 5, -5]} intensity={0.5} color="#ff6600" />
      
      {objects.map(obj => (
        <CollisionBox 
          key={obj.id}
          object={obj}
          selected={selectedId === obj.id}
          onClick={() => onSelect(obj.id)}
        />
      ))}
      
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.01, 0]}>
        <planeGeometry args={[30, 30]} />
        <meshStandardMaterial color="#1a1a2e" />
      </mesh>
      
      <Grid 
        args={[30, 30]} 
        cellSize={1}
        cellThickness={0.5}
        cellColor="#333"
        sectionSize={5}
        sectionThickness={1}
        sectionColor="#444"
        fadeDistance={25}
        infiniteGrid
      />
    </>
  )
}

// 主组件
export default function CollisionViewerSimple() {
  const [objects, setObjects] = useState<CollisionObject[]>(initialObjects)
  const [selectedId, setSelectedId] = useState<string | null>(null)
  
  const selectedObject = objects.find(o => o.id === selectedId)
  
  const stats = {
    total: objects.length,
    collisions: objects.filter(o => o.hasCollision).length,
    cleared: objects.filter(o => !o.hasCollision).length
  }

  return (
    <div style={{ display: 'flex', height: 'calc(100vh - 150px)' }}>
      {/* 3D 视图 */}
      <div style={{ flex: 1, position: 'relative' }}>
        <Canvas shadows>
          <PerspectiveCamera makeDefault position={[8, 8, 8]} fov={50} />
          <OrbitControls enableDamping dampingFactor={0.05} />
          <CollisionScene 
            objects={objects} 
            selectedId={selectedId}
            onSelect={setSelectedId}
          />
        </Canvas>
        
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
          <div style={{ color: '#ff0000', marginBottom: '4px' }}>■ 碰撞物体</div>
          <div style={{ color: '#667eea' }}>■ 正常物体</div>
        </div>
      </div>
      
      {/* 右侧面板 */}
      <div style={{ 
        width: '300px', 
        background: '#1a1a2e', 
        padding: '16px',
        borderLeft: '1px solid #333',
        overflow: 'auto'
      }}>
        <h3 style={{ marginTop: 0 }}>碰撞检测</h3>
        
        {/* 统计 */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', marginBottom: '16px' }}>
          <div style={statCard}>
            <div style={{ fontSize: '24px', fontWeight: 'bold' }}>{stats.total}</div>
            <div style={{ color: '#888', fontSize: '12px' }}>总物体</div>
          </div>
          <div style={{ ...statCard, border: '1px solid #ff0000' }}>
            <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#ff0000' }}>{stats.collisions}</div>
            <div style={{ color: '#888', fontSize: '12px' }}>碰撞数</div>
          </div>
        </div>
        
        {/* 物体列表 */}
        <h4>物体列表</h4>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {objects.map(obj => (
            <div 
              key={obj.id}
              onClick={() => setSelectedId(obj.id)}
              style={{
                padding: '10px',
                background: selectedId === obj.id ? '#333' : '#252540',
                borderRadius: '6px',
                cursor: 'pointer',
                borderLeft: obj.hasCollision ? '3px solid #ff0000' : '3px solid transparent'
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span>{obj.name}</span>
                {obj.hasCollision && <span style={{ color: '#ff0000' }}>⚠️</span>}
              </div>
              <div style={{ fontSize: '12px', color: '#888', marginTop: '4px' }}>
                位置: ({obj.position.join(', ')})
              </div>
            </div>
          ))}
        </div>
        
        {/* 选中物体详情 */}
        {selectedObject && (
          <div style={{ marginTop: '16px', padding: '12px', background: '#252540', borderRadius: '8px' }}>
            <h4 style={{ marginTop: 0 }}>{selectedObject.name}</h4>
            <div style={{ fontSize: '13px', color: '#aaa' }}>
              <p>尺寸: {selectedObject.size.join(' × ')}</p>
              <p>状态: {selectedObject.hasCollision ? '⚠️ 碰撞' : '✅ 正常'}</p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

const statCard = {
  background: '#252540',
  padding: '12px',
  borderRadius: '8px',
  textAlign: 'center' as const
}
