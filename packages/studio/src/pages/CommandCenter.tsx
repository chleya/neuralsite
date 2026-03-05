import { useState, useEffect } from 'react'
import ReactECharts from 'echarts-for-react'

// ECharts 配置类型
// eslint-disable-next-line @typescript-eslint/no-explicit-any
type EChartsOption = any

// ============== 类型定义 ==============

// 进度数据
interface ProgressData {
  planned: number      // 计划进度 %
  actual: number       // 实际进度 %
  phase: string        // 阶段名称
  startDate: string    // 开始日期
  endDate: string      // 结束日期
  status: 'normal' | 'warning' | 'delayed'  // 状态
}

// 质量问题
interface QualityIssue {
  id: string
  type: string         // 问题类型
  severity: 'low' | 'medium' | 'high' | 'critical'  // 严重程度
  status: 'pending' | 'processing' | 'resolved'   // 状态
  station: string      // 桩号位置
  createTime: string   // 创建时间
  resolveTime?: string // 解决时间
}

// 安全问题
interface SafetyIssue {
  id: string
  category: string     // 隐患类别
  riskLevel: 'low' | 'medium' | 'high' | 'critical'  // 风险等级
  location: string     // 位置
  status: 'open' | 'processing' | 'closed'  // 状态
  reportTime: string   // 报告时间
}

// 成本数据
interface CostData {
  category: string     // 类别
  budget: number       // 预算
  actual: number       // 实际
  forecast: number     // 预测
}

// ============== 模拟数据 ==============

const mockProgressData: ProgressData[] = [
  { planned: 100, actual: 100, phase: '勘察设计', startDate: '2025-01-01', endDate: '2025-03-31', status: 'normal' },
  { planned: 80, actual: 75, phase: '基础施工', startDate: '2025-04-01', endDate: '2025-08-31', status: 'warning' },
  { planned: 40, actual: 35, phase: '主体结构', startDate: '2025-09-01', endDate: '2025-12-31', status: 'normal' },
  { planned: 10, actual: 5, phase: '机电安装', startDate: '2026-01-01', endDate: '2026-03-31', status: 'delayed' },
  { planned: 0, actual: 0, phase: '竣工验收', startDate: '2026-04-01', endDate: '2026-06-30', status: 'normal' }
]

const mockQualityIssues: QualityIssue[] = [
  { id: 'Q001', type: '混凝土强度不足', severity: 'high', status: 'resolved', station: 'K12+500', createTime: '2025-06-15', resolveTime: '2025-06-20' },
  { id: 'Q002', type: '钢筋保护层偏薄', severity: 'medium', status: 'processing', station: 'K15+200', createTime: '2025-07-10' },
  { id: 'Q003', type: '防水层开裂', severity: 'low', status: 'pending', station: 'K8+800', createTime: '2025-08-05' },
  { id: 'Q004', type: '焊接质量不合格', severity: 'critical', status: 'processing', station: 'K20+300', createTime: '2025-08-12' },
  { id: 'Q005', type: '混凝土裂缝', severity: 'medium', status: 'resolved', station: 'K18+600', createTime: '2025-07-22', resolveTime: '2025-07-28' }
]

const mockSafetyIssues: SafetyIssue[] = [
  { id: 'S001', category: '临边防护', riskLevel: 'high', location: 'K15+200', status: 'open', reportTime: '2025-08-10' },
  { id: 'S002', category: '临时用电', riskLevel: 'critical', location: 'K12+500', status: 'processing', reportTime: '2025-08-08' },
  { id: 'S003', category: '脚手架', riskLevel: 'medium', location: 'K18+600', status: 'closed', reportTime: '2025-08-05' },
  { id: 'S004', category: '基坑作业', riskLevel: 'high', location: 'K20+300', status: 'open', reportTime: '2025-08-12' },
  { id: 'S005', category: '起重作业', riskLevel: 'medium', location: 'K8+800', status: 'closed', reportTime: '2025-07-28' }
]

const mockCostData: CostData[] = [
  { category: '土建工程', budget: 50000000, actual: 42000000, forecast: 48000000 },
  { category: '机电工程', budget: 20000000, actual: 8000000, forecast: 22000000 },
  { category: '装修工程', budget: 15000000, actual: 2000000, forecast: 16000000 },
  { category: '配套设施', budget: 10000000, actual: 3500000, forecast: 9500000 },
  { category: '其他费用', budget: 5000000, actual: 2800000, forecast: 5200000 }
]

// ============== 组件 ==============

// 1. 进度追踪组件
function ProgressTracker({ data }: { data: ProgressData[] }) {
  const chartOption: EChartsOption = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' }
    },
    legend: {
      data: ['计划进度', '实际进度'],
      textStyle: { color: '#888' },
      bottom: 0
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%',
      top: '10%',
      containLabel: true
    },
    xAxis: {
      type: 'value',
      max: 100,
      axisLabel: { color: '#888', formatter: '{value}%' },
      splitLine: { lineStyle: { color: '#333' } }
    },
    yAxis: {
      type: 'category',
      data: data.map(d => d.phase),
      axisLabel: { color: '#ccc' },
      axisLine: { lineStyle: { color: '#444' } }
    },
    series: [
      {
        name: '计划进度',
        type: 'bar',
        data: data.map(d => d.planned),
        itemStyle: { color: '#4a5568', borderRadius: [0, 4, 4, 0] },
        barGap: '-100%',
        barWidth: '60%'
      },
      {
        name: '实际进度',
        type: 'bar',
        data: data.map((d) => ({
          value: d.actual,
          itemStyle: {
            color: d.status === 'delayed' ? '#e53e3e' : d.status === 'warning' ? '#dd6b20' : '#00ff88',
            borderRadius: [0, 4, 4, 0]
          }
        })),
        barWidth: '60%',
        label: {
          show: true,
          position: 'right',
          formatter: '{c}%',
          color: '#fff'
        }
      }
    ]
  }

  // 滞后预警
  const delayedItems = data.filter(d => d.status === 'delayed' || d.status === 'warning')

  return (
    <div className="chart-card">
      <div className="chart-header">
        <h3>📊 进度追踪</h3>
        {delayedItems.length > 0 && (
          <span className="warning-badge">
            ⚠️ {delayedItems.length} 项滞后
          </span>
        )}
      </div>
      <ReactECharts option={chartOption} style={{ height: '280px' }} />
      
      {/* 进度表格 */}
      <div className="progress-table">
        <table>
          <thead>
            <tr>
              <th>阶段</th>
              <th>计划</th>
              <th>实际</th>
              <th>偏差</th>
              <th>状态</th>
            </tr>
          </thead>
          <tbody>
            {data.map((item, idx) => {
              const diff = item.actual - item.planned
              return (
                <tr key={idx}>
                  <td>{item.phase}</td>
                  <td>{item.planned}%</td>
                  <td>{item.actual}%</td>
                  <td className={diff < 0 ? 'negative' : 'positive'}>
                    {diff > 0 ? '+' : ''}{diff}%
                  </td>
                  <td>
                    <span className={`status-tag ${item.status}`}>
                      {item.status === 'normal' ? '正常' : item.status === 'warning' ? '预警' : '滞后'}
                    </span>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}

// 2. 质量看板组件
function QualityDashboard({ issues }: { issues: QualityIssue[] }) {
  const resolved = issues.filter(i => i.status === 'resolved').length
  const rectifyRate = issues.length > 0 ? Math.round((resolved / issues.length) * 100) : 0

  // 问题分布饼图
  const distributionOption: EChartsOption = {
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    legend: { orient: 'vertical', right: 10, top: 'center', textStyle: { color: '#888' } },
    series: [{
      type: 'pie',
      radius: ['40%', '70%'],
      center: ['35%', '50%'],
      avoidLabelOverlap: false,
      label: { show: false },
      data: [
        { value: issues.filter(i => i.severity === 'critical').length, name: '严重', itemStyle: { color: '#e53e3e' } },
        { value: issues.filter(i => i.severity === 'high').length, name: '高风险', itemStyle: { color: '#dd6b20' } },
        { value: issues.filter(i => i.severity === 'medium').length, name: '中风险', itemStyle: { color: '#d69e2e' } },
        { value: issues.filter(i => i.severity === 'low').length, name: '低风险', itemStyle: { color: '#38a169' } }
      ].filter(d => d.value > 0)
    }]
  }

  // 整改率趋势图
  const trendOption: EChartsOption = {
    tooltip: { trigger: 'axis' },
    grid: { left: '3%', right: '4%', bottom: '3%', top: '10%', containLabel: true },
    xAxis: {
      type: 'category',
      data: ['1月', '2月', '3月', '4月', '5月', '6月'],
      axisLabel: { color: '#888' },
      axisLine: { lineStyle: { color: '#444' } }
    },
    yAxis: {
      type: 'value',
      max: 100,
      axisLabel: { color: '#888', formatter: '{value}%' },
      splitLine: { lineStyle: { color: '#333' } }
    },
    series: [{
      type: 'line',
      data: [65, 72, 78, 82, 85, rectifyRate],
      smooth: true,
      areaStyle: {
        color: {
          type: 'linear',
          x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: 'rgba(0, 255, 136, 0.3)' },
            { offset: 1, color: 'rgba(0, 255, 136, 0)' }
          ]
        }
      },
      lineStyle: { color: '#00ff88', width: 2 },
      itemStyle: { color: '#00ff88' }
    }]
  }

  return (
    <div className="chart-card">
      <div className="chart-header">
        <h3>🔧 质量看板</h3>
        <span className="rectify-rate">整改率: {rectifyRate}%</span>
      </div>
      
      <div className="quality-stats">
        <div className="stat-item">
          <div className="stat-num">{issues.length}</div>
          <div className="stat-label">问题总数</div>
        </div>
        <div className="stat-item">
          <div className="stat-num warning">{issues.filter(i => i.severity === 'high' || i.severity === 'critical').length}</div>
          <div className="stat-label">高风险</div>
        </div>
        <div className="stat-item">
          <div className="stat-num success">{resolved}</div>
          <div className="stat-label">已整改</div>
        </div>
      </div>

      <div className="quality-charts">
        <ReactECharts option={distributionOption} style={{ height: '200px' }} />
        <ReactECharts option={trendOption} style={{ height: '200px' }} />
      </div>

      {/* 问题列表 */}
      <div className="issue-list">
        <h4>质量问题列表</h4>
        {issues.slice(0, 5).map(issue => (
          <div key={issue.id} className="issue-item">
            <span className={`severity ${issue.severity}`}>
              {issue.severity === 'critical' ? '🔴' : issue.severity === 'high' ? '🟠' : issue.severity === 'medium' ? '🟡' : '🟢'}
            </span>
            <span className="issue-type">{issue.type}</span>
            <span className="issue-station">{issue.station}</span>
            <span className={`status ${issue.status}`}>
              {issue.status === 'pending' ? '待处理' : issue.status === 'processing' ? '处理中' : '已解决'}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}

// 3. 安全监控组件
function SafetyMonitor({ issues }: { issues: SafetyIssue[] }) {
  const openCount = issues.filter(i => i.status === 'open').length
  
  // 隐患分布柱状图
  const distributionOption: EChartsOption = {
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: '3%', right: '4%', bottom: '3%', top: '15%', containLabel: true },
    xAxis: {
      type: 'category',
      data: [...new Set(issues.map(i => i.category))],
      axisLabel: { color: '#888', rotate: 30 },
      axisLine: { lineStyle: { color: '#444' } }
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: '#888' },
      splitLine: { lineStyle: { color: '#333' } }
    },
    series: [{
      type: 'bar',
      data: [...new Set(issues.map(i => i.category))].map(cat => ({
        value: issues.filter(i => i.category === cat).length,
        itemStyle: {
          color: issues.filter(i => i.category === cat && i.riskLevel === 'critical').length > 0 
            ? '#e53e3e' 
            : '#667eea'
        }
      })),
      barWidth: '50%',
      itemStyle: { borderRadius: [4, 4, 0, 0] }
    }]
  }

  // 风险等级分布
  const riskOption: EChartsOption = {
    tooltip: { trigger: 'item' },
    series: [{
      type: 'pie',
      radius: ['30%', '60%'],
      center: ['50%', '50%'],
      label: { 
        show: true, 
        formatter: '{b}: {c}',
        color: '#ccc',
        fontSize: 11
      },
      data: [
        { value: issues.filter(i => i.riskLevel === 'critical').length, name: '重大风险', itemStyle: { color: '#e53e3e' } },
        { value: issues.filter(i => i.riskLevel === 'high').length, name: '高风险', itemStyle: { color: '#dd6b20' } },
        { value: issues.filter(i => i.riskLevel === 'medium').length, name: '中风险', itemStyle: { color: '#d69e2e' } },
        { value: issues.filter(i => i.riskLevel === 'low').length, name: '低风险', itemStyle: { color: '#38a169' } }
      ].filter(d => d.value > 0)
    }]
  }

  return (
    <div className="chart-card">
      <div className="chart-header">
        <h3>🛡️ 安全监控</h3>
        {openCount > 0 && (
          <span className="danger-badge">
            ⚠️ {openCount} 项待处理
          </span>
        )}
      </div>

      <div className="safety-stats">
        <div className="stat-item">
          <div className="stat-num danger">{issues.length}</div>
          <div className="stat-label">隐患总数</div>
        </div>
        <div className="stat-item">
          <div className="stat-num warning">{openCount}</div>
          <div className="stat-label">待处理</div>
        </div>
        <div className="stat-item">
          <div className="stat-num">{issues.filter(i => i.status === 'closed').length}</div>
          <div className="stat-label">已闭合</div>
        </div>
      </div>

      <div className="safety-charts">
        <ReactECharts option={distributionOption} style={{ height: '200px' }} />
        <ReactECharts option={riskOption} style={{ height: '200px' }} />
      </div>

      {/* 隐患列表 */}
      <div className="hazard-list">
        <h4>安全隐患列表</h4>
        {issues.slice(0, 5).map(issue => (
          <div key={issue.id} className="hazard-item">
            <span className={`risk-level ${issue.riskLevel}`}>
              {issue.riskLevel === 'critical' ? '🔴' : issue.riskLevel === 'high' ? '🟠' : issue.riskLevel === 'medium' ? '🟡' : '🟢'}
            </span>
            <span className="hazard-category">{issue.category}</span>
            <span className="hazard-location">{issue.location}</span>
            <span className={`status ${issue.status}`}>
              {issue.status === 'open' ? '待处理' : issue.status === 'processing' ? '处理中' : '已闭合'}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}

// 4. 成本分析组件
function CostAnalysis({ data }: { data: CostData[] }) {
  const totalBudget = data.reduce((sum, d) => sum + d.budget, 0)
  const totalActual = data.reduce((sum, d) => sum + d.actual, 0)
  const totalForecast = data.reduce((sum, d) => sum + d.forecast, 0)
  const costRate = ((totalActual / totalBudget) * 100).toFixed(1)

  // 成本对比图
  const compareOption: EChartsOption = {
    tooltip: { 
      trigger: 'axis',
      formatter: (params: any) => {
        const item = params[0]
        const budget = data.find(d => d.category === item.name)?.budget || 0
        const actual = data.find(d => d.category === item.name)?.actual || 0
        const forecast = data.find(d => d.category === item.name)?.forecast || 0
        return `${item.name}<br/>预算: ¥${(budget/10000).toFixed(0)}万<br/>实际: ¥${(actual/10000).toFixed(0)}万<br/>预测: ¥${(forecast/10000).toFixed(0)}万`
      }
    },
    legend: {
      data: ['预算', '实际', '预测'],
      textStyle: { color: '#888' },
      bottom: 0
    },
    grid: { left: '3%', right: '4%', bottom: '15%', top: '10%', containLabel: true },
    xAxis: {
      type: 'category',
      data: data.map(d => d.category),
      axisLabel: { color: '#888', rotate: 20 },
      axisLine: { lineStyle: { color: '#444' } }
    },
    yAxis: {
      type: 'value',
      axisLabel: { 
        color: '#888', 
        formatter: (value: number) => `¥${(value / 10000).toFixed(0)}万`
      },
      splitLine: { lineStyle: { color: '#333' } }
    },
    series: [
      {
        name: '预算',
        type: 'bar',
        data: data.map(d => d.budget),
        itemStyle: { color: '#4a5568' }
      },
      {
        name: '实际',
        type: 'bar',
        data: data.map(d => d.actual),
        itemStyle: { color: '#667eea' }
      },
      {
        name: '预测',
        type: 'bar',
        data: data.map(d => d.forecast),
        itemStyle: { color: '#00ff88' }
      }
    ]
  }

  // 成本占比饼图
  const pieOption: EChartsOption = {
    tooltip: { 
      trigger: 'item',
      formatter: (params: any) => `${params.name}<br/>¥${(params.value/10000).toFixed(1)}万 (${params.percent}%)`
    },
    legend: { orient: 'vertical', right: 10, top: 'center', textStyle: { color: '#888' } },
    series: [{
      type: 'pie',
      radius: ['40%', '70%'],
      center: ['35%', '50%'],
      data: data.map(d => ({
        name: d.category,
        value: d.actual
      })),
      label: { show: false },
      itemStyle: {
        color: (params: any) => {
          const colors = ['#667eea', '#00ff88', '#d69e2e', '#e53e3e', '#38a169']
          return colors[params.dataIndex % colors.length]
        }
      }
    }]
  }

  return (
    <div className="chart-card">
      <div className="chart-header">
        <h3>💰 成本分析</h3>
        <span className={`cost-rate ${parseFloat(costRate) > 90 ? 'danger' : parseFloat(costRate) > 75 ? 'warning' : ''}`}>
          资金使用率: {costRate}%
        </span>
      </div>

      <div className="cost-stats">
        <div className="stat-item">
          <div className="stat-num">¥{(totalBudget / 100000000).toFixed(1)}亿</div>
          <div className="stat-label">总预算</div>
        </div>
        <div className="stat-item">
          <div className="stat-num">¥{(totalActual / 100000000).toFixed(1)}亿</div>
          <div className="stat-label">已使用</div>
        </div>
        <div className="stat-item">
          <div className="stat-num">¥{(totalForecast / 100000000).toFixed(1)}亿</div>
          <div className="stat-label">预计</div>
        </div>
      </div>

      <div className="cost-charts">
        <ReactECharts option={compareOption} style={{ height: '250px' }} />
        <ReactECharts option={pieOption} style={{ height: '250px' }} />
      </div>
    </div>
  )
}

// 5. 总览卡片组件
function SummaryCard({ 
  title, 
  value, 
  subtitle, 
  icon, 
  trend,
  trendValue 
}: { 
  title: string
  value: string | number
  subtitle?: string
  icon: string
  trend?: 'up' | 'down' | 'neutral'
  trendValue?: string
}) {
  return (
    <div className="summary-card">
      <div className="summary-icon">{icon}</div>
      <div className="summary-content">
        <div className="summary-title">{title}</div>
        <div className="summary-value">{value}</div>
        {subtitle && <div className="summary-subtitle">{subtitle}</div>}
        {trend && trendValue && (
          <div className={`summary-trend ${trend}`}>
            {trend === 'up' ? '↑' : trend === 'down' ? '↓' : '→'} {trendValue}
          </div>
        )}
      </div>
    </div>
  )
}

// ============== 主页面组件 ==============

export default function CommandCenter() {
  const [loading, setLoading] = useState(true)
  const [lastUpdate, setLastUpdate] = useState(new Date())
  const [autoRefresh, setAutoRefresh] = useState(true)
  const [refreshInterval, setRefreshInterval] = useState(30) // 秒

  // 实际项目中，这里应该调用 API 获取数据
  const [progressData] = useState<ProgressData[]>(mockProgressData)
  const [qualityIssues] = useState<QualityIssue[]>(mockQualityIssues)
  const [safetyIssues] = useState<SafetyIssue[]>(mockSafetyIssues)
  const [costData] = useState<CostData[]>(mockCostData)

  // 模拟数据加载
  useEffect(() => {
    const timer = setTimeout(() => setLoading(false), 500)
    return () => clearTimeout(timer)
  }, [])

  // 自动刷新
  useEffect(() => {
    if (!autoRefresh) return
    
    const interval = setInterval(() => {
      setLastUpdate(new Date())
      // 实际项目中这里应该调用 API 刷新数据
      console.log('Refreshing data...')
    }, refreshInterval * 1000)
    
    return () => clearInterval(interval)
  }, [autoRefresh, refreshInterval])

  // 计算总进度
  const overallProgress = Math.round(
    progressData.reduce((sum, p) => sum + p.actual, 0) / progressData.length
  )

  // 计算整改率
  const rectifyRate = qualityIssues.length > 0 
    ? Math.round((qualityIssues.filter(i => i.status === 'resolved').length / qualityIssues.length) * 100)
    : 0

  // 计算安全问题
  const openSafetyIssues = safetyIssues.filter(i => i.status === 'open').length
  const totalBudget = costData.reduce((sum, d) => sum + d.budget, 0)
  const totalSpent = costData.reduce((sum, d) => sum + d.actual, 0)
  const costRate = ((totalSpent / totalBudget) * 100).toFixed(1)

  if (loading) {
    return (
      <div className="command-center loading">
        <div className="loading-spinner">加载中...</div>
      </div>
    )
  }

  return (
    <div className="command-center">
      {/* 顶部状态栏 */}
      <div className="cc-header">
        <div className="cc-title">
          <h1>🎯 施工指挥舱</h1>
          <p>项目管理层的可视化决策界面</p>
        </div>
        
        <div className="cc-status">
          <div className="status-item">
            <span className="status-label">最后更新:</span>
            <span className="status-value">
              {lastUpdate.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
            </span>
          </div>
          <div className="status-item">
            <label className="auto-refresh-toggle">
              <input 
                type="checkbox" 
                checked={autoRefresh} 
                onChange={(e) => setAutoRefresh(e.target.checked)}
              />
              <span>自动刷新</span>
            </label>
            {autoRefresh && (
              <select 
                value={refreshInterval} 
                onChange={(e) => setRefreshInterval(Number(e.target.value))}
                className="refresh-interval"
              >
                <option value={10}>10秒</option>
                <option value={30}>30秒</option>
                <option value={60}>60秒</option>
              </select>
            )}
          </div>
        </div>
      </div>

      {/* 统计摘要 */}
      <div className="cc-summary">
        <SummaryCard 
          title="总体进度" 
          value={`${overallProgress}%`} 
          subtitle="领先/滞后"
          icon="📈"
          trend={overallProgress >= 50 ? 'up' : 'down'}
          trendValue="+2.3%"
        />
        <SummaryCard 
          title="质量问题" 
          value={qualityIssues.length}
          subtitle={`整改率 ${rectifyRate}%`}
          icon="🔧"
          trend={rectifyRate >= 70 ? 'up' : 'neutral'}
          trendValue="+5%"
        />
        <SummaryCard 
          title="安全隐患" 
          value={openSafetyIssues}
          subtitle={`共 ${safetyIssues.length} 项`}
          icon="🛡️"
          trend={openSafetyIssues === 0 ? 'up' : 'down'}
          trendValue={openSafetyIssues > 0 ? '需关注' : '无异常'}
        />
        <SummaryCard 
          title="成本使用" 
          value={`${costRate}%`}
          subtitle="预算使用率"
          icon="💰"
          trend={parseFloat(costRate) < 80 ? 'up' : 'down'}
          trendValue={parseFloat(costRate) < 80 ? '正常' : '预警'}
        />
      </div>

      {/* 图表区域 */}
      <div className="cc-charts">
        <div className="charts-row">
          <div className="chart-container half">
            <ProgressTracker data={progressData} />
          </div>
          <div className="chart-container half">
            <QualityDashboard issues={qualityIssues} />
          </div>
        </div>
        
        <div className="charts-row">
          <div className="chart-container half">
            <SafetyMonitor issues={safetyIssues} />
          </div>
          <div className="chart-container half">
            <CostAnalysis data={costData} />
          </div>
        </div>
      </div>

      <style>{`
        .command-center {
          padding: 20px;
          height: 100%;
          overflow-y: auto;
          background: #0a0a15;
        }

        .command-center.loading {
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .loading-spinner {
          color: #00ff88;
          font-size: 18px;
        }

        /* 顶部状态栏 */
        .cc-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 24px;
          background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
          padding: 20px 24px;
          border-radius: 12px;
          border: 1px solid #333;
        }

        .cc-title h1 {
          font-size: 24px;
          margin-bottom: 4px;
          color: #fff;
        }

        .cc-title p {
          font-size: 13px;
          color: #888;
        }

        .cc-status {
          display: flex;
          align-items: center;
          gap: 24px;
        }

        .status-item {
          display: flex;
          align-items: center;
          gap: 8px;
        }

        .status-label {
          font-size: 12px;
          color: #888;
        }

        .status-value {
          font-size: 13px;
          color: #00ff88;
          font-family: monospace;
        }

        .auto-refresh-toggle {
          display: flex;
          align-items: center;
          gap: 6px;
          font-size: 12px;
          color: #ccc;
          cursor: pointer;
        }

        .auto-refresh-toggle input {
          width: 16px;
          height: 16px;
          accent-color: #00ff88;
        }

        .refresh-interval {
          background: #252540;
          border: 1px solid #444;
          border-radius: 4px;
          color: #fff;
          font-size: 12px;
          padding: 4px 8px;
          margin-left: 4px;
        }

        /* 统计摘要 */
        .cc-summary {
          display: grid;
          grid-template-columns: repeat(4, 1fr);
          gap: 16px;
          margin-bottom: 24px;
        }

        .summary-card {
          background: #1a1a2e;
          border-radius: 12px;
          padding: 20px;
          display: flex;
          align-items: center;
          gap: 16px;
          border: 1px solid #333;
          transition: transform 0.2s, box-shadow 0.2s;
        }

        .summary-card:hover {
          transform: translateY(-2px);
          box-shadow: 0 8px 25px rgba(0, 255, 136, 0.1);
        }

        .summary-icon {
          font-size: 36px;
        }

        .summary-title {
          font-size: 12px;
          color: #888;
          margin-bottom: 4px;
        }

        .summary-value {
          font-size: 28px;
          font-weight: 700;
          color: #00ff88;
        }

        .summary-subtitle {
          font-size: 11px;
          color: #666;
          margin-top: 2px;
        }

        .summary-trend {
          font-size: 11px;
          margin-top: 4px;
        }

        .summary-trend.up { color: #00ff88; }
        .summary-trend.down { color: #e53e3e; }
        .summary-trend.neutral { color: #d69e2e; }

        /* 图表区域 */
        .cc-charts {
          display: flex;
          flex-direction: column;
          gap: 20px;
        }

        .charts-row {
          display: flex;
          gap: 20px;
        }

        .chart-container {
          flex: 1;
        }

        .chart-container.half {
          flex: 1;
        }

        /* 图表卡片通用样式 */
        .chart-card {
          background: #1a1a2e;
          border-radius: 12px;
          padding: 20px;
          border: 1px solid #333;
          height: 100%;
        }

        .chart-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 16px;
        }

        .chart-header h3 {
          font-size: 16px;
          color: #fff;
        }

        .warning-badge, .danger-badge, .rectify-rate, .cost-rate {
          font-size: 12px;
          padding: 4px 10px;
          border-radius: 12px;
          font-weight: 500;
        }

        .warning-badge {
          background: rgba(214, 158, 46, 0.2);
          color: #d69e2e;
        }

        .danger-badge {
          background: rgba(229, 62, 62, 0.2);
          color: #e53e3e;
        }

        .rectify-rate, .cost-rate {
          background: rgba(0, 255, 136, 0.15);
          color: #00ff88;
        }

        .cost-rate.warning {
          background: rgba(214, 158, 46, 0.2);
          color: #d69e2e;
        }

        .cost-rate.danger {
          background: rgba(229, 62, 62, 0.2);
          color: #e53e3e;
        }

        /* 统计卡片 */
        .quality-stats, .safety-stats, .cost-stats {
          display: flex;
          gap: 16px;
          margin-bottom: 16px;
        }

        .quality-stats .stat-item, .safety-stats .stat-item, .cost-stats .stat-item {
          flex: 1;
          text-align: center;
          padding: 12px;
          background: #252540;
          border-radius: 8px;
        }

        .quality-stats .stat-num, .safety-stats .stat-num, .cost-stats .stat-num {
          font-size: 24px;
          font-weight: 700;
          color: #fff;
        }

        .quality-stats .stat-num.warning, .safety-stats .stat-num.warning, .cost-stats .stat-num.warning {
          color: #d69e2e;
        }

        .quality-stats .stat-num.success {
          color: #00ff88;
        }

        .quality-stats .stat-num.danger, .safety-stats .stat-num.danger {
          color: #e53e3e;
        }

        .quality-stats .stat-label, .safety-stats .stat-label, .cost-stats .stat-label {
          font-size: 11px;
          color: #888;
          margin-top: 4px;
        }

        /* 图表区域 */
        .quality-charts, .safety-charts, .cost-charts {
          display: flex;
          gap: 16px;
          margin-bottom: 16px;
        }

        .quality-charts > div, .safety-charts > div, .cost-charts > div {
          flex: 1;
        }

        /* 进度表格 */
        .progress-table {
          margin-top: 16px;
        }

        .progress-table table {
          width: 100%;
          border-collapse: collapse;
          font-size: 12px;
        }

        .progress-table th, .progress-table td {
          padding: 10px 8px;
          text-align: left;
          border-bottom: 1px solid #333;
        }

        .progress-table th {
          color: #888;
          font-weight: 500;
          background: #252540;
        }

        .progress-table td {
          color: #ccc;
        }

        .progress-table td.positive {
          color: #00ff88;
        }

        .progress-table td.negative {
          color: #e53e3e;
        }

        .status-tag {
          display: inline-block;
          padding: 2px 8px;
          border-radius: 10px;
          font-size: 11px;
          font-weight: 500;
        }

        .status-tag.normal {
          background: rgba(0, 255, 136, 0.15);
          color: #00ff88;
        }

        .status-tag.warning {
          background: rgba(214, 158, 46, 0.2);
          color: #d69e2e;
        }

        .status-tag.delayed {
          background: rgba(229, 62, 62, 0.2);
          color: #e53e3e;
        }

        .status-tag.pending {
          background: rgba(128, 128, 128, 0.2);
          color: #888;
        }

        .status-tag.processing {
          background: rgba(102, 126, 234, 0.2);
          color: #667eea;
        }

        .status-tag.resolved, .status-tag.closed {
          background: rgba(0, 255, 136, 0.15);
          color: #00ff88;
        }

        /* 问题列表 */
        .issue-list, .hazard-list {
          margin-top: 16px;
        }

        .issue-list h4, .hazard-list h4 {
          font-size: 13px;
          color: #888;
          margin-bottom: 12px;
        }

        .issue-item, .hazard-item {
          display: flex;
          align-items: center;
          padding: 10px 12px;
          background: #252540;
          border-radius: 6px;
          margin-bottom: 8px;
          font-size: 12px;
        }

        .issue-item .severity, .hazard-item .risk-level {
          margin-right: 10px;
        }

        .issue-item .issue-type, .hazard-item .hazard-category {
          flex: 1;
          color: #ccc;
        }

        .issue-item .issue-station, .hazard-item .hazard-location {
          color: #00ff88;
          margin: 0 16px;
          font-family: monospace;
        }

        /* 响应式 */
        @media (max-width: 1400px) {
          .cc-summary {
            grid-template-columns: repeat(2, 1fr);
          }
        }

        @media (max-width: 1200px) {
          .charts-row {
            flex-direction: column;
          }
        }

        @media (max-width: 768px) {
          .cc-header {
            flex-direction: column;
            gap: 16px;
          }

          .cc-summary {
            grid-template-columns: 1fr;
          }

          .quality-charts, .safety-charts {
            flex-direction: column;
          }
        }
      `}</style>
    </div>
  )
}
