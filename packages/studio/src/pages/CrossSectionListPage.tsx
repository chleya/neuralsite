import { useState, useEffect, useCallback } from 'react';
import { useApp } from '../context/AppContext';
import { CrossSection, CrossSectionListParams } from '../api/types';
import { crossSectionsApi } from '../api/endpoints';
import { ArrowLeft, Search, Edit, Trash2, Download, ChevronLeft, ChevronRight, Eye } from 'lucide-react';

interface CrossSectionListPageProps {
  onNavigate?: (page: string, params?: Record<string, unknown>) => void;
}

// 模拟数据
const mockCrossSections: CrossSection[] = [
  {
    cs_id: '1',
    project_id: 'demo',
    route_id: 'demo',
    station: 0,
    station_display: 'K0+000',
    cs_type: 'full',
    points: [
      { offset: -20, elevation: 105 },
      { offset: -10, elevation: 102 },
      { offset: 0, elevation: 100 },
      { offset: 10, elevation: 101 },
      { offset: 20, elevation: 103 },
    ],
    sync_status: 'synced',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    cs_id: '2',
    project_id: 'demo',
    route_id: 'demo',
    station: 500,
    station_display: 'K0+500',
    cs_type: 'full',
    points: [
      { offset: -20, elevation: 115 },
      { offset: -10, elevation: 112 },
      { offset: 0, elevation: 110 },
      { offset: 10, elevation: 111 },
      { offset: 20, elevation: 113 },
    ],
    sync_status: 'synced',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    cs_id: '3',
    project_id: 'demo',
    route_id: 'demo',
    station: 1000,
    station_display: 'K1+000',
    cs_type: 'center',
    points: [
      { offset: -3, elevation: 108 },
      { offset: 0, elevation: 107.5 },
      { offset: 3, elevation: 107 },
    ],
    sync_status: 'synced',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
];

export default function CrossSectionListPage({ onNavigate }: CrossSectionListPageProps) {
  const { state } = useApp();
  const [crossSections, setCrossSections] = useState<CrossSection[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [limit] = useState(10);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [viewMode, setViewMode] = useState<'table' | 'detail'>('table');
  const [selectedSection, setSelectedSection] = useState<CrossSection | null>(null);

  // 加载数据
  const loadCrossSections = useCallback(async () => {
    setLoading(true);
    try {
      const params: CrossSectionListParams = {
        project_id: state.selectedProject?.project_id || 'demo',
        route_id: state.routeId || 'demo',
        page,
        limit,
        search: search || undefined,
      };

      await new Promise(resolve => setTimeout(resolve, 300));
      
      let filtered = [...mockCrossSections];
      if (search) {
        filtered = filtered.filter(cs => 
          cs.station_display.toLowerCase().includes(search.toLowerCase()) ||
          cs.cs_type.toLowerCase().includes(search.toLowerCase())
        );
      }
      
      setCrossSections(filtered);
      setTotal(filtered.length);
    } catch (error) {
      console.error('Failed to load cross sections:', error);
    } finally {
      setLoading(false);
    }
  }, [page, search, state.selectedProject?.project_id, state.routeId]);

  useEffect(() => {
    loadCrossSections();
  }, [loadCrossSections]);

  // 处理搜索
  const handleSearch = useCallback((e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    loadCrossSections();
  }, [loadCrossSections]);

  // 处理单选
  const handleSelect = useCallback((id: string) => {
    setSelectedIds(prev => 
      prev.includes(id) 
        ? prev.filter(i => i !== id)
        : [...prev, id]
    );
  }, []);

  // 处理删除
  const handleDelete = useCallback(async (id: string) => {
    if (!confirm('确定要删除这条横断面记录吗？')) return;
    
    try {
      await new Promise(resolve => setTimeout(resolve, 300));
      setCrossSections(prev => prev.filter(cs => cs.cs_id !== id));
    } catch (error) {
      console.error('Failed to delete cross section:', error);
    }
  }, []);

  // 查看详情
  const handleViewDetail = useCallback((section: CrossSection) => {
    setSelectedSection(section);
    setViewMode('detail');
  }, []);

  // 导出数据
  const handleExport = useCallback(() => {
    const csvContent = [
      ['断面ID', '桩号', '类型', '点数', '同步状态'].join(','),
      ...crossSections.map(cs => [
        cs.cs_id,
        cs.station_display,
        cs.cs_type,
        cs.points.length,
        cs.sync_status,
      ].join(','))
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `cross_sections_${new Date().toISOString().split('T')[0]}.csv`;
    link.click();
    URL.revokeObjectURL(url);
  }, [crossSections]);

  const totalPages = Math.ceil(total / limit);

  const csTypeLabels: Record<string, string> = {
    full: '全断面',
    center: '中桩',
    left: '左半',
    right: '右半',
  };

  // 渲染详情模式
  if (viewMode === 'detail' && selectedSection) {
    return (
      <div className="cross-section-detail-page">
        <div className="page-header">
          <button className="btn-back" onClick={() => setViewMode('table')}>
            <ArrowLeft size={20} />
            返回列表
          </button>
          <h1>📐 断面详情 - {selectedSection.station_display}</h1>
        </div>

        <div className="detail-content">
          <div className="detail-section">
            <h3>基本信息</h3>
            <div className="detail-grid">
              <div className="detail-item">
                <span className="label">桩号</span>
                <span className="value">{selectedSection.station_display}</span>
              </div>
              <div className="detail-item">
                <span className="label">类型</span>
                <span className="value">{csTypeLabels[selectedSection.cs_type]}</span>
              </div>
              <div className="detail-item">
                <span className="label">点数</span>
                <span className="value">{selectedSection.points.length}</span>
              </div>
              <div className="detail-item">
                <span className="label">创建时间</span>
                <span className="value">{new Date(selectedSection.created_at).toLocaleString()}</span>
              </div>
            </div>
          </div>

          <div className="detail-section">
            <h3>断面点数据</h3>
            <table className="points-table">
              <thead>
                <tr>
                  <th>#</th>
                  <th>偏移量(m)</th>
                  <th>高程(m)</th>
                  <th>描述</th>
                </tr>
              </thead>
              <tbody>
                {selectedSection.points.map((point, idx) => (
                  <tr key={idx}>
                    <td>{idx + 1}</td>
                    <td>{point.offset.toFixed(2)}</td>
                    <td>{point.elevation.toFixed(3)}</td>
                    <td>{point.description || '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* 简单的断面图示 */}
          <div className="detail-section">
            <h3>断面示意</h3>
            <div className="section-diagram">
              <div className="diagram-container">
                {selectedSection.points.map((point, idx) => (
                  <div
                    key={idx}
                    className="diagram-point"
                    style={{
                      left: `${((point.offset + 25) / 50) * 100}%`,
                      bottom: `${((point.elevation - Math.min(...selectedSection.points.map(p => p.elevation))) / 
                        (Math.max(...selectedSection.points.map(p => p.elevation)) - 
                        Math.min(...selectedSection.points.map(p => p.elevation)) || 1)) * 80 + 10}%`,
                    }}
                    title={`偏移: ${point.offset}m, 高程: ${point.elevation}m`}
                  />
                ))}
                <div className="diagram-center" style={{ left: '50%' }} />
              </div>
              <div className="diagram-labels">
                <span>左←</span>
                <span>桩号: {selectedSection.station_display}</span>
                <span>→右</span>
              </div>
            </div>
          </div>
        </div>

        <style>{`
          .cross-section-detail-page {
            display: flex;
            flex-direction: column;
            height: 100%;
            padding: 20px;
            overflow-y: auto;
            background: #0f0f1a;
          }

          .page-header {
            display: flex;
            align-items: center;
            gap: 20px;
            margin-bottom: 20px;
          }

          .page-header h1 {
            flex: 1;
            font-size: 20px;
            color: #fff;
            margin: 0;
          }

          .btn-back {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 8px 16px;
            background: #252540;
            border: 1px solid #444;
            border-radius: 6px;
            color: #aaa;
            cursor: pointer;
          }

          .detail-content {
            flex: 1;
            overflow-y: auto;
          }

          .detail-section {
            background: #1a1a2e;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 16px;
          }

          .detail-section h3 {
            font-size: 14px;
            color: #00ff88;
            margin-bottom: 16px;
            padding-bottom: 8px;
            border-bottom: 1px solid #333;
          }

          .detail-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 16px;
          }

          .detail-item {
            display: flex;
            flex-direction: column;
            gap: 4px;
          }

          .detail-item .label {
            font-size: 12px;
            color: #666;
          }

          .detail-item .value {
            font-size: 14px;
            color: #fff;
          }

          .points-table {
            width: 100%;
            border-collapse: collapse;
          }

          .points-table th,
          .points-table td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #252540;
          }

          .points-table th {
            color: #888;
            font-size: 12px;
          }

          .points-table td {
            color: #ddd;
            font-size: 13px;
          }

          .section-diagram {
            padding: 20px;
            background: #252540;
            border-radius: 8px;
          }

          .diagram-container {
            position: relative;
            height: 150px;
            border-bottom: 2px solid #667eea;
          }

          .diagram-point {
            position: absolute;
            width: 10px;
            height: 10px;
            background: #00ff88;
            border-radius: 50%;
            transform: translateX(-50%);
          }

          .diagram-center {
            position: absolute;
            bottom: 0;
            width: 2px;
            height: 100%;
            background: #ff6b6b;
            opacity: 0.5;
          }

          .diagram-labels {
            display: flex;
            justify-content: space-between;
            margin-top: 8px;
            font-size: 12px;
            color: #666;
          }
        `}</style>
      </div>
    );
  }

  return (
    <div className="cross-section-list-page">
      {/* 顶部导航 */}
      <div className="page-header">
        <button className="btn-back" onClick={() => onNavigate?.('dashboard')}>
          <ArrowLeft size={20} />
          返回
        </button>
        <h1>📋 横断面列表</h1>
      </div>

      {/* 工具栏 */}
      <div className="toolbar">
        <form onSubmit={handleSearch} className="search-form">
          <div className="search-input">
            <Search size={18} />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="搜索桩号、类型..."
            />
          </div>
          <button type="submit">搜索</button>
        </form>

        <div className="toolbar-actions">
          <button className="btn-action" onClick={() => onNavigate?.('cross-section-entry')}>
            录入
          </button>
          <button className="btn-action" onClick={handleExport}>
            <Download size={18} />
            导出
          </button>
        </div>
      </div>

      {/* 数据表格 */}
      <div className="table-container">
        <table className="data-table">
          <thead>
            <tr>
              <th>桩号</th>
              <th>类型</th>
              <th>点数</th>
              <th>偏移范围</th>
              <th>高程范围</th>
              <th>同步状态</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={7} className="loading-cell">
                  加载中...
                </td>
              </tr>
            ) : crossSections.length === 0 ? (
              <tr>
                <td colSpan={7} className="empty-cell">
                  暂无数据
                </td>
              </tr>
            ) : (
              crossSections.map((cs) => {
                const offsets = cs.points.map(p => p.offset);
                const elevations = cs.points.map(p => p.elevation);
                return (
                  <tr key={cs.cs_id}>
                    <td className="station-cell">{cs.station_display}</td>
                    <td>
                      <span className={`cs-type ${cs.cs_type}`}>
                        {csTypeLabels[cs.cs_type]}
                      </span>
                    </td>
                    <td>{cs.points.length}</td>
                    <td>{Math.min(...offsets).toFixed(1)} ~ {Math.max(...offsets).toFixed(1)}</td>
                    <td>{Math.min(...elevations).toFixed(2)} ~ {Math.max(...elevations).toFixed(2)}</td>
                    <td>
                      <span className={`sync-status ${cs.sync_status}`}>
                        {cs.sync_status === 'synced' ? '已同步' : '待同步'}
                      </span>
                    </td>
                    <td className="actions-cell">
                      <button
                        className="btn-icon"
                        title="查看详情"
                        onClick={() => handleViewDetail(cs)}
                      >
                        <Eye size={16} />
                      </button>
                      <button
                        className="btn-icon"
                        title="编辑"
                        onClick={() => onNavigate?.('cross-section-entry', { editId: cs.cs_id })}
                      >
                        <Edit size={16} />
                      </button>
                      <button
                        className="btn-icon danger"
                        title="删除"
                        onClick={() => handleDelete(cs.cs_id)}
                      >
                        <Trash2 size={16} />
                      </button>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* 分页 */}
      <div className="pagination">
        <span className="pagination-info">
          共 {total} 条记录，第 {page}/{totalPages || 1} 页
        </span>
        <div className="pagination-buttons">
          <button
            disabled={page <= 1}
            onClick={() => setPage(p => p - 1)}
          >
            <ChevronLeft size={18} />
            上一页
          </button>
          <button
            disabled={page >= totalPages}
            onClick={() => setPage(p => p + 1)}
          >
            下一页
            <ChevronRight size={18} />
          </button>
        </div>
      </div>

      <style>{`
        .cross-section-list-page {
          display: flex;
          flex-direction: column;
          height: 100%;
          padding: 20px;
          overflow: hidden;
          background: #0f0f1a;
        }

        .page-header {
          display: flex;
          align-items: center;
          gap: 20px;
          margin-bottom: 20px;
        }

        .page-header h1 {
          flex: 1;
          font-size: 20px;
          color: #fff;
          margin: 0;
        }

        .btn-back {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 8px 16px;
          background: #252540;
          border: 1px solid #444;
          border-radius: 6px;
          color: #aaa;
          cursor: pointer;
        }

        .toolbar {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 16px;
          gap: 16px;
        }

        .search-form {
          display: flex;
          gap: 12px;
          flex: 1;
          max-width: 500px;
        }

        .search-input {
          flex: 1;
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 8px 14px;
          background: #1a1a2e;
          border: 1px solid #444;
          border-radius: 6px;
          color: #aaa;
        }

        .search-input input {
          flex: 1;
          background: transparent;
          border: none;
          color: #fff;
          font-size: 14px;
          outline: none;
        }

        .search-form button {
          padding: 8px 20px;
          background: #667eea;
          border: none;
          border-radius: 6px;
          color: #fff;
          font-size: 14px;
          cursor: pointer;
        }

        .toolbar-actions {
          display: flex;
          gap: 12px;
        }

        .btn-action {
          display: flex;
          align-items: center;
          gap: 6px;
          padding: 8px 16px;
          background: #252540;
          border: 1px solid #444;
          border-radius: 6px;
          color: #aaa;
          font-size: 13px;
          cursor: pointer;
        }

        .table-container {
          flex: 1;
          overflow: auto;
          background: #1a1a2e;
          border-radius: 12px;
        }

        .data-table {
          width: 100%;
          border-collapse: collapse;
        }

        .data-table th,
        .data-table td {
          padding: 12px 16px;
          text-align: left;
          border-bottom: 1px solid #252540;
        }

        .data-table th {
          background: #252540;
          color: #888;
          font-size: 12px;
          font-weight: 500;
        }

        .data-table td {
          color: #ddd;
          font-size: 13px;
        }

        .data-table tbody tr:hover {
          background: rgba(102, 126, 234, 0.05);
        }

        .station-cell {
          font-weight: 600;
          color: #00ff88;
        }

        .cs-type {
          display: inline-block;
          padding: 4px 8px;
          border-radius: 4px;
          font-size: 11px;
          background: rgba(102, 126, 234, 0.2);
          color: #667eea;
        }

        .cs-type.full { background: rgba(0, 255, 136, 0.2); color: #00ff88; }
        .cs-type.center { background: rgba(255, 193, 7, 0.2); color: #ffc107; }
        .cs-type.left { background: rgba(255, 107, 107, 0.2); color: #ff6b6b; }
        .cs-type.right { background: rgba(78, 205, 196, 0.2); color: #4ecdc4; }

        .sync-status {
          display: inline-block;
          padding: 4px 8px;
          border-radius: 4px;
          font-size: 11px;
        }

        .sync-status.synced {
          background: rgba(0, 255, 136, 0.1);
          color: #00ff88;
        }

        .sync-status.pending {
          background: rgba(255, 193, 7, 0.1);
          color: #ffc107;
        }

        .actions-cell {
          display: flex;
          gap: 8px;
        }

        .btn-icon {
          padding: 6px;
          background: transparent;
          border: none;
          color: #aaa;
          cursor: pointer;
          border-radius: 4px;
        }

        .btn-icon:hover {
          background: rgba(102, 126, 234, 0.1);
          color: #667eea;
        }

        .btn-icon.danger:hover {
          background: rgba(255, 107, 107, 0.1);
          color: #ff6b6b;
        }

        .loading-cell,
        .empty-cell {
          text-align: center;
          padding: 40px !important;
          color: #666;
        }

        .pagination {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 16px;
          background: #1a1a2e;
          border-radius: 12px;
          margin-top: 16px;
        }

        .pagination-info {
          color: #888;
          font-size: 13px;
        }

        .pagination-buttons {
          display: flex;
          gap: 12px;
        }

        .pagination-buttons button {
          display: flex;
          align-items: center;
          gap: 6px;
          padding: 8px 16px;
          background: #252540;
          border: 1px solid #444;
          border-radius: 6px;
          color: #aaa;
          font-size: 13px;
          cursor: pointer;
        }

        .pagination-buttons button:hover:not(:disabled) {
          background: #333;
          color: #fff;
        }

        .pagination-buttons button:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }
      `}</style>
    </div>
  );
}
