import { useState, useRef, useMemo, useCallback } from 'react'
import { Canvas, ThreeEvent, useFrame } from '@react-three/fiber'
import { OrbitControls, Html, Text, Line, Grid } from '@react-three/drei'
import * as THREE from 'three'

// ==================== 类型定义 ====================
interface SelectableObject {
  id: string
  name: string
  type: 'building' | 'road' | 'tree' | 'pole' | 'vehicle'
  position: [number, number, number]
  size: [number, number, number]
  color: string
  properties?: Record<string, string | number>
}

interface Annotation {
  id: string
  position: [number, number, number]
  title: string
  content: string
  color?: string
}

interface Measurement {
  id: string
  start: [number, number, number]
  end: [number, number, number]
  distance: number
  type: 'distance' | 'area'
}

interface SceneInteractionProps {
  objects?: SelectableObject[]
  annotations?: Annotation[]
  measurements?: Measurement[]
  onSelect?: (object: SelectableObject | null) => void
  onMeasure?: (measurement: Measurement) => void
}

// ==================== 可选择对象 ====================
function SelectableObjectMesh({ 
  obj, 
  selected, 
  onClick 
}: { 
  obj: SelectableObject
  selected?: boolean
  onClick?: (e: ThreeEvent<MouseEvent>, el: SelectableObject) => void
}) {
  const meshRef = useRef<THREE.Mesh>(null)
  const [hovered, setHovered] = useState(false)
  
  const [x, y, z] = obj.position
  const [w, h, d] = obj.size

  return (
    <group>
      <mesh
        ref={meshRef}
        position={[x, y + h/2, z]}
        onClick={(e) => {
          e.stopPropagation()
          onClick?.(e, obj)
        }}
        onPointerOver={() => setHovered(true)}
        onPointerOut={() => setHovered(false)}
      >
        <boxGeometry args={[w, h, d]} />
        <meshStandardMaterial 
          color={obj.color}
          transparent
          opacity={selected ? 1 : hovered ? 0.9 : 0.7}
          emissive={selected ? '#ffff00' : hovered ? obj.color : '#000000'}
          emissiveIntensity={selected ? 0.3 : hovered ? 0.2 : 0}
        />
      </mesh>
      
      {/* 选中边框 */}
      {selected && (
        <lineSegments position={[x, y + h/2, z]}>
          <edgesGeometry args={[new THREE.BoxGeometry(w * 1.02, h * 1.02, d * 1.02)]} />
          <lineBasicMaterial color="#ffff00" linewidth={2} />
        </lineSegments>
      )}
    </group>
  )
}

// ==================== 信息标注 ====================
function AnnotationMarker({ 
  annotation,
  onEdit,
  onDelete
}: { 
  annotation: Annotation
  onEdit?: (a: Annotation) => void
  onDelete?: (id: string) => void
}) {
  const [expanded, setExpanded] = useState(false)
  const color = annotation.color || '#ff6b6b'

  return (
    <group position={annotation.position}>
      {/* 标注点 */}
      <mesh onClick={() => setExpanded(!expanded)}>
        <sphereGeometry args={[0.5, 16, 16]} />
        <meshStandardMaterial 
          color={color}
          emissive={color}
          emissiveIntensity={0.5}
        />
      </mesh>
      
      {/* 标注线 */}
      <Line 
        points={[[0, 0, 0], [0, -3, 0]]}
        color={color}
        lineWidth={2}
      />
      
      {/* 标注内容 */}
      <Html position={[0, -3.5, 0]} center distanceFactor={30}>
        <div style={{
          background: 'rgba(26, 26, 46, 0.95)',
          padding: expanded ? '10px 14px' : '6px 10px',
          borderRadius: 6,
          border: `1px solid ${color}`,
          minWidth: 120,
          cursor: 'pointer',
          transition: 'all 0.2s'
        }}>
          <div style={{ 
            color: '#fff', 
            fontWeight: 'bold',
            fontSize: expanded ? 14 : 12,
            marginBottom: expanded ? 6 : 0
          }}>
            {annotation.title}
          </div>
          
          {expanded && (
            <>
              <div style={{ color: '#ccc', fontSize: 12, marginBottom: 8 }}>
                {annotation.content}
              </div>
              <div style={{ display: 'flex', gap: 8 }}>
                <button 
                  onClick={(e) => { e.stopPropagation(); onEdit?.(annotation) }}
                  style={{
                    padding: '2px 8px',
                    fontSize: 11,
                    background: '#4a90e2',
                    border: 'none',
                    borderRadius: 3,
                    color: 'white',
                    cursor: 'pointer'
                  }}
                >
                  编辑
                </button>
                <button 
                  onClick={(e) => { e.stopPropagation(); onDelete?.(annotation.id) }}
                  style={{
                    padding: '2px 8px',
                    fontSize: 11,
                    background: '#e74c3c',
                    border: 'none',
                    borderRadius: 3,
                    color: 'white',
                    cursor: 'pointer'
                  }}
                >
                  删除
                </button>
              </div>
            </>
          )}
        </div>
      </Html>
    </group>
  )
}

// ==================== 测量线 ====================
function MeasurementLine({ 
  measurement,
  active
}: { 
  measurement: Measurement
  active?: boolean
}) {
  const start = new THREE.Vector3(...measurement.start)
  const end = new THREE.Vector3(...measurement.end)
  const mid = start.clone().add(end).multiplyScalar(0.5)

  return (
    <group>
      {/* 测量线 */}
      <Line 
        points={[start, end]}
        color={active ? '#00ff00' : '#ffd700'}
        lineWidth={3}
      />
      
      {/* 起点标记 */}
      <mesh position={start.toArray()}>
        <sphereGeometry args={[0.3, 16, 16]} />
        <meshStandardMaterial color={active ? '#00ff00' : '#ffd700'} />
      </mesh>
      
      {/* 终点标记 */}
      <mesh position={end.toArray()}>
        <sphereGeometry args={[0.3, 16, 16]} />
        <meshStandardMaterial color={active ? '#00ff00' : '#ffd700'} />
      </mesh>
      
      {/* 距离标签 */}
      <Html position={mid.toArray()} center>
        <div style={{
          background: 'rgba(0,0,0,0.8)',
          padding: '4px 8px',
          borderRadius: 4,
          color: '#ffd700',
          fontSize: 12,
          fontWeight: 'bold',
          whiteSpace: 'nowrap'
        }}>
          {measurement.distance.toFixed(2)} m
        </div>
      </Html>
    </group>
  )
}

// ==================== 测量中的临时线 ====================
function TempMeasurementLine({ 
  start,
  end
}: { 
  start: [number, number, number]
  end: [number, number, number]
}) {
  const startVec = new THREE.Vector3(...start)
  const endVec = new THREE.Vector3(...end)
  const mid = startVec.clone().add(endVec).multiplyScalar(0.5)
  const distance = startVec.distanceTo(endVec)

  return (
    <group>
      <Line 
        points={[startVec, endVec]}
        color="#00ff00"
        lineWidth={2}
        dashed
      />
      
      <Html position={mid.toArray()} center>
        <div style={{
          background: 'rgba(0,0,0,0.8)',
          padding: '4px 8px',
          borderRadius: 4,
          color: '#00ff00',
          fontSize: 12,
          fontWeight: 'bold',
          whiteSpace: 'nowrap'
        }}>
          {distance.toFixed(2)} m
        </div>
      </Html>
    </group>
  )
}

// ==================== 测量面板 ====================
function MeasurementPanel({ 
  mode,
  measurements,
  onClear
}: { 
  mode: 'select' | 'measure' | 'annotate'
  measurements: Measurement[]
  onClear: () => void
}) {
  return (
    <div style={{
      position: 'absolute',
      bottom: 80,
      left: '50%',
      transform: 'translateX(-50%)',
      background: 'rgba(26, 26, 46, 0.95)',
      padding: '10px 16px',
      borderRadius: 8,
      border: '1px solid #444',
      display: 'flex',
      alignItems: 'center',
      gap: '20px'
    }}>
      <div style={{ color: '#fff', fontSize: 13 }}>
        当前模式: 
        <span style={{ 
          color: mode === 'select' ? '#4a90e2' : 
                 mode === 'measure' ? '#ffd700' : '#ff6b6b',
          marginLeft: 8,
          fontWeight: 'bold'
        }}>
          {mode === 'select' ? '选择' : mode === 'measure' ? '测量' : '标注'}
        </span>
      </div>
      
      {measurements.length > 0 && (
        <div style={{ color: '#ffd700', fontSize: 13 }}>
          已测量: {measurements.length} 条
        </div>
      )}
      
      {measurements.length > 0 && (
        <button
          onClick={onClear}
          style={{
            padding: '4px 12px',
            background: '#e74c3c',
            border: 'none',
            borderRadius: 4,
            color: 'white',
            cursor: 'pointer',
            fontSize: 12
          }}
        >
          清除测量
        </button>
      )}
    </div>
  )
}

// ==================== 选中信息面板 ====================
function SelectionPanel({ 
  selected,
  onClear
}: { 
  selected: SelectableObject | null
  onClear: () => void
}) {
  if (!selected) return null

  return (
    <div style={{
      position: 'absolute',
      top: 80,
      right: 20,
      width: 280,
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
        <span style={{ color: '#00ff88', fontWeight: 'bold' }}>
          {selected.name}
        </span>
        <button
          onClick={onClear}
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
          <span style={{ color: selected.color }}>{selected.type}</span>
        </div>
        
        <div style={{ marginBottom: 8 }}>
          <span style={{ color: '#888' }}>位置: </span>
          <span>({selected.position.join(', ')})</span>
        </div>
        
        <div style={{ marginBottom: 8 }}>
          <span style={{ color: '#888' }}>尺寸: </span>
          <span>{selected.size.join(' × ')}</span>
        </div>
        
        {selected.properties && Object.entries(selected.properties).map(([key, value]) => (
          <div key={key} style={{ marginBottom: 6 }}>
            <span style={{ color: '#888' }}>{key}: </span>
            <span>{value}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

// ==================== 工具栏 ====================
function Toolbar({ 
  mode,
  onModeChange,
  onAddAnnotation
}: { 
  mode: 'select' | 'measure' | 'annotate'
  onModeChange: (mode: 'select' | 'measure' | 'annotate') => void
  onAddAnnotation?: () => void
}) {
  return (
    <div style={{
      position: 'absolute',
      top: 80,
      left: 20,
      background: 'rgba(26, 26, 46, 0.95)',
      padding: '10px',
      borderRadius: 8,
      border: '1px solid #444',
      display: 'flex',
      flexDirection: 'column',
      gap: '8px'
    }}>
      <button
        onClick={() => onModeChange('select')}
        style={{
          padding: '10px 16px',
          background: mode === 'select' ? '#4a90e2' : 'transparent',
          border: '1px solid #444',
          borderRadius: 6,
          color: 'white',
          cursor: 'pointer',
          fontSize: 13,
          display: 'flex',
          alignItems: 'center',
          gap: 8
        }}
      >
        👆 选择
      </button>
      
      <button
        onClick={() => onModeChange('measure')}
        style={{
          padding: '10px 16px',
          background: mode === 'measure' ? '#ffd700' : 'transparent',
          border: '1px solid #444',
          borderRadius: 6,
          color: mode === 'measure' ? '#000' : 'white',
          cursor: 'pointer',
          fontSize: 13,
          display: 'flex',
          alignItems: 'center',
          gap: 8
        }}
      >
        📏 测量
      </button>
      
      <button
        onClick={() => { onModeChange('annotate'); onAddAnnotation?.() }}
        style={{
          padding: '10px 16px',
          background: mode === 'annotate' ? '#ff6b6b' : 'transparent',
          border: '1px solid #444',
          borderRadius: 6,
          color: 'white',
          cursor: 'pointer',
          fontSize: 13,
          display: 'flex',
          alignItems: 'center',
          gap: 8
        }}
      >
        📍 标注
      </button>
    </div>
  )
}

// ==================== 主组件 ====================
export default function SceneInteraction({ 
  objects: propObjects,
  annotations: propAnnotations,
  measurements: propMeasurements,
  onSelect,
  onMeasure 
}: SceneInteractionProps) {
  // 默认场景对象
  const defaultObjects: SelectableObject[] = [
    { id: 'bld-1', name: '办公楼', type: 'building', position: [-15, 0, -15], size: [20, 15, 15], color: '#4a90e2', properties: { 楼层: 5, 面积: '3000m²' } },
    { id: 'bld-2', name: '仓库', type: 'building', position: [15, 0, -10], size: [12, 8, 18], color: '#8b7355', properties: { 用途: '存储', 面积: '1500m²' } },
    { id: 'road-1', name: '主干道', type: 'road', position: [0, 0.1, 0], size: [100, 0.2, 8], color: '#2d3436', properties: { 宽度: '8m', 车道: 4 } },
    { id: 'tree-1', name: '景观树A', type: 'tree', position: [-8, 0, 5], size: [2, 6, 2], color: '#2ecc71', properties: { 品种: '银杏', 高度: '6m' } },
    { id: 'tree-2', name: '景观树B', type: 'tree', position: [8, 0, 5], size: [2, 5, 2], color: '#27ae60', properties: { 品种: '桂花', 高度: '5m' } },
    { id: 'pole-1', name: '路灯杆', type: 'pole', position: [-5, 0, 10], size: [0.3, 8, 0.3], color: '#f39c12', properties: { 高度: '8m', 功率: '200W' } },
    { id: 'pole-2', name: '路灯杆', type: 'pole', position: [5, 0, 10], size: [0.3, 8, 0.3], color: '#f39c12', properties: { 高度: '8m', 功率: '200W' } },
    { id: 'veh-1', name: '工程车', type: 'vehicle', position: [10, 0, 5], size: [4, 2, 2], color: '#e74c3c', properties: { 型号: '东风牌', 载重: '5吨' } }
  ]

  const defaultAnnotations: Annotation[] = [
    { id: 'ann-1', position: [-15, 18, -15], title: '办公楼', content: '5层框架结构，建筑面积3000㎡', color: '#4a90e2' },
    { id: 'ann-2', position: [15, 10, -10], title: '仓库', content: '单层钢结构，用于物资存储', color: '#8b7355' }
  ]

  const objects = propObjects || defaultObjects
  const annotations = propAnnotations || defaultAnnotations
  
  const [mode, setMode] = useState<'select' | 'measure' | 'annotate'>('select')
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [measurements, setMeasurements] = useState<Measurement[]>(propMeasurements || [])
  const [tempMeasurePoint, setTempMeasurePoint] = useState<[number, number, number] | null>(null)
  const [sceneAnnotations, setSceneAnnotations] = useState<Annotation[]>(annotations)
  const [measureStart, setMeasureStart] = useState<[number, number, number] | null>(null)

  const selected = objects.find(o => o.id === selectedId) || null

  const handleObjectClick = (e: ThreeEvent<MouseEvent>, obj: SelectableObject) => {
    if (mode === 'select') {
      setSelectedId(obj.id)
      onSelect?.(obj)
    }
  }

  const handleGroundClick = (e: ThreeEvent<MouseEvent>) => {
    const point = e.point
    
    if (mode === 'measure') {
      if (!measureStart) {
        setMeasureStart([point.x, point.y, point.z])
      } else {
        const end: [number, number, number] = [point.x, point.y, point.z]
        const startVec = new THREE.Vector3(...measureStart)
        const endVec = new THREE.Vector3(...end)
        const distance = startVec.distanceTo(endVec)
        
        const newMeasurement: Measurement = {
          id: `meas-${Date.now()}`,
          start: measureStart,
          end,
          distance,
          type: 'distance'
        }
        
        setMeasurements([...measurements, newMeasurement])
        onMeasure?.(newMeasurement)
        setMeasureStart(null)
      }
    }
  }

  const handleAddAnnotation = () => {
    const newAnnotation: Annotation = {
      id: `ann-${Date.now()}`,
      position: [0, 5, 0],
      title: '新标注',
      content: '点击编辑内容',
      color: '#ff6b6b'
    }
    setSceneAnnotations([...sceneAnnotations, newAnnotation])
  }

  const handleDeleteAnnotation = (id: string) => {
    setSceneAnnotations(sceneAnnotations.filter(a => a.id !== id))
  }

  const handleClearMeasurements = () => {
    setMeasurements([])
    setMeasureStart(null)
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
        alignItems: 'center'
      }}>
        <h3 style={{ margin: 0, color: '#00ff88' }}>🎯 场景交互增强</h3>
        
        <div style={{ 
          padding: '6px 12px', 
          background: '#2a2a4a', 
          borderRadius: 4,
          color: '#888',
          fontSize: 13
        }}>
          点击选择构件 → 测量距离 → 添加信息标注
        </div>
        
        <div style={{ marginLeft: 'auto', color: '#888', fontSize: 13 }}>
          {objects.length} 个对象 / {sceneAnnotations.length} 个标注 / {measurements.length} 条测量
        </div>
      </div>
      
      {/* 3D画布 */}
      <div style={{ flex: 1, position: 'relative' }}>
        <Canvas 
          camera={{ position: [40, 30, 40], fov: 55 }}
          onPointerMissed={() => {
            if (mode === 'select') setSelectedId(null)
          }}
        >
          <color attach="background" args={['#0a0a15']} />
          
          <ambientLight intensity={0.5} />
          <directionalLight position={[30, 50, 20]} intensity={1} castShadow />
          <pointLight position={[0, 20, 0]} intensity={0.5} color="#4ecdc4" />
          
          <Grid 
            args={[100, 100]} 
            cellSize={2} 
            cellThickness={0.5}
            sectionSize={10}
            sectionThickness={1}
            fadeDistance={80}
            infiniteGrid
            cellColor="#333"
            sectionColor="#555"
          />
          
          {/* 地面 - 用于点击测量 */}
          <mesh 
            rotation={[-Math.PI / 2, 0, 0]} 
            position={[0, 0, 0]}
            onClick={handleGroundClick}
          >
            <planeGeometry args={[200, 200]} />
            <meshBasicMaterial visible={false} />
          </mesh>
          
          {/* 场景对象 */}
          {objects.map(obj => (
            <SelectableObjectMesh
              key={obj.id}
              obj={obj}
              selected={obj.id === selectedId}
              onClick={handleObjectClick}
            />
          ))}
          
          {/* 标注 */}
          {sceneAnnotations.map(ann => (
            <AnnotationMarker
              key={ann.id}
              annotation={ann}
              onDelete={handleDeleteAnnotation}
            />
          ))}
          
          {/* 测量结果 */}
          {measurements.map(meas => (
            <MeasurementLine 
              key={meas.id} 
              measurement={meas}
              active={true}
            />
          ))}
          
          {/* 临时测量线 */}
          {measureStart && tempMeasurePoint && (
            <TempMeasurementLine 
              start={measureStart}
              end={tempMeasurePoint}
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
        
        {/* 工具栏 */}
        <Toolbar 
          mode={mode}
          onModeChange={setMode}
          onAddAnnotation={handleAddAnnotation}
        />
        
        {/* 选中信息面板 */}
        <SelectionPanel 
          selected={selected}
          onClear={() => { setSelectedId(null); onSelect?.(null) }}
        />
        
        {/* 测量面板 */}
        <MeasurementPanel 
          mode={mode}
          measurements={measurements}
          onClear={handleClearMeasurements}
        />
        
        {/* 测量提示 */}
        {mode === 'measure' && !measureStart && (
          <div style={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            background: 'rgba(0,0,0,0.8)',
            padding: '16px 24px',
            borderRadius: 8,
            color: '#ffd700',
            fontSize: 14,
            pointerEvents: 'none'
          }}>
            点击地面设置起点，再次点击设置终点
          </div>
        )}
        
        {measureStart && (
          <div style={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
            background: 'rgba(0,0,0,0.8)',
            padding: '16px 24px',
            borderRadius: 8,
            color: '#00ff00',
            fontSize: 14,
            pointerEvents: 'none'
          }}>
            起点已设置，点击终点完成测量
          </div>
        )}
      </div>
    </div>
  )
}
