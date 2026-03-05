// Route3D Page - Project-isolated 3D route visualization
// Features: Measurement tools, annotations, cross-sections, stake marks

import { useState, useCallback } from 'react'
import Project3DViewer from '../components/Project3DViewer'

// Mock project list - in real app, fetch from API
const PROJECT_LIST = [
  { id: 'demo', name: '演示项目', status: 'active' },
  { id: 'project-001', name: '京沪高速改造', status: 'active' },
  { id: 'project-002', name: '城市快速路', status: 'draft' },
  { id: 'project-003', name: '山区公路', status: 'active' },
]

export default function Route3DPage() {
  const [currentProject, setCurrentProject] = useState('demo')
  const [selectedStation, setSelectedStation] = useState<string | null>(null)
  
  // Handle station click from 3D viewer
  const handleStationClick = useCallback((station: string) => {
    setSelectedStation(station)
    console.log('Selected station:', station)
  }, [])

  return (
    <div style={{ 
      display: 'flex', 
      height: '100vh',
      background: '#0a0a15'
    }}>
      {/* Sidebar */}
      <div style={{
        width: '260px',
        background: '#12121f',
        borderRight: '1px solid #2a2a3e',
        display: 'flex',
        flexDirection: 'column'
      }}>
        {/* Header */}
        <div style={{
          padding: '20px',
          borderBottom: '1px solid #2a2a3e'
        }}>
          <h2 style={{ 
            margin: 0, 
            fontSize: '18px', 
            color: '#00ff88',
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}>
            🛣️ 路线三维
          </h2>
          <p style={{ 
            margin: '8px 0 0 0', 
            fontSize: '12px', 
            color: '#666' 
          }}>
            项目隔离的三维路线可视化
          </p>
        </div>
        
        {/* Project list */}
        <div style={{ flex: 1, overflow: 'auto', padding: '12px' }}>
          <div style={{ 
            fontSize: '11px', 
            color: '#666', 
            marginBottom: '8px',
            textTransform: 'uppercase',
            letterSpacing: '1px'
          }}>
            项目列表
          </div>
          
          {PROJECT_LIST.map(project => (
            <button
              key={project.id}
              onClick={() => setCurrentProject(project.id)}
              style={{
                width: '100%',
                padding: '12px 16px',
                marginBottom: '8px',
                background: currentProject === project.id ? 'rgba(102, 126, 234, 0.2)' : '#1a1a2e',
                border: `1px solid ${currentProject === project.id ? '#667eea' : '#2a2a3e'}`,
                borderRadius: '8px',
                color: currentProject === project.id ? '#fff' : '#888',
                cursor: 'pointer',
                textAlign: 'left',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                transition: 'all 0.2s'
              }}
            >
              <span style={{ fontSize: '14px' }}>{project.name}</span>
              <span style={{
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                background: project.status === 'active' ? '#00ff88' : '#666'
              }} />
            </button>
          ))}
        </div>
        
        {/* Stats */}
        <div style={{
          padding: '16px',
          borderTop: '1px solid #2a2a3e',
          background: '#0f0f1a'
        }}>
          <div style={{ fontSize: '11px', color: '#666', marginBottom: '12px' }}>
            当前项目统计
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
            <div style={{ 
              background: '#1a1a2e', 
              padding: '12px', 
              borderRadius: '8px',
              textAlign: 'center'
            }}>
              <div style={{ fontSize: '20px', color: '#00ff88', fontWeight: 'bold' }}>60</div>
              <div style={{ fontSize: '10px', color: '#666' }}>桩号点</div>
            </div>
            <div style={{ 
              background: '#1a1a2e', 
              padding: '12px', 
              borderRadius: '8px',
              textAlign: 'center'
            }}>
              <div style={{ fontSize: '20px', color: '#667eea', fontWeight: 'bold' }}>1.2km</div>
              <div style={{ fontSize: '10px', color: '#666' }}>总长度</div>
            </div>
          </div>
        </div>
        
        {/* Help */}
        <div style={{
          padding: '16px',
          borderTop: '1px solid #2a2a3e',
          fontSize: '11px',
          color: '#555'
        }}>
          <div style={{ marginBottom: '8px', color: '#888' }}>操作指南</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            <div>🖱️ 左键拖拽: 旋转视图</div>
            <div>🖱️ 右键拖拽: 平移视图</div>
            <div>🖱️ 滚轮: 缩放</div>
            <div>📏 测量工具: 点击两点测量距离</div>
            <div>📍 标注: 添加关键点标注</div>
          </div>
        </div>
      </div>
      
      {/* Main 3D viewer */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        {/* Selected station bar */}
        {selectedStation && (
          <div style={{
            padding: '12px 20px',
            background: 'linear-gradient(90deg, rgba(102, 126, 234, 0.3), transparent)',
            borderBottom: '1px solid #2a2a3e',
            display: 'flex',
            alignItems: 'center',
            gap: '12px'
          }}>
            <span style={{ color: '#888', fontSize: '13px' }}>已选桩号:</span>
            <span style={{ 
              color: '#ffd700', 
              fontSize: '18px', 
              fontWeight: 'bold' 
            }}>
              {selectedStation}
            </span>
            <button
              onClick={() => setSelectedStation(null)}
              style={{
                marginLeft: 'auto',
                padding: '6px 12px',
                background: 'transparent',
                border: '1px solid #444',
                borderRadius: '4px',
                color: '#888',
                cursor: 'pointer',
                fontSize: '12px'
              }}
            >
              清除选择
            </button>
          </div>
        )}
        
        {/* 3D Viewer */}
        <div style={{ flex: 1 }}>
          <Project3DViewer
            projectId={currentProject}
            onStationClick={handleStationClick}
          />
        </div>
      </div>
    </div>
  )
}
