import { useState, useEffect } from 'react'
import './index.css'

// 页面组件
import VersionCompare from './pages/VersionCompare'
import PhotoAIAnnotator from './pages/PhotoAIAnnotator'

// 正确的导入
import { useUserStore } from './stores/userStore'
import { useAppStore } from './stores/appStore'

// 3D组件
import ModelPreview from './components/three/ModelPreviewSimple'
import CollisionViewer from './components/three/CollisionViewerSimple'
import Scheduler3D from './components/three/Scheduler3DSimple'
import Route3DViewer from './components/three/Route3DSimple'

type Page = 
  | 'login' 
  | 'dashboard' 
  | 'project-list'
  | 'project-form'
  | 'project-detail'
  | 'route-list'
  | 'route-form'
  | 'route-detail'
  | 'station-query'
  | 'station-entry'
  | 'station-list'
  | 'photo'
  | 'photo-list'
  | 'photo-upload'
  | 'photo-ai-annotator'
  | 'model' 
  | 'knowledge'
  | 'collision'
  | 'road'
  | 'command'
  | 'route3d'
  | 'cross-section-entry'
  | 'cross-section-list'
  | 'data-import'
  | 'version-compare'

const pages: Record<Page, { title: string; icon: string }> = {
  'login': { title: '登录', icon: '[L]' },
  'dashboard': { title: '仪表盘', icon: '[D]' },
  'project-list': { title: '项目列表', icon: '[P]' },
  'project-form': { title: '新建项目', icon: '[+P]' },
  'project-detail': { title: '项目详情', icon: '[PD]' },
  'route-list': { title: '路线列表', icon: '[R]' },
  'route-form': { title: '新建路线', icon: '[+R]' },
  'route-detail': { title: '路线详情', icon: '[RD]' },
  'station-query': { title: '桩号查询', icon: '[Q]' },
  'station-entry': { title: '桩号录入', icon: '[+S]' },
  'station-list': { title: '桩号列表', icon: '[SL]' },
  'photo': { title: '照片浏览', icon: '[Ph]' },
  'photo-list': { title: '照片列表', icon: '[PL]' },
  'photo-upload': { title: '照片上传', icon: '[+Ph]' },
  'photo-ai-annotator': { title: 'AI标注', icon: '[AI]' },
  'model': { title: '三维模型', icon: '[M]' },
  'knowledge': { title: '知识库', icon: '[K]' },
  'collision': { title: '碰撞检测', icon: '[C]' },
  'road': { title: '道路建模', icon: '[RD]' },
  'command': { title: '指挥舱', icon: '[Cmd]' },
  'route3d': { title: '路线三维', icon: '[R3]' },
  'cross-section-entry': { title: '横断面录入', icon: '[X]' },
  'cross-section-list': { title: '横断面列表', icon: '[XL]' },
  'data-import': { title: '数据导入', icon: '[I]' },
  'version-compare': { title: '版本对比', icon: '[VC]' },
}

function App() {
  const [activePage, setActivePage] = useState<Page>('dashboard')
  const [pageProps, setPageProps] = useState<any>({})
  const { user, isAuthenticated, logout, token } = useUserStore()
  const appStore = useAppStore()
  
  // 检查登录状态
  useEffect(() => {
    if (!isAuthenticated && !token && activePage !== 'login') {
      setActivePage('login')
    }
  }, [isAuthenticated, token])

  const handleLogin = () => {
    setActivePage('dashboard')
  }

  const handleLogout = async () => {
    await logout()
    setActivePage('login')
  }

  const navigate = (page: Page, props?: any) => {
    if (props) setPageProps(props)
    setActivePage(page)
  }

  const renderPage = () => {
    switch (activePage) {
      case 'login':
        return <LoginPage onLogin={handleLogin} />
      case 'dashboard':
        return <Dashboard onNavigate={navigate} />
      case 'project-list':
        return <ProjectListPage onNavigate={navigate} {...pageProps} />
      case 'project-form':
        return <ProjectFormPage onNavigate={navigate} {...pageProps} />
      case 'project-detail':
        return <ProjectDetailPage onNavigate={navigate} {...pageProps} />
      case 'route-list':
        return <RouteListPage onNavigate={navigate} {...pageProps} />
      case 'route-form':
        return <RouteFormPage onNavigate={navigate} {...pageProps} />
      case 'route-detail':
        return <RouteDetailPage onNavigate={navigate} {...pageProps} />
      case 'station-query':
        return <StationQuery />
      case 'station-entry':
        return <StationEntry onNavigate={navigate} {...pageProps} />
      case 'station-list':
        return <StationList onNavigate={navigate} {...pageProps} />
      case 'photo':
        return <PhotoBrowser />
      case 'photo-list':
        return <PhotoList onNavigate={navigate} {...pageProps} />
      case 'photo-upload':
        return <PhotoUpload onNavigate={navigate} {...pageProps} />
      case 'photo-ai-annotator':
        return <PhotoAIAnnotator onNavigate={navigate} {...pageProps} />
      case 'model':
        return <ModelPreviewPage />
      case 'knowledge':
        return <KnowledgeQA />
      case 'collision':
        return <CollisionViewerPage />
      case 'road':
        return <Route3DPage />
      case 'command':
        return <CommandCenter />
      case 'route3d':
        return <Route3DPage />
      case 'cross-section-entry':
        return <CrossSectionEntry onNavigate={navigate} {...pageProps} />
      case 'cross-section-list':
        return <CrossSectionList onNavigate={navigate} {...pageProps} />
      case 'data-import':
        return <DataImport onNavigate={navigate} {...pageProps} />
      case 'version-compare':
        return <VersionCompare />
      default:
        return <Dashboard onNavigate={navigate} />
    }
  }

  // 登录页
  if (activePage === 'login') {
    return (
      <div style={{ 
        minHeight: '100vh', 
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center'
      }}>
        <LoginPage onLogin={handleLogin} />
      </div>
    )
  }

  return (
    <div className="app">
      <header style={{ 
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', 
        padding: '16px 24px' 
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h1 style={{ margin: 0, fontSize: '22px' }}>NeuralSite Studio</h1>
            <p style={{ margin: 0, fontSize: '12px', opacity: 0.9 }}>公路工程智能分析平台</p>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            {user && <span>{user.username}</span>}
            <button onClick={handleLogout} style={{
              padding: '8px 16px',
              background: 'rgba(255,255,255,0.2)',
              border: 'none',
              borderRadius: '4px',
              color: 'white',
              cursor: 'pointer'
            }}>
              退出
            </button>
          </div>
        </div>
      </header>
      
      <nav style={{ 
        display: 'flex', 
        background: '#1a1a2e', 
        borderBottom: '1px solid #333',
        padding: '0 16px',
        overflowX: 'auto'
      }}>
        {(Object.keys(pages) as Page[]).map(page => (
          <button
            key={page}
            onClick={() => setActivePage(page)}
            style={{
              marginRight: '4px',
              padding: '10px 14px',
              background: activePage === page ? '#667eea' : 'transparent',
              color: activePage === page ? 'white' : '#aaa',
              border: 'none',
              borderRadius: '4px 4px 0 0',
              cursor: 'pointer',
              whiteSpace: 'nowrap',
              fontSize: '13px'
            }}
          >
            {pages[page].icon} {pages[page].title}
          </button>
        ))}
      </nav>
      
      <main style={{ flex: 1, overflow: 'auto', background: '#0f0f1a' }}>
        {renderPage()}
      </main>
    </div>
  )
}

// ===== 登录页面 =====
function LoginPage({ onLogin }: { onLogin: () => void }) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const { login } = useUserStore()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    
    try {
      await login({ username, password })
      onLogin()
    } catch (err: any) {
      setError(err?.message || '用户名或密码错误')
    } finally {
      setLoading(false)
    }
  }

  // 演示登录 - 不需要后端
  const handleDemoLogin = () => {
    // 直接设置用户状态，无需API
    const demoUser = {
      user_id: 'demo-001',
      username: 'demo',
      real_name: '演示用户',
      role: 'admin' as const,
      is_active: true,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    }
    localStorage.setItem('access_token', 'demo-token')
    // 直接修改store状态
    useUserStore.setState({ 
      user: demoUser, 
      token: 'demo-token', 
      isAuthenticated: true 
    })
    onLogin()
  }

  return (
    <div style={{ 
      background: 'white', 
      padding: '40px', 
      borderRadius: '12px',
      width: '100%',
      maxWidth: '400px',
      boxShadow: '0 20px 60px rgba(0,0,0,0.3)'
    }}>
      <div style={{ textAlign: 'center', marginBottom: '30px' }}>
        <svg width="60" height="60" viewBox="0 0 48 48" fill="none" style={{ margin: '0 auto' }}>
          <circle cx="24" cy="24" r="20" stroke="#4f8cff" strokeWidth="2" />
          <circle cx="24" cy="24" r="8" fill="#4f8cff" />
          <circle cx="24" cy="24" r="3" fill="#0f0f1a" />
        </svg>
        <h1 style={{ marginTop: '16px', color: '#333' }}>NeuralSite Studio</h1>
        <p style={{ color: '#666' }}>登录以继续</p>
      </div>
      
      <form onSubmit={handleSubmit}>
        {error && (
          <div style={{ 
            background: '#fee', 
            color: '#c00', 
            padding: '10px', 
            borderRadius: '4px', 
            marginBottom: '16px' 
          }}>
            {error}
          </div>
        )}
        
        <input
          type="text"
          placeholder="用户名"
          value={username}
          onChange={e => setUsername(e.target.value)}
          style={{
            width: '100%',
            padding: '12px',
            marginBottom: '12px',
            border: '1px solid #ddd',
            borderRadius: '6px',
            boxSizing: 'border-box'
          }}
        />
        
        <input
          type="password"
          placeholder="密码"
          value={password}
          onChange={e => setPassword(e.target.value)}
          style={{
            width: '100%',
            padding: '12px',
            marginBottom: '20px',
            border: '1px solid #ddd',
            borderRadius: '6px',
            boxSizing: 'border-box'
          }}
        />
        
        <button
          type="submit"
          disabled={loading}
          style={{
            width: '100%',
            padding: '12px',
            background: loading ? '#999' : '#667eea',
            color: 'white',
            border: 'none',
            borderRadius: '6px',
            cursor: loading ? 'not-allowed' : 'pointer',
            fontSize: '16px'
          }}
        >
          {loading ? '登录中...' : '登录'}
        </button>
        
        <button
          type="button"
          onClick={handleDemoLogin}
          style={{
            width: '100%',
            padding: '12px',
            background: '#28a745',
            color: 'white',
            border: 'none',
            borderRadius: '6px',
            cursor: 'pointer',
            fontSize: '16px',
            marginTop: '10px'
          }}
        >
          演示登录
        </button>
      </form>
    </div>
  )
}

// ===== 仪表盘 =====
function Dashboard({ onNavigate }: { onNavigate: (p: Page) => void }) {
  const { user } = useUserStore()
  const { selectedProject } = useAppStore()
  const [stats, setStats] = useState({ projects: 0, routes: 0, stations: 0, photos: 0 })

  useEffect(() => {
    // 模拟加载统计数据
    setStats({ projects: 0, routes: 0, stations: 0, photos: 0 })
  }, [selectedProject])

  return (
    <div style={{ padding: '20px' }}>
      <h1>欢迎 {user?.username || '用户'}!</h1>
      
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px', marginTop: '20px' }}>
        <StatCard title="项目数" value={stats.projects} icon="📁" onClick={() => onNavigate('project-list')} />
        <StatCard title="路线数" value={stats.routes} icon="🛣️" onClick={() => onNavigate('route-list')} />
        <StatCard title="桩点数" value={stats.stations} icon="📍" onClick={() => onNavigate('station-list')} />
        <StatCard title="照片数" value={stats.photos} icon="📷" onClick={() => onNavigate('photo-list')} />
      </div>

      <h2 style={{ marginTop: '30px' }}>快速操作</h2>
      <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', marginTop: '12px' }}>
        <QuickAction label="新建项目" onClick={() => onNavigate('project-form')} />
        <QuickAction label="新建路线" onClick={() => onNavigate('route-form')} />
        <QuickAction label="录入桩号" onClick={() => onNavigate('station-entry')} />
        <QuickAction label="上传照片" onClick={() => onNavigate('photo-upload')} />
        <QuickAction label="碰撞检测" onClick={() => onNavigate('collision')} />
        <QuickAction label="知识库" onClick={() => onNavigate('knowledge')} />
      </div>
    </div>
  )
}

function StatCard({ title, value, icon, onClick }: { title: string; value: number; icon: string; onClick?: () => void }) {
  return (
    <div 
      onClick={onClick}
      style={{ 
        background: '#1a1a2e', 
        padding: '20px', 
        borderRadius: '8px',
        cursor: onClick ? 'pointer' : 'default',
        transition: 'transform 0.2s'
      }}
    >
      <span style={{ fontSize: '24px' }}>{icon}</span>
      <h3 style={{ color: '#888', margin: '10px 0' }}>{title}</h3>
      <p style={{ fontSize: '32px', margin: 0 }}>{value}</p>
    </div>
  )
}

function QuickAction({ label, onClick }: { label: string; onClick: () => void }) {
  return (
    <button 
      onClick={onClick}
      style={{
        padding: '12px 24px',
        background: '#1a1a2e',
        color: 'white',
        border: '1px solid #333',
        borderRadius: '6px',
        cursor: 'pointer'
      }}
    >
      {label}
    </button>
  )
}

// ===== 项目页面 =====
function ProjectListPage({ onNavigate }: { onNavigate: (p: Page, props?: any) => void }) {
  const [projects, setProjects] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const { selectedProject, setSelectedProject } = useAppStore()

  useEffect(() => {
    loadProjects()
  }, [])

  const loadProjects = async () => {
    setLoading(true)
    try {
      // 这里可以调用API
      setProjects([])
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ padding: '20px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1>项目列表</h1>
        <button onClick={() => onNavigate('project-form')} style={btnStyle}>+ 新建项目</button>
      </div>
      
      {loading ? (
        <p>加载中...</p>
      ) : projects.length === 0 ? (
        <div style={{ textAlign: 'center', marginTop: '40px', color: '#888' }}>
          <p>暂无项目</p>
          <button onClick={() => onNavigate('project-form')} style={btnStyle}>创建第一个项目</button>
        </div>
      ) : (
        <div style={{ display: 'grid', gap: '12px', marginTop: '20px' }}>
          {projects.map(p => (
            <div key={p.id} style={cardStyle} onClick={() => { setSelectedProject(p); onNavigate('project-detail', { projectId: p.id }) }}>
              <h3>{p.name}</h3>
              <p style={{ color: '#888' }}>{p.description}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function ProjectFormPage({ onNavigate }: { onNavigate: (p: Page, props?: any) => void }) {
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      // 调用API创建项目
      onNavigate('project-list')
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ padding: '20px', maxWidth: '600px' }}>
      <h1>新建项目</h1>
      <form onSubmit={handleSubmit} style={{ marginTop: '20px' }}>
        <div style={{ marginBottom: '16px' }}>
          <label style={{ display: 'block', marginBottom: '8px' }}>项目名称</label>
          <input value={name} onChange={e => setName(e.target.value)} style={inputStyle} required />
        </div>
        <div style={{ marginBottom: '16px' }}>
          <label style={{ display: 'block', marginBottom: '8px' }}>描述</label>
          <textarea value={description} onChange={e => setDescription(e.target.value)} style={{ ...inputStyle, minHeight: '100px' }} />
        </div>
        <div style={{ display: 'flex', gap: '12px' }}>
          <button type="submit" disabled={loading} style={btnStyle}>{loading ? '保存中...' : '保存'}</button>
          <button type="button" onClick={() => onNavigate('project-list')} style={{ ...btnStyle, background: '#666' }}>取消</button>
        </div>
      </form>
    </div>
  )
}

function ProjectDetailPage({ onNavigate }: { onNavigate: (p: Page, props?: any) => void }) {
  const { selectedProject } = useAppStore()

  if (!selectedProject) {
    return <div style={{ padding: '20px' }}><p>请先选择项目</p><button onClick={() => onNavigate('project-list')}>返回</button></div>
  }

  return (
    <div style={{ padding: '20px' }}>
      <h1>{selectedProject.name}</h1>
      <p style={{ color: '#888' }}>{selectedProject.description}</p>
      
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px', marginTop: '20px' }}>
        <button style={cardStyle} onClick={() => onNavigate('route-list')}>🛣️ 路线管理</button>
        <button style={cardStyle} onClick={() => onNavigate('station-list')}>📍 桩号管理</button>
        <button style={cardStyle} onClick={() => onNavigate('photo-list')}>📷 照片管理</button>
      </div>
    </div>
  )
}

// ===== 路线页面 =====
function RouteListPage({ onNavigate }: { onNavigate: (p: Page, props?: any) => void }) {
  const { selectedProject } = useAppStore()
  const [routes, setRoutes] = useState<any[]>([])

  return (
    <div style={{ padding: '20px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
        <h1>路线列表 {selectedProject ? `- ${selectedProject.name}` : ''}</h1>
        <button onClick={() => onNavigate('route-form')} style={btnStyle}>+ 新建路线</button>
      </div>
      {routes.length === 0 ? (
        <p style={{ color: '#888', marginTop: '20px' }}>暂无路线</p>
      ) : (
        <div style={{ marginTop: '20px' }}>{routes.map(r => <div key={r.id} style={cardStyle}>{r.name}</div>)}</div>
      )}
    </div>
  )
}

function RouteFormPage({ onNavigate }: { onNavigate: (p: Page, props?: any) => void }) {
  const [name, setName] = useState('')
  return (
    <div style={{ padding: '20px' }}>
      <h1>新建路线</h1>
      <input value={name} onChange={e => setName(e.target.value)} placeholder="路线名称" style={inputStyle} />
      <div style={{ marginTop: '16px' }}>
        <button onClick={() => onNavigate('route-list')} style={btnStyle}>保存</button>
      </div>
    </div>
  )
}

function RouteDetailPage({ onNavigate }: { onNavigate: (p: Page, props?: any) => void }) {
  return <div style={{ padding: '20px' }}><h1>路线详情</h1></div>
}

// ===== 桩号页面 =====
function StationQuery() {
  const [query, setQuery] = useState('')
  return (
    <div style={{ padding: '20px' }}>
      <h1>桩号查询</h1>
      <input value={query} onChange={e => setQuery(e.target.value)} placeholder="输入桩号" style={inputStyle} />
    </div>
  )
}

function StationEntry({ onNavigate }: { onNavigate: (p: Page, props?: any) => void }) {
  return (
    <div style={{ padding: '20px' }}>
      <h1>桩号录入</h1>
      <p style={{ color: '#888' }}>录入桩号信息</p>
    </div>
  )
}

function StationList({ onNavigate }: { onNavigate: (p: Page, props?: any) => void }) {
  return (
    <div style={{ padding: '20px' }}>
      <h1>桩号列表</h1>
    </div>
  )
}

// ===== 照片页面 =====
function PhotoBrowser() {
  return <div style={{ padding: '20px' }}><h1>照片浏览</h1></div>
}

function PhotoList({ onNavigate }: { onNavigate: (p: Page, props?: any) => void }) {
  return <div style={{ padding: '20px' }}><h1>照片列表</h1></div>
}

function PhotoUpload({ onNavigate }: { onNavigate: (p: Page, props?: any) => void }) {
  return <div style={{ padding: '20px' }}><h1>照片上传</h1></div>
}

// ===== 3D/模型页面 =====
function ModelPreviewPage() {
  return <ModelPreview3D />
}

function CollisionViewerPage() {
  return <CollisionViewer3D />
}

function Route3DPage() {
  return <Route3DViewer />
}

// 3D组件包装器（避免命名冲突）
function ModelPreview3D() {
  // @ts-ignore
  return <ModelPreview />
}

function CollisionViewer3D() {
  // @ts-ignore
  return <CollisionViewer />
}

function Scheduler3D3D() {
  // @ts-ignore
  return <Scheduler3D />
}

// ===== 其他页面 =====
function KnowledgeQA() {
  const [query, setQuery] = useState('')
  const [answer, setAnswer] = useState('')
  
  const handleAsk = () => {
    setAnswer('AI功能开发中...')
  }

  return (
    <div style={{ padding: '20px' }}>
      <h1>知识库问答</h1>
      <div style={{ marginTop: '20px' }}>
        <input 
          value={query} 
          onChange={e => setQuery(e.target.value)} 
          placeholder="输入问题..." 
          style={{ ...inputStyle, marginBottom: '12px' }}
        />
        <button onClick={handleAsk} style={btnStyle}>提问</button>
        {answer && <div style={{ marginTop: '20px', padding: '16px', background: '#1a1a2e', borderRadius: '8px' }}>{answer}</div>}
      </div>
    </div>
  )
}

function CommandCenter() {
  return (
    <div style={{ padding: '20px' }}>
      <h1>指挥舱</h1>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '16px', marginTop: '20px' }}>
        <div style={cardStyle}><h3>在线设备</h3><p style={{ fontSize: '24px' }}>0</p></div>
        <div style={cardStyle}><h3>待处理任务</h3><p style={{ fontSize: '24px' }}>0</p></div>
        <div style={cardStyle}><h3>告警数量</h3><p style={{ fontSize: '24px' }}>0</p></div>
        <div style={cardStyle}><h3>今日巡检</h3><p style={{ fontSize: '24px' }}>0</p></div>
      </div>
    </div>
  )
}

function CrossSectionEntry({ onNavigate }: { onNavigate: (p: Page, props?: any) => void }) {
  return <div style={{ padding: '20px' }}><h1>横断面录入</h1></div>
}

function CrossSectionList({ onNavigate }: { onNavigate: (p: Page, props?: any) => void }) {
  return <div style={{ padding: '20px' }}><h1>横断面列表</h1></div>
}

function DataImport({ onNavigate }: { onNavigate: (p: Page, props?: any) => void }) {
  return (
    <div style={{ padding: '20px' }}>
      <h1>数据导入</h1>
      <div style={{ marginTop: '20px', border: '2px dashed #333', padding: '40px', textAlign: 'center', borderRadius: '8px' }}>
        <p style={{ color: '#888' }}>拖拽文件到此处或点击选择</p>
        <input type="file" style={{ marginTop: '12px' }} />
      </div>
    </div>
  )
}

// ===== 样式 =====
const btnStyle = {
  padding: '10px 20px',
  background: '#667eea',
  color: 'white',
  border: 'none',
  borderRadius: '6px',
  cursor: 'pointer' as const
}

const inputStyle = {
  width: '100%',
  padding: '12px',
  background: '#1a1a2e',
  border: '1px solid #333',
  borderRadius: '6px',
  color: 'white',
  boxSizing: 'border-box' as const
}

const cardStyle = {
  background: '#1a1a2e',
  padding: '16px',
  borderRadius: '8px',
  cursor: 'pointer' as const
}

export default App
