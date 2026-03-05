import { useState, useCallback, useRef, useMemo } from 'react';
import { useApp } from '../context/AppContext';
import * as XLSX from 'xlsx';
import { ArrowLeft, Upload, FileSpreadsheet, Check, AlertCircle, X, Download, Play, Settings, ChevronDown, Loader2, FileType } from 'lucide-react';

interface DataImportPageProps {
  onNavigate?: (page: string) => void;
}

type ImportType = 'stations' | 'crossSections';

interface ParsedRow {
  [key: string]: string | number | undefined;
}

interface FieldMapping {
  sourceField: string;
  targetField: string;
  required: boolean;
}

interface ImportResult {
  success: number;
  failed: number;
  errors: { row: number; message: string }[];
  warnings: { row: number; message: string }[];
}

interface ImportProgress {
  stage: 'parsing' | 'validating' | 'importing' | 'complete';
  current: number;
  total: number;
  message: string;
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
  const [projectId] = useState(state.selectedProject?.project_id || 'demo');
  const [routeId, setRouteId] = useState(state.routeId || 'demo');
  const [error, setError] = useState<string | null>(null);
  
  // 字段映射配置
  const [showMappingConfig, setShowMappingConfig] = useState(false);
  const [fieldMappings, setFieldMappings] = useState<FieldMapping[]>([
    { sourceField: '桩号', targetField: 'station_display', required: true },
    { sourceField: 'X坐标', targetField: 'x', required: true },
    { sourceField: 'Y坐标', targetField: 'y', required: true },
    { sourceField: '高程Z', targetField: 'z', required: false },
    { sourceField: '方位角', targetField: 'azimuth', required: false },
    { sourceField: '平曲线', targetField: 'horizontal_elem', required: false },
    { sourceField: '纵曲线', targetField: 'vertical_elem', required: false },
    { sourceField: '备注', targetField: 'description', required: false },
  ]);
  
  // 导入进度
  const [progress, setProgress] = useState<ImportProgress | null>(null);
  const [showErrorDetails, setShowErrorDetails] = useState(false);

  // 根据导入类型更新字段映射
  const updateFieldMappingsForType = useCallback((type: ImportType) => {
    if (type === 'stations') {
      setFieldMappings([
        { sourceField: '桩号', targetField: 'station_display', required: true },
        { sourceField: 'X坐标', targetField: 'x', required: true },
        { sourceField: 'Y坐标', targetField: 'y', required: true },
        { sourceField: '高程Z', targetField: 'z', required: false },
        { sourceField: '方位角', targetField: 'azimuth', required: false },
        { sourceField: '平曲线', targetField: 'horizontal_elem', required: false },
        { sourceField: '纵曲线', targetField: 'vertical_elem', required: false },
        { sourceField: '备注', targetField: 'description', required: false },
      ]);
    } else {
      setFieldMappings([
        { sourceField: '桩号', targetField: 'station_display', required: true },
        { sourceField: '断面类型', targetField: 'cs_type', required: true },
        { sourceField: '偏移量1', targetField: 'offset1', required: false },
        { sourceField: '高程1', targetField: 'elevation1', required: false },
        { sourceField: '偏移量2', targetField: 'offset2', required: false },
        { sourceField: '高程2', targetField: 'elevation2', required: false },
        { sourceField: '备注', targetField: 'description', required: false },
      ]);
    }
  }, []);

  // 模板数据
  const templates: Record<ImportType, string[][]> = {
    stations: [
      ['桩号', 'X坐标', 'Y坐标', '高程Z', '方位角', '平曲线', '纵曲线', '备注'],
      ['K0+000', '500000', '3000000', '100', '45', '直线', '直线', ''],
      ['K0+500', '500353.55', '3000353.55', '110', '45', '缓和曲线', '直线', ''],
      ['K1+000', '500707.1', '3000707.1', '107.5', '45', '圆曲线', '凹形竖曲线', ''],
    ],
    crossSections: [
      ['桩号', '断面类型', '偏移量1', '高程1', '偏移量2', '高程2'],
      ['K0+000', 'full', '-10', '102', '0', '100'],
      ['K0+500', 'full', '-10', '112', '0', '110'],
    ],
  };

  // 使用xlsx解析文件
  const parseFile = useCallback(async (file: File): Promise<{ headers: string[]; data: ParsedRow[] }> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      
      reader.onload = (e) => {
        try {
          const data = e.target?.result;
          let workbook: XLSX.WorkBook;
          
          if (file.name.endsWith('.csv')) {
            workbook = XLSX.read(data, { type: 'string' });
          } else {
            workbook = XLSX.read(data, { type: 'binary' });
          }
          
          const firstSheetName = workbook.SheetNames[0];
          const worksheet = workbook.Sheets[firstSheetName];
          
          const jsonData = XLSX.utils.sheet_to_json(worksheet, { 
            defval: '',
            header: 1 
          }) as (string | number | undefined)[][];
          
          if (jsonData.length < 2) {
            reject(new Error('文件格式错误，需要至少包含表头和一行数据'));
            return;
          }
          
          const fileHeaders = (jsonData[0] as (string | number)[]).map(h => String(h).trim());
          
          const parsed: ParsedRow[] = [];
          for (let i = 1; i < jsonData.length; i++) {
            const row = jsonData[i];
            const parsedRow: ParsedRow = {};
            
            fileHeaders.forEach((header, index) => {
              const value = row[index];
              if (value !== undefined && value !== '') {
                const num = typeof value === 'number' ? value : parseFloat(String(value));
                parsedRow[header] = isNaN(num) ? String(value) : num;
              }
            });
            
            if (Object.keys(parsedRow).length > 0) {
              parsed.push(parsedRow);
            }
          }
          
          resolve({ headers: fileHeaders, data: parsed });
        } catch (err) {
          reject(new Error('文件解析失败，请确保文件格式正确'));
        }
      };
      
      reader.onerror = () => reject(new Error('文件读取失败'));
      reader.readAsBinaryString(file);
    });
  }, []);

  // 处理文件选择
  const handleFileSelect = useCallback(async (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (!selectedFile) return;

    const validExtensions = ['.csv', '.xlsx', '.xls'];
    const ext = selectedFile.name.toLowerCase().slice(selectedFile.name.lastIndexOf('.'));
    if (!validExtensions.includes(ext)) {
      setError('不支持的文件格式，请选择 CSV、XLSX 或 XLS 文件');
      return;
    }

    setFile(selectedFile);
    setResult(null);
    setError(null);
    setProgress({ stage: 'parsing', current: 0, total: 100, message: '正在解析文件...' });

    try {
      const { headers: fileHeaders, data: parsed } = await parseFile(selectedFile);
      setHeaders(fileHeaders);
      setParsedData(parsed);
      setProgress(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : '文件解析失败');
      setProgress(null);
    }
  }, [parseFile]);

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

  // 验证单行数据
  const validateRow = (row: ParsedRow, index: number): { valid: boolean; errors: string[] } => {
    const errors: string[] = [];
    
    fieldMappings.forEach(field => {
      const value = row[field.sourceField];
      if (field.required && (value === undefined || value === '' || value === null)) {
        errors.push(`缺少必填字段: ${field.sourceField}`);
      }
    });
    
    return { valid: errors.length === 0, errors };
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
    setProgress({ stage: 'validating', current: 0, total: parsedData.length, message: '正在验证数据...' });

    const errors: { row: number; message: string }[] = [];
    const warnings: { row: number; message: string }[] = [];
    let successCount = 0;
    let failedCount = 0;

    try {
      // 阶段1：验证数据
      const validationResults = parsedData.map((row, index) => {
        const validation = validateRow(row, index);
        return { index, ...validation };
      });

      validationResults.forEach(result => {
        if (!result.valid) {
          result.errors.forEach(err => {
            errors.push({ row: result.index + 1, message: err });
          });
        }
      });

      setProgress({ stage: 'validating', current: parsedData.length, total: parsedData.length, message: '验证完成' });

      const criticalErrors = errors.filter(e => 
        e.message.includes('必填字段') || e.message.includes('X坐标') || e.message.includes('Y坐标')
      );

      if (criticalErrors.length > 0 && criticalErrors.length >= parsedData.length * 0.5) {
        setProgress(null);
        setResult({ success: 0, failed: parsedData.length, errors: criticalErrors, warnings });
        setImporting(false);
        return;
      }

      // 阶段2：导入数据
      setProgress({ stage: 'importing', current: 0, total: parsedData.length, message: '正在导入数据...' });

      const validData = parsedData.filter((_, idx) => validationResults[idx].valid);

      for (let i = 0; i < validData.length; i++) {
        await new Promise(resolve => setTimeout(resolve, 30));
        
        const row = validData[i];
        
        if (importType === 'stations') {
          const stationDisplay = String(row['桩号'] || row['station_display'] || '');
          
          if (!stationDisplay) {
            errors.push({ row: i + 1, message: '桩号为空' });
            failedCount++;
            continue;
          }
          
          const xVal = row['X坐标'] ?? row['x'];
          const yVal = row['Y坐标'] ?? row['y'];
          
          if (xVal === undefined || yVal === undefined) {
            errors.push({ row: i + 1, message: '缺少坐标数据' });
            failedCount++;
            continue;
          }

          successCount++;
          
        } else {
          const stationDisplay = String(row['桩号'] || row['station_display'] || '');
          
          if (!stationDisplay) {
            errors.push({ row: i + 1, message: '桩号为空' });
            failedCount++;
            continue;
          }

          const hasPoints = Object.keys(row).some(k => k.includes('偏移量') || k.includes('offset'));
          if (!hasPoints) {
            warnings.push({ row: i + 1, message: '未检测' });
          }
到断面点数据          
          successCount++;
        }
        
        setProgress({ stage: 'importing', current: i + 1, total: validData.length, message: `正在导入 ${i + 1}/${validData.length}...` });
      }

      setProgress({ stage: 'complete', current: parsedData.length, total: parsedData.length, message: '导入完成' });

      setResult({ success: successCount, failed: failedCount, errors, warnings });

    } catch (err) {
      setError(err instanceof Error ? err.message : '导入失败，请重试');
    } finally {
      setTimeout(() => {
        setImporting(false);
        setProgress(null);
      }, 1000);
    }
  }, [parsedData, importType, fieldMappings]);

  // 清空数据
  const handleClear = useCallback(() => {
    setFile(null);
    setParsedData([]);
    setHeaders([]);
    setResult(null);
    setError(null);
    setProgress(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  }, []);

  // 更新字段映射
  const updateMapping = useCallback((index: number, sourceField: string) => {
    setFieldMappings(prev => {
      const updated = [...prev];
      updated[index] = { ...updated[index], sourceField };
      return updated;
    });
  }, []);

  // 预览数据
  const mappedPreviewData = useMemo(() => {
    if (parsedData.length === 0) return [];
    
    return parsedData.slice(0, 20).map(row => {
      const mapped: Record<string, string | number> = {};
      fieldMappings.forEach(field => {
        const value = row[field.sourceField];
        mapped[field.targetField] = value !== undefined ? value : '-';
      });
      return mapped;
    });
  }, [parsedData, fieldMappings]);

  const progressPercent = progress ? Math.round((progress.current / progress.total) * 100) : 0;

  return (
    <div className="data-import-page">
      <div className="page-header">
        <button className="btn-back" onClick={() => onNavigate?.('dashboard')}>
          <ArrowLeft size={20} />
          返回
        </button>
        <h1>📥 数据导入</h1>
      </div>

      {error && (
        <div className="alert error">
          <AlertCircle size={18} />
          {error}
          <button className="alert-close" onClick={() => setError(null)}><X size={14}/></button>
        </div>
      )}

      {result && (
        <div className={`alert ${result.failed === 0 ? 'success' : 'warning'}`}>
          <Check size={18} />
          导入完成：成功 {result.success} 条，失败 {result.failed} 条
          {(result.errors.length > 0 || result.warnings.length > 0) && (
            <span className="error-count" onClick={() => setShowErrorDetails(!showErrorDetails)}>
              （点击查看详情）
            </span>
          )}
        </div>
      )}

      {progress && (
        <div className="progress-container">
          <div className="progress-info">
            <Loader2 size={18} className="spinner" />
            <span>{progress.message}</span>
            <span className="progress-percent">{progressPercent}%</span>
          </div>
          <div className="progress-bar">
            <div className="progress-fill" style={{ width: `${progressPercent}%` }}></div>
          </div>
        </div>
      )}

      <div className="content-grid">
        <div className="config-panel">
          <div className="panel-section">
            <h3>1. 选择数据类型</h3>
            <div className="type-selector">
              <button
                className={importType === 'stations' ? 'active' : ''}
                onClick={() => { setImportType('stations'); updateFieldMappingsForType('stations'); handleClear(); }}
              >
                <FileSpreadsheet size={20} />
                <span>桩号数据</span>
              </button>
              <button
                className={importType === 'crossSections' ? 'active' : ''}
                onClick={() => { setImportType('crossSections'); updateFieldMappingsForType('crossSections'); handleClear(); }}
              >
                <FileType size={20} />
                <span>横断面数据</span>
              </button>
            </div>
          </div>

          <div className="panel-section">
            <h3>2. 项目信息</h3>
            <div className="form-group">
              <label>项目ID</label>
              <input type="text" value={projectId} disabled className="input-disabled" />
            </div>
            <div className="form-group">
              <label>路线ID</label>
              <input type="text" value={routeId} onChange={(e) => setRouteId(e.target.value)} placeholder="路线ID" />
            </div>
          </div>

          <div className="panel-section">
            <h3>3. 选择文件</h3>
            <div className="drop-zone" onClick={() => fileInputRef.current?.click()}>
              <input ref={fileInputRef} type="file" accept=".csv,.xlsx,.xls" onChange={handleFileSelect} style={{ display: 'none' }} />
              <Upload size={32} />
              <p>点击选择CSV/Excel文件</p>
              <span className="drop-hint">支持 .csv, .xlsx, .xls 格式</span>
            </div>
            <button className="btn-template" onClick={handleDownloadTemplate}>
              <Download size={16} />
              下载导入模板
            </button>
          </div>

          <div className="panel-section">
            <div className="section-header" onClick={() => setShowMappingConfig(!showMappingConfig)}>
              <h3><Settings size={16} />4. 字段映射配置</h3>
              <ChevronDown size={18} className={showMappingConfig ? 'rotate' : ''} />
            </div>
            
            {showMappingConfig && (
              <div className="mapping-config">
                <p className="mapping-hint">将源文件列映射到目标字段</p>
                <div className="mapping-list">
                  {fieldMappings.map((mapping, index) => (
                    <div key={index} className="mapping-item">
                      <select value={mapping.sourceField} onChange={(e) => updateMapping(index, e.target.value)} className="mapping-select">
                        <option value="">-- 选择源字段 --</option>
                        {headers.map(header => (
                          <option key={header} value={header}>{header}</option>
                        ))}
                      </select>
                      <span className="mapping-arrow">→</span>
                      <div className="mapping-target">
                        <span className="target-name">{mapping.targetField}</span>
                        {mapping.required && <span className="required-tag">必填</span>}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        <div className="preview-panel">
          <div className="panel-header">
            <h3>数据预览</h3>
            {parsedData.length > 0 && <span className="data-count">{parsedData.length} 行</span>}
          </div>

          {parsedData.length === 0 ? (
            <div className="empty-preview">
              <FileSpreadsheet size={48} />
              <p>请先选择导入文件</p>
              <span>支持 CSV, XLSX, XLS 格式</span>
            </div>
          ) : (
            <>
              {file && (
                <div className="file-info">
                  <span className="file-name"><FileSpreadsheet size={16} />{file.name}</span>
                  <button className="btn-clear" onClick={handleClear}><X size={14} />清除</button>
                </div>
              )}

              <div className="table-container">
                <table className="preview-table">
                  <thead>
                    <tr>
                      <th>#</th>
                      {fieldMappings.map((field, index) => (
                        <th key={index}>{field.targetField}{field.required && <span className="required-dot"></span>}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {mappedPreviewData.map((row, rowIndex) => (
                      <tr key={rowIndex} className={rowIndex % 2 === 0 ? 'even-row' : 'odd-row'}>
                        <td className="row-num">{rowIndex + 1}</td>
                        {fieldMappings.map((field, colIndex) => (
                          <td key={colIndex} className={row[field.targetField] === '-' ? 'empty-cell' : ''}>
                            {row[field.targetField]}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
                {parsedData.length > 20 && <div className="table-footer">显示前20行，共 {parsedData.length} 行</div>}
              </div>

              <div className="import-actions">
                <button className="btn-import" onClick={handleImport} disabled={importing || parsedData.length === 0}>
                  {importing ? <><Loader2 size={18} className="spinner" />导入中...</> : <><Play size={18} />开始导入 ({parsedData.length} 条)</>}
                </button>
              </div>
            </>
          )}
        </div>
      </div>

      {showErrorDetails && result && (result.errors.length > 0 || result.warnings.length > 0) && (
        <div className="error-details">
          <div className="details-header">
            <h4>导入详情</h4>
            <button className="btn-close-details" onClick={() => setShowErrorDetails(false)}><X size={16} /></button>
          </div>
          
          {result.errors.length > 0 && (
            <div className="error-section">
              <h5 className="error-title"><AlertCircle size={14} />错误 ({result.errors.length})</h5>
              <ul>
                {result.errors.slice(0, 20).map((err, index) => (
                  <li key={index} className="error-item"><span className="error-row">第{err.row}行</span><span className="error-msg">{err.message}</span></li>
                ))}
                {result.errors.length > 20 && <li className="more-errors">...还有 {result.errors.length - 20} 个错误</li>}
              </ul>
            </div>
          )}

          {result.warnings.length > 0 && (
            <div className="warning-section">
              <h5 className="warning-title"><AlertCircle size={14} />警告 ({result.warnings.length})</h5>
              <ul>
                {result.warnings.slice(0, 10).map((warn, index) => (
                  <li key={index} className="warning-item"><span className="warning-row">第{warn.row}行</span><span className="warning-msg">{warn.message}</span></li>
                ))}
                {result.warnings.length > 10 && <li className="more-warnings">...还有 {result.warnings.length - 10} 个警告</li>}
              </ul>
            </div>
          )}
        </div>
      )}

      <style>{`
        .data-import-page { display: flex; flex-direction: column; height: 100%; padding: 20px; overflow-y: auto; background: #0f0f1a; }
        .page-header { display: flex; align-items: center; gap: 20px; margin-bottom: 20px; }
        .page-header h1 { flex: 1; font-size: 20px; color: #fff; margin: 0; }
        .btn-back { display: flex; align-items: center; gap: 8px; padding: 8px 16px; background: #252540; border: 1px solid #444; border-radius: 6px; color: #aaa; cursor: pointer; }
        .alert { display: flex; align-items: center; gap: 10px; padding: 12px 16px; border-radius: 8px; margin-bottom: 16px; font-size: 14px; position: relative; }
        .alert.success { background: rgba(0, 255, 136, 0.1); border: 1px solid #00ff88; color: #00ff88; }
        .alert.warning { background: rgba(255, 193, 7, 0.1); border: 1px solid #ffc107; color: #ffc107; }
        .alert.error { background: rgba(255, 107, 107, 0.1); border: 1px solid #ff6b6b; color: #ff6b6b; }
        .alert-close { margin-left: auto; background: none; border: none; color: inherit; cursor: pointer; opacity: 0.7; }
        .alert-close:hover { opacity: 1; }
        .error-count { text-decoration: underline; cursor: pointer; margin-left: auto; }
        .progress-container { background: #1a1a2e; border-radius: 8px; padding: 16px; margin-bottom: 16px; }
        .progress-info { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; font-size: 13px; color: #aaa; }
        .progress-percent { margin-left: auto; color: #667eea; font-weight: 600; }
        .progress-bar { height: 6px; background: #252540; border-radius: 3px; overflow: hidden; }
        .progress-fill { height: 100%; background: linear-gradient(90deg, #667eea, #764ba2); border-radius: 3px; transition: width 0.3s ease; }
        .spinner { animation: spin 1s linear infinite; }
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
        .content-grid { display: grid; grid-template-columns: 380px 1fr; gap: 20px; flex: 1; min-height: 0; }
        .config-panel, .preview-panel { display: flex; flex-direction: column; background: #1a1a2e; border-radius: 12px; padding: 20px; overflow: hidden; }
        .panel-section { margin-bottom: 24px; }
        .panel-section h3 { font-size: 14px; color: #00ff88; margin: 0 0 16px; display: flex; align-items: center; gap: 8px; }
        .section-header { display: flex; justify-content: space-between; align-items: center; cursor: pointer; margin-bottom: 16px; }
        .section-header h3 { margin: 0; }
        .section-header svg { color: #888; transition: transform 0.2s; }
        .section-header .rotate { transform: rotate(180deg); }
        .type-selector { display: flex; gap: 12px; }
        .type-selector button { flex: 1; display: flex; flex-direction: column; align-items: center; gap: 8px; padding: 16px; background: #252540; border: 2px solid #444; border-radius: 8px; color: #aaa; cursor: pointer; transition: all 0.2s; }
        .type-selector button:hover { border-color: #667eea; }
        .type-selector button.active { border-color: #667eea; background: rgba(102, 126, 234, 0.1); color: #667eea; }
        .type-selector button span { font-size: 13px; }
        .form-group { margin-bottom: 12px; }
        .form-group label { display: block; font-size: 12px; color: #888; margin-bottom: 6px; }
        .form-group input { width: 100%; padding: 10px 12px; background: #252540; border: 1px solid #444; border-radius: 6px; color: #fff; font-size: 13px; }
        .form-group input:focus { outline: none; border-color: #667eea; }
        .input-disabled { background: #1a1a2e !important; color: #666 !important; cursor: not-allowed; }
        .drop-zone { display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 30px; border: 2px dashed #444; border-radius: 8px; cursor: pointer; transition: all 0.2s; color: #666; }
        .drop-zone:hover { border-color: #667eea; background: rgba(102, 126, 234, 0.05); }
        .drop-zone p { margin: 12px 0 4px; color: #aaa; font-size: 13px; }
        .drop-hint { font-size: 11px; color: #666; }
        .btn-template { display: flex; align-items: center; justify-content: center; gap: 8px; width: 100%; margin-top: 12px; padding: 10px; background: #252540; border: 1px solid #444; border-radius: 6px; color: #aaa; font-size: 13px; cursor: pointer; }
        .btn-template:hover { background: #333; color: #fff; }
        .mapping-config { animation: slideDown 0.2s ease; }
        @keyframes slideDown { from { opacity: 0; transform: translateY(-10px); } to { opacity: 1; transform: translateY(0); } }
        .mapping-hint { font-size: 12px; color: #666; margin: 0 0 12px; }
        .mapping-list { display: flex; flex-direction: column; gap: 8px; max-height: 200px; overflow-y: auto; }
        .mapping-item { display: flex; align-items: center; gap: 8px; padding: 8px; background: #252540; border-radius: 6px; }
        .mapping-select { flex: 1; padding: 6px 8px; background: #1a1a2e; border: 1px solid #444; border-radius: 4px; color: #fff; font-size: 12px; }
        .mapping-arrow { color: #667eea; font-weight: bold; }
        .mapping-target { display: flex; align-items: center; gap: 6px; min-width: 100px; }
        .target-name { font-size: 12px; color: #aaa; }
        .required-tag { font-size: 10px; padding: 2px 6px; background: #ff6b6b; color: #fff; border-radius: 4px; }
        .panel-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
        .panel-header h3 { font-size: 16px; color: #fff; margin: 0; }
        .data-count { font-size: 12px; color: #888; background: #252540; padding: 4px 10px; border-radius: 12px; }
        .empty-preview { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; color: #444; }
        .empty-preview p { margin: 16px 0 8px; font-size: 14px; }
        .empty-preview span { font-size: 12px; }
        .file-info { display: flex; justify-content: space-between; align-items: center; padding: 10px 14px; background: #252540; border-radius: 6px; margin-bottom: 12px; }
        .file-name { display: flex; align-items: center; gap: 8px; font-size: 13px; color: #fff; }
        .btn-clear { display: flex; align-items: center; gap: 4px; padding: 4px 10px; background: transparent; border: none; color: #ff6b6b; font-size: 12px; cursor: pointer; }
        .table-container { flex: 1; overflow: auto; background: #252540; border-radius: 8px; }
        .preview-table { width: 100%; border-collapse: collapse; }
        .preview-table th, .preview-table td { padding: 10px 12px; text-align: left; border-bottom: 1px solid #333; white-space: nowrap; }
        .preview-table th { background: #1a1a2e; color: #888; font-size: 11px; font-weight: 500; position: sticky; top: 0; }
        .preview-table td { color: #ddd; font-size: 12px; }
        .required-dot { display: inline-block; width: 6px; height: 6px; background: #ff6b6b; border-radius: 50%; margin-left: 4px; }
        .row-num { color: #666 !important; width: 40px; text-align: center; }
        .empty-cell { color: #666 !important; font-style: italic; }
        .even-row { background: rgba(255,255,255,0.02); }
        .odd-row { background: rgba(255,255,255,0.05); }
        .table-footer { padding: 10px; text-align: center; font-size: 12px; color: #666; background: #1a1a2e; }
        .import-actions { margin-top: 16px; }
        .btn-import { width: 100%; display: flex; align-items: center; justify-content: center; gap: 8px; padding: 14px; background: linear-gradient(135deg, #667eea, #764ba2); border: none; border-radius: 8px; color: #fff; font-size: 14px; font-weight: 600; cursor: pointer; }
        .btn-import:hover:not(:disabled) { transform: translateY(-2px); }
        .btn-import:disabled { opacity: 0.6; cursor: not-allowed; }
        .error-details { margin-top: 20px; padding: 16px; background: #1a1a2e; border-radius: 8px; max-height: 300px; overflow-y: auto; }
        .details-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
        .details-header h4 { font-size: 14px; color: #fff; margin: 0; }
        .btn-close-details { background: none; border: none; color: #888; cursor: pointer; padding: 4px; }
        .btn-close-details:hover { color: #fff; }
        .error-section, .warning-section { margin-bottom: 16px; }
        .error-section:last-child, .warning-section:last-child { margin-bottom: 0; }
        .error-title, .warning-title { display: flex; align-items: center; gap: 6px; font-size: 13px; margin: 0 0 10px; }
        .error-title { color: #ff6b6b; }
        .warning-title { color: #ffc107; }
        .error-details ul { margin: 0; padding-left: 20px; }
        .error-item, .warning-item { display: flex; gap: 12px; margin-bottom: 6px; font-size: 12px; }
        .error-row, .warning-row { color: #888; min-width: 60px; }
        .error-msg, .warning-msg { color: #ccc; }
        .more-errors, .more-warnings { color: #666; font-style: italic; font-size: 12px; }
      `}</style>
    </div>
  );
}