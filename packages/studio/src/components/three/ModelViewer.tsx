import { useState, useCallback, useRef, Suspense } from 'react'
import { Canvas, ThreeEvent } from '@react-three/fiber'
import * as THREE from 'three'

import SceneSetup, { EnhancedOrbitControls, EnhancedOrbitControlsProps } from './SceneSetup'
import ModelLoader from './ModelLoader'

// ============================================================================
// Types
// ============================================================================

export interface MeasurementPoint {
  id: string
  position: THREE.Vector3
}

export interface Measurement {
  id: string
  points: [MeasurementPoint, MeasurementPoint]
  distance: number
}

export interface ModelViewerProps {
  /** Project ID for data isolation */
  projectId?: string
  /** Route ID for data isolation */
  routeId?: string
  /** Model URL */
  modelUrl?: string
  /** Model format */
  modelFormat?: 'gltf' | 'glb' | 'obj' | 'stl'
  /** Enable measurement tool */
  enableMeasurement?: boolean
  /** Measurement mode */
  measurementMode?: 'distance' | 'angle'
  /** Scene configuration */
  sceneConfig?: {
    environment?: boolean | string
    environmentPreset?: 'sunset' | 'dawn' | 'night' | 'warehouse' | 'forest' | 'apartment' | 'studio' | 'city' | 'park' | 'lobby'
    shadows?: boolean
    grid?: boolean
    gridSize?: number
    gridDivisions?: number
    gridColor?: string
    backgroundColor?: string
    ambientIntensity?: number
    directionalIntensity?: number
    autoRotate?: boolean
    autoRotateSpeed?: number
  }
  /** Camera configuration */
  cameraConfig?: {
    position?: [number, number, number]
    fov?: number
  }
  /** OrbitControls configuration */
  controlsConfig?: EnhancedOrbitControlsProps
  /** On measurement complete */
  onMeasurementComplete?: (measurement: Measurement) => void
  /** On model load */
  onModelLoad?: (model: THREE.Object3D) => void
  /** On error */
  onError?: (error: Error) => void
  /** Loading fallback */
  loadingFallback?: React.ReactNode
  /** Class name */
  className?: string
  /** Style */
  style?: React.CSSProperties
}

// ============================================================================
// Measurement Tool Component
// ============================================================================

interface MeasurementToolProps {
  mode: 'distance' | 'angle'
  onComplete: (measurement: Measurement) => void
}

function MeasurementTool({ mode, onComplete }: MeasurementToolProps) {
  const [points, setPoints] = useState<MeasurementPoint[]>([])
  const [isDrawing, setIsDrawing] = useState(false)
  const lineRef = useRef<THREE.Line>(null)
  const markersRef = useRef<THREE.Group>(null)
  
  // Handle click on the model/surface
  const handleClick = useCallback((event: ThreeEvent<MouseEvent>) => {
    event.stopPropagation()
    
    const point: MeasurementPoint = {
      id: `point-${Date.now()}`,
      position: event.point.clone(),
    }
    
    if (mode === 'distance') {
      if (points.length === 0) {
        setPoints([point])
        setIsDrawing(true)
      } else if (points.length === 1) {
        const distance = points[0].position.distanceTo(point.position)
        const measurement: Measurement = {
          id: `measurement-${Date.now()}`,
          points: [points[0], point],
          distance,
        }
        onComplete(measurement)
        setPoints([])
        setIsDrawing(false)
      }
    }
  }, [points, mode, onComplete])
  
  return (
    <>
      {/* Click handler mesh (invisible) */}
      <mesh visible={false} onClick={handleClick}>
        <planeGeometry args={[1000, 1000]} />
        <meshBasicMaterial transparent opacity={0} />
      </mesh>
      
      {/* Point markers */}
      {points.map((point) => (
        <mesh key={point.id} position={point.position}>
          <sphereGeometry args={[0.05, 16, 16]} />
          <meshBasicMaterial color="#ff4444" />
        </mesh>
      ))}
      
      {/* Line between points when drawing */}
      {isDrawing && points.length > 0 && (
        <line>
          <bufferGeometry>
            <bufferAttribute
              attach="attributes-position"
              count={2}
              array={new Float32Array([
                points[0].position.x, points[0].position.y, points[0].position.z,
                0, 0, 0, // Will be updated
              ])}
              itemSize={3}
            />
          </bufferGeometry>
          <lineBasicMaterial color="#ff4444" linewidth={2} />
        </line>
      )}
    </>
  )
}

// ============================================================================
// Distance Measurement Display
// ============================================================================

interface MeasurementLineProps {
  measurement: Measurement
}

function MeasurementLine({ measurement }: MeasurementLineProps) {
  const { points, distance } = measurement
  
  const midPoint = new THREE.Vector3()
    .addVectors(points[0].position, points[1].position)
    .multiplyScalar(0.5)
  
  return (
    <>
      {/* Line */}
      <line>
        <bufferGeometry>
          <bufferAttribute
            attach="attributes-position"
            count={2}
            array={new Float32Array([
              points[0].position.x, points[0].position.y, points[0].position.z,
              points[1].position.x, points[1].position.y, points[1].position.z,
            ])}
            itemSize={3}
          />
        </bufferGeometry>
        <lineBasicMaterial color="#44ff44" linewidth={2} />
      </line>
      
      {/* Start point */}
      <mesh position={points[0].position}>
        <sphereGeometry args={[0.03, 16, 16]} />
        <meshBasicMaterial color="#44ff44" />
      </mesh>
      
      {/* End point */}
      <mesh position={points[1].position}>
        <sphereGeometry args={[0.03, 16, 16]} />
        <meshBasicMaterial color="#44ff44" />
      </mesh>
      
      {/* Distance label */}
      <sprite position={midPoint} scale={[0.5, 0.25, 1]}>
        <spriteMaterial
          color="#ffffff"
          transparent
          opacity={0.8}
        />
      </sprite>
    </>
  )
}

// ============================================================================
// Model Content (Inner Component)
// ============================================================================

interface ModelContentProps {
  modelUrl?: string
  modelFormat?: 'gltf' | 'glb' | 'obj' | 'stl'
  enableMeasurement: boolean
  measurementMode: 'distance' | 'angle'
  onMeasurementComplete: (measurement: Measurement) => void
  onModelLoad?: (model: THREE.Object3D) => void
  onError?: (error: Error) => void
  loadingFallback?: React.ReactNode
}

function ModelContent({
  modelUrl,
  modelFormat,
  enableMeasurement,
  measurementMode,
  onMeasurementComplete,
  onModelLoad,
  onError,
  loadingFallback,
}: ModelContentProps) {
  const [measurements, setMeasurements] = useState<Measurement[]>([])
  
  const handleMeasurementComplete = useCallback((measurement: Measurement) => {
    setMeasurements((prev) => [...prev, measurement])
    onMeasurementComplete(measurement)
  }, [onMeasurementComplete])
  
  return (
    <>
      {/* Model Loader */}
      {modelUrl && (
        <ModelLoader
          url={modelUrl}
          format={modelFormat}
          onLoad={onModelLoad}
          onError={onError}
          fallback={loadingFallback}
        />
      )}
      
      {/* Measurement tool */}
      {enableMeasurement && (
        <MeasurementTool
          mode={measurementMode}
          onComplete={handleMeasurementComplete}
        />
      )}
      
      {/* Render existing measurements */}
      {measurements.map((measurement) => (
        <MeasurementLine key={measurement.id} measurement={measurement} />
      ))}
    </>
  )
}

// ============================================================================
// Main ModelViewer Component
// ============================================================================

export default function ModelViewer({
  projectId,
  routeId,
  modelUrl,
  modelFormat,
  enableMeasurement = false,
  measurementMode = 'distance',
  sceneConfig = {},
  cameraConfig = {},
  controlsConfig = {},
  onMeasurementComplete,
  onModelLoad,
  onError,
  loadingFallback,
  className,
  style,
}: ModelViewerProps) {
  // Log project/route context for debugging
  const context = useRef({ projectId, routeId })
  
  // Determine model URL based on project/route
  const effectiveModelUrl = modelUrl || (projectId ? `/api/projects/${projectId}/model` : undefined)
  
  const handleMeasurementComplete = useCallback((measurement: Measurement) => {
    console.log(`[ModelViewer][${projectId || 'default'}] Measurement:`, measurement)
    onMeasurementComplete?.(measurement)
  }, [projectId, onMeasurementComplete])
  
  return (
    <div
      className={className}
      style={{
        width: '100%',
        height: '100%',
        position: 'relative',
        ...style,
      }}
      data-project-id={projectId}
      data-route-id={routeId}
    >
      <Canvas
        shadows
        gl={{
          antialias: true,
          toneMapping: THREE.ACESFilmicToneMapping,
          toneMappingExposure: 1,
        }}
        camera={{
          position: cameraConfig.position || [5, 5, 5],
          fov: cameraConfig.fov || 50,
          near: 0.1,
          far: 1000,
        }}
      >
        <Suspense fallback={loadingFallback}>
          {/* Scene Setup */}
          <SceneSetup
            environment={sceneConfig.environment}
            environmentPreset={sceneConfig.environmentPreset}
            shadows={sceneConfig.shadows}
            grid={sceneConfig.grid}
            gridSize={sceneConfig.gridSize}
            gridDivisions={sceneConfig.gridDivisions}
            gridColor={sceneConfig.gridColor}
            backgroundColor={sceneConfig.backgroundColor}
            ambientIntensity={sceneConfig.ambientIntensity}
            directionalIntensity={sceneConfig.directionalIntensity}
            autoRotate={sceneConfig.autoRotate}
            autoRotateSpeed={sceneConfig.autoRotateSpeed}
            controls={false} // We'll handle controls separately
          />
          
          {/* Model Content */}
          <ModelContent
            modelUrl={effectiveModelUrl}
            modelFormat={modelFormat}
            enableMeasurement={enableMeasurement}
            measurementMode={measurementMode}
            onMeasurementComplete={handleMeasurementComplete}
            onModelLoad={onModelLoad}
            onError={onError}
            loadingFallback={loadingFallback}
          />
          
          {/* Enhanced Controls */}
          <EnhancedOrbitControls
            enableDamping={controlsConfig.enableDamping ?? true}
            dampingFactor={controlsConfig.dampingFactor ?? 0.05}
            enableZoom={controlsConfig.enableZoom ?? true}
            enablePan={controlsConfig.enablePan ?? true}
            enableRotate={controlsConfig.enableRotate ?? true}
            minDistance={controlsConfig.minDistance ?? 0.1}
            maxDistance={controlsConfig.maxDistance ?? 1000}
            minPolarAngle={controlsConfig.minPolarAngle ?? 0}
            maxPolarAngle={controlsConfig.maxPolarAngle ?? Math.PI}
            autoRotate={controlsConfig.autoRotate ?? false}
            autoRotateSpeed={controlsConfig.autoRotateSpeed ?? 2}
            target={controlsConfig.target ?? [0, 0, 0]}
          />
        </Suspense>
      </Canvas>
    </div>
  )
}

// ============================================================================
// Export Types
// ============================================================================

export type { EnhancedOrbitControlsProps }
