import { useState } from 'react'
import { useApp } from '../context/AppContext'
import { usePhotos } from '../hooks/useApiCache'

// 模拟照片数据
const mockPhotos = [
  { id: '1', url: 'https://picsum.photos/800/600?random=1', thumbnail: 'https://picsum.photos/200/150?random=1', station: 'K0+100', capture_time: '2024-01-15 10:30', type: '全景' },
  { id: '2', url: 'https://picsum.photos/800/600?random=2', thumbnail: 'https://picsum.photos/200/150?random=2', station: 'K0+200', capture_time: '2024-01-15 10:35', type: '细节' },
  { id: '3', url: 'https://picsum.photos/800/600?random=3', thumbnail: 'https://picsum.photos/200/150?random=3', station: 'K0+500', capture_time: '2024-01-15 11:00', type: '全景' },
  { id: '4', url: 'https://picsum.photos/800/600?random=4', thumbnail: 'https://picsum.photos/200/150?random=4', station: 'K1+000', capture_time: '2024-01-15 11:30', type: '施工' },
  { id: '5https://picsum.photos/', url: '800/600?random=5', thumbnail: 'https://picsum.photos/200/150?random=5', station: 'K1+200', capture_time: '2024-01-15 12:00', type: '细节' },
  { id: '6', url: 'https://picsum.photos/800/600?random=6', thumbnail: 'https://picsum.photos/200/150?random=6', station: 'K1+500', capture_time: '2024-01-15 13:00', type: '全景' },
  { id: '7', url: 'https://picsum.photos/800/600?random=7', thumbnail: 'https://picsum.photos/200/150?random=7', station: 'K2+000', capture_time: '2024-01-15 14:00', type: '施工' },
  { id: '8', url: 'https://picsum.photos/800/600?random=8', thumbnail: 'https://picsum.photos/200/150?random=8', station: 'K2+300', capture_time: '2024-01-15 14:30', type: '细节' },
]

export default function PhotoBrowser() {
  const { dispatch } = useApp()
  const [routeId, setRouteId] = useState('')
  const [stationFilter, setStationFilter] = useState('')
  const [typeFilter, setTypeFilter] = useState('')
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid')
  const [lightboxPhoto, setLightboxPhoto] = useState<any>(null)
  
  // 使用缓存Hook
  const { data: photos } = usePhotos(routeId, stationFilter)
  
  // 实际使用的照片数据（优先使用API，否则用模拟）
  const displayPhotos = photos || mockPhotos
  
  // 过滤
  const filteredPhotos = displayPhotos.filter(p => {
    if (stationFilter && !p.station.includes(stationFilter)) return false
    if (typeFilter && p.type !== typeFilter) return false
    return true
  })
  
  // 获取唯一类型
  const types = [...new Set(displayPhotos.map(p => p.type))]
  
  // 处理照片点击
  const handlePhotoClick = (photo: any) => {
    dispatch({ type: 'SET_SELECTED_PHOTO', payload: photo })
    setLightboxPhoto(photo)
  }
  
  // 关闭灯箱
  const closeLightbox = () => {
    setLightboxPhoto(null)
  }

  return (
    <div className="photo-browser">
      {/* 筛选栏 */}
      <div className="filter-bar">
        <h2>📷 照片浏览</h2>
        
        <div className="filters">
          <select value={routeId} onChange={(e) => setRouteId(e.target.value)}>
            <option value="">全部路线</option>
            <option value="demo">demo - 演示路线</option>
          </select>
          
          <input 
            type="text" 
            placeholder="桩号筛选..."
            value={stationFilter}
            onChange={(e) => setStationFilter(e.target.value)}
          />
          
          <select value={typeFilter} onChange={(e) => setTypeFilter(e.target.value)}>
            <option value="">全部类型</option>
            {types.map(t => (
              <option key={t} value={t}>{t}</option>
            ))}
          </select>
          
          <div className="view-toggle">
            <button 
              className={viewMode === 'grid' ? 'active' : ''}
              onClick={() => setViewMode('grid')}
            >
              ▦
            </button>
            <button 
              className={viewMode === 'list' ? 'active' : ''}
              onClick={() => setViewMode('list')}
            >
              ☰
            </button>
          </div>
        </div>
        
        <div className="photo-count">
          共 {filteredPhotos.length} 张照片
        </div>
      </div>
      
      {/* 照片网格/列表 */}
      <div className={`photo-${viewMode}`}>
        {filteredPhotos.map(photo => (
          <div 
            key={photo.id} 
            className="photo-item"
            onClick={() => handlePhotoClick(photo)}
          >
            <img src={photo.thumbnail} alt={photo.station} />
            {viewMode === 'grid' && (
              <div className="photo-info">
                <span className="station">{photo.station}</span>
                <span className="type">{photo.type}</span>
              </div>
            )}
            {viewMode === 'list' && (
              <div className="photo-details">
                <img src={photo.thumbnail} alt={photo.station} />
                <div className="details">
                  <div className="station">{photo.station}</div>
                  <div className="meta">
                    <span>{photo.type}</span>
                    <span>{photo.capture_time}</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
      
      {filteredPhotos.length === 0 && (
        <div className="empty">
          <p>没有找到符合条件的照片</p>
        </div>
      )}
      
      {/* 灯箱预览 */}
      {lightboxPhoto && (
        <div className="lightbox" onClick={closeLightbox}>
          <div className="lightbox-content" onClick={(e) => e.stopPropagation()}>
            <img src={lightboxPhoto.url} alt={lightboxPhoto.station} />
            <div className="lightbox-info">
              <h3>{lightboxPhoto.station}</h3>
              <p>类型: {lightboxPhoto.type}</p>
              <p>拍摄时间: {lightboxPhoto.capture_time}</p>
              <button onClick={closeLightbox}>关闭</button>
            </div>
          </div>
        </div>
      )}
      
      <style>{`
        .photo-browser {
          display: flex;
          flex-direction: column;
          height: 100%;
          padding: 20px;
        }
        
        .filter-bar {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 20px;
          flex-wrap: wrap;
          gap: 12px;
        }
        
        .filter-bar h2 {
          font-size: 18px;
          color: #00ff88;
        }
        
        .filters {
          display: flex;
          gap: 10px;
          align-items: center;
        }
        
        .filters select,
        .filters input {
          padding: 8px 12px;
          background: #252540;
          border: 1px solid #444;
          border-radius: 6px;
          color: #fff;
          font-size: 13px;
        }
        
        .filters select:focus,
        .filters input:focus {
          outline: none;
          border-color: #667eea;
        }
        
        .view-toggle {
          display: flex;
          background: #252540;
          border-radius: 6px;
          overflow: hidden;
        }
        
        .view-toggle button {
          padding: 8px 12px;
          background: transparent;
          border: none;
          color: #888;
          cursor: pointer;
          font-size: 16px;
        }
        
        .view-toggle button.active {
          background: #667eea;
          color: #fff;
        }
        
        .photo-count {
          font-size: 13px;
          color: #666;
        }
        
        .photo-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
          gap: 16px;
          flex: 1;
          overflow-y: auto;
        }
        
        .photo-list {
          display: flex;
          flex-direction: column;
          gap: 12px;
          flex: 1;
          overflow-y: auto;
        }
        
        .photo-item {
          cursor: pointer;
          border-radius: 8px;
          overflow: hidden;
          transition: transform 0.2s, box-shadow 0.2s;
        }
        
        .photo-item:hover {
          transform: translateY(-4px);
          box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3);
        }
        
        .photo-grid .photo-item img {
          width: 100%;
          height: 150px;
          object-fit: cover;
          display: block;
        }
        
        .photo-info {
          background: #1a1a2e;
          padding: 10px;
          display: flex;
          justify-content: space-between;
          align-items: center;
        }
        
        .photo-info .station {
          color: #00ff88;
          font-weight: 500;
        }
        
        .photo-info .type {
          font-size: 11px;
          color: #888;
          background: #252540;
          padding: 2px 8px;
          border-radius: 4px;
        }
        
        .photo-list .photo-item {
          display: flex;
          background: #1a1a2e;
        }
        
        .photo-list .photo-item img {
          width: 120px;
          height: 80px;
          object-fit: cover;
        }
        
        .photo-details {
          display: flex;
          flex: 1;
        }
        
        .photo-details .details {
          padding: 12px;
          display: flex;
          flex-direction: column;
          justify-content: center;
          gap: 8px;
        }
        
        .photo-details .station {
          color: #00ff88;
          font-size: 16px;
          font-weight: 500;
        }
        
        .photo-details .meta {
          display: flex;
          gap: 16px;
          font-size: 12px;
          color: #888;
        }
        
        .empty {
          display: flex;
          align-items: center;
          justify-content: center;
          flex: 1;
          color: #666;
        }
        
        /* 灯箱样式 */
        .lightbox {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(0, 0, 0, 0.9);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 1000;
        }
        
        .lightbox-content {
          max-width: 90%;
          max-height: 90%;
          display: flex;
          flex-direction: column;
          align-items: center;
        }
        
        .lightbox-content img {
          max-width: 100%;
          max-height: 70vh;
          border-radius: 8px;
        }
        
        .lightbox-info {
          margin-top: 16px;
          text-align: center;
          color: #fff;
        }
        
        .lightbox-info h3 {
          color: #00ff88;
          margin-bottom: 8px;
        }
        
        .lightbox-info p {
          font-size: 13px;
          color: #888;
          margin: 4px 0;
        }
        
        .lightbox-info button {
          margin-top: 16px;
          padding: 8px 24px;
          background: #667eea;
          border: none;
          border-radius: 6px;
          color: #fff;
          cursor: pointer;
        }
      `}</style>
    </div>
  )
}
