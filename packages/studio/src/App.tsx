import { useState, useEffect } from 'react'
import { AppProvider } from './context/AppContext'
import Dashboard from './pages/Dashboard'
import StationQuery from './pages/StationQuery'
import PhotoBrowser from './pages/PhotoBrowser'
import ModelPreview from './pages/ModelPreview'
import KnowledgeQA from './pages/KnowledgeQA'
import CommandCenter from './pages/CommandCenter'
import './index.css'

type Page = 'dashboard' | 'station' | 'photo' | 'model' | 'knowledge' | 'collision' | 'road' | 'command'

// 页面配置
const pages: Record<Page, { title: string; icon: string }> = {
  dashboard: { title: '首页', icon: '🏠' },
  command: { title: '指挥舱', icon: '🎯' },
  station: { title: '桩号查询', icon: '🔍' },
  photo: { title: '照片浏览', icon: '📷' },
  model: { title: '三维预览', icon: '🎮' },
  knowledge: { title: '知识问答', icon: '💡' },
  collision: { title: '碰撞检测', icon: '⚡' },
  road: { title: '道路建模', icon: '🛣️' }
}

function AppContent() {
  const [activePage, setActivePage] = useState<Page>('dashboard')
  
  // 监听页面切换事件
  useEffect(() => {
    const handleNavigate = (e: CustomEvent) => {
      const page = e.detail as Page
      if (pages[page]) {
        setActivePage(page)
      }
    }
    
    window.addEventListener('navigate', handleNavigate as EventListener)
    return () => {
      window.removeEventListener('navigate', handleNavigate as EventListener)
    }
  }, [])
  
  // 渲染页面内容
  const renderPage = () => {
    switch (activePage) {
      case 'dashboard':
        return <Dashboard />
      case 'command':
        return <CommandCenter />
      case 'station':
        return <StationQuery />
      case 'photo':
        return <PhotoBrowser />
      case 'model':
        return <ModelPreview />
      case 'knowledge':
        return <KnowledgeQA />
      case 'collision':
      case 'road':
        // 原有功能保留，需要导入组件
        return <div style={{ padding: 20, color: '#888' }}>
          {activePage === 'collision' ? '碰撞检测' : '道路建模'} - 该功能正在重构中
        </div>
      default:
        return <Dashboard />
    }
  }
  
  return (
    <div className="app">
      {/* 顶部导航 */}
      <header className="header">
        <div className="header-content">
          <div className="logo">
            <h1>🛣️ NeuralSite Studio</h1>
            <p>公路工程智能分析平台</p>
          </div>
        </div>
      </header>
      
      {/* 导航栏 */}
      <nav className="nav">
        {(Object.keys(pages) as Page[]).map(page => (
          <button
            key={page}
            className={`nav-item ${activePage === page ? 'active' : ''}`}
            onClick={() => setActivePage(page)}
          >
            <span className="nav-icon">{pages[page].icon}</span>
            <span className="nav-text">{pages[page].title}</span>
          </button>
        ))}
      </nav>
      
      {/* 主内容区 */}
      <main className="main">
        {renderPage()}
      </main>
    </div>
  )
}

function App() {
  return (
    <AppProvider>
      <AppContent />
    </AppProvider>
  )
}

export default App
