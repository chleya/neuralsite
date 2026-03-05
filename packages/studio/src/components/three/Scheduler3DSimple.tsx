// Scheduler 3D - 施工调度可视化
// 基于 React Three Fiber

import { useState, useRef } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { OrbitControls, Grid, Text, PerspectiveCamera } from '@react-three/drei'
import * as THREE from 'three'

// 任务类型
interface Task {
  id: string
  name: string
  startDay: number
  duration: number
  color: string
  position: [number, number, number]
}

// 示例任务数据
const tasks: Task[] = [
  { id: '1', name: '基础施工', startDay: 1, duration: 5, color: '#667eea', position: [0, 0.5, 0] },
  { id: '2', name: '主体结构', startDay: 6, duration: 8, color: '#764ba2', position: [0, 0.5, 2] },
  { id: '3', name: '机电安装', startDay: 10, duration: 6, color: '#28a745', position: [0, 0.5, 4] },
  { id: '4', name: '装饰装修', startDay: 14, duration: 7, color: '#ffc107', position: [0, 0.5, 6] },
  { id: '5', name: '竣工验收', startDay: 20, duration: 3, color: '#dc3545', position: [0, 0.5, 8] },
]

// 时间轴
const totalDays = 25

// 任务条组件
function TaskBar({ task, day, isActive }: { task: Task; day: number; isActive: boolean }) {
  const meshRef = useRef<THREE.Mesh>(null)
  
  useFrame(() => {
    if (meshRef.current) {
      // 激活状态浮动动画
      if (isActive) {
        meshRef.current.position.y = task.position[1] + Math.sin(Date.now() / 500) * 0.1
      }
    }
  })
  
  const isVisible = day >= task.startDay && day <= task.startDay + task.duration
  
  if (!isVisible) return null
  
  return (
    <group position={[task.position[0], task.position[1], task.position[2]]}>
      <mesh ref={meshRef}>
        <boxGeometry args={[0.8, 0.4, task.duration * 0.4]} />
        <meshStandardMaterial 
          color={task.color} 
          transparent 
          opacity={isActive ? 1 : 0.7}
        />
      </mesh>
      <Text
        position={[1, 0, 0]}
        fontSize={0.3}
        color="white"
        anchorX="left"
      >
        {task.name}
      </Text>
    </group>
  )
}

// 地面网格
function Ground() {
  return (
    <>
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.01, 4]}>
        <planeGeometry args={[10, 20]} />
        <meshStandardMaterial color="#1a1a2e" />
      </mesh>
      <Grid
        args={[10, 20]}
        cellSize={1}
        cellThickness={0.5}
        cellColor="#333"
        sectionSize={5}
        sectionThickness={1}
        sectionColor="#444"
        position={[0, 0, 4]}
      />
    </>
  )
}

// 主组件
export default function Scheduler3D() {
  const [currentDay, setCurrentDay] = useState(1)
  const [isPlaying, setIsPlaying] = useState(false)
  const [speed, setSpeed] = useState(1)
  
  // 模拟时间推进
  useState(() => {
    if (isPlaying) {
      const interval = setInterval(() => {
        setCurrentDay(d => d >= totalDays ? 1 : d + 0.1 * speed)
      }, 100)
      return () => clearInterval(interval)
    }
  })
  
  const currentTask = tasks.find(t => 
    currentDay >= t.startDay && currentDay <= t.startDay + t.duration
  )
  
  return (
    <div style={{ width: '100%', height: 'calc(100vh - 150px)', display: 'flex', flexDirection: 'column' }}>
      {/* 工具栏 */}
      <div style={{
        padding: '10px 16px',
        background: '#1a1a2e',
        borderBottom: '1px solid #333',
        display: 'flex',
        alignItems: 'center',
        gap: '16px'
      }}>
        <button 
          onClick={() => setIsPlaying(!isPlaying)}
          style={{
            padding: '8px 16px',
            background: isPlaying ? '#dc3545' : '#28a745',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer'
          }}
        >
          {isPlaying ? '⏸ 暂停' : '▶ 播放'}
        </button>
        
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ color: '#888' }}>速度:</span>
          <select 
            value={speed} 
            onChange={e => setSpeed(Number(e.target.value))}
            style={{ background: '#333', color: 'white', border: 'none', padding: '4px 8px', borderRadius: '4px' }}
          >
            <option value={0.5}>0.5x</option>
            <option value={1}>1x</option>
            <option value={2}>2x</option>
            <option value={5}>5x</option>
          </select>
        </div>
        
        <div style={{ flex: 1 }} />
        
        <div style={{ display: 'flex', gap: '8px' }}>
          <input 
            type="range" 
            min={1} 
            max={totalDays} 
            value={currentDay}
            onChange={e => setCurrentDay(Number(e.target.value))}
            style={{ width: '200px' }}
          />
          <span style={{ color: 'white', minWidth: '80px' }}>
            第 {Math.floor(currentDay)} 天
          </span>
        </div>
      </div>
      
      {/* 3D 视图 */}
      <div style={{ flex: 1, position: 'relative' }}>
        <Canvas>
          <PerspectiveCamera makeDefault position={[8, 8, 12]} fov={50} />
          <OrbitControls enableDamping dampingFactor={0.05} />
          
          <ambientLight intensity={0.6} />
          <directionalLight position={[10, 15, 10]} intensity={1} />
          
          {/* 任务条 */}
          {tasks.map(task => (
            <TaskBar 
              key={task.id} 
              task={task} 
              day={currentDay}
              isActive={currentTask?.id === task.id}
            />
          ))}
          
          <Ground />
          
          {/* 地面标记 */}
          {Array.from({ length: totalDays }).map((_, i) => (
            <mesh key={i} position={[-4.5, 0.01, 0.2 + i * 0.8]}>
              <boxGeometry args={[0.1, 0.02, 0.02]} />
              <meshStandardMaterial color={i + 1 === Math.floor(currentDay) ? '#ff0000' : '#666'} />
            </mesh>
          ))}
        </Canvas>
        
        {/* 底部时间轴 */}
        <div style={{
          position: 'absolute',
          bottom: 0,
          left: 0,
          right: 0,
          background: 'rgba(0,0,0,0.8)',
          padding: '10px 20px',
          display: 'flex',
          justifyContent: 'space-between',
          fontSize: '12px',
          color: '#888'
        }}>
          <span>第1天</span>
          <span>第{totalDays}天</span>
        </div>
      </div>
      
      {/* 当前任务信息 */}
      {currentTask && (
        <div style={{
          position: 'absolute',
          top: 60,
          right: 10,
          background: 'rgba(0,0,0,0.9)',
          padding: '16px',
          borderRadius: '8px',
          border: `2px solid ${currentTask.color}`
        }}>
          <h4 style={{ margin: '0 0 8px 0', color: currentTask.color }}>{currentTask.name}</h4>
          <div style={{ fontSize: '13px', color: '#aaa' }}>
            <p>第{currentTask.startDay}天 - 第{currentTask.startDay + currentTask.duration}天</p>
            <p>工期: {currentTask.duration}天</p>
          </div>
        </div>
      )}
    </div>
  )
}
