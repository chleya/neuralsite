import { useState, useEffect, useCallback } from 'react';
import { useApp } from '../context/AppContext';
import { Station, StationListParams } from '../api/types';
import { stationsApi } from '../api/endpoints';
import { ArrowLeft, Search, Edit, Trash2, Download, Upload, ChevronLeft, ChevronRight } from 'lucide-react';

interface StationListPageProps {
  onNavigate?: (page: string, params?: Record<string, unknown>) => void;
}

// 模拟数据
const mockStations: Station[] = [
  {
    station_id: '1',
    project_id: 'demo',
    route_id: 'demo',
    station: 0,
    station_display: 'K0+000',
    x: 500000,
    y: 3000000,
    z: 100,
    azimuth: 45,
    horizontal_elem: '直线',
    vertical_elem: '凸形竖曲线',
    sync_status: 'synced',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    station_id: '2',
    project_id: 'demo',
    route_id: 'demo',
    station: 500,
    station_display: 'K0+500',
    x: 500353.55,
    y: 3000353.55,
    z: 110,
    azimuth: 45,
    horizontal_elem: '缓和曲线',
    vertical_elem: '直线',
    sync_status: 'synced',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    station_id: '3',
    project_id: 'demo',
    route_id: 'demo',
    station: 1000,
    station_display: 'K1+000',
    x: 500707.1,
    y: 3000707.1,
    z: 107.5,
    azimuth: 45,
    horizontal_elem: '圆曲线',
    vertical_elem: '凹形竖曲线',
    sync_status: 'synced',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    station_id: '4',
    project_id: 'demo',
    route_id: 'demo',
    station: 1500,
    station_display: 'K1+500',
    x: 501060.66,
    y: 3001060.66,
    z: 105,
    azimuth: 45,
    horizontal_elem: '圆曲线',
    vertical_elem: '直线',
    sync_status: 'synced',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    station_id: '5',
    project_id: 'demo',
    route_id: 'demo',
    station: 2000,
    station_display: 'K2+000',
    x: 501414.21,
    y: 3001414.21,
    z: 102.5,
    azimuth: 45,
    horizontal_elem: '缓和曲线',
    vertical_elem: '凸形竖曲线',
    sync_status: 'synced',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
];

export default function StationListPage({ onNavigate }: StationListPageProps) {
  const { state } = useApp();
  const [stations, setStations] = useState<Station[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [limit] = useState(10);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);

  // 加载数据
  const loadStations = useCallback(async () => {
    setLoading(true);
    try {
      const params: StationListParams = {
        project_id: state.selectedProject?.project_id || 'demo',
        route_id: state.routeId || 'demo',
        page,
        limit,
        search: search || undefined,
      };

      // 模拟API调用（后端未启动时）
      await new Promise(resolve => setTimeout(resolve, 300));
      
      let filtered = [...mockStations];
      if (search) {
        filtered = filtered.filter(s => 
          s.station_display.toLowerCase().includes(search.toLowerCase()) ||
          s.horizontal_elem?.toLowerCase().includes(search.toLowerCase()) ||
          s.vertical_elem?.toLowerCase().includes(search.toLowerCase())
        );
      }
      
      setStations(filtered);
      setTotal(filtered.length);
    } catch (error) {
      console.error('Failed to load stations:', error);
    } finally {
      setLoading(false);
    }
  }, [page, search, state.selectedProject?.project_id, state.routeId]);

  useEffect(() => {
    loadStations();
  }, [loadStations]);

  // 处理搜索
  const handleSearch = useCallback((e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    loadStations();
  }, [loadStations]);

  // 处理全选
  const handleSelectAll = useCallback(() => {
    if (selectedIds.length === stations.length) {
      setSelectedIds([]);
    } else {
      setSelectedIds(stations.map(s => s.station_id));
    }
  }, [stations, selectedIds]);

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
    if (!confirm('确定要删除这条桩号记录吗？')) return;
    
    try {
      // 模拟API调用
      await new Promise(resolve => setTimeout(resolve, 300));
      setStations(prev => prev.filter(s => s.station_id !== id));
    } catch (error) {
      console.error('Failed to delete station:', error);
    }
  }, []);

  // 批量删除
  const handleBatchDelete = useCallback(async () => {
    if (!confirm(`确定要删除选中的 ${selectedIds.length} 条记录吗？`)) return;
    
    try {
      // 模拟API调用
      await new Promise(resolve => setTimeout(resolve, 300));
      setStations(prev => prev.filter(s => !selectedIds.includes(s.station_id)));
      setSelectedIds([]);
    } catch (error) {
      console.error('Failed to delete stations:', error);
    }
  }, [selectedIds]);

  // 导出数据
  const handleExport = useCallback(() => {
    const csvContent = [
      ['桩号ID', '桩号显示', 'X坐标', 'Y坐标', '高程Z', '方位角', '平曲线', '纵曲线'].join(','),
      ...stations.map(s => [
        s.station_id,
        s.station_display,
        s.x,
        s.y,
        s.z,
        s.azimuth,
        s.horizontal_elem || '',
        s.vertical_elem || '',
      ].join(','))
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `stations_${new Date().toISOString().split('T')[0]}.csv`;
    link.click();
    URL.revokeObjectURL(url);
  }, [stations]);

  const totalPages = Math.ceil(total / limit);

  return (
    <div className="station-list-page">
      {/* 顶部导航 */}
      <div className="page-header">
        <button className="btn-back" onClick={() => onNavigate?.('dashboard')}>
          <ArrowLeft size={20} />
          返回
        </button>
        <h1>📋 桩号列表</h1>
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
              placeholder="搜索桩号、线元..."
            />
          </div>
          <button type="submit">搜索</button>
        </form>

        <div className="toolbar-actions">
          <button className="btn-action" onClick={() => onNavigate?.('station-entry')}>
            <Upload size={18} />
            录入
          </button>
          <button className="btn-action" onClick={handleExport}>
            <Download size={18} />
            导出
          </button>
          {selectedIds.length > 0 && (
            <button className="btn-action danger" onClick={handleBatchDelete}>
              <Trash2 size={18} />
              删除选中 ({selectedIds.length})
            </button>
          )}
        </div>
      </div>

      {/* 数据表格 */}
      <div className="table-container">
        <table className="data-table">
          <thead>
            <tr>
              <th className="checkbox-col">
                <input
                  type="checkbox"
                  checked={selectedIds.length === stations.length && stations.length > 0}
                  onChange={handleSelectAll}
                />
              </th>
              <th>桩号显示</th>
              <th>X坐标</th>
              <th>Y坐标</th>
              <th>高程Z(m)</th>
              <th>方位角(°)</th>
              <th>平曲线</th>
              <th>纵曲线</th>
              <th>同步状态</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={10} className="loading-cell">
                  加载中...
                </td>
              </tr>
            ) : stations.length === 0 ? (
              <tr>
                <td colSpan={10} className="empty-cell">
                  暂无数据
                </td>
              </tr>
            ) : (
              stations.map((station) => (
                <tr key={station.station_id}>
                  <td className="checkbox-col">
                    <input
                      type="checkbox"
                      checked={selectedIds.includes(station.station_id)}
                      onChange={() => handleSelect(station.station_id)}
                    />
                  </td>
                  <td className="station-cell">{station.station_display}</td>
                  <td>{station.x.toFixed(3)}</td>
                  <td>{station.y.toFixed(3)}</td>
                  <td>{station.z.toFixed(3)}</td>
                  <td>{station.azimuth?.toFixed(1)}</td>
                  <td>{station.horizontal_elem || '-'}</td>
                  <td>{station.vertical_elem || '-'}</td>
                  <td>
                    <span className={`sync-status ${station.sync_status}`}>
                      {station.sync_status === 'synced' ? '已同步' : 
                       station.sync_status === 'pending' ? '待同步' : '冲突'}
                    </span>
                  </td>
                  <td className="actions-cell">
                    <button
                      className="btn-icon"
                      title="编辑"
                      onClick={() => onNavigate?.('station-entry', { editId: station.station_id })}
                    >
                      <Edit size={16} />
                    </button>
                    <button
                      className="btn-icon danger"
                      title="删除"
                      onClick={() => handleDelete(station.station_id)}
                    >
                      <Trash2 size={16} />
                    </button>
                  </td>
                </tr>
              ))
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
        .station-list-page {
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

        .btn-back:hover {
          background: #333;
          color: #fff;
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

        .search-form button:hover {
          background: #5a6fd6;
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
          transition: all 0.2s;
        }

        .btn-action:hover {
          background: #333;
          color: #fff;
        }

        .btn-action.danger {
          border-color: #ff6b6b;
          color: #ff6b6b;
        }

        .btn-action.danger:hover {
          background: #ff6b6b;
          color: #fff;
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
          position: sticky;
          top: 0;
          z-index: 1;
        }

        .data-table td {
          color: #ddd;
          font-size: 13px;
        }

        .data-table tbody tr:hover {
          background: rgba(102, 126, 234, 0.05);
        }

        .checkbox-col {
          width: 40px;
          text-align: center;
        }

        .checkbox-col input {
          cursor: pointer;
        }

        .station-cell {
          font-weight: 600;
          color: #00ff88;
        }

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

        .sync-status.conflict {
          background: rgba(255, 107, 107, 0.1);
          color: #ff6b6b;
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
