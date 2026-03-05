/**
 * CollisionPanel - 碰撞列表面板
 * 显示碰撞列表、统计信息和详情
 */

import { useState, useMemo } from 'react'
import {
  CollisionPoint,
  CollisionSeverity,
  CollisionType,
  CollisionStatus,
  CollisionStatistics,
} from '../../types/collision'

// ============================================================================
// Types
// ============================================================================

export interface CollisionPanelProps {
  /** 碰撞列表数据 */
  collisions: CollisionPoint[]
  /** 统计数据 */
  statistics?: CollisionStatistics
  /** 当前选中的碰撞ID */
  selectedId?: string | null
  /** 是否加载中 */
  loading?: boolean
  /** 点击碰撞项回调 */
  onSelect?: (collision: CollisionPoint) => void
  /** 查看详情回调 */
  onViewDetail?: (collision: CollisionPoint) => void
  /** 状态变更回调 */
  onStatusChange?: (ids: string[], status: CollisionStatus) => void
  /** 刷新回调 */
  onRefresh?: () => void
  /** 是否显示统计面板 */
  showStatistics?: boolean
  /** 是否显示过滤器 */
  showFilters?: boolean
  /** 自定义样式类名 */
  className?: string
}

// ============================================================================
// Constants
// ============================================================================

const severityConfig: Record<CollisionSeverity, { label: string; color: string; bgColor: string }> = {
  critical: { label: '严重', color: '#ff3333', bgColor: 'rgba(255,51,51,0.15)' },
  major: { label: '重要', color: '#ff8800', bgColor: 'rgba(255,136,0,0.15)' },
  minor: { label: '轻微', color: '#ffcc00', bgColor: 'rgba(255,204,0,0.15)' },
  warning: { label: '警告', color: '#4488ff', bgColor: 'rgba(68,136,255,0.15)' },
}

const statusConfig: Record<CollisionStatus, { label: string; color: string }> = {
  detected: { label: '已检测', color: '#ff8800' },
  confirmed: { label: '已确认', color: '#4488ff' },
  resolved: { label: '已解决', color: '#00cc66' },
  ignored: { label: '已忽略', color: '#888888' },
}

const typeConfig: Record<CollisionType, { label: string; icon: string }> = {
  component_collision: { label: '构件碰撞', icon: '⚠️' },
  clearance_violation: { label: '净空不足', icon: '📏' },
  overlap: { label: '重叠', icon: '🔄' },
  proximity: { label: '临近', icon: '📍' },
  penetration: { label: '穿透', icon: '🔨' },
}

// ============================================================================
// Statistics Card Component
// ============================================================================

function StatisticsCard({
  title,
  value,
  color,
  icon,
}: {
  title: string
  value: number
  color: string
  icon?: string
}) {
  return (
    <div
      style={{
        background: 'rgba(30, 30, 50, 0.8)',
        borderRadius: '8px',
        padding: '12px 16px',
        border: `1px solid ${color}40`,
        display: 'flex',
        flexDirection: 'column',
        gap: '4px',
      }}
    >
      <div style={{ fontSize: '11px', color: '#888', display: 'flex', alignItems: 'center', gap: '4px' }}>
        {icon && <span>{icon}</span>}
        {title}
      </div>
      <div style={{ fontSize: '24px', fontWeight: 700, color }}>{value}</div>
    </div>
  )
}

// ============================================================================
// Collision Item Component
// ============================================================================

function CollisionItem({
  collision,
  selected,
  onClick,
  onViewDetail,
}: {
  collision: CollisionPoint
  selected?: boolean
  onClick?: () => void
  onViewDetail?: () => void
}) {
  const severity = severityConfig[collision.severity]
  const status = statusConfig[collision.status]
  const type = typeConfig[collision.collision_type]
  
  return (
    <div
      onClick={onClick}
      style={{
        background: selected ? 'rgba(68, 136, 255, 0.15)' : 'rgba(30, 30, 50, 0.6)',
        border: `1px solid ${selected ? '#4488ff' : 'rgba(255,255,255,0.1)'}`,
        borderRadius: '8px',
        padding: '12px',
        cursor: 'pointer',
        transition: 'all 0.2s ease',
      }}
    >
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '16px' }}>{type.icon}</span>
          <span style={{ fontWeight: 600, color: severity.color }}>{severity.label}</span>
        </div>
        <span style={{ fontSize: '11px', color: status.color, background: `${status.color}20`, padding: '2px 8px', borderRadius: '4px' }}>
          {status.label}
        </span>
      </div>
      
      {/* Location */}
      <div style={{ fontSize: '13px', color: '#ccc', marginBottom: '6px' }}>
        {collision.station_display || `X:${collision.x.toFixed(1)} Y:${collision.y.toFixed(1)} Z:${collision.z.toFixed(1)}`}
      </div>
      
      {/* Info */}
      <div style={{ display: 'flex', gap: '12px', fontSize: '11px', color: '#888' }}>
        {collision.distance !== undefined && (
          <span>距离: <span style={{ color: '#ff6666' }}>{collision.distance.toFixed(3)}m</span></span>
        )}
        <span>LOD{collision.lod_level}</span>
      </div>
      
      {/* Description */}
      {collision.description && (
        <div style={{ fontSize: '11px', color: '#666', marginTop: '6px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
          {collision.description}
        </div>
      )}
      
      {/* Actions */}
      {selected && (
        <div style={{ marginTop: '8px', display: 'flex', gap: '8px' }}>
          <button
            onClick={(e) => {
              e.stopPropagation()
              onViewDetail?.()
            }}
            style={{
              flex: 1,
              padding: '6px',
              background: 'rgba(68, 136, 255, 0.2)',
              border: '1px solid #4488ff',
              borderRadius: '4px',
              color: '#4488ff',
              fontSize: '11px',
              cursor: 'pointer',
            }}
          >
            查看详情
          </button>
        </div>
      )}
    </div>
  )
}

// ============================================================================
// Main CollisionPanel Component
// ============================================================================

export default function CollisionPanel({
  collisions,
  statistics,
  selectedId,
  loading = false,
  onSelect,
  onViewDetail,
  onStatusChange,
  onRefresh,
  showStatistics = true,
  showFilters = true,
  className,
}: CollisionPanelProps) {
  const [filterSeverity, setFilterSeverity] = useState<CollisionSeverity | 'all'>('all')
  const [filterStatus, setFilterStatus] = useState<CollisionStatus | 'all'>('all')
  const [filterType, setFilterType] = useState<CollisionType | 'all'>('all')
  const [searchText, setSearchText] = useState('')
  
  // 过滤后的碰撞列表
  const filteredCollisions = useMemo(() => {
    return collisions.filter((collision) => {
      if (filterSeverity !== 'all' && collision.severity !== filterSeverity) return false
      if (filterStatus !== 'all' && collision.status !== filterStatus) return false
      if (filterType !== 'all' && collision.collision_type !== filterType) return false
      if (searchText) {
        const search = searchText.toLowerCase()
        const matchStation = collision.station_display?.toLowerCase().includes(search)
        const matchDesc = collision.description?.toLowerCase().includes(search)
        const matchId = collision.id.toLowerCase().includes(search)
        if (!matchStation && !matchDesc && !matchId) return false
      }
      return true
    })
  }, [collisions, filterSeverity, filterStatus, filterType, searchText])
  
  // 批量操作
  const handleBatchResolve = () => {
    if (selectedId) {
      onStatusChange?.([selectedId], 'resolved')
    }
  }
  
  const handleBatchIgnore = () => {
    if (selectedId) {
      onStatusChange?.([selectedId], 'ignored')
    }
  }
  
  return (
    <div
      className={className}
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        background: '#12121a',
        borderRadius: '12px',
        overflow: 'hidden',
      }}
    >
      {/* Header */}
      <div
        style={{
          padding: '16px',
          borderBottom: '1px solid rgba(255,255,255,0.1)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <div>
          <h3 style={{ margin: 0, fontSize: '16px', color: 'white' }}>碰撞检测</h3>
          <p style={{ margin: '4px 0 0', fontSize: '12px', color: '#888' }}>
            共 {collisions.length} 条记录
          </p>
        </div>
        {onRefresh && (
          <button
            onClick={onRefresh}
            disabled={loading}
            style={{
              padding: '8px 16px',
              background: loading ? '#333' : 'linear-gradient(135deg, #667eea, #764ba2)',
              border: 'none',
              borderRadius: '6px',
              color: 'white',
              fontSize: '12px',
              cursor: loading ? 'not-allowed' : 'pointer',
            }}
          >
            {loading ? '加载中...' : '刷新'}
          </button>
        )}
      </div>
      
      {/* Statistics */}
      {showStatistics && statistics && (
        <div
          style={{
            padding: '16px',
            borderBottom: '1px solid rgba(255,255,255,0.1)',
            display: 'grid',
            gridTemplateColumns: 'repeat(4, 1fr)',
            gap: '8px',
          }}
        >
          <StatisticsCard title="总数" value={statistics.total} color="#ffffff" icon="📊" />
          <StatisticsCard title="严重" value={statistics.by_severity.critical || 0} color="#ff3333" icon="🔴" />
          <StatisticsCard title="重要" value={statistics.by_severity.major || 0} color="#ff8800" icon="🟠" />
          <StatisticsCard title="已解决" value={statistics.by_status.resolved || 0} color="#00cc66" icon="✅" />
        </div>
      )}
      
      {/* Filters */}
      {showFilters && (
        <div
          style={{
            padding: '12px 16px',
            borderBottom: '1px solid rgba(255,255,255,0.1)',
            display: 'flex',
            flexDirection: 'column',
            gap: '8px',
          }}
        >
          {/* Search */}
          <input
            type="text"
            placeholder="搜索碰撞..."
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            style={{
              width: '100%',
              padding: '8px 12px',
              background: 'rgba(30, 30, 50, 0.8)',
              border: '1px solid rgba(255,255,255,0.1)',
              borderRadius: '6px',
              color: 'white',
              fontSize: '13px',
              outline: 'none',
            }}
          />
          
          {/* Filter Tags */}
          <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
            {/* Severity Filter */}
            <select
              value={filterSeverity}
              onChange={(e) => setFilterSeverity(e.target.value as CollisionSeverity | 'all')}
              style={{
                padding: '4px 8px',
                background: 'rgba(30, 30, 50, 0.8)',
                border: '1px solid rgba(255,255,255,0.1)',
                borderRadius: '4px',
                color: 'white',
                fontSize: '11px',
                outline: 'none',
              }}
            >
              <option value="all">全部严重度</option>
              <option value="critical">严重</option>
              <option value="major">重要</option>
              <option value="minor">轻微</option>
              <option value="warning">警告</option>
            </select>
            
            {/* Status Filter */}
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value as CollisionStatus | 'all')}
              style={{
                padding: '4px 8px',
                background: 'rgba(30, 30, 50, 0.8)',
                border: '1px solid rgba(255,255,255,0.1)',
                borderRadius: '4px',
                color: 'white',
                fontSize: '11px',
                outline: 'none',
              }}
            >
              <option value="all">全部状态</option>
              <option value="detected">已检测</option>
              <option value="confirmed">已确认</option>
              <option value="resolved">已解决</option>
              <option value="ignored">已忽略</option>
            </select>
            
            {/* Type Filter */}
            <select
              value={filterType}
              onChange={(e) => setFilterType(e.target.value as CollisionType | 'all')}
              style={{
                padding: '4px 8px',
                background: 'rgba(30, 30, 50, 0.8)',
                border: '1px solid rgba(255,255,255,0.1)',
                borderRadius: '4px',
                color: 'white',
                fontSize: '11px',
                outline: 'none',
              }}
            >
              <option value="all">全部类型</option>
              <option value="component_collision">构件碰撞</option>
              <option value="clearance_violation">净空不足</option>
              <option value="overlap">重叠</option>
              <option value="proximity">临近</option>
              <option value="penetration">穿透</option>
            </select>
          </div>
        </div>
      )}
      
      {/* Collision List */}
      <div
        style={{
          flex: 1,
          overflow: 'auto',
          padding: '12px',
          display: 'flex',
          flexDirection: 'column',
          gap: '8px',
        }}
      >
        {loading ? (
          <div style={{ textAlign: 'center', padding: '40px', color: '#888' }}>
            加载中...
          </div>
        ) : filteredCollisions.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '40px', color: '#888' }}>
            暂无碰撞数据
          </div>
        ) : (
          filteredCollisions.map((collision) => (
            <CollisionItem
              key={collision.id}
              collision={collision}
              selected={collision.id === selectedId}
              onClick={() => onSelect?.(collision)}
              onViewDetail={() => onViewDetail?.(collision)}
            />
          ))
        )}
      </div>
      
      {/* Batch Actions */}
      {selectedId && (
        <div
          style={{
            padding: '12px 16px',
            borderTop: '1px solid rgba(255,255,255,0.1)',
            display: 'flex',
            gap: '8px',
          }}
        >
          <button
            onClick={handleBatchResolve}
            style={{
              flex: 1,
              padding: '8px',
              background: 'rgba(0, 204, 102, 0.2)',
              border: '1px solid #00cc66',
              borderRadius: '6px',
              color: '#00cc66',
              fontSize: '12px',
              cursor: 'pointer',
            }}
          >
            标记解决
          </button>
          <button
            onClick={handleBatchIgnore}
            style={{
              flex: 1,
              padding: '8px',
              background: 'rgba(136, 136, 136, 0.2)',
              border: '1px solid #888888',
              borderRadius: '6px',
              color: '#888888',
              fontSize: '12px',
              cursor: 'pointer',
            }}
          >
            忽略
          </button>
        </div>
      )}
    </div>
  )
}

// Export types
export type { CollisionPanelProps }
