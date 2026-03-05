// Project-isolated 3D Route Viewer
// Loads and displays route data based on current project ID

import { useState, useEffect, useCallback, useMemo } from 'react'
import { useAppStore } from '../stores/appStore'
import Enhanced3DViewer, { 
  Coordinate, 
  ProjectData, 
  Annotation, 
  Measurement 
} from './Enhanced3DViewer'
import CrossSectionPreview from './CrossSectionPreview'

// Mock project route data - in real app, this would come from API
const PROJECT_ROUTE_DATA: Record<string, ProjectData> = {
  'demo': {
    projectId: 'demo',
    projectName: '演示项目',
    roadWidth: 20,
    laneCount: 4,
    coordinates: generateDemoCoordinates('demo')
  },
  'project-001': {
    projectId: 'project-001',
    projectName: '京沪高速改造',
    roadWidth: 24,
    laneCount: 6,
    coordinates: generateDemoCoordinates('project-001')
  },
  'project-002': {
    projectId: 'project-002',
    projectName: '城市快速路',
    roadWidth: 16,
    laneCount: 4,
    coordinates: generateDemoCoordinates('project-002')
  }
}

// Generate demo coordinates based on project
function generateDemoCoordinates(projectId: string): Coordinate[] {
  const coords: Coordinate[] = []
  const seed = projectId.split('').reduce((a, c) => a + c.charCodeAt(0), 0)
  const count = 60 + (seed % 80)
  
  for (let i = 0; i < count; i++) {
    const progress = i / count
    const baseX = i * 10
    const baseY = i * 5 + Math.sin(progress * Math.PI * 2) * 30
    const baseZ = 50 + progress * 50 + Math.sin(i * 0.1) * 3
    
    // Add some vertical variation (hills/valleys)
    const hillEffect = Math.sin(i * 0.05) * 10
    
    coords.push({
      station: `K${Math.floor(i / 10) + 1}+${(i % 10) * 10}`,
      x: baseX,
      y: baseY,
      z: baseZ + hillEffect,
      azimuth: 45 + Math.sin(i * 0.03) * 15 + (seed % 10 - 5)
    })
  }
  
  return coords
}

interface Project3DViewerProps {
  projectId?: string
  height?: string | number
  onStationClick?: (station: string) => void
}

export default function Project3DViewer({
  projectId: propProjectId,
  height = '100%',
  onStationClick
}: Project3DViewerProps) {
  // Get project ID from store or props
  const storeProjectId = useAppStore(state => state.currentProjectId)
  const projectId = propProjectId || storeProjectId || 'demo'
  
  // State
  const [viewMode, setViewMode] = useState<'3d' | 'section' | 'split'>('3d')
  const [selectedStation, setSelectedStation] = useState<string | null>(null)
  const [annotations, setAnnotations] = useState<Annotation[]>([])
  const [measurements, setMeasurements] = useState<Measurement[]>([])
  
  // Get project data
  const projectData = useMemo(() => {
    // Check if we have mock data for this project
    if (PROJECT_ROUTE_DATA[projectId]) {
      return PROJECT_ROUTE_DATA[projectId]
    }
    
    // Generate data for unknown projects
    return {
      projectId,
      projectName: `项目 ${projectId}`,
      roadWidth: 20,
      laneCount: 4,
      coordinates: generateDemoCoordinates(projectId)
    }
  }, [projectId])
  
  // Handle station click from 3D view
  const handleStationClick = useCallback((station: string) => {
    setSelectedStation(station)
    onStationClick?.(station)
  }, [onStationClick])
  
  // Handle cross-section station select
  const handleSectionStationSelect = useCallback((station: string) => {
    setSelectedStation(station)
    onStationClick?.(station)
  }, [onStationClick])
  
  // Handle new annotation
  const handleAnnotationAdd = useCallback((annotation: Annotation) => {
    setAnnotations(prev => [...prev, annotation])
  }, [])
  
  // Handle new measurement
  const handleMeasurementComplete = useCallback((measurement: Measurement) => {
    setMeasurements(prev => [...prev, measurement])
  }, [])
  
  // Clear all measurements
  const clearMeasurements = useCallback(() => {
    setMeasurements([])
  }, [])
  
  // Clear all annotations
  const clearAnnotations = useCallback(() => {
    setAnnotations([])
  }, [])

  return (
    <div style={{ 
      display: 'flex', 
      flexDirection: 'column', 
      height,
      background: '#0a0a15'
    }}>
      {/* View mode tabs */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        padding: '8px 16px',
        background: '#1a1a2e',
        borderBottom: '1px solid #333',
        gap: '8px'
      }}>
        <div style={{
          display: 'flex',
          background: '#0f0f1a',
          borderRadius: '8px',
          padding: '4px'
        }}>
          <button
            onClick={() => setViewMode('3d')}
            style={{
              padding: '8px 16px',
              background: viewMode === '3d' ? '#667eea' : 'transparent',
              border: 'none',
              borderRadius: '6px',
              color: viewMode === '3d' ? 'white' : '#888',
              cursor: 'pointer',
              fontSize: '13px',
              fontWeight: 'bold',
              transition: 'all 0.2s'
            }}
          >
            🌍 三维视图
          </button>
          <button
            onClick={() => setViewMode('section')}
            style={{
              padding: '8px 16px',
              background: viewMode === 'section' ? '#667eea' : 'transparent',
              border: 'none',
              borderRadius: '6px',
              color: viewMode === 'section' ? 'white' : '#888',
              cursor: 'pointer',
              fontSize: '13px',
              fontWeight: 'bold',
              transition: 'all 0.2s'
            }}
          >
            🔀 横断面
          </button>
          <button
            onClick={() => setViewMode('split')}
            style={{
              padding: '8px 16px',
              background: viewMode === 'split' ? '#667eea' : 'transparent',
              border: 'none',
              borderRadius: '6px',
              color: viewMode === 'split' ? 'white' : '#888',
              cursor: 'pointer',
              fontSize: '13px',
              fontWeight: 'bold',
              transition: 'all 0.2s'
            }}
          >
            📊 分屏视图
          </button>
        </div>
        
        <div style={{ flex: 1 }} />
        
        {/* Project info */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '12px'
        }}>
          <span style={{
            padding: '4px 12px',
            background: 'rgba(102, 126, 234, 0.2)',
            borderRadius: '12px',
            color: '#667eea',
            fontSize: '12px'
          }}>
            📁 {projectData.projectName}
          </span>
          
          <span style={{
            padding: '4px 12px',
            background: 'rgba(0, 255, 136, 0.1)',
            borderRadius: '12px',
            color: '#00ff88',
            fontSize: '11px'
          }}>
            桩号: {selectedStation || '未选择'}
          </span>
        </div>
        
        {/* Clear buttons */}
        <div style={{ display: 'flex', gap: '8px' }}>
          {measurements.length > 0 && (
            <button
              onClick={clearMeasurements}
              style={{
                padding: '6px 12px',
                background: '#ff4444',
                border: 'none',
                borderRadius: '6px',
                color: 'white',
                cursor: 'pointer',
                fontSize: '11px'
              }}
            >
              清除测量 ({measurements.length})
            </button>
          )}
          
          {annotations.length > 0 && (
            <button
              onClick={clearAnnotations}
              style={{
                padding: '6px 12px',
                background: '#ff4444',
                border: 'none',
                borderRadius: '6px',
                color: 'white',
                cursor: 'pointer',
                fontSize: '11px'
              }}
            >
              清除标注 ({annotations.length})
            </button>
          )}
        </div>
      </div>
      
      {/* Main content */}
      <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
        {viewMode === '3d' && (
          <Enhanced3DViewer
            projectId={projectId}
            projectData={projectData}
            coordinates={projectData.coordinates}
            roadWidth={projectData.roadWidth}
            laneCount={projectData.laneCount}
            showStakeMarks={true}
            onStationClick={handleStationClick}
            onMeasurementComplete={handleMeasurementComplete}
            onAnnotationAdd={handleAnnotationAdd}
          />
        )}
        
        {viewMode === 'section' && (
          <CrossSectionPreview
            coordinates={projectData.coordinates}
            selectedStation={selectedStation || undefined}
            roadWidth={projectData.roadWidth}
            onStationSelect={handleSectionStationSelect}
          />
        )}
        
        {viewMode === 'split' && (
          <>
            <div style={{ flex: 1, borderRight: '1px solid #333' }}>
              <Enhanced3DViewer
                projectId={projectId}
                projectData={projectData}
                coordinates={projectData.coordinates}
                roadWidth={projectData.roadWidth}
                laneCount={projectData.laneCount}
                showStakeMarks={true}
                onStationClick={handleStationClick}
                onMeasurementComplete={handleMeasurementComplete}
                onAnnotationAdd={handleAnnotationAdd}
              />
            </div>
            <div style={{ flex: 1 }}>
              <CrossSectionPreview
                coordinates={projectData.coordinates}
                selectedStation={selectedStation || undefined}
                roadWidth={projectData.roadWidth}
                onStationSelect={handleSectionStationSelect}
              />
            </div>
          </>
        )}
      </div>
      
      {/* Stats footer */}
      <div style={{
        padding: '8px 16px',
        background: '#1a1a2e',
        borderTop: '1px solid #333',
        display: 'flex',
        gap: '24px',
        fontSize: '11px',
        color: '#888'
      }}>
        <span>📍 桩号点: {projectData.coordinates.length}</span>
        <span>📏 测量: {measurements.length}</span>
        <span>🏷️ 标注: {annotations.length}</span>
        <span>🛣️ 路宽: {projectData.roadWidth}m</span>
        <span>🚗 车道: {projectData.laneCount}</span>
        <span style={{ marginLeft: 'auto', color: '#00ff88' }}>
          总长度: {((projectData.coordinates[projectData.coordinates.length-1]?.x || 0) / 1000).toFixed(2)} km
        </span>
      </div>
    </div>
  )
}
