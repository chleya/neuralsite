import { useState } from 'react'

// 模拟统计数据
const mockStats = {
  totalRoutes: 12,
  totalStations: 156,
  totalPhotos: 2340,
  totalModels: 28,
  recentActivity: [
    { id: 1, type: 'photo', action: '上传新照片', station: 'K12+500', time: '2分钟前' },
    { id: 2, type: 'model', action: '生成三维模型', station: 'K8+000 - K10+000', time: '15分钟前' },
    { id: 3, type: 'query', action: '桩号查询', station: 'K5+230', time: '1小时前' },
    { id: 4, type: 'collision', action: '碰撞检测完成', station: 'K3+100', time: '2小时前' },
    { id: 5, type: 'photo', action: '照片标注更新', station: 'K15+800', time: '3小时前' }
  ]
}

export default function Dashboard() {
  const [, setActiveSection] = useState<string | null>(null)

  const navigateTo = (section: string) => {
    setActiveSection(section)
    // 触发页面切换事件
    window.dispatchEvent(new CustomEvent('navigate', { detail: section }))
  }

  return (
    <div className="dashboard">
      {/* 欢迎区域 */}
      <div className="welcome-section">
        <h1>🛣️ NeuralSite Studio</h1>
        <p>欢迎使用公路工程智能分析平台</p>
      </div>

      {/* 统计卡片 */}
      <div className="stats-grid">
        <div className="stat-card" onClick={() => navigateTo('station')}>
          <div className="stat-icon">📍</div>
          <div className="stat-content">
            <div className="stat-value">{mockStats.totalRoutes}</div>
            <div className="stat-label">路线总数</div>
          </div>
        </div>
        
        <div className="stat-card" onClick={() => navigateTo('station')}>
          <div className="stat-icon">📏</div>
          <div className="stat-content">
            <div className="stat-value">{mockStats.totalStations}</div>
            <div className="stat-label">桩号数量</div>
          </div>
        </div>
        
        <div className="stat-card" onClick={() => navigateTo('photo')}>
          <div className="stat-icon">📷</div>
          <div className="stat-content">
            <div className="stat-value">{mockStats.totalPhotos}</div>
            <div className="stat-label">照片总数</div>
          </div>
        </div>
        
        <div className="stat-card" onClick={() => navigateTo('model')}>
          <div className="stat-icon">🎮</div>
          <div className="stat-content">
            <div className="stat-value">{mockStats.totalModels}</div>
            <div className="stat-label">三维模型</div>
          </div>
        </div>
      </div>

      {/* 功能入口 */}
      <div className="features-section">
        <h2>快速入口</h2>
        <div className="features-grid">
          <div className="feature-card" onClick={() => navigateTo('station')}>
            <div className="feature-icon">🔍</div>
            <h3>桩号查询</h3>
            <p>根据桩号查询道路坐标、平面线形、纵断面信息</p>
          </div>
          
          <div className="feature-card" onClick={() => navigateTo('photo')}>
            <div className="feature-icon">🖼️</div>
            <h3>照片浏览</h3>
            <p>查看道路现场照片，按桩号筛选浏览</p>
          </div>
          
          <div className="feature-card" onClick={() => navigateTo('model')}>
            <div className="feature-icon">🎯</div>
            <h3>三维预览</h3>
            <p>三维可视化道路模型，支持交互查看</p>
          </div>
          
          <div className="feature-card" onClick={() => navigateTo('knowledge')}>
            <div className="feature-icon">💡</div>
            <h3>知识问答</h3>
            <p>智能问答，查询公路工程相关知识</p>
          </div>
        </div>
      </div>

      {/* 最近活动 */}
      <div className="activity-section">
        <h2>最近活动</h2>
        <div className="activity-list">
          {mockStats.recentActivity.map((item) => (
            <div key={item.id} className="activity-item">
              <span className={`activity-type type-${item.type}`}>
                {item.type === 'photo' && '📷'}
                {item.type === 'model' && '🎮'}
                {item.type === 'query' && '🔍'}
                {item.type === 'collision' && '⚡'}
              </span>
              <span className="activity-action">{item.action}</span>
              <span className="activity-station">{item.station}</span>
              <span className="activity-time">{item.time}</span>
            </div>
          ))}
        </div>
      </div>

      <style>{`
        .dashboard {
          padding: 20px;
          height: 100%;
          overflow-y: auto;
        }
        
        .welcome-section {
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          padding: 30px;
          border-radius: 12px;
          margin-bottom: 24px;
        }
        
        .welcome-section h1 {
          font-size: 28px;
          margin-bottom: 8px;
        }
        
        .welcome-section p {
          opacity: 0.9;
          font-size: 14px;
        }
        
        .stats-grid {
          display: grid;
          grid-template-columns: repeat(4, 1fr);
          gap: 16px;
          margin-bottom: 24px;
        }
        
        .stat-card {
          background: #1a1a2e;
          border-radius: 12px;
          padding: 20px;
          display: flex;
          align-items: center;
          gap: 16px;
          cursor: pointer;
          transition: transform 0.2s, box-shadow 0.2s;
        }
        
        .stat-card:hover {
          transform: translateY(-4px);
          box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
        }
        
        .stat-icon {
          font-size: 32px;
        }
        
        .stat-value {
          font-size: 28px;
          font-weight: 700;
          color: #00ff88;
        }
        
        .stat-label {
          font-size: 13px;
          color: #888;
        }
        
        .features-section, .activity-section {
          margin-bottom: 24px;
        }
        
        .features-section h2, .activity-section h2 {
          font-size: 18px;
          margin-bottom: 16px;
          color: #eee;
        }
        
        .features-grid {
          display: grid;
          grid-template-columns: repeat(4, 1fr);
          gap: 16px;
        }
        
        .feature-card {
          background: #1a1a2e;
          border-radius: 12px;
          padding: 24px;
          cursor: pointer;
          transition: transform 0.2s, box-shadow 0.2s;
          border: 1px solid transparent;
        }
        
        .feature-card:hover {
          transform: translateY(-4px);
          border-color: #667eea;
          box-shadow: 0 8px 25px rgba(102, 126, 234, 0.2);
        }
        
        .feature-icon {
          font-size: 36px;
          margin-bottom: 12px;
        }
        
        .feature-card h3 {
          font-size: 16px;
          margin-bottom: 8px;
          color: #fff;
        }
        
        .feature-card p {
          font-size: 12px;
          color: #888;
          line-height: 1.5;
        }
        
        .activity-list {
          background: #1a1a2e;
          border-radius: 12px;
          overflow: hidden;
        }
        
        .activity-item {
          display: flex;
          align-items: center;
          padding: 14px 20px;
          border-bottom: 1px solid #333;
          font-size: 13px;
        }
        
        .activity-item:last-child {
          border-bottom: none;
        }
        
        .activity-type {
          margin-right: 12px;
          font-size: 16px;
        }
        
        .activity-action {
          flex: 1;
          color: #eee;
        }
        
        .activity-station {
          color: #00ff88;
          margin-right: 16px;
        }
        
        .activity-time {
          color: #666;
          font-size: 12px;
        }
        
        @media (max-width: 1200px) {
          .stats-grid, .features-grid {
            grid-template-columns: repeat(2, 1fr);
          }
        }
      `}</style>
    </div>
  )
}
