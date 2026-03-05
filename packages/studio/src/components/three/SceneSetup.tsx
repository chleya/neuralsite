import { useRef, useMemo } from 'react'
import { useThree, useFrame } from '@react-three/fiber'
import {
  Environment,
  ContactShadows,
  PerspectiveCamera,
  OrbitControls,
  Grid,
  AccumulativeShadows,
  RandomizedLight,
} from '@react-three/drei'
import * as THREE from 'three'

// ============================================================================
// Types
// ============================================================================

export interface SceneSetupProps {
  /** Enable environment lighting */
  environment?: boolean | string
  /** Environment preset (sunset, dawn, night, warehouse, forest, apartment, studio, city, park, lobby) */
  environmentPreset?: 'sunset' | 'dawn' | 'night' | 'warehouse' | 'forest' | 'apartment' | 'studio' | 'city' | 'park' | 'lobby'
  /** Enable contact shadows */
  shadows?: boolean
  /** Enable grid */
  grid?: boolean
  /** Grid size */
  gridSize?: number
  /** Grid divisions */
  gridDivisions?: number
  /** Grid color */
  gridColor?: string
  /** Background color */
  backgroundColor?: string
  /** Camera position */
  cameraPosition?: [number, number, number]
  /** Camera fov */
  cameraFov?: number
  /** Enable orbit controls */
  controls?: boolean
  /** Orbit controls configuration */
  controlsConfig?: {
    enableDamping?: boolean
    dampingFactor?: number
    enableZoom?: boolean
    enablePan?: boolean
    enableRotate?: boolean
    minDistance?: number
    maxDistance?: number
    minPolarAngle?: number
    maxPolarAngle?: number
  }
  /** Ambient light intensity */
  ambientIntensity?: number
  /** Directional light intensity */
  directionalIntensity?: number
  /** Enable auto rotate */
  autoRotate?: boolean
  /** Auto rotate speed */
  autoRotateSpeed?: number
}

// ============================================================================
// Scene Background
// ============================================================================

function SceneBackground({ color }: { color?: string }) {
  const { scene } = useThree()
  
  useMemo(() => {
    if (color) {
      scene.background = new THREE.Color(color)
    } else {
      scene.background = null
    }
  }, [scene, color])
  
  return null
}

// ============================================================================
// Lighting Setup
// ============================================================================

function LightingSetup({
  ambientIntensity = 0.5,
  directionalIntensity = 1,
}: {
  ambientIntensity?: number
  directionalIntensity?: number
}) {
  const directionalRef = useRef<THREE.DirectionalLight>(null)
  
  return (
    <>
      <ambientLight intensity={ambientIntensity} />
      <directionalLight
        ref={directionalRef}
        position={[10, 10, 5]}
        intensity={directionalIntensity}
        castShadow
        shadow-mapSize={[2048, 2048]}
        shadow-camera-far={50}
        shadow-camera-left={-10}
        shadow-camera-right={10}
        shadow-camera-top={10}
        shadow-camera-bottom={-10}
      />
    </>
  )
}

// ============================================================================
// Enhanced OrbitControls
// ============================================================================

interface EnhancedOrbitControlsProps {
  enableDamping?: boolean
  dampingFactor?: number
  enableZoom?: boolean
  enablePan?: boolean
  enableRotate?: boolean
  minDistance?: number
  maxDistance?: number
  minPolarAngle?: number
  maxPolarAngle?: number
  autoRotate?: boolean
  autoRotateSpeed?: number
  target?: [number, number, number]
}

export function EnhancedOrbitControls({
  enableDamping = true,
  dampingFactor = 0.05,
  enableZoom = true,
  enablePan = true,
  enableRotate = true,
  minDistance = 0.1,
  maxDistance = 1000,
  minPolarAngle = 0,
  maxPolarAngle = Math.PI,
  autoRotate = false,
  autoRotateSpeed = 2,
  target = [0, 0, 0],
}: EnhancedOrbitControlsProps) {
  const controlsRef = useRef<any>(null)
  
  return (
    <OrbitControls
      ref={controlsRef}
      enableDamping={enableDamping}
      dampingFactor={dampingFactor}
      enableZoom={enableZoom}
      enablePan={enablePan}
      enableRotate={enableRotate}
      minDistance={minDistance}
      maxDistance={maxDistance}
      minPolarAngle={minPolarAngle}
      maxPolarAngle={maxPolarAngle}
      autoRotate={autoRotate}
      autoRotateSpeed={autoRotateSpeed}
      target={target}
    />
  )
}

// ============================================================================
// Main SceneSetup Component
// ============================================================================

export default function SceneSetup({
  environment = true,
  environmentPreset = 'city',
  shadows = true,
  grid = true,
  gridSize = 10,
  gridDivisions = 10,
  gridColor = '#444444',
  backgroundColor,
  cameraPosition = [5, 5, 5],
  cameraFov = 50,
  controls = true,
  controlsConfig = {},
  ambientIntensity = 0.5,
  directionalIntensity = 1,
  autoRotate = false,
  autoRotateSpeed = 2,
}: SceneSetupProps) {
  const {
    enableDamping = true,
    dampingFactor = 0.05,
    enableZoom = true,
    enablePan = true,
    enableRotate = true,
    minDistance = 0.1,
    maxDistance = 1000,
    minPolarAngle = 0,
    maxPolarAngle = Math.PI,
  } = controlsConfig

  return (
    <>
      {/* Background */}
      {backgroundColor && <SceneBackground color={backgroundColor} />}
      
      {/* Camera */}
      <PerspectiveCamera
        makeDefault
        position={cameraPosition}
        fov={cameraFov}
        near={0.1}
        far={1000}
      />
      
      {/* Lighting */}
      <LightingSetup
        ambientIntensity={ambientIntensity}
        directionalIntensity={directionalIntensity}
      />
      
      {/* Environment */}
      {environment && (
        <Environment
          preset={environmentPreset}
          background={false}
        />
      )}
      
      {/* Shadows */}
      {shadows && (
        <ContactShadows
          position={[0, -0.01, 0]}
          opacity={0.5}
          scale={10}
          blur={2}
          far={4}
        />
      )}
      
      {/* Grid */}
      {grid && (
        <Grid
          args={[gridSize, gridDivisions]}
          cellSize={gridSize / gridDivisions}
          cellThickness={0.5}
          cellColor={gridColor}
          sectionSize={gridSize / 5}
          sectionThickness={1}
          sectionColor="#666666"
          fadeDistance={30}
          fadeStrength={1}
          followCamera={false}
          infiniteGrid={true}
        />
      )}
      
      {/* Controls */}
      {controls && (
        <EnhancedOrbitControls
          enableDamping={enableDamping}
          dampingFactor={dampingFactor}
          enableZoom={enableZoom}
          enablePan={enablePan}
          enableRotate={enableRotate}
          minDistance={minDistance}
          maxDistance={maxDistance}
          minPolarAngle={minPolarAngle}
          maxPolarAngle={maxPolarAngle}
          autoRotate={autoRotate}
          autoRotateSpeed={autoRotateSpeed}
        />
      )}
    </>
  )
}

// Export sub-components for granular control
export { EnhancedOrbitControls }
export type { EnhancedOrbitControlsProps }
