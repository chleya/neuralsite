import { Suspense, useState, useEffect, useCallback } from 'react'
import { useLoader } from '@react-three/fiber'
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader'
import { OBJLoader } from 'three/examples/jsm/loaders/OBJLoader'
import { STLLoader } from 'three/examples/jsm/loaders/STLLoader'
import { DRACOLoader } from 'three/examples/jsm/loaders/DRACOLoader'
import * as THREE from 'three'

// ============================================================================
// Types
// ============================================================================

export type ModelFormat = 'gltf' | 'glb' | 'obj' | 'stl'

export interface ModelLoaderProps {
  /** Model URL or path */
  url: string
  /** Model format (auto-detected from extension if not provided) */
  format?: ModelFormat
  /** Enable draco compression decoding */
  draco?: boolean
  /** Draco decoder path */
  dracoPath?: string
  /** Center the model */
  center?: boolean
  /** Scale the model to fit */
  scaleToFit?: number
  /** Rotation to apply */
  rotation?: [number, number, number]
  /** Material override */
  material?: THREE.Material | THREE.Material[]
  /** On load callback */
  onLoad?: (model: THREE.Object3D) => void
  /** On error callback */
  onError?: (error: Error) => void
  /** On progress callback */
  onProgress?: (progress: THREE.ProgressEvent) => void
  /** Enable shadows */
  castShadow?: boolean
  receiveShadow?: boolean
  /** Loading placeholder */
  fallback?: React.ReactNode
}

interface LoadedModelProps {
  model: THREE.Object3D
  castShadow?: boolean
  receiveShadow?: boolean
  material?: THREE.Material | THREE.Material[]
}

// ============================================================================
// Model Processor
// ============================================================================

function processModel(
  model: THREE.Object3D,
  center: boolean,
  scaleToFit?: number,
  rotation?: [number, number, number]
): THREE.Object3D {
  // Apply rotation
  if (rotation) {
    model.rotation.set(
      THREE.MathUtils.degToRad(rotation[0]),
      THREE.MathUtils.degToRad(rotation[1]),
      THREE.MathUtils.degToRad(rotation[2])
    )
  }
  
  // Center model
  if (center) {
    const box = new THREE.Box3().setFromObject(model)
    const centerOffset = box.getCenter(new THREE.Vector3())
    model.position.sub(centerOffset)
  }
  
  // Scale to fit
  if (scaleToFit) {
    const box = new THREE.Box3().setFromObject(model)
    const size = box.getSize(new THREE.Vector3())
    const maxDim = Math.max(size.x, size.y, size.z)
    const scale = scaleToFit / maxDim
    model.scale.setScalar(scale)
    
    // Re-center after scaling
    const newBox = new THREE.Box3().setFromObject(model)
    const newCenter = newBox.getCenter(new THREE.Vector3())
    model.position.sub(newCenter)
  }
  
  // Enable shadows recursively
  model.traverse((child) => {
    if (child instanceof THREE.Mesh) {
      child.castShadow = true
      child.receiveShadow = true
    }
  })
  
  return model
}

// ============================================================================
// GLTF/GLB Loader with Draco Support
// ============================================================================

function useGLTFWithDraco(
  url: string,
  draco: boolean,
  dracoPath: string,
  onProgress?: (progress: THREE.ProgressEvent) => void
): THREE.Object3D | null {
  const [gltf, setGltf] = useState<THREE.Object3D | null>(null)
  
  useEffect(() => {
    const loader = new GLTFLoader()
    
    // Setup Draco decoder
    if (draco) {
      const dracoLoader = new DRACOLoader()
      dracoLoader.setDecoderPath(dracoPath)
      loader.setDRACOLoader(dracoLoader)
    }
    
    loader.load(
      url,
      (gltf) => {
        setGltf(gltf.scene)
      },
      (progress) => {
        onProgress?.(progress)
      },
      (error) => {
        console.error('Error loading GLTF:', error)
      }
    )
    
    return () => {
      if (draco) {
        loader.dispose()
      }
    }
  }, [url, draco, dracoPath, onProgress])
  
  return gltf
}

// ============================================================================
// OBJ Loader
// ============================================================================

function useOBJLoader(
  url: string,
  onProgress?: (progress: THREE.ProgressEvent) => void
): THREE.Object3D | null {
  const [obj, setObj] = useState<THREE.Object3D | null>(null)
  
  useEffect(() => {
    const loader = new OBJLoader()
    
    loader.load(
      url,
      (object) => {
        setObj(object)
      },
      (progress) => {
        onProgress?.(progress)
      },
      (error) => {
        console.error('Error loading OBJ:', error)
      }
    )
  }, [url, onProgress])
  
  return obj
}

// ============================================================================
// STL Loader
// ============================================================================

function useSTLLoader(
  url: string,
  onProgress?: (progress: THREE.ProgressEvent) => void
): THREE.Object3D | null {
  const [stl, setStl] = useState<THREE.Object3D | null>(null)
  
  useEffect(() => {
    const loader = new STLLoader()
    
    loader.load(
      url,
      (geometry) => {
        const material = new THREE.MeshStandardMaterial({
          color: 0xaaaaaa,
          metalness: 0.3,
          roughness: 0.7,
        })
        const mesh = new THREE.Mesh(geometry, material)
        setStl(mesh)
      },
      (progress) => {
        onProgress?.(progress)
      },
      (error) => {
        console.error('Error loading STL:', error)
      }
    )
  }, [url, onProgress])
  
  return stl
}

// ============================================================================
// Format Detector
// ============================================================================

function detectFormat(url: string, providedFormat?: ModelFormat): ModelFormat {
  if (providedFormat) return providedFormat
  
  const extension = url.split('.').pop()?.toLowerCase()
  
  switch (extension) {
    case 'gltf':
      return 'gltf'
    case 'glb':
      return 'glb'
    case 'obj':
      return 'obj'
    case 'stl':
      return 'stl'
    default:
      return 'gltf'
  }
}

// ============================================================================
// Loaded Model Component
// ============================================================================

function LoadedModel({
  model,
  castShadow = true,
  receiveShadow = true,
  material,
}: LoadedModelProps) {
  useEffect(() => {
    if (material) {
      model.traverse((child) => {
        if (child instanceof THREE.Mesh) {
          if (Array.isArray(material)) {
            child.material = material
          } else {
            child.material = material
          }
        }
      })
    }
  }, [model, material])
  
  return (
    <primitive
      object={model}
      castShadow={castShadow}
      receiveShadow={receiveShadow}
    />
  )
}

// ============================================================================
// Loading Fallback
// ============================================================================

function LoadingFallback({ fallback }: { fallback?: React.ReactNode }) {
  if (fallback) return <>{fallback}</>
  
  return (
    <mesh>
      <boxGeometry args={[1, 1, 1]} />
      <meshStandardMaterial color="#cccccc" wireframe />
    </mesh>
  )
}

// ============================================================================
// Main ModelLoader Component
// ============================================================================

export default function ModelLoader({
  url,
  format,
  draco = true,
  dracoPath = '/draco',
  center = true,
  scaleToFit,
  rotation,
  material,
  onLoad,
  onError,
  onProgress,
  castShadow = true,
  receiveShadow = true,
  fallback,
}: ModelLoaderProps) {
  const [error, setError] = useState<Error | null>(null)
  const detectedFormat = detectFormat(url, format)
  
  // Load model based on format
  const model = (() => {
    switch (detectedFormat) {
      case 'gltf':
      case 'glb':
        return useGLTFWithDraco(url, draco, dracoPath, onProgress)
      case 'obj':
        return useOBJLoader(url, onProgress)
      case 'stl':
        return useSTLLoader(url, onProgress)
      default:
        return null
    }
  })()
  
  // Handle errors
  useEffect(() => {
    if (error) {
      onError?.(error)
    }
  }, [error, onError])
  
  // Handle successful load
  useEffect(() => {
    if (model) {
      const processed = processModel(model, center, scaleToFit, rotation)
      onLoad?.(processed)
    }
  }, [model, center, scaleToFit, rotation, onLoad])
  
  // Render
  if (!url) return null
  
  return (
    <Suspense fallback={<LoadingFallback fallback={fallback} />}>
      {model ? (
        <LoadedModel
          model={model}
          castShadow={castShadow}
          receiveShadow={receiveShadow}
          material={material}
        />
      ) : (
        <LoadingFallback fallback={fallback} />
      )}
    </Suspense>
  )
}

// ============================================================================
// Utility Functions
// ============================================================================

/**
 * Load a model outside of React context
 */
export async function loadModel(
  url: string,
  format?: ModelFormat,
  options?: {
    draco?: boolean
    dracoPath?: string
    center?: boolean
    scaleToFit?: number
    rotation?: [number, number, number]
  }
): Promise<THREE.Object3D> {
  const detectedFormat = detectFormat(url, format)
  const { draco = true, dracoPath = '/draco', center = true, scaleToFit, rotation } = options || {}
  
  return new Promise((resolve, reject) => {
    let loader: THREE.Loader
    
    switch (detectedFormat) {
      case 'gltf':
      case 'glb':
        loader = new GLTFLoader()
        if (draco) {
          const dracoLoader = new DRACOLoader()
          dracoLoader.setDecoderPath(dracoPath)
          ;(loader as GLTFLoader).setDRACOLoader(dracoLoader)
        }
        break
      case 'obj':
        loader = new OBJLoader()
        break
      case 'stl':
        loader = new STLLoader()
        break
      default:
        reject(new Error(`Unsupported format: ${detectedFormat}`))
        return
    }
    
    loader.load(
      url,
      (result) => {
        const model = detectedFormat === 'gltf' || detectedFormat === 'glb'
          ? (result as any).scene
          : result as THREE.Object3D
        
        const processed = processModel(model, center, scaleToFit, rotation)
        resolve(processed)
      },
      undefined,
      (error) => {
        reject(error)
      }
    )
  })
}

/**
 * Supported formats
 */
export const SUPPORTED_FORMATS: { ext: string; name: string; mime: string }[] = [
  { ext: 'gltf', name: 'GLTF', mime: 'model/gltf+json' },
  { ext: 'glb', name: 'GLB', mime: 'model/gltf-binary' },
  { ext: 'obj', name: 'OBJ', mime: 'model/obj' },
  { ext: 'stl', name: 'STL', mime: 'model/stl' },
]
