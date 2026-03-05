// Cross-Section Preview Component
// Shows 2D cross-section views at specific stations

import { useMemo, useState } from 'react'
import { Coordinate, CrossSection } from './Enhanced3DViewer'

interface CrossSectionPreviewProps {
  coordinates: Coordinate[]
  selectedStation?: string
  roadWidth?: number
  onStationSelect?: (station: string) => void
}

// Generate cross-section data from coordinates
const generateCrossSections = (
  coordinates: Coordinate[],
  roadWidth: number
): CrossSection[] => {
  return coordinates.map((c, idx) => {
    const elevation = c.z
    const baseElevation = coordinates[0]?.z || 0
    const elevationDiff = elevation - baseElevation
    
    // Determine cut/fill based on elevation change
    let cutFill: 'cut' | 'fill' | 'mixed' = 'fill'
    if (elevationDiff > 2) cutFill = 'cut'
    else if (Math.abs(elevationDiff) < 1) cutFill = 'mixed'
    
    return {
      station: c.station,
      position: { x: c.x, y: c.y, z: c.z } as any,
      leftWidth: roadWidth / 2 + Math.random() * 3,
      rightWidth: roadWidth / 2 + Math.random() * 3,
      elevation: c.z,
      cutFill
    }
  })
}

// Single cross-section render
function CrossSectionView({ 
  data,
  width = 300,
  height = 200 
}: { 
  data: CrossSection
  width?: number
  height?: number
}) {
  const isCut = data.cutFill === 'cut'
  const isFill = data.cutFill === 'fill'
  
  // Calculate dimensions
  const centerX = width / 2
  const groundY = height * 0.7
  const surfaceY = groundY - 20
  
  // Road surface width (scaled)
  const roadHalfWidth = 60
  const leftEdge = centerX - roadHalfWidth
  const rightEdge = centerX + roadHalfWidth
  
  // Slope lines
  const slopeLength = 40
  const leftSlopeEnd = leftEdge - slopeLength
  const rightSlopeEnd = rightEdge + slopeLength
  const slopeEndY = isCut ? groundY + 30 : groundY - 30
  
  return (
    <svg width={width} height={height} style={{ background: '#1a1a2e', borderRadius: 8 }}>
      {/* Ground line */}
      <line 
        x1={10} y1={groundY} 
        x2={width - 10} y2={groundY} 
        stroke="#666" 
        strokeWidth={2} 
      />
      
      {/* Left slope */}
      <line 
        x1={leftEdge} y1={surfaceY} 
        x2={leftSlopeEnd} y2={slopeEndY} 
        stroke={isCut ? '#ff6b6b' : '#4ecdc4'} 
        strokeWidth={2}
        strokeDasharray={isCut ? '5,5' : undefined}
      />
      
      {/* Right slope */}
      <line 
        x1={rightEdge} y1={surfaceY} 
        x2={rightSlopeEnd} y2={slopeEndY} 
        stroke={isCut ? '#ff6b6b' : '#4ecdc4'} 
        strokeWidth={2}
        strokeDasharray={isCut ? '5,5' : undefined}
      />
      
      {/* Road surface */}
      <rect 
        x={leftEdge} 
        y={surfaceY} 
        width={roadHalfWidth * 2} 
        height={groundY - surfaceY}
        fill={isCut ? '#ff6b6b' : isFill ? '#4ecdc4' : '#888'}
        opacity={0.6}
      />
      
      {/* Center line */}
      <line 
        x1={centerX} y1={surfaceY - 5} 
        x2={centerX} y2={groundY} 
        stroke="#ffd700" 
        strokeWidth={2}
        strokeDasharray="5,3"
      />
      
      {/* Road markings */}
      <line 
        x1={centerX - 30} y1={surfaceY + 5} 
        x2={centerX + 30} y2={surfaceY + 5} 
        stroke="#fff" 
        strokeWidth={3}
      />
      
      {/* Labels */}
      <text x={leftEdge - 10} y={surfaceY + 15} fill="#aaa" fontSize="10" textAnchor="end">
        左 {data.leftWidth.toFixed(1)}m
      </text>
      <text x={rightEdge + 10} y={surfaceY + 15} fill="#aaa" fontSize="10" textAnchor="start">
        右 {data.rightWidth.toFixed(1)}m
      </text>
      
      {/* Station label */}
      <text x={centerX} y={20} fill="#fff" fontSize="14" fontWeight="bold" textAnchor="middle">
        {data.station}
      </text>
      
      {/* Elevation */}
      <text x={centerX} y={40} fill="#00ff88" fontSize="11" textAnchor="middle">
        高程: {data.elevation.toFixed(2)}m
      </text>
      
      {/* Cut/Fill indicator */}
      <text 
        x={width - 60} 
        y={height - 15} 
        fill={isCut ? '#ff6b6b' : isFill ? '#4ecdc4' : '#888'} 
        fontSize="12" 
        fontWeight="bold"
      >
        {isCut ? '🔴 开挖' : isFill ? '🟢 填方' : '⚪ 半填半挖'}
      </text>
    </svg>
  )
}

export default function CrossSectionPreview({
  coordinates,
  selectedStation,
  roadWidth = 20,
  onStationSelect
}: CrossSectionPreviewProps) {
  const [viewMode, setViewMode] = useState<'single' | 'compare'>('single')
  
  const crossSections = useMemo(() => 
    generateCrossSections(coordinates, roadWidth),
    [coordinates, roadWidth]
  )
  
  // Find selected or default section
  const selectedIndex = useMemo(() => {
    if (selectedStation) {
      const idx = crossSections.findIndex(cs => cs.station === selectedStation)
      return idx >= 0 ? idx : Math.floor(crossSections.length / 2)
    }
    return Math.floor(crossSections.length / 2)
  }, [crossSections, selectedStation])
  
  const currentSection = crossSections[selectedIndex]
  const prevSection = crossSections[selectedIndex - 1]
  const nextSection = crossSections[selectedIndex + 1]
  
  // Quick navigation
  const goToPrev = () => onStationSelect?.(prevSection?.station || selectedStation || '')
  const goToNext = () => onStationSelect?.(nextSection?.station || selectedStation || '')
  
  return (
    <div style={{ 
      display: 'flex', 
      flexDirection: 'column', 
      height: '100%',
      background: '#0f0f1a',
      padding: '16px'
    }}>
      {/* Header */}
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        marginBottom: '16px'
      }}>
        <h3 style={{ margin: 0, color: '#00ff88', fontSize: '16px' }}>
          🔀 横断面预览
        </h3>
        
        <div style={{ display: 'flex', gap: '8px' }}>
          <button
            onClick={() => setViewMode('single')}
            style={{
              padding: '6px 12px',
              background: viewMode === 'single' ? '#667eea' : '#252540',
              border: '1px solid #444',
              borderRadius: '4px',
              color: 'white',
              cursor: 'pointer',
              fontSize: '11px'
            }}
          >
            单个
          </button>
          <button
            onClick={() => setViewMode('compare')}
            style={{
              padding: '6px 12px',
              background: viewMode === 'compare' ? '#667eea' : '#252540',
              border: '1px solid #444',
              borderRadius: '4px',
              color: 'white',
              cursor: 'pointer',
              fontSize: '11px'
            }}
          >
            对比
          </button>
        </div>
      </div>
      
      {/* Navigation */}
      <div style={{ 
        display: 'flex', 
        alignItems: 'center', 
        gap: '12px',
        marginBottom: '16px'
      }}>
        <button
          onClick={goToPrev}
          disabled={!prevSection}
          style={{
            padding: '8px 16px',
            background: '#252540',
            border: '1px solid #444',
            borderRadius: '6px',
            color: prevSection ? 'white' : '#666',
            cursor: prevSection ? 'pointer' : 'not-allowed'
          }}
        >
          ← 上一桩号
        </button>
        
        <div style={{ flex: 1, textAlign: 'center' }}>
          <span style={{ color: '#ffd700', fontSize: '14px', fontWeight: 'bold' }}>
            {currentSection?.station || 'K0+000'}
          </span>
        </div>
        
        <button
          onClick={goToNext}
          disabled={!nextSection}
          style={{
            padding: '8px 16px',
            background: '#252540',
            border: '1px solid #444',
            borderRadius: '6px',
            color: nextSection ? 'white' : '#666',
            cursor: nextSection ? 'pointer' : 'not-allowed'
          }}
        >
          下一桩号 →
        </button>
      </div>
      
      {/* Cross section view(s) */}
      <div style={{ flex: 1, display: 'flex', gap: '16px', justifyContent: 'center' }}>
        {viewMode === 'single' ? (
          currentSection && (
            <CrossSectionView data={currentSection} />
          )
        ) : (
          <>
            {prevSection && <CrossSectionView data={prevSection} />}
            {currentSection && <CrossSectionView data={currentSection} />}
            {nextSection && <CrossSectionView data={nextSection} />}
          </>
        )}
      </div>
      
      {/* Station selector */}
      <div style={{ 
        marginTop: '16px',
        display: 'flex',
        flexWrap: 'wrap',
        gap: '4px',
        maxHeight: '80px',
        overflowY: 'auto'
      }}>
        {crossSections.filter((_, i) => i % 5 === 0).map((cs, i) => (
          <button
            key={cs.station}
            onClick={() => onStationSelect?.(cs.station)}
            style={{
              padding: '4px 8px',
              background: cs.station === currentSection?.station ? '#667eea' : '#252540',
              border: '1px solid #444',
              borderRadius: '4px',
              color: cs.station === currentSection?.station ? 'white' : '#aaa',
              cursor: 'pointer',
              fontSize: '10px'
            }}
          >
            {cs.station}
          </button>
        ))}
      </div>
      
      {/* Stats */}
      <div style={{ 
        marginTop: '12px',
        padding: '10px',
        background: '#1a1a2e',
        borderRadius: '6px',
        display: 'grid',
        gridTemplateColumns: 'repeat(3, 1fr)',
        gap: '8px',
        fontSize: '11px'
      }}>
        <div>
          <div style={{ color: '#666' }}>高程</div>
          <div style={{ color: '#00ff88' }}>{currentSection?.elevation.toFixed(2)}m</div>
        </div>
        <div>
          <div style={{ color: '#666' }}>左幅宽</div>
          <div style={{ color: '#4ecdc4' }}>{currentSection?.leftWidth.toFixed(1)}m</div>
        </div>
        <div>
          <div style={{ color: '#666' }}>右幅宽</div>
          <div style={{ color: '#4ecdc4' }}>{currentSection?.rightWidth.toFixed(1)}m</div>
        </div>
      </div>
    </div>
  )
}
