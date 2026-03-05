import { useState, useCallback, useRef } from 'react';
import { photosApi } from '../api/endpoints';
import { Photo } from '../api/types';
import { 
  ArrowLeft, 
  Upload, 
  Image, 
  X, 
  Check, 
  AlertCircle, 
  Sparkles, 
  Save, 
  RefreshCw,
  Eye,
  Edit3,
  ChevronDown,
  Loader2,
  CheckCircle,
  AlertTriangle,
  Info
} from 'lucide-react';

// AI 分类类型定义
interface AIClassification {
  constructionStatus: string;    // 施工状态
  constructionStatusOptions: string[];
  part: string;                    // 部位
  partOptions: string[];
  issueType: string;               // 问题类型
  issueTypeOptions: string[];
  confidence: number;              // 置信度
  suggestions: string[];
}

// 施工状态选项
const CONSTRUCTION_STATUS_OPTIONS = [
  '未开工', '准备阶段', '施工中', '已完成', '停工中', '验收中'
];

// 部位选项
const PART_OPTIONS = [
  '路基', '路面', '桥梁', '隧道', '涵洞', '防护工程', 
  '排水系统', '交通安全设施', '绿化', '房建', '机电', '其他'
];

// 问题类型选项
const ISSUE_TYPE_OPTIONS = [
  '无问题', '质量问题', '安全隐患', '进度滞后', '设计变更', 
  '材料问题', '施工工艺问题', '环境问题', '其他'
];

interface PhotoAIAnnotatorProps {
  onNavigate?: (page: string) => void;
}

export default function PhotoAIAnnotator({ onNavigate }: PhotoAIAnnotatorProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  // 照片状态
  const [photos, setPhotos] = useState<Array<{
    file: File;
    preview: string;
    id: string;
    classification?: AIClassification;
    isVerified: boolean;
    saving: boolean;
  }>>([]);
  
  // 当前选中的照片索引
  const [selectedIndex, setSelectedIndex] = useState<number>(0);
  
  // 消息提示
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  
  // 项目信息
  const [projectId] = useState('demo');
  const [station, setStation] = useState('');
  const [stationDisplay, setStationDisplay] = useState('');
  const [description, setDescription] = useState('');

  // AI 分类中
  const [classifying, setClassifying] = useState(false);

  // 处理文件选择
  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const newFiles = Array.from(e.target.files).filter(file => 
        file.type.startsWith('image/')
      );
      
      const newPhotos = newFiles.map(file => ({
        file,
        preview: URL.createObjectURL(file),
        id: `photo_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        isVerified: false,
        saving: false
      }));
      
      setPhotos(prev => [...prev, ...newPhotos]);
      if (selectedIndex === -1 && newPhotos.length > 0) {
        setSelectedIndex(photos.length);
      }
      setError(null);
    }
  }, [photos.length, selectedIndex]);

  // 移除照片
  const handleRemovePhoto = useCallback((index: number) => {
    setPhotos(prev => prev.filter((_, i) => i !== index));
    if (selectedIndex >= index && selectedIndex > 0) {
      setSelectedIndex(prev => prev - 1);
    }
  }, [selectedIndex]);

  // 模拟 AI 分类 (实际应调用后端 API)
  const handleAIClassify = useCallback(async (photoId: string) => {
    setClassifying(true);
    
    try {
      // 模拟 API 调用延迟
      await new Promise(resolve => setTimeout(resolve, 1000 + Math.random() * 1000));
      
      // 模拟 AI 分类结果
      const mockClassification: AIClassification = {
        constructionStatus: CONSTRUCTION_STATUS_OPTIONS[Math.floor(Math.random() * CONSTRUCTION_STATUS_OPTIONS.length)],
        constructionStatusOptions: CONSTRUCTION_STATUS_OPTIONS,
        part: PART_OPTIONS[Math.floor(Math.random() * PART_OPTIONS.length)],
        partOptions: PART_OPTIONS,
        issueType: ISSUE_TYPE_OPTIONS[Math.floor(Math.random() * 3)], // 前3个选项概率更高
        issueTypeOptions: ISSUE_TYPE_OPTIONS,
        confidence: 0.7 + Math.random() * 0.25,
        suggestions: [
          '建议检查施工日志',
          '确认现场安全措施',
          '记录具体施工情况'
        ]
      };
      
      setPhotos(prev => prev.map(p => 
        p.id === photoId 
          ? { ...p, classification: mockClassification }
          : p
      ));
      
      setSuccess('AI 分类完成！');
      setTimeout(() => setSuccess(null), 3000);
      
    } catch (err) {
      setError('AI 分类失败，请重试');
    } finally {
      setClassifying(false);
    }
  }, []);

  // 批量 AI 分类
  const handleBatchClassify = useCallback(async () => {
    if (photos.length === 0) {
      setError('请先选择照片');
      return;
    }
    
    setClassifying(true);
    
    for (let i = 0; i < photos.length; i++) {
      const photo = photos[i];
      if (!photo.classification) {
        await handleAIClassify(photo.id);
      }
    }
    
    setClassifying(false);
  }, [photos, handleAIClassify]);

  // 更新分类结果
  const handleUpdateClassification = useCallback((photoId: string, field: keyof AIClassification, value: string) => {
    setPhotos(prev => prev.map(p => {
      if (p.id === photoId && p.classification) {
        return {
          ...p,
          classification: {
            ...p.classification,
            [field]: value
          }
        };
      }
      return p;
    }));
  }, []);

  // 确认分类结果
  const handleVerify = useCallback((photoId: string) => {
    setPhotos(prev => prev.map(p => 
      p.id === photoId 
        ? { ...p, isVerified: true }
        : p
    ));
    setSuccess('已确认分类结果！');
    setTimeout(() => setSuccess(null), 3000);
  }, []);

  // 保存到数据库
  const handleSaveToDatabase = useCallback(async () => {
    const unverified = photos.filter(p => !p.isVerified);
    if (unverified.length > 0) {
      setError(`还有 ${unverified.length} 张照片未确认分类结果`);
      return;
    }
    
    if (photos.length === 0) {
      setError('没有可保存的照片');
      return;
    }
    
    // 保存每张照片
    setPhotos(prev => prev.map(p => ({ ...p, saving: true })));
    
    try {
      // 模拟保存到后端
      for (const photo of photos) {
        // 实际应调用 photosApi.upload 和 photosApi.update
        // 这里模拟保存成功
        await new Promise(resolve => setTimeout(resolve, 500));
      }
      
      setSuccess(`成功保存 ${photos.length} 张照片到数据库！`);
      setTimeout(() => setSuccess(null), 3000);
      
      // 清空已保存的照片
      setPhotos([]);
      setSelectedIndex(-1);
      
    } catch (err) {
      setError('保存失败，请重试');
    } finally {
      setPhotos(prev => prev.map(p => ({ ...p, saving: false })));
    }
  }, [photos]);

  // 解析桩号
  const parseStationValue = (display: string): number => {
    const match = display.match(/^([Kk])?(\d+)\+(\d{3})$/);
    if (match) {
      return parseInt(match[2]) * 1000 + parseInt(match[3]);
    }
    return parseFloat(display) || 0;
  };

  // 当前选中的照片
  const selectedPhoto = photos[selectedIndex];

  // 统计
  const totalPhotos = photos.length;
  const classifiedCount = photos.filter(p => p.classification).length;
  const verifiedCount = photos.filter(p => p.isVerified).length;

  return (
    <div className="photo-ai-annotator">
      {/* 顶部导航 */}
      <div className="page-header">
        <button className="btn-back" onClick={() => onNavigate?.('dashboard')}>
          <ArrowLeft size={20} />
          返回
        </button>
        <h1>🤖 照片AI标注</h1>
        <div className="header-stats">
          <span className="stat">
            <Image size={16} /> {totalPhotos} 张
          </span>
          <span className="stat">
            <Sparkles size={16} /> {classifiedCount} 已分类
          </span>
          <span className="stat verified">
            <CheckCircle size={16} /> {verifiedCount} 已确认
          </span>
        </div>
      </div>

      {/* 消息提示 */}
      {success && (
        <div className="alert success">
          <Check size={18} />
          {success}
        </div>
      )}
      {error && (
        <div className="alert error">
          <AlertCircle size={18} />
          {error}
        </div>
      )}

      <div className="content-layout">
        {/* 左侧：照片列表 */}
        <div className="photo-list-panel">
          <div className="panel-header">
            <h3>照片列表</h3>
            <button 
              className="btn-add-photo"
              onClick={() => fileInputRef.current?.click()}
            >
              <Upload size={16} />
              添加照片
            </button>
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              multiple
              onChange={handleFileSelect}
              style={{ display: 'none' }}
            />
          </div>

          {photos.length === 0 ? (
            <div className="empty-list">
              <Image size={48} />
              <p>暂无照片</p>
              <span>点击上方按钮添加照片</span>
            </div>
          ) : (
            <div className="photo-list">
              {photos.map((photo, index) => (
                <div 
                  key={photo.id}
                  className={`photo-list-item ${selectedIndex === index ? 'selected' : ''} ${photo.isVerified ? 'verified' : ''}`}
                  onClick={() => setSelectedIndex(index)}
                >
                  <div className="photo-thumb">
                    <img src={photo.preview} alt="" />
                    {photo.isVerified && (
                      <div className="verified-badge">
                        <CheckCircle size={14} />
                      </div>
                    )}
                  </div>
                  <div className="photo-meta">
                    <span className="photo-name">{photo.file.name}</span>
                    <span className="photo-status">
                      {photo.classification 
                        ? (photo.isVerified ? '✓ 已确认' : '⚠ 待确认')
                        : '○ 待分类'
                      }
                    </span>
                  </div>
                  <button 
                    className="btn-remove"
                    onClick={(e) => {
                      e.stopPropagation();
                      handleRemovePhoto(index);
                    }}
                  >
                    <X size={14} />
                  </button>
                </div>
              ))}
            </div>
          )}

          {/* 批量操作 */}
          {photos.length > 0 && (
            <div className="batch-actions">
              <button 
                className="btn-ai-classify"
                onClick={handleBatchClassify}
                disabled={classifying}
              >
                {classifying ? (
                  <Loader2 size={16} className="spin" />
                ) : (
                  <Sparkles size={16} />
                )}
                批量AI分类
              </button>
              <button 
                className="btn-save"
                onClick={handleSaveToDatabase}
                disabled={verifiedCount === 0}
              >
                <Save size={16} />
                保存到数据库
              </button>
            </div>
          )}
        </div>

        {/* 中间：照片预览 */}
        <div className="photo-preview-panel">
          <div className="panel-header">
            <h3>照片预览</h3>
          </div>

          {selectedPhoto ? (
            <div className="preview-container">
              <img 
                src={selectedPhoto.preview} 
                alt="预览" 
                className="preview-image"
              />
              
              {/* 照片操作 */}
              <div className="preview-actions">
                {!selectedPhoto.classification && (
                  <button 
                    className="btn-ai-classify-single"
                    onClick={() => handleAIClassify(selectedPhoto.id)}
                    disabled={classifying}
                  >
                    {classifying ? (
                      <Loader2 size={18} className="spin" />
                    ) : (
                      <Sparkles size={18} />
                    )}
                    AI 分类
                  </button>
                )}
                {selectedPhoto.classification && !selectedPhoto.isVerified && (
                  <button 
                    className="btn-verify"
                    onClick={() => handleVerify(selectedPhoto.id)}
                  >
                    <CheckCircle size={18} />
                    确认分类
                  </button>
                )}
                {selectedPhoto.isVerified && (
                  <span className="verified-label">
                    <CheckCircle size={18} />
                    已确认
                  </span>
                )}
              </div>
            </div>
          ) : (
            <div className="empty-preview">
              <Image size={64} />
              <p>选择一张照片进行预览和标注</p>
            </div>
          )}
        </div>

        {/* 右侧：AI分类结果 */}
        <div className="classification-panel">
          <div className="panel-header">
            <h3>AI 分类结果</h3>
            {selectedPhoto?.classification && (
              <span className="confidence-badge">
                置信度: {(selectedPhoto.classification.confidence * 100).toFixed(0)}%
              </span>
            )}
          </div>

          {selectedPhoto?.classification ? (
            <div className="classification-content">
              {/* 施工状态 */}
              <div className="classification-item">
                <label>
                  <Info size={16} />
                  施工状态
                </label>
                <div className="select-wrapper">
                  <select
                    value={selectedPhoto.classification.constructionStatus}
                    onChange={(e) => handleUpdateClassification(
                      selectedPhoto.id, 
                      'constructionStatus', 
                      e.target.value
                    )}
                    disabled={selectedPhoto.isVerified}
                  >
                    {selectedPhoto.classification.constructionStatusOptions.map(opt => (
                      <option key={opt} value={opt}>{opt}</option>
                    ))}
                  </select>
                  <ChevronDown size={16} className="select-icon" />
                </div>
              </div>

              {/* 部位 */}
              <div className="classification-item">
                <label>
                  <Info size={16} />
                  部位
                </label>
                <div className="select-wrapper">
                  <select
                    value={selectedPhoto.classification.part}
                    onChange={(e) => handleUpdateClassification(
                      selectedPhoto.id, 
                      'part', 
                      e.target.value
                    )}
                    disabled={selectedPhoto.isVerified}
                  >
                    {selectedPhoto.classification.partOptions.map(opt => (
                      <option key={opt} value={opt}>{opt}</option>
                    ))}
                  </select>
                  <ChevronDown size={16} className="select-icon" />
                </div>
              </div>

              {/* 问题类型 */}
              <div className="classification-item">
                <label>
                  <AlertTriangle size={16} />
                  问题类型
                </label>
                <div className="select-wrapper">
                  <select
                    value={selectedPhoto.classification.issueType}
                    onChange={(e) => handleUpdateClassification(
                      selectedPhoto.id, 
                      'issueType', 
                      e.target.value
                    )}
                    disabled={selectedPhoto.isVerified}
                  >
                    {selectedPhoto.classification.issueTypeOptions.map(opt => (
                      <option key={opt} value={opt}>{opt}</option>
                    ))}
                  </select>
                  <ChevronDown size={16} className="select-icon" />
                </div>
              </div>

              {/* 置信度显示 */}
              <div className="confidence-display">
                <div className="confidence-bar">
                  <div 
                    className="confidence-fill"
                    style={{ 
                      width: `${selectedPhoto.classification.confidence * 100}%`,
                      background: selectedPhoto.classification.confidence > 0.8 
                        ? '#00ff88' 
                        : selectedPhoto.classification.confidence > 0.6 
                          ? '#ffa500' 
                          : '#ff6b6b'
                    }}
                  />
                </div>
                <span className="confidence-text">
                  AI 置信度: {(selectedPhoto.classification.confidence * 100).toFixed(1)}%
                </span>
              </div>

              {/* 建议 */}
              {selectedPhoto.classification.suggestions.length > 0 && (
                <div className="suggestions">
                  <h4>
                    <Sparkles size={16} />
                    建议
                  </h4>
                  <ul>
                    {selectedPhoto.classification.suggestions.map((suggestion, i) => (
                      <li key={i}>{suggestion}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* 元数据表单 */}
              <div className="metadata-form">
                <h4>照片信息</h4>
                
                <div className="form-group">
                  <label>桩号 (米)</label>
                  <input
                    type="number"
                    value={station}
                    onChange={(e) => {
                      setStation(e.target.value);
                      const value = parseStationValue(e.target.value);
                      if (value > 0) {
                        const km = Math.floor(value / 1000);
                        const m = value % 1000;
                        setStationDisplay(`K${km}+${m.toString().padStart(3, '0')}`);
                      }
                    }}
                    placeholder="桩号"
                  />
                </div>

                <div className="form-group">
                  <label>桩号显示</label>
                  <input
                    type="text"
                    value={stationDisplay}
                    onChange={(e) => setStationDisplay(e.target.value)}
                    placeholder="K0+500"
                  />
                </div>

                <div className="form-group">
                  <label>描述</label>
                  <textarea
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    placeholder="照片描述信息"
                    rows={3}
                  />
                </div>
              </div>
            </div>
          ) : (
            <div className="empty-classification">
              <Sparkles size={48} />
              <p>暂无分类结果</p>
              <span>点击"AI 分类"按钮进行分析</span>
            </div>
          )}
        </div>
      </div>

      <style>{`
        .photo-ai-annotator {
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

        .header-stats {
          display: flex;
          gap: 16px;
        }

        .header-stats .stat {
          display: flex;
          align-items: center;
          gap: 6px;
          font-size: 13px;
          color: #888;
        }

        .header-stats .stat.verified {
          color: #00ff88;
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

        .alert.error {
          background: rgba(255, 107, 107, 0.1);
          border: 1px solid #ff6b6b;
          color: #ff6b6b;
        }

        .content-layout {
          display: grid;
          grid-template-columns: 280px 1fr 320px;
          gap: 20px;
          flex: 1;
          overflow: hidden;
        }

        .photo-list-panel,
        .photo-preview-panel,
        .classification-panel {
          display: flex;
          flex-direction: column;
          background: #1a1a2e;
          border-radius: 12px;
          padding: 16px;
          overflow: hidden;
        }

        .panel-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 16px;
        }

        .panel-header h3 {
          font-size: 14px;
          color: #fff;
          margin: 0;
        }

        .confidence-badge {
          font-size: 11px;
          color: #00ff88;
          background: rgba(0, 255, 136, 0.1);
          padding: 4px 8px;
          border-radius: 12px;
        }

        .btn-add-photo {
          display: flex;
          align-items: center;
          gap: 6px;
          padding: 6px 12px;
          background: #667eea;
          border: none;
          border-radius: 6px;
          color: #fff;
          font-size: 12px;
          cursor: pointer;
        }

        .btn-add-photo:hover {
          background: #5a6fd6;
        }

        .empty-list {
          flex: 1;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          color: #444;
        }

        .empty-list p {
          margin: 12px 0 4px;
          font-size: 14px;
        }

        .empty-list span {
          font-size: 12px;
          color: #666;
        }

        .photo-list {
          flex: 1;
          overflow-y: auto;
        }

        .photo-list-item {
          display: flex;
          align-items: center;
          gap: 10px;
          padding: 8px;
          background: #252540;
          border-radius: 8px;
          margin-bottom: 8px;
          cursor: pointer;
          border: 2px solid transparent;
          transition: all 0.2s;
        }

        .photo-list-item:hover {
          background: #2a2a4a;
        }

        .photo-list-item.selected {
          border-color: #667eea;
          background: rgba(102, 126, 234, 0.1);
        }

        .photo-list-item.verified {
          border-color: #00ff88;
        }

        .photo-thumb {
          position: relative;
          width: 48px;
          height: 48px;
          border-radius: 6px;
          overflow: hidden;
          flex-shrink: 0;
        }

        .photo-thumb img {
          width: 100%;
          height: 100%;
          object-fit: cover;
        }

        .verified-badge {
          position: absolute;
          top: -4px;
          right: -4px;
          background: #00ff88;
          border-radius: 50%;
          padding: 2px;
          color: #000;
        }

        .photo-meta {
          flex: 1;
          min-width: 0;
        }

        .photo-name {
          display: block;
          font-size: 12px;
          color: #fff;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }

        .photo-status {
          font-size: 11px;
          color: #888;
        }

        .btn-remove {
          padding: 4px;
          background: transparent;
          border: none;
          color: #666;
          cursor: pointer;
          border-radius: 4px;
        }

        .btn-remove:hover {
          background: rgba(255, 107, 107, 0.2);
          color: #ff6b6b;
        }

        .batch-actions {
          display: flex;
          gap: 8px;
          margin-top: 12px;
        }

        .btn-ai-classify,
        .btn-save {
          flex: 1;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 6px;
          padding: 10px;
          border: none;
          border-radius: 6px;
          font-size: 12px;
          cursor: pointer;
        }

        .btn-ai-classify {
          background: linear-gradient(135deg, #667eea, #764ba2);
          color: #fff;
        }

        .btn-ai-classify:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }

        .btn-save {
          background: #00ff88;
          color: #000;
          font-weight: 600;
        }

        .btn-save:disabled {
          background: #333;
          color: #666;
          cursor: not-allowed;
        }

        .spin {
          animation: spin 1s linear infinite;
        }

        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
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
          margin-top: 12px;
          font-size: 14px;
        }

        .preview-container {
          flex: 1;
          display: flex;
          flex-direction: column;
          overflow: hidden;
        }

        .preview-image {
          flex: 1;
          max-height: calc(100% - 60px);
          object-fit: contain;
          border-radius: 8px;
          background: #000;
        }

        .preview-actions {
          display: flex;
          justify-content: center;
          gap: 12px;
          margin-top: 16px;
        }

        .btn-ai-classify-single,
        .btn-verify {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 10px 20px;
          border: none;
          border-radius: 8px;
          font-size: 14px;
          cursor: pointer;
        }

        .btn-ai-classify-single {
          background: linear-gradient(135deg, #667eea, #764ba2);
          color: #fff;
        }

        .btn-verify {
          background: #00ff88;
          color: #000;
          font-weight: 600;
        }

        .verified-label {
          display: flex;
          align-items: center;
          gap: 8px;
          padding: 10px 20px;
          background: rgba(0, 255, 136, 0.1);
          border: 1px solid #00ff88;
          border-radius: 8px;
          color: #00ff88;
          font-size: 14px;
        }

        .empty-classification {
          flex: 1;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          color: #444;
        }

        .empty-classification p {
          margin: 16px 0 4px;
          font-size: 14px;
        }

        .empty-classification span {
          font-size: 12px;
          color: #666;
        }

        .classification-content {
          flex: 1;
          overflow-y: auto;
        }

        .classification-item {
          margin-bottom: 16px;
        }

        .classification-item label {
          display: flex;
          align-items: center;
          gap: 6px;
          font-size: 12px;
          color: #888;
          margin-bottom: 8px;
        }

        .select-wrapper {
          position: relative;
        }

        .select-wrapper select {
          width: 100%;
          padding: 10px 32px 10px 12px;
          background: #252540;
          border: 1px solid #444;
          border-radius: 6px;
          color: #fff;
          font-size: 13px;
          appearance: none;
          cursor: pointer;
        }

        .select-wrapper select:focus {
          outline: none;
          border-color: #667eea;
        }

        .select-wrapper select:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }

        .select-icon {
          position: absolute;
          right: 10px;
          top: 50%;
          transform: translateY(-50%);
          color: #666;
          pointer-events: none;
        }

        .confidence-display {
          margin: 20px 0;
          padding: 12px;
          background: #252540;
          border-radius: 8px;
        }

        .confidence-bar {
          height: 8px;
          background: #333;
          border-radius: 4px;
          overflow: hidden;
        }

        .confidence-fill {
          height: 100%;
          border-radius: 4px;
          transition: width 0.3s ease;
        }

        .confidence-text {
          display: block;
          margin-top: 8px;
          font-size: 12px;
          color: #888;
          text-align: center;
        }

        .suggestions {
          margin-bottom: 20px;
          padding: 12px;
          background: rgba(102, 126, 234, 0.1);
          border: 1px solid rgba(102, 126, 234, 0.3);
          border-radius: 8px;
        }

        .suggestions h4 {
          display: flex;
          align-items: center;
          gap: 6px;
          margin: 0 0 10px;
          font-size: 12px;
          color: #667eea;
        }

        .suggestions ul {
          margin: 0;
          padding-left: 20px;
        }

        .suggestions li {
          font-size: 12px;
          color: #aaa;
          margin-bottom: 4px;
        }

        .metadata-form {
          padding-top: 16px;
          border-top: 1px solid #333;
        }

        .metadata-form h4 {
          font-size: 13px;
          color: #00ff88;
          margin: 0 0 12px;
        }

        .metadata-form .form-group {
          margin-bottom: 12px;
        }

        .metadata-form label {
          display: block;
          font-size: 11px;
          color: #666;
          margin-bottom: 4px;
        }

        .metadata-form input,
        .metadata-form textarea {
          width: 100%;
          padding: 8px 10px;
          background: #252540;
          border: 1px solid #444;
          border-radius: 6px;
          color: #fff;
          font-size: 12px;
        }

        .metadata-form input:focus,
        .metadata-form textarea:focus {
          outline: none;
          border-color: #667eea;
        }

        .metadata-form textarea {
          resize: none;
        }
      `}</style>
    </div>
  );
}
