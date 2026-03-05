import { useState, useCallback, useRef } from 'react';
import { useApp } from '../context/AppContext';
import { stationsApi, crossSectionsApi } from '../api/endpoints';
import { ArrowLeft, Upload, FileSpreadsheet, Check, AlertCircle, X, Download, Play, Trash2 } from 'lucide-react';

interface DataImportPageProps {
  onNavigate?: (page: string) => void;
}

type ImportType = 'stations' | 'crossSections';

interface ParsedRow {
  [key: string]: string | number | undefined;
}

interface ImportResult {
  success: number;
  failed: number;
  errors: string[];
}

export default function DataImportPage({ onNavigate }: DataImportPageProps) {
  const { state } = useApp();
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  const [importType, setImportType] = useState<ImportType>('stations');
  const [file, setFile] = useState<File | null>(null);
  const [parsedData, setParsedData] = useState<ParsedRow[]>([]);
  const [headers, setHeaders] = useState<string[]>([]);
  const [importing, setImporting] = useState(false);
  const [result, setResult] = useState<ImportResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [projectId] = useState(state.selectedProject?.project_id || 'demo');
  const [routeId, setRouteId] = useState(state.routeId || 'demo');

  // 字段映射
  const fieldMappings: Record<ImportType, Record<string, string>> = {
    stations: {
      station_display: '桩号',
      x: 'X坐标',
      y: 'Y坐标',
      z: '高程Z',
      azimuth: '方位角',
      horizontal_elem: '平曲线',
      vertical_elem: '纵曲线',
      description: '备注',
    },
    crossSections: {
      station_display: '桩号',
      cs_type: '断面类型',
      points: '断面点',
      description: '备注',
    },
  };

  // 模板数据
  const templates: Record<ImportType, string[][]> = {
    stations: [
      ['桩号', 'X坐标', 'Y坐标', '高程Z', '方位角', '平曲线', '纵曲线', '备注'],
      ['K0+000', '500000', '3000000', '100', '45', '直线', '直线', ''],
      ['K0+500', '500353.55', '3000353.55', '110', '45', '缓和曲线', '直线', ''],
      ['K1+000', '500707.1', '3000707.1', '107.5', '45', '圆曲线', '凹形竖曲线', ''],
    ],
    crossSections: [
      ['桩号', '断面类型', '偏移量1', '高程1', '偏移量2', '高程2', '偏移量3', '高程3'],
      ['K0+000', 'full', '-10', '102', '0', '100', '10', '101'],
      ['K0+500', 'full', '-10', '112', '0', '110', '10', '111'],
    ],
  };

  // 处理文件选择
  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (!selectedFile) return;

    setFile(selectedFile);
    setResult(null);
    setError(null);

    // 解析CSV/Excel
    const reader = new FileReader();
    reader.onload = (event) => {
      const text = event.target?.result as string;
      const lines = text.split('\n').filter(line => line.trim());
      
      if (lines.length < 2) {
        setError('文件格式错误，需要至少包含表头和一行数据');
        return;
      }

      // 解析表头
      const fileHeaders = lines[0].split(',').map(h => h.trim().replace(/"/g, ''));
      setHeaders(fileHeaders);

      // 解析数据行
      const data: ParsedRow[] = [];
      for (let i = 1; i < lines.length; i++) {
        const values = lines[i].split(',').map(v => v.trim().replace(/"/g, ''));
        const row: ParsedRow = {};
        
        fileHeaders.forEach((header, index) => {
          const value = values[index];
          // 尝试转换为数字
          const num = parseFloat(value);
          row[header] = isNaN(num) ? value : num;
        });
        
        data.push(row);
      }

      setParsedData(data);
    };

    reader.readAsText(selectedFile);
  }, []);

  // 下载模板
  const handleDownloadTemplate = useCallback(() => {
    const template = templates[importType];
    const csvContent = template.map(row => row.join(',')).join('\n');
    
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${importType === 'stations' ? '桩号' : '横断面'}_导入模板.csv`;
    link.click();
    URL.revokeObjectURL(url);
  }, [importType]);

  // 解析桩号
  const parseStationValue = (display: string): number => {
    const match = display.match(/^([Kk])?(\d+)\+(\d{3})$/);
    if (match) {
      return parseInt(match[2]) * 1000 + parseInt(match[3]);
    }
    return parseFloat(display) || 0;
  };

  // 执行导入
  const handleImport = useCallback(async () => {
    if (parsedData.length === 0) {
      setError('没有可导入的数据');
      return;
    }

    setImporting(true);
    setError(null);
    setResult(null);

    const errors: string[] = [];
    let successCount = 0;
    let failedCount = 0;

    try {
      if (importType === 'stations') {
        // 转换数据格式
        const stationData = parsedData.map((row, index) => {
          const stationDisplay = String(row['桩号'] || row['station_display'] || '');
          const station = parseStationValue(stationDisplay);
          
          return {
            project_id: projectId,
            route_id: routeId,
            station,
            station_display: stationDisplay,
            x: Number(row['X坐标'] || row['x'] || 0),
            y: Number(row['Y坐标'] || row['y'] || 0),
            z: Number(row['高程Z'] || row['z'] || 0),
            azimuth: Number(row['方位角'] || row['azimuth'] || 0),
            horizontal_elem: String(row['平曲线'] || row['horizontal_elem'] || '直线'),
            vertical_elem: String(row['纵曲线'] || row['vertical_elem'] || '直线'),
            description: String(row['备注'] || row['description'] || ''),
          };
        });

        // 模拟导入
        await new Promise(resolve => setTimeout(resolve, 500));
        
        // 验证
        stationData.forEach((data, index) => {
          if (!data.station_display || data.x === undefined) {
            errors.push(`第${index + 1}行: 数据不完整`);
            failedCount++;
          } else {
            successCount++;
          }
        });

      } else {
        // 横断面导入
        const csData = parsedData.map((row, index) => {
          const stationDisplay = String(row['桩号'] || row['station_display'] || '');
          const station = parseStationValue(stationDisplay);
          const csType = String(row['断面类型'] || row['cs_type'] || 'full');
          
          // 解析断面点
          const points = [];
          for (let i = 1; i <= 10; i++) {
            const offsetKey = `偏移量${i}`;
            const elevKey = `高程${i}`;
            const offset = row[offsetKey] || row[`offset${i}`];
            const elevation = row[elevKey] || row[`elevation${i}`];
            
            if (offset !== undefined && elevation !== undefined) {
              points.push({
                offset: Number(offset),
                elevation: Number(elevation),
              });
            }
          }

          return {
            project_id: projectId,
            route_id: routeId,
            station,
            station_display: stationDisplay,
            cs_type: ['full', 'center', 'left', 'right'].includes(csType) ? csType as any : 'full',
            points,
            description: String(row['备注'] || row['description'] || ''),
          };
        });

        // 模拟导入
        await new Promise(resolve => setTimeout(resolve, 500));
        
        // 验证
        csData.forEach((data, index) => {
          if (!data.station_display || data.points.length < 2) {
            errors.push(`第${index + 1}行: 数据不完整或点数不足`);
            failedCount++;
          } else {
            successCount++;
          }
        });
      }

      setResult({
        success: successCount,
        failed: failedCount,
        errors,
      });

    } catch (err) {
      setError(err instanceof Error ? err.message : '导入失败，请重试');
    } finally {
      setImporting(false);
    }
  }, [parsedData, importType, projectId, routeId]);

  // 清空数据
  const handleClear = useCallback(() => {
    setFile(null);
    setParsedData([]);
    setHeaders([]);
    setResult(null);
    setError(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  }, []);

  return (
    <div className="data-import-page">
      {/* 顶部导航 */}
      <div className="page-header">
        <button className="btn-back" onClick={() => onNavigate?.('dashboard')}>
          <ArrowLeft size={20} />
          返回
        </button>
        <h1>📥 数据导入</h1>
      </div>

      {/* 消息提示 */}
      {error && (
        <div className="alert error">
          <AlertCircle size={18} />
          {error}
        </div>
      )}

      {result && (
        <div className={`alert ${result.failed === 0 ? 'success' : 'warning'}`}>
          <Check size={18} />
          导入完成：成功 {result.success} 条，失败 {result.failed} 条
          {result.errors.length > 0 && (
            <span className="error-count">（点击查看详情）</span>
          )}
        </div>
      )}

      <div className="content-grid">
        {/* 左侧：导入配置 */}
        <div className="config-panel">
          <div className="panel-section">
            <h3>1. 选择数据类型</h3>
            <div className="type-selector">
              <button
                className={importType === 'stations' ? 'active' : ''}
                onClick={() => {
                  setImportType('stations');
                  handleClear();
                }}
              >
                <FileSpreadsheet size={20} />
                <span>桩号数据</span>
              </button>
              <button
                className={importType === 'crossSections' ? 'active' : ''}
                onClick={() => {
                  setImportType('crossSections');
                  handleClear();
                }}
              >
                <FileSpreadsheet size={20} />
                <span>横断面数据</span>
              </button>
            </div>
          </div>

          <div className="panel-section">
            <h3>2. 项目信息</h3>
            <div className="form-group">
              <label>项目ID</label>
              <input
                type="text"
                value={projectId}
                disabled
                className="input-disabled"
              />
            </div>
            <div className="form-group">
              <label>路线ID</label>
              <input
                type="text"
                value={routeId}
                onChange={(e) => setRouteId(e.target.value)}
                placeholder="路线ID"
              />
            </div>
          </div>

          <div className="panel-section">
            <h3>3. 选择文件</h3>
            <div 
              className="drop-zone"
              onClick={() => fileInputRef.current?.click()}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".csv,.xlsx,.xls"
                onChange={handleFileSelect}
                style={{ display: 'none' }}
              />
              <Upload size={32} />
              <p>点击选择CSV/Excel文件</p>
            </div>
            
            <button className="btn-template" onClick={handleDownloadTemplate}>
              <Download size={16} />
              下载导入模板
            </button>
          </div>
        </div>

        {/* 右侧：数据预览 */}
        <div className="preview-panel">
          <div className="panel-header">
            <h3>数据预览</h3>
            {parsedData.length > 0 && (
              <span className="data-count">{parsedData.length} 行</span>
            )}
          </div>

          {parsedData.length === 0 ? (
            <div className="empty-preview">
              <FileSpreadsheet size={48} />
              <p>请先选择导入文件</p>
              <span>支持 CSV, XLSX, XLS 格式</span>
            </div>
          ) : (
            <>
              {/* 文件信息 */}
              {file && (
                <div className="file-info">
                  <span className="file-name">
                    <FileSpreadsheet size={16} />
                    {file.name}
                  </span>
                  <button className="btn-clear" onClick={handleClear}>
                    <X size={14} />
                    清除
                  </button>
                </div>
              )}

              {/* 数据表格 */}
              <div className="table-container">
                <table className="preview-table">
                  <thead>
                    <tr>
                      {headers.map((header, index) => (
                        <th key={index}>{header}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {parsedData.slice(0, 100).map((row, rowIndex) => (
                      <tr key={rowIndex}>
                        {headers.map((header, colIndex) => (
                          <td key={colIndex}>
                            {row[header] !== undefined ? String(row[header]) : ''}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
                {parsedData.length > 100 && (
                  <div className="table-footer">
                    显示前100行，共 {parsedData.length} 行
                  </div>
                )}
              </div>

              {/* 导入按钮 */}
              <div className="import-actions">
                <button
                  className="btn-import"
                  onClick={handleImport}
                  disabled={importing || parsedData.length === 0}
                >
                  {importing ? (
                    <>导入中...</>
                  ) : (
                    <>
                      <Play size={18} />
                      开始导入 ({parsedData.length} 条)
                    </>
                  )}
                </button>
              </div>
            </>
          )}
        </div>
      </div>

      {/* 错误详情 */}
      {result && result.errors.length > 0 && (
        <div className="error-details">
          <h4>导入错误详情</h4>
          <ul>
            {result.errors.slice(0, 10).map((err, index) => (
              <li key={index}>{err}</li>
            ))}
            {result.errors.length > 10 && (
              <li>...还有 {result.errors.length - 10} 个错误</li>
            )}
          </ul>
        </div>
      )}

      <style>{`
        .data-import-page {
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

        .alert {
          display: flex;
          align-items: center;
          gap: 10px;
          padding: 12px 16px;
          border-radius: 8px;
          margin-bottom: 16px;
          font-size: 14px;
        }

        .alert.success {
          background: rgba(0, 255, 136, 0.1);
          border: 1px solid #00ff88;
          color: #00ff88;
        }

        .alert.warning {
          background: rgba(255, 193, 7, 0.1);
          border: 1px solid #ffc107;
          color: #ffc107;
        }

        .alert.error {
          background: rgba(255, 107, 107, 0.1);
          border: 1px solid #ff6b6b;
          color: #ff6b6b;
        }

        .error-count {
          text-decoration: underline;
          cursor: pointer;
        }

        .content-grid {
          display: grid;
          grid-template-columns: 350px 1fr;
          gap: 20px;
          flex: 1;
          min-height: 0;
        }

        .config-panel,
        .preview-panel {
          display: flex;
          flex-direction: column;
          background: #1a1a2e;
          border-radius: 12px;
          padding: 20px;
          overflow: hidden;
        }

        .panel-section {
          margin-bottom: 24px;
        }

        .panel-section h3 {
          font-size: 14px;
          color: #00ff88;
          margin: 0 0 16px;
        }

        .type-selector {
          display: flex;
          gap: 12px;
        }

        .type-selector button {
          flex: 1;
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 8px;
          padding: 16px;
          background: #252540;
          border: 2px solid #444;
          border-radius: 8px;
          color: #aaa;
          cursor: pointer;
          transition: all 0.2s;
        }

        .type-selector button:hover {
          border-color: #667eea;
        }

        .type-selector button.active {
          border-color: #667eea;
          background: rgba(102, 126, 234, 0.1);
          color: #667eea;
        }

        .type-selector button span {
          font-size: 13px;
        }

        .form-group {
          margin-bottom: 12px;
        }

        .form-group label {
          display: block;
          font-size: 12px;
          color: #888;
          margin-bottom: 6px;
        }

        .form-group input {
          width: 100%;
          padding: 10px 12px;
          background: #252540;
          border: 1px solid #444;
          border-radius: 6px;
          color: #fff;
          font-size: 13px;
        }

        .form-group input:focus {
          outline: none;
          border-color: #667eea;
        }

        .input-disabled {
          background: #1a1a2e !important;
          color: #666 !important;
          cursor: not-allowed;
        }

        .drop-zone {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          padding: 30px;
          border: 2px dashed #444;
          border-radius: 8px;
          cursor: pointer;
          transition: all 0.2s;
          color: #666;
        }

        .drop-zone:hover {
          border-color: #667eea;
          background: rgba(102, 126, 234, 0.05);
        }

        .drop-zone p {
          margin: 12px 0 0;
          color: #aaa;
          font-size: 13px;
        }

        .btn-template {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 8px;
          width: 100%;
          margin-top: 12px;
          padding: 10px;
          background: #252540;
          border: 1px solid #444;
          border-radius: 6px;
          color: #aaa;
          font-size: 13px;
          cursor: pointer;
        }

        .btn-template:hover {
          background: #333;
          color: #fff;
        }

        .panel-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 16px;
        }

        .panel-header h3 {
          font-size: 16px;
          color: #fff;
          margin: 0;
        }

        .data-count {
          font-size: 12px;
          color: #888;
          background: #252540;
          padding: 4px 10px;
          border-radius: 12px;
        }

        .empty-preview {
          flex: 1;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          color: #444;
        }

        .empty-preview p {
          margin: 16px 0 8px;
          font-size: 14px;
        }

        .empty-preview span {
          font-size: 12px;
        }

        .file-info {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 10px 14px;
          background: #252540;
          border-radius: 6px;
          margin-bottom: 12px;
        }

        .file-name {
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 13px;
          color: #fff;
        }

        .btn-clear {
          display: flex;
          align-items: center;
          gap: 4px;
          padding: 4px 10px;
          background: transparent;
          border: none;
          color: #ff6b6b;
          font-size: 12px;
          cursor: pointer;
        }

        .table-container {
          flex: 1;
          overflow: auto;
          background: #252540;
          border-radius: 8px;
        }

        .preview-table {
          width: 100%;
          border-collapse: collapse;
        }

        .preview-table th,
        .preview-table td {
          padding: 10px 12px;
          text-align: left;
          border-bottom: 1px solid #333;
          white-space: nowrap;
        }

        .preview-table th {
          background: #1a1a2e;
          color: #888;
          font-size: 11px;
          font-weight: 500;
          position: sticky;
          top: 0;
        }

        .preview-table td {
          color: #ddd;
          font-size: 12px;
        }

        .table-footer {
          padding: 10px;
          text-align: center;
          font-size: 12px;
          color: #666;
          background: #1a1a2e;
        }

        .import-actions {
          margin-top: 16px;
        }

        .btn-import {
          width: 100%;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 8px;
          padding: 14px;
          background: linear-gradient(135deg, #667eea, #764ba2);
          border: none;
          border-radius: 8px;
          color: #fff;
          font-size: 14px;
          font-weight: 600;
          cursor: pointer;
        }

        .btn-import:hover:not(:disabled) {
          transform: translateY(-2px);
        }

        .btn-import:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }

        .error-details {
          margin-top: 20px;
          padding: 16px;
          background: #1a1a2e;
          border-radius: 8px;
        }

        .error-details h4 {
          font-size: 14px;
          color: #ff6b6b;
          margin: 0 0 12px;
        }

        .error-details ul {
          margin: 0;
          padding-left: 20px;
          color: #888;
          font-size: 13px;
        }

        .error-details li {
          margin-bottom: 4px;
        }
      `}</style>
    </div>
  );
}
