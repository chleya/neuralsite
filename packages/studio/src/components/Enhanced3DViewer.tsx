// Enhanced 3D Viewer with measurement, annotation, and cross-section features
// Uses @react-three/fiber and @react-three/drei

import { useState, useRef, useMemo, useCallback, Suspense } from 'react'
import { Canvas, useThree, ThreeEvent } from '@react-three/fiber'
import { 
  OrbitControls, 
  Grid, 
  Line, 
  Text, 
  Html, 
  Measure,
  Box,
  Sphere,
  TransformControls,
  useHelper,
  Billboard
} from '@react-three/drei'
import * as THREE from 'three'

// ==================== Types ====================
export interface Coordinate {
  station: string
  x: number
  y: number
  z: number
  azimuth: number
}

export interface ProjectData {
  projectId: string
  projectName: string
  coordinates: Coordinate[]
  roadWidth: number
  laneCount: number
}

export interface Annotation {
  id: string
  position: THREE.Vector3
  content: string
  type: 'marker' | 'text' | 'warning'
  color: string
  station?: string
}

export interface Measurement {
  id: string
  startPoint: THREE.Vector3
  endPoint: THREE.Vector3
  distance: number
  type: 'distance' | 'height'
  label?: string
}

export interface CrossSection {
  station: string
  position: THREE.Vector3
  leftWidth: number
  rightWidth: number
  elevation: number
  cutFill: 'cut' | 'fill' | 'mixed'
}

// ==================== Props ====================
interface Enhanced3DViewerProps {
  projectId?: string
  projectData?: ProjectData
  coordinates?: Coordinate[]
  showRoadSurface?: boolean
  showSlope?: boolean
  showDrainage?: boolean
  showCenterLine?: boolean
  showStakeMarks?: boolean
  showCrossSections?: boolean
  roadWidth?: number
  laneCount?: number
  onStationClick?: (station: string) => void
  onMeasurementComplete?: (measurement: Measurement) => void
  onAnnotationAdd?: (annotation: Annotation) => void
}

// ==================== Utility Functions ====================
const transformCoord = (c: Coordinate, baseX: number, baseY: number): THREE.Vector3 => {
  return new THREE.Vector3(
    (c.x - baseX) / 100,
    c.z / 10,
    (c.y - baseY) / 100
  )
}

// Generate demo coordinates based on project
const generateProjectCoordinates = (projectId: string): Coordinate[] => {
  const coords: Coordinate[] = []
  const baseSeed = projectId.split('').reduce((a, c) => a + c.charCodeAt(0), 0)
  const count = 50 + (baseSeed % 100)
  
  for (let i = 0; i < count; i++) {
    const variance = Math.sin(baseSeed * 0.1 + i * 0.1) * 20
    coords.push({
      station: `K${Math.floor(i / 10) + 1}+${(i % 10) * 10}`,
      x: i * 10 + variance,
      y: i * 5 + variance * 0.5,
      z: i * 0.5 + Math.sin(i * 0.1) * 2 + Math.random() * 1,
      azimuth: 45 + Math.sin(i * 0.05) * 10 + (baseSeed % 20 - 10)
    })
  }
  return coords
}

// ==================== Measurement Tool Component ====================
function MeasurementTool({ 
  onMeasurementComplete 
}: { 
  onMeasurementComplete?: (m: Measurement) => void 
}) {
  const { camera, raycaster, scene } = useThree()
  const [startPoint, setStartPoint] = useState<THREE.Vector3 | null>(null)
  const [endPoint, setEndPoint] = useState<THREE.Vector3 | null>(null)
  const [isActive, setIsActive] = useState(false)
  const [mode, setMode] = useState<'distance' | 'height'>('distance')
  const planeRef = useRef<THREE.Mesh>(null)

  const handleClick = useCallback((e: ThreeEvent<MouseEvent>) => {
    if (!isActive) return
    
    const point = e.point.clone()
    
    if (!startPoint) {
      setStartPoint(point)
    } else {
      setEndPoint(point)
      
      // Calculate distance
      const distance = startPoint.distanceTo(point)
      
      const measurement: Measurement = {
        id: `measure-${Date.now()}`,
        startPoint: startPoint.clone(),
        endPoint: point.clone(),
        distance,
        type: mode,
        label: `${distance.toFixed(2)}m`
      }
      
      onMeasurementComplete?.(measurement)
      
      // Reset for next measurement
      setStartPoint(null)
      setEndPoint(null)
    }
  }, [isActive, startPoint, mode, onMeasurementComplete])

  const activeMeasurement = useMemo(() => {
    if (startPoint && endPoint) {
      return {
        start: startPoint,
        end: endPoint,
        distance: startPoint.distanceTo(endPoint)
      }
    }
    return null
  }, [startPoint, endPoint])

  return (
    <group>
      {/* Invisible plane for clicking */}
      <mesh 
        ref={planeRef}
        visible={false}
        onClick={handleClick}
        position={[0, 0, 0]}
      >
        <planeGeometry args={[1000, 1000]} />
        <meshBasicMaterial side={THREE.DoubleSide} />
      </mesh>

      {/* Start point marker */}
      {startPoint && (
        <mesh position={startPoint.toArray()}>
          <sphereGeometry args={[0.3, 16, 16]} />
          <meshStandardMaterial color="#ff6b6b" emissive="#ff0000" emissiveIntensity={0.5} />
        </mesh>
      )}

      {/* Active measurement line */}
      {activeMeasurement && (
        <>
          <Line 
            points={[activeMeasurement.start, activeMeasurement.end]} 
            color="#ffd700" 
            lineWidth={3} 
          />
          <Html position={[
            (activeMeasurement.start.x + activeMeasurement.end.x) / 2,
            (activeMeasurement.start.y + activeMeasurement.end.y) / 2 + 1,
            (activeMeasurement.start.z + activeMeasurement.end.z) / 2
          ]}>
            <div style={{ 
              background: 'rgba(0,0,0,0.8)', 
              color: '#ffd700', 
              padding: '4px 8px', 
              borderRadius: '4px',
              fontSize: '12px',
              fontWeight: 'bold',
              whiteSpace: 'nowrap'
            }}>
              {activeMeasurement.distance.toFixed(2)}m
            </div>
          </Html>
        </>
      )}
    </group>
  )
}

// ==================== Annotation Component ====================
function AnnotationMarker({ 
  annotation, 
  onDelete 
}: { 
  annotation: Annotation
  onDelete?: (id: string) => void
}) {
  const [showTooltip, setShowTooltip] = useState(false)
  
  return (
    <group position={annotation.position.toArray()}>
      <Billboard follow={true}>
        <mesh 
          onPointerOver={() => setShowTooltip(true)}
          onPointerOut={() => setShowTooltip(false)}
        >
          <sphereGeometry args={[0.5, 16, 16]} />
          <meshStandardMaterial 
            color={annotation.color} 
            emissive={annotation.color}
            emissiveIntensity={0.3}
          />
        </mesh>
        
        {showTooltip && (
          <Html position={[0, 1.5, 0]} center>
            <div style={{
              background: 'rgba(0,0,0,0.9)',
              color: 'white',
              padding: '8px 12px',
              borderRadius: '6px',
              fontSize: '12px',
              maxWidth: '200px',
              border: `2px solid ${annotation.color}`
            }}>
              <div style={{ fontWeight: 'bold', marginBottom: '4px' }}>{annotation.station}</div>
              <div>{annotation.content}</div>
              {onDelete && (
                <button 
                  onClick={() => onDelete(annotation.id)}
                  style={{
                    marginTop: '8px',
                    padding: '4px 8px',
                    background: '#ff4444',
                    border: 'none',
                    borderRadius: '4px',
                    color: 'white',
                    cursor: 'pointer',
                    fontSize: '10px'
                  }}
                >
                  删除
                </button>
              )}
            </div>
          </Html>
        )}
        
        {/* Type icon */}
        <Text 
          position={[0.8, 0, 0]} 
          fontSize={0.8} 
          color={annotation.color}
          anchorX="center"
          anchorY="middle"
        >
          {annotation.type === 'warning' ? '⚠️' : annotation.type === 'marker' ? '📍' : '💬'}
        </Text>
      </Billboard>
    </group>
  )
}

// ==================== Center Line Component ====================
function CenterLine({ 
  coordinates, 
  baseX, 
  baseY,
  onStationClick 
}: { 
  coordinates: Coordinate[]
  baseX: number
  baseY: number
  onStationClick?: (station: string) => void
}) {
  const points = useMemo(() => 
    coordinates.map(c => transformCoord(c, baseX, baseY)),
    [coordinates, baseX, baseY]
  )

  if (points.length < 2) return null

  return (
    <group>
      <Line points={points} color="#00ff88" lineWidth={4} />
      
      {/* Start point */}
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
      
      {/* End point */}
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
    </group>
  )
}

// ==================== Stake Marks Component ====================
function StakeMarks({ 
  coordinates, 
  baseX, 
  baseY,
  onStationClick 
}: { 
  coordinates: Coordinate[]
  baseX: number
  baseY: number
  onStationClick?: (station: string) => void
}) {
  const marks = useMemo(() => {
    return coordinates.filter((_, i) => i % 10 === 0).map((c, i) => {
      const idx = i * 10
      if (idx >= coordinates.length) return null
      const pos = transformCoord(c, baseX, baseY)
      return { pos, station: c.station, index: idx }
    }).filter(Boolean)
  }, [coordinates, baseX, baseY])

  return (
    <group>
      {marks.map((mark: any) => (
        <group key={mark.index} position={mark.pos.toArray()}>
          {/* Stake pole */}
          <mesh position={[0, 0.5, 0]}>
            <cylinderGeometry args={[0.15, 0.15, 1, 8]} />
            <meshStandardMaterial color="#ffd93d" emissive="#ffaa00" emissiveIntensity={0.3} />
          </mesh>
          
          {/* Stake base */}
          <mesh position={[0, 0, 0]}>
            <cylinderGeometry args={[0.3, 0.3, 0.1, 8]} />
            <meshStandardMaterial color="#cc8800" />
          </mesh>
          
          {/* Station label */}
          <Billboard follow={true}>
            <Text 
              position={[0, 2, 0]} 
              fontSize={1.5} 
              color="#ffd93d"
              anchorX="center"
              anchorY="bottom"
            >
              {mark.station}
            </Text>
          </Billboard>
        </group>
      ))}
    </group>
  )
}

// ==================== Cross Section Viewer ====================
function CrossSectionViewer({ 
  coordinates,
  baseX, 
  baseY,
  roadWidth = 20,
  selectedStation,
  onStationSelect
}: { 
  coordinates: Coordinate[]
  baseX: number
  baseY: number
  roadWidth?: number
  selectedStation?: string | null
  onStationSelect?: (station: string) => void
}) {
  const crossSections = useMemo(() => {
    return coordinates.filter((_, i) => i % 20 === 0).map(c => {
      const pos = transformCoord(c, baseX, baseY)
      const isCut = c.z > 50
      return {
        station: c.station,
        position: pos,
        leftWidth: roadWidth / 200 + Math.random() * 2,
        rightWidth: roadWidth / 200 + Math.random() * 2,
        elevation: c.z,
        cutFill: isCut ? 'cut' : 'fill'
      }
    })
  }, [coordinates, baseX, baseY, roadWidth])

  return (
    <group>
      {crossSections.map((cs, i) => (
        <group key={i} position={cs.position.toArray()}>
          {/* Cross section plane */}
          <mesh rotation={[Math.PI / 2, 0, 0]}>
            <planeGeometry args={[cs.leftWidth + cs.rightWidth, 3]} />
            <meshStandardMaterial 
              color={cs.cutFill === 'cut' ? '#ff6b6b' : '#4ecdc4'} 
              side={THREE.DoubleSide}
              opacity={0.6}
              transparent
            />
          </mesh>
          
          {/* Station label */}
          <Billboard follow={true}>
            <Text 
              position={[0, 2.5, 0]} 
              fontSize={1} 
              color={cs.cutFill === 'cut' ? '#ff6b6b' : '#4ecdc4'}
              anchorX="center"
            >
              {cs.station}
            </Text>
          </Billboard>
        </group>
      ))}
    </group>
  )
}

// ==================== Road Surface Component ====================
function RoadSurface({ 
  coordinates, 
  baseX, 
  baseY,
  width = 10,
  laneCount = 4 
}: { 
  coordinates: Coordinate[]
  baseX: number
  baseY: number
  width?: number
  laneCount?: number
}) {
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
      <mesh geometry={geometry}>
        <meshStandardMaterial 
          color="#2d3436" 
          side={THREE.DoubleSide}
          roughness={0.8}
        />
      </mesh>
      
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

// ==================== Scene Component ====================
function Scene({ 
  coordinates,
  options,
  measurements,
  annotations,
  onStationClick,
  onMeasurementComplete,
  onAnnotationClick
}: { 
  coordinates: Coordinate[]
  options: {
    showRoadSurface: boolean
    showSlope: boolean
    showDrainage: boolean
    showCenterLine: boolean
    showStakeMarks: boolean
    showCrossSections: boolean
    roadWidth: number
    laneCount: number
    measurementMode: 'none' | 'distance' | 'height'
  }
  measurements?: Measurement[]
  annotations?: Annotation[]
  onStationClick?: (station: string) => void
  onMeasurementComplete?: (m: Measurement) => void
  onAnnotationClick?: (pos: THREE.Vector3) => void
}) {
  const baseX = coordinates[0]?.x || 0
  const baseY = coordinates[0]?.y || 0

  const handleCanvasClick = useCallback((e: ThreeEvent<MouseEvent>) => {
    if (options.measurementMode === 'none') return
    
    // Let MeasurementTool handle this
  }, [options.measurementMode])

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
        <CenterLine 
          coordinates={coordinates} 
          baseX={baseX} 
          baseY={baseY}
          onStationClick={onStationClick}
        />
      )}
      
      {coordinates.length > 0 && options.showStakeMarks && (
        <StakeMarks 
          coordinates={coordinates} 
          baseX={baseX} 
          baseY={baseY}
          onStationClick={onStationClick}
        />
      )}
      
      {coordinates.length > 0 && options.showRoadSurface && (
        <RoadSurface 
          coordinates={coordinates} 
          baseX={baseX} 
          baseY={baseY}
          width={options.roadWidth}
          laneCount={options.laneCount}
        />
      )}
      
      {coordinates.length > 0 && options.showCrossSections && (
        <CrossSectionViewer 
          coordinates={coordinates} 
          baseX={baseX} 
          baseY={baseY}
          roadWidth={options.roadWidth}
        />
      )}
      
      {/* Render saved measurements */}
      {measurements?.map(m => (
        <group key={m.id}>
          <Line 
            points={[m.startPoint, m.endPoint]} 
            color="#ffd700" 
            lineWidth={2}
          />
          <mesh position={m.startPoint.toArray()}>
            <sphereGeometry args={[0.2, 8, 8]} />
            <meshStandardMaterial color="#ffd700" />
          </mesh>
          <mesh position={m.endPoint.toArray()}>
            <sphereGeometry args={[0.2, 8, 8]} />
            <meshStandardMaterial color="#ffd700" />
          </mesh>
        </group>
      ))}
      
      {/* Render annotations */}
      {annotations?.map(a => (
        <AnnotationMarker key={a.id} annotation={a} />
      ))}
      
      {/* Measurement tool overlay */}
      {options.measurementMode !== 'none' && (
        <MeasurementTool onMeasurementComplete={onMeasurementComplete} />
      )}
      
      <OrbitControls 
        enableDamping 
        dampingFactor={0.05}
        minDistance={10}
        maxDistance={300}
      />
    </>
  )
}

// ==================== Main Component ====================
export default function Enhanced3DViewer({
  projectId = 'default',
  projectData,
  coordinates: propCoordinates,
  showRoadSurface = true,
  showSlope = false,
  showDrainage = false,
  showCenterLine = true,
  showStakeMarks = true,
  showCrossSections = false,
  roadWidth = 20,
  laneCount = 4,
  onStationClick,
  onMeasurementComplete,
  onAnnotationAdd
}: Enhanced3DViewerProps) {
  // Load project-specific coordinates
  const coordinates = useMemo(() => {
    if (propCoordinates && propCoordinates.length > 0) {
      return propCoordinates
    }
    if (projectData?.coordinates && projectData.length > 0) {
      return projectData.coordinates
    }
    // Generate demo data based on projectId
    return generateProjectCoordinates(projectId)
  }, [projectId, projectData, propCoordinates])

  // State
  const [options, setOptions] = useState({
    showRoadSurface,
    showSlope,
    showDrainage,
    showCenterLine,
    showStakeMarks,
    showCrossSections,
    roadWidth,
    laneCount,
    measurementMode: 'none' as 'none' | 'distance' | 'height'
  })

  const [measurements, setMeasurements] = useState<Measurement[]>([])
  const [annotations, setAnnotations] = useState<Annotation[]>([])
  const [selectedTool, setSelectedTool] = useState<'select' | 'measure' | 'annotate' | 'section'>('select')

  const handleMeasurementComplete = useCallback((m: Measurement) => {
    setMeasurements(prev => [...prev, m])
    onMeasurementComplete?.(m)
  }, [onMeasurementComplete])

  const handleAddAnnotation = useCallback((content: string, type: Annotation['type'] = 'marker') => {
    // Add annotation at center of scene
    const annotation: Annotation = {
      id: `anno-${Date.now()}`,
      position: new THREE.Vector3(0, 5, 0),
      content,
      type,
      color: type === 'warning' ? '#ff6b6b' : '#4ecdc4',
      station: coordinates[Math.floor(coordinates.length / 2)]?.station
    }
    setAnnotations(prev => [...prev, annotation])
    onAnnotationAdd?.(annotation)
  }, [coordinates, onAnnotationAdd])

  const handleDeleteAnnotation = useCallback((id: string) => {
    setAnnotations(prev => prev.filter(a => a.id !== id))
  }, [])

  return (
    <div style={{ 
      width: '100%', 
      height: '100%', 
      display: 'flex', 
      flexDirection: 'column',
      background: '#0a0a15'
    }}>
      {/* Toolbar */}
      <div style={{
        padding: '12px 20px',
        background: '#1a1a2e',
        borderBottom: '1px solid #333',
        display: 'flex',
        gap: '12px',
        flexWrap: 'wrap',
        alignItems: 'center'
      }}>
        {/* Tool buttons */}
        <div style={{ display: 'flex', gap: '4px' }}>
          <button
            onClick={() => { setSelectedTool('select'); setOptions(o => ({ ...o, measurementMode: 'none' })) }}
            style={{
              padding: '8px 12px',
              background: selectedTool === 'select' ? '#667eea' : '#252540',
              border: '1px solid #444',
              borderRadius: '6px',
              color: 'white',
              cursor: 'pointer',
              fontSize: '12px'
            }}
          >
            🖱️ 选择
          </button>
          <button
            onClick={() => { setSelectedTool('measure'); setOptions(o => ({ ...o, measurementMode: 'distance' })) }}
            style={{
              padding: '8px 12px',
              background: selectedTool === 'measure' ? '#667eea' : '#252540',
              border: '1px solid #444',
              borderRadius: '6px',
              color: 'white',
              cursor: 'pointer',
              fontSize: '12px'
            }}
          >
            📏 测量
          </button>
          <button
            onClick={() => { setSelectedTool('annotate'); setOptions(o => ({ ...o, measurementMode: 'none' })) }}
            style={{
              padding: '8px 12px',
              background: selectedTool === 'annotate' ? '#667eea' : '#252540',
              border: '1px solid #444',
              borderRadius: '6px',
              color: 'white',
              cursor: 'pointer',
              fontSize: '12px'
            }}
          >
            📍 标注
          </button>
          <button
            onClick={() => { setSelectedTool('section'); setOptions(o => ({ ...o, showCrossSections: !o.showCrossSections })) }}
            style={{
              padding: '8px 12px',
              background: options.showCrossSections ? '#667eea' : '#252540',
              border: '1px solid #444',
              borderRadius: '6px',
              color: 'white',
              cursor: 'pointer',
              fontSize: '12px'
            }}
          >
            🔀 截面
          </button>
        </div>

        <div style={{ width: '1px', height: '24px', background: '#444' }} />

        {/* Display options */}
        <label style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#ccc', fontSize: 12 }}>
          <input 
            type="checkbox" 
            checked={options.showCenterLine}
            onChange={(e) => setOptions(o => ({ ...o, showCenterLine: e.target.checked }))}
          />
          中心线
        </label>
        
        <label style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#ccc', fontSize: 12 }}>
          <input 
            type="checkbox" 
            checked={options.showRoadSurface}
            onChange={(e) => setOptions(o => ({ ...o, showRoadSurface: e.target.checked }))}
          />
          路面
        </label>
        
        <label style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#ccc', fontSize: 12 }}>
          <input 
            type="checkbox" 
            checked={options.showStakeMarks}
            onChange={(e) => setOptions(o => ({ ...o, showStakeMarks: e.target.checked }))}
          />
          桩号
        </label>

        <div style={{ width: '1px', height: '24px', background: '#444' }} />

        {/* Width slider */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ color: '#ccc', fontSize: 12 }}>路宽:</span>
          <input 
            type="range" 
            min="10" 
            max="40" 
            value={options.roadWidth}
            onChange={(e) => setOptions(o => ({ ...o, roadWidth: Number(e.target.value) }))}
            style={{ width: 80 }}
          />
          <span style={{ color: '#00ff88', fontSize: 12, minWidth: 30 }}>{options.roadWidth}m</span>
        </div>

        {/* Clear measurements */}
        {measurements.length > 0 && (
          <button
            onClick={() => setMeasurements([])}
            style={{
              padding: '8px 12px',
              background: '#ff4444',
              border: 'none',
              borderRadius: '6px',
              color: 'white',
              cursor: 'pointer',
              fontSize: '12px'
            }}
          >
            清除测量
          </button>
        )}

        {/* Project badge */}
        <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ 
            background: '#667eea', 
            padding: '4px 10px', 
            borderRadius: '12px', 
            fontSize: 11,
            color: 'white'
          }}>
            项目: {projectId}
          </span>
        </div>
      </div>
      
      {/* 3D Canvas */}
      <div style={{ flex: 1, position: 'relative' }}>
        <Canvas camera={{ position: [50, 50, 50], fov: 60 }} shadows>
          <color attach="background" args={['#0a0a15']} />
          <Suspense fallback={null}>
            <Scene 
              coordinates={coordinates}
              options={options}
              measurements={measurements}
              annotations={annotations}
              onStationClick={onStationClick}
              onMeasurementComplete={handleMeasurementComplete}
            />
          </Suspense>
        </Canvas>

        {/* Tool instructions */}
        {options.measurementMode !== 'none' && (
          <div style={{
            position: 'absolute',
            top: 20,
            left: '50%',
            transform: 'translateX(-50%)',
            background: 'rgba(102, 126, 234, 0.9)',
            padding: '8px 16px',
            borderRadius: '8px',
            color: 'white',
            fontSize: 12
          }}>
            {options.measurementMode === 'distance' ? '📏 点击两点进行距离测量' : '📐 点击两点进行高度测量'}
          </div>
        )}

        {/* Legend */}
        <div style={{
          position: 'absolute',
          bottom: 20,
          left: 20,
          background: 'rgba(0,0,0,0.8)',
          padding: '12px 16px',
          borderRadius: 8,
          fontSize: 11,
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
            <span style={{ width: 20, height: 3, background: '#ffd93d', marginRight: 8 }}></span>
            桩号标记
          </div>
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <span style={{ width: 20, height: 3, background: '#ff6b6b', marginRight: 8 }}></span>
            截面视图
          </div>
        </div>
        
        {/* Stats */}
        <div style={{
          position: 'absolute',
          top: 20,
          right: 20,
          background: 'rgba(0,0,0,0.8)',
          padding: '10px 15px',
          borderRadius: 8,
          fontSize: 11,
          color: '#00ff88'
        }}>
          <div>桩号点: {coordinates.length}</div>
          <div>测量数: {measurements.length}</div>
          <div>标注数: {annotations.length}</div>
          <div>道路长度: {((coordinates[coordinates.length-1]?.x - coordinates[0]?.x) / 1000 || 0).toFixed(2)} km</div>
        </div>

        {/* Annotations panel */}
        {annotations.length > 0 && (
          <div style={{
            position: 'absolute',
            top: 80,
            left: 20,
            background: 'rgba(0,0,0,0.8)',
            padding: '10px 15px',
            borderRadius: 8,
            fontSize: 11,
            maxWidth: '200px'
          }}>
            <div style={{ color: '#4ecdc4', fontWeight: 'bold', marginBottom: '8px' }}>📍 标注列表</div>
            {annotations.map(a => (
              <div key={a.id} style={{ color: '#ccc', marginBottom: '4px', display: 'flex', justifyContent: 'space-between' }}>
                <span>{a.station}</span>
                <button 
                  onClick={() => handleDeleteAnnotation(a.id)}
                  style={{ background: 'transparent', border: 'none', color: '#ff4444', cursor: 'pointer' }}
                >
                  ×
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
