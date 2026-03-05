import { useState, useCallback } from 'react'
import { useApp } from '../context/AppContext'

// 本地模拟数据（后端未启动时使用）
const mockStationData: Record<string, any> = {
  'K0+000': { station: 'K0+000', x: 500000, y: 3000000, z: 100, azimuth: 45, horizontal_elem: '直线', vertical_elem: '凸形竖曲线' },
  'K0+500': { station: 'K0+500', x: 500353.55, y: 3000353.55, z: 110, azimuth: 45, horizontal_elem: '缓和曲线', vertical_elem: '直线' },
  'K1+000': { station: 'K1+000', x: 500707.1, y: 3000707.1, z: 107.5, azimuth: 45, horizontal_elem: '圆曲线', vertical_elem: '凹形竖曲线' },
  'K1+500': { station: 'K1+500', x: 501060.66, y: 3001060.66, z: 105, azimuth: 45, horizontal_elem: '圆曲线', vertical_elem: '直线' },
  'K2+000': { station: 'K2+000', x: 501414.21, y: 3001414.21, z: 102.5, azimuth: 45, horizontal_elem: '缓和曲线', vertical_elem: '凸形竖曲线' }
}

interface StationResult {
  station: string
  x: number
  y: number
  z: number
  azimuth: number
  horizontal_elem?: string
  vertical_elem?: string
}

export default function StationQuery() {
  const { state, dispatch } = useApp()
  const [inputStation, setInputStation] = useState('')
  const [routeId, setRouteId] = useState('demo')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [stationData, setStationData] = useState<StationResult | null>(null)
  
  // 处理查询
  const handleQuery = useCallback(() => {
    if (!inputStation.trim()) return
    
    setLoading(true)
    setError(null)
    
    // 模拟查询（如果后端未启动）
    setTimeout(() => {
      const mockData = mockStationData[inputStation.trim()]
      if (mockData) {
        setStationData(mockData)
        dispatch({ type: 'SET_SELECTED_STATION', payload: inputStation.trim() })
        dispatch({ type: 'SET_COORDINATES', payload: [mockData] })
      } else {
        setError('未找到该桩号')
      }
      setLoading(false)
    }, 300)
  }, [inputStation, dispatch])
  
  // 常用桩号快捷选择
  const quickStations = ['K0+000', 'K0+500', 'K1+000', 'K1+500', 'K2+000']
  
  // 处理键盘事件
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleQuery()
    }
  }

  return (
    <div className="station-query">
      {/* 查询表单 */}
      <div className="query-panel">
        <h2>🔍 桩号查询</h2>
        
        <div className="form-row">
          <div className="form-group">
            <label>路线ID</label>
            <select 
              value={routeId} 
              onChange={(e) => setRouteId(e.target.value)}
            >
              <option value="demo">demo - 演示路线</option>
              <option value="G001">G001 - 京港澳高速</option>
              <option value="G002">G002 - 京沪高速</option>
            </select>
          </div>
          
          <div className="form-group flex-1">
            <label>桩号</label>
            <input 
              type="text" 
              value={inputStation}
              onChange={(e) => setInputStation(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="例如: K0+500"
            />
          </div>
          
          <button className="btn-query" onClick={handleQuery}>
            查询
          </button>
        </div>
        
        {/* 快速选择 */}
        <div className="quick-select">
          <span>快速选择:</span>
          {quickStations.map(station => (
            <button 
              key={station}
              className={`quick-btn ${state.selectedStation === station ? 'active' : ''}`}
              onClick={() => {
                setInputStation(station)
                dispatch({ type: 'SET_SELECTED_STATION', payload: station })
              }}
            >
              {station}
            </button>
          ))}
        </div>
      </div>
      
      {/* 结果展示 */}
      <div className="result-panel">
        {loading ? (
          <div className="loading">查询中...</div>
        ) : error ? (
          <div className="error">{error}</div>
        ) : stationData || state.coordinates[0] ? (
          <div className="result-content">
            <h3>查询结果</h3>
            
            <div className="result-grid">
              <div className="result-item">
                <span className="label">桩号</span>
                <span className="value">{stationData?.station || state.coordinates[0]?.station}</span>
              </div>
              <div className="result-item">
                <span className="label">X坐标</span>
                <span className="value">{stationData?.x?.toFixed(3) || state.coordinates[0]?.x?.toFixed(3)}</span>
              </div>
              <div className="result-item">
                <span className="label">Y坐标</span>
                <span className="value">{stationData?.y?.toFixed(3) || state.coordinates[0]?.y?.toFixed(3)}</span>
              </div>
              <div className="result-item">
                <span className="label">高程Z</span>
                <span className="value">{stationData?.z?.toFixed(3) || state.coordinates[0]?.z?.toFixed(3)} m</span>
              </div>
              <div className="result-item">
                <span className="label">方位角</span>
                <span className="value">{stationData?.azimuth || state.coordinates[0]?.azimuth}°</span>
              </div>
              <div className="result-item">
                <span className="label">平曲线元素</span>
                <span className="value">{stationData?.horizontal_elem || '直线'}</span>
              </div>
              <div className="result-item">
                <span className="label">纵曲线元素</span>
                <span className="value">{stationData?.vertical_elem || '直线'}</span>
              </div>
            </div>
            
            {/* 坐标操作 */}
            <div className="result-actions">
              <button className="btn-action" onClick={() => {
                const coord = stationData || state.coordinates[0]
                if (coord) {
                  navigator.clipboard.writeText(`${coord.x}, ${coord.y}, ${coord.z}`)
                }
              }}>
                📋 复制坐标
              </button>
              <button className="btn-action" onClick={() => {
                window.dispatchEvent(new CustomEvent('navigate', { detail: 'model' }))
              }}>
                🎮 查看三维
              </button>
            </div>
          </div>
        ) : (
          <div className="empty">
            <p>请输入桩号进行查询</p>
            <p className="hint">支持格式: K0+000, K1+500 等</p>
          </div>
        )}
      </div>
      
      <style>{`
        .station-query {
          display: flex;
          flex-direction: column;
          height: 100%;
          padding: 20px;
          gap: 20px;
          overflow-y: auto;
        }
        
        .query-panel {
          background: #1a1a2e;
          border-radius: 12px;
          padding: 20px;
        }
        
        .query-panel h2 {
          font-size: 18px;
          margin-bottom: 20px;
          color: #00ff88;
        }
        
        .form-row {
          display: flex;
          gap: 12px;
          align-items: flex-end;
        }
        
        .form-group {
          display: flex;
          flex-direction: column;
          gap: 6px;
        }
        
        .form-group.flex-1 {
          flex: 1;
        }
        
        .form-group label {
          font-size: 12px;
          color: #888;
        }
        
        .form-group input,
        .form-group select {
          padding: 10px 14px;
          background: #252540;
          border: 1px solid #444;
          border-radius: 6px;
          color: #fff;
          font-size: 14px;
        }
        
        .form-group input:focus,
        .form-group select:focus {
          outline: none;
          border-color: #667eea;
        }
        
        .btn-query {
          padding: 10px 24px;
          background: linear-gradient(135deg, #667eea, #764ba2);
          border: none;
          border-radius: 6px;
          color: #fff;
          font-size: 14px;
          font-weight: 600;
          cursor: pointer;
          transition: transform 0.2s;
        }
        
        .btn-query:hover {
          transform: translateY(-2px);
        }
        
        .quick-select {
          margin-top: 16px;
          display: flex;
          align-items: center;
          gap: 8px;
          flex-wrap: wrap;
        }
        
        .quick-select span {
          font-size: 12px;
          color: #888;
        }
        
        .quick-btn {
          padding: 6px 12px;
          background: #252540;
          border: 1px solid #444;
          border-radius: 4px;
          color: #aaa;
          font-size: 12px;
          cursor: pointer;
          transition: all 0.2s;
        }
        
        .quick-btn:hover, .quick-btn.active {
          background: #667eea;
          border-color: #667eea;
          color: #fff;
        }
        
        .result-panel {
          flex: 1;
          background: #1a1a2e;
          border-radius: 12px;
          padding: 20px;
        }
        
        .result-content h3 {
          font-size: 16px;
          margin-bottom: 16px;
          color: #fff;
        }
        
        .result-grid {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 12px;
        }
        
        .result-item {
          background: #252540;
          padding: 12px;
          border-radius: 8px;
          display: flex;
          flex-direction: column;
          gap: 4px;
        }
        
        .result-item .label {
          font-size: 11px;
          color: #666;
        }
        
        .result-item .value {
          font-size: 14px;
          color: #00ff88;
          font-weight: 500;
        }
        
        .result-actions {
          margin-top: 20px;
          display: flex;
          gap: 12px;
        }
        
        .btn-action {
          padding: 10px 16px;
          background: #252540;
          border: 1px solid #444;
          border-radius: 6px;
          color: #fff;
          font-size: 13px;
          cursor: pointer;
          transition: all 0.2s;
        }
        
        .btn-action:hover {
          background: #333;
          border-color: #667eea;
        }
        
        .loading, .error, .empty {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          height: 200px;
          color: #666;
        }
        
        .error {
          color: #ff6b6b;
        }
        
        .empty .hint {
          font-size: 12px;
          margin-top: 8px;
        }
      `}</style>
    </div>
  )
}
