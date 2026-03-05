import { useState, useRef, useMemo, useCallback } from 'react'
import { Canvas, ThreeEvent } from '@react-three/fiber'
import { OrbitControls, Grid, Html } from '@react-three/drei'
import * as THREE from 'three'

// ==================== 类型定义 ====================
interface BIMElement {
  id: string
  name: string
  type: 'wall' | 'column' | 'beam' | 'slab' | 'door' | 'window' | 'equipment'
  position: [number, number, number]
  size: [number, number, number]
  properties?: Record<string, string | number>
  children?: BIMElement[]
}

interface BIMModel {
  id: string
  name: string
  elements: BIMElement[]
}

interface BIMViewerProps {
  model?: BIMModel
  selectable?: boolean
  showProperties?: boolean
}

// ==================== 颜色映射 ====================
const typeColors: Record<string, string> = {
  wall: '#8b7355',
  column: '#4a90e2',
  beam: '#e74c3c',
  slab: '#95a5a6',
  door: '#f39c12',
  window: '#3498db',
  equipment: '#2ecc71'
}

// ==================== BIM构件组件 ====================
function BIMElementMesh({ 
  element, 
  selected, 
  onClick 
}: { 
  element: BIMElement
  selected?: boolean
  onClick?: (e: ThreeEvent<MouseEvent>, el: BIMElement) => void
}) {
  const meshRef = useRef<THREE.Mesh>(null)
  const [hovered, setHovered] = useState(false)
  
  const color = typeColors[element.type] || '#cccccc'
  const [x, y, z] = element.position
  const [w, h, d] = element.size

  return (
    <group>
      <mesh
        ref={meshRef}
        position={[x, y + h/2, z]}
        onClick={(e) => onClick?.(e, element)}
        onPointerOver={() => setHovered(true)}
        onPointerOut={() => setHovered(false)}
      >
        <boxGeometry args={[w, h, d]} />
        <meshStandardMaterial 
          color={color}
          transparent
          opacity={selected ? 1 : 0.85}
        />
      </mesh>
      
      {selected && (
        <lineSegments position={[x, y + h/2, z]}>
          <edgesGeometry args={[new THREE.BoxGeometry(w, h, d)]} />
          <lineBasicMaterial color="#ffff00" />
        </lineSegments>
      )}
      
      {element.children?.map((child, idx) => (
        <BIMElementMesh
          key={`${child.id}-${idx}`}
          element={child}
          onClick={onClick}
        />
      ))}
    </group>
  )
}

// ==================== 属性面板 ====================
function PropertyPanel({ 
  element, 
  onClose 
}: { 
  element: BIMElement | null
  onClose: () => void
}) {
  if (!element) return null
  
  return (
    <div style={{
      position: 'absolute',
      top: 80,
      right: 20,
      width: 280,
      background: 'rgba(26, 26, 46, 0.95)',
      borderRadius: 8,
      border: '1px solid #444',
      overflow: 'hidden',
    }}>
      <div style={{
        padding: '12px 16px',
        background: '#2a2a4a',
        borderBottom: '1px solid #444',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <span style={{ color: '#00ff88', fontWeight: 'bold' }}>
          {element.name}
        </span>
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
          <span style={{ color: '#888' }}>类型: </span>
          <span style={{ color: typeColors[element.type] || '#fff' }}>
            {element.type}
          </span>
        </div>
        
        <div style={{ marginBottom: 8 }}>
          <span style={{ color: '#888' }}>位置: </span>
          <span>({element.position.join(', ')})</span>
        </div>
        
        <div style={{ marginBottom: 8 }}>
          <span style={{ color: '#888' }}>尺寸: </span>
          <span>{element.size.join(' × ')}</span>
        </div>
        
        {element.properties && Object.entries(element.properties).map(([key, value]) => (
          <div key={key} style={{ marginBottom: 6 }}>
            <span style={{ color: '#888' }}>{key}: </span>
            <span>{value}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

// ==================== 图例 ====================
function Legend() {
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
      <div style={{ fontWeight: 'bold', marginBottom: 8, color: '#fff' }}>构件类型</div>
      {Object.entries(typeColors).map(([type, color]) => (
        <div key={type} style={{ display: 'flex', alignItems: 'center', marginBottom: 4 }}>
          <span style={{ 
            width: 16, 
            height: 16, 
            background: color, 
            marginRight: 8,
            borderRadius: 2
          }}></span>
          {type}
        </div>
      ))}
    </div>
  )
}

// ==================== 统计面板 ====================
function StatsPanel({ model }: { model: BIMModel }) {
  const typeCounts = useMemo(() => {
    const counts: Record<string, number> = {}
    const countElements = (elements: BIMElement[]) => {
      elements.forEach(el => {
        counts[el.type] = (counts[el.type] || 0) + 1
        if (el.children) countElements(el.children)
      })
    }
    countElements(model.elements)
    return counts
  }, [model])

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
      <div style={{ fontWeight: 'bold', marginBottom: 8, color: '#fff' }}>{model.name}</div>
      <div>总构件: {Object.values(typeCounts).reduce((a, b) => a + b, 0)}</div>
      {Object.entries(typeCounts).map(([type, count]) => (
        <div key={type} style={{ color: typeColors[type] || '#ccc' }}>
          {type}: {count}
        </div>
      ))}
    </div>
  )
}

// ==================== 主组件 ====================
export default function BIMViewer({ 
  model: propModel,
  selectable = true,
  showProperties = true 
}: BIMViewerProps) {
  const defaultModel: BIMModel = useMemo(() => ({
    id: 'demo-building',
    name: '示例建筑',
    elements: [
      { id: 'col-1', name: 'A-1柱', type: 'column', position: [-8, 0, -8], size: [0.5, 12, 0.5], properties: { '材料': 'C30混凝土', '配筋': '4Φ25' } },
      { id: 'col-2', name: 'A-2柱', type: 'column', position: [-8, 0, 8], size: [0.5, 12, 0.5], properties: { '材料': 'C30混凝土', '配筋': '4Φ25' } },
      { id: 'col-3', name: 'B-1柱', type: 'column', position: [8, 0, -8], size: [0.5, 12, 0.5], properties: { '材料': 'C30混凝土', '配筋': '4Φ25' } },
      { id: 'col-4', name: 'B-2柱', type: 'column', position: [8, 0, 8], size: [0.5, 12, 0.5], properties: { '材料': 'C30混凝土', '配筋': '4Φ25' } },
      { id: 'beam-1', name: 'A轴梁', type: 'beam', position: [0, 10, -8], size: [16, 0.6, 0.4], properties: { '材料': 'C30混凝土' } },
      { id: 'beam-2', name: 'B轴梁', type: 'beam', position: [0, 10, 8], size: [16, 0.6, 0.4], properties: { '材料': 'C30混凝土' } },
      { id: 'slab-1', name: '一层楼板', type: 'slab', position: [0, 5, 0], size: [17, 0.3, 17], properties: { '厚度': '120mm' } },
      { id: 'slab-2', name: '二层楼板', type: 'slab', position: [0, 15, 0], size: [17, 0.3, 17], properties: { '厚度': '120mm' } },
      { id: 'wall-1', name: '北墙', type: 'wall', position: [0, 6, -10], size: [20, 12, 0.3], properties: { '厚度': '200mm' } },
      { id: 'wall-2', name: '南墙', type: 'wall', position: [0, 6, 10], size: [20, 12, 0.3], properties: { '厚度': '200mm' } },
      { id: 'door-1', name: '主入口门', type: 'door', position: [0, 1.5, 10], size: [2, 3, 0.1], properties: { '型号': 'M1' } },
      { id: 'window-1', name: '北窗1', type: 'window', position: [-5, 8, -10], size: [3, 2.5, 0.1], properties: { '型号': 'C1' } },
      { id: 'equip-1', name: '空调机组', type: 'equipment', position: [6, 0.5, -6], size: [2, 1, 1.5], properties: { '型号': 'KF-120', '功率': '12kW' } }
    ]
  }), [])

  const model = propModel || defaultModel
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [viewMode, setViewMode] = useState<'3d' | 'x' | 'y' | 'z'>('3d')

  const handleSelect = (element: BIMElement | null) => {
    if (!selectable) return
    setSelectedId(element?.id || null)
  }

  const cameraPositions = {
    '3d': [30, 25, 30],
    'x': [50, 5, 0],
    'y': [0, 50, 0.1],
    'z': [0, 5, 50]
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
        <h3 style={{ margin: 0, color: '#00ff88' }}>🏗️ BIM模型查看器</h3>
        
        <div style={{ display: 'flex', gap: '8px' }}>
          {(['3d', 'x', 'y', 'z'] as const).map(mode => (
            <button
              key={mode}
              onClick={() => setViewMode(mode)}
              style={{
                padding: '6px 14px',
                background: viewMode === mode ? '#667eea' : '#333',
                border: 'none',
                borderRadius: 4,
                color: 'white',
                cursor: 'pointer',
                fontSize: 13
              }}
            >
              {mode === '3d' ? '3D视图' : `${mode}轴视图`}
            </button>
          ))}
        </div>
        
        <label style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#ccc', fontSize: 14 }}>
          <input 
            type="checkbox" 
            checked={selectable}
            onChange={(e) => {
              if (!e.target.checked) setSelectedId(null)
            }}
          />
          可选择构件
        </label>
      </div>
      
      {/* 3D画布 */}
      <div style={{ flex: 1, position: 'relative' }}>
        <Canvas 
          camera={{ 
            position: cameraPositions[viewMode] as [number, number, number], 
            fov: 50 
          }}
          shadows
        >
          <color attach="background" args={['#0a0a15']} />
          
          <ambientLight intensity={0.5} />
          <directionalLight position={[20, 30, 10]} intensity={1} castShadow />
          <pointLight position={[-10, 20, -10]} intensity={0.5} color="#4ecdc4" />
          
          <Grid 
            args={[100, 100]} 
            cellSize={1} 
            cellThickness={0.5}
            sectionSize={5}
            sectionThickness={1}
            fadeDistance={80}
            infiniteGrid
            cellColor="#333"
            sectionColor="#555"
          />
          
          <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.01, 0]} receiveShadow>
            <planeGeometry args={[100, 100]} />
            <meshStandardMaterial color="#1a1a2e" />
          </mesh>
          
          {model.elements.map((element) => (
            <BIMElementMesh
              key={element.id}
              element={element}
              selected={element.id === selectedId}
              onClick={(_, el) => handleSelect(el)}
            />
          ))}
          
          <axesHelper args={[10]} />
          
          <OrbitControls 
            enableDamping 
            dampingFactor={0.05}
            minDistance={5}
            maxDistance={150}
          />
        </Canvas>
        
        <Legend />
        <StatsPanel model={model} />
        
        {showProperties && selectedId && (
          <PropertyPanel 
            element={model.elements.find(e => e.id === selectedId) || null} 
            onClose={() => setSelectedId(null)} 
          />
        )}
      </div>
    </div>
  )
}
