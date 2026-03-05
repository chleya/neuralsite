// 3D Model Preview Component
// 基于 React Three Fiber

import { useState, useRef } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { OrbitControls, Grid, Html, PerspectiveCamera } from '@react-three/drei'
import * as THREE from 'three'

// 旋转的立方体组件
function RotatingBox({ position, color }: { position: [number, number, number]; color: string }) {
  const meshRef = useRef<THREE.Mesh>(null)
  
  useFrame((state, delta) => {
    if (meshRef.current) {
      meshRef.current.rotation.x += delta * 0.5
      meshRef.current.rotation.y += delta * 0.3
    }
  })
  
  return (
    <mesh ref={meshRef} position={position}>
      <boxGeometry args={[1, 1, 1]} />
      <meshStandardMaterial color={color} />
    </mesh>
  )
}

// 地面网格
function Ground() {
  return (
    <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.5, 0]} receiveShadow>
      <planeGeometry args={[50, 50]} />
      <meshStandardMaterial color="#1a1a2e" />
    </mesh>
  )
}

// 示例3D场景
function DemoScene() {
  return (
    <>
      <ambientLight intensity={0.5} />
      <directionalLight position={[10, 10, 5]} intensity={1} castShadow />
      
      <RotatingBox position={[0, 0.5, 0]} color="#667eea" />
      <RotatingBox position={[-3, 0.5, 2]} color="#764ba2" />
      <RotatingBox position={[3, 0.5, -2]} color="#28a745" />
      <RotatingBox position={[2, 0.5, 3]} color="#ffc107" />
      <RotatingBox position={[-2, 0.5, -3]} color="#dc3545" />
      
      <Ground />
      
      <Grid 
        args={[50, 50]} 
        cellSize={1} 
        cellThickness={0.5}
        cellColor="#333"
        sectionSize={5}
        sectionThickness={1}
        sectionColor="#444"
        fadeDistance={30}
        infiniteGrid
      />
    </>
  )
}

// 主组件
export default function ModelPreview() {
  const [showHelp, setShowHelp] = useState(true)
  
  return (
    <div style={{ width: '100%', height: 'calc(100vh - 150px)', position: 'relative' }}>
      {/* 工具栏 */}
      <div style={{
        position: 'absolute',
        top: 10,
        left: 10,
        zIndex: 10,
        display: 'flex',
        gap: '8px',
        background: 'rgba(0,0,0,0.7)',
        padding: '10px',
        borderRadius: '8px'
      }}>
        <button style={toolbarBtn} onClick={() => setShowHelp(!showHelp)}>
          {showHelp ? '隐藏帮助' : '显示帮助'}
        </button>
        <button style={toolbarBtn}>重置视角</button>
        <button style={toolbarBtn}>切换视角</button>
      </div>

      {/* 帮助信息 */}
      {showHelp && (
        <div style={{
          position: 'absolute',
          bottom: 10,
          left: 10,
          zIndex: 10,
          background: 'rgba(0,0,0,0.8)',
          padding: '15px',
          borderRadius: '8px',
          maxWidth: '300px',
          fontSize: '13px',
          color: '#aaa'
        }}>
          <h4 style={{ margin: '0 0 10px 0', color: '#fff' }}>操作说明</h4>
          <ul style={{ margin: 0, paddingLeft: '20px' }}>
            <li>鼠标左键拖拽 - 旋转视角</li>
            <li>鼠标右键拖拽 - 平移视角</li>
            <li>滚轮 - 缩放</li>
            <li>点击物体 - 选中物体</li>
          </ul>
        </div>
      )}

      {/* 3D Canvas */}
      <Canvas shadows>
        <PerspectiveCamera makeDefault position={[8, 8, 8]} fov={50} />
        <OrbitControls 
          enableDamping 
          dampingFactor={0.05}
          minDistance={2}
          maxDistance={50}
        />
        <DemoScene />
      </Canvas>
    </div>
  )
}

const toolbarBtn = {
  padding: '8px 12px',
  background: '#333',
  color: 'white',
  border: 'none',
  borderRadius: '4px',
  cursor: 'pointer',
  fontSize: '13px'
}
