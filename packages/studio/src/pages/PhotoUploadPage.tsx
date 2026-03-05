import { useState, useCallback, useRef } from 'react';
import { useApp } from '../context/AppContext';
import { photosApi } from '../api/endpoints';
import { Photo } from '../api/types';
import { ArrowLeft, Upload, Image, X, Check, AlertCircle, Trash2, Link } from 'lucide-react';

interface PhotoUploadPageProps {
  onNavigate?: (page: string) => void;
}

export default function PhotoUploadPage({ onNavigate }: PhotoUploadPageProps) {
  const { state } = useApp();
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  const [files, setFiles] = useState<File[]>([]);
  const [uploadProgress, setUploadProgress] = useState<Record<string, number>>({});
  const [uploadedPhotos, setUploadedPhotos] = useState<Photo[]>([]);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  
  // 表单状态
  const [projectId, setProjectId] = useState(state.selectedProject?.project_id || 'demo');
  const [station, setStation] = useState('');
  const [stationDisplay, setStationDisplay] = useState('');
  const [description, setDescription] = useState('');

  // 处理文件选择
  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const newFiles = Array.from(e.target.files).filter(file => 
        file.type.startsWith('image/')
      );
      setFiles(prev => [...prev, ...newFiles]);
      setError(null);
    }
  }, []);

  // 移除文件
  const handleRemoveFile = useCallback((index: number) => {
    setFiles(prev => prev.filter((_, i) => i !== index));
  }, []);

  // 清空所有文件
  const handleClearFiles = useCallback(() => {
    setFiles([]);
    setUploadedPhotos([]);
    setUploadProgress({});
  }, []);

  // 上传文件
  const handleUpload = useCallback(async () => {
    if (files.length === 0) {
      setError('请先选择要上传的照片');
      return;
    }

    setUploading(true);
    setError(null);
    setSuccess(null);

    try {
      // 模拟批量上传
      const results: Photo[] = [];
      
      for (let i = 0; i < files.length; i++) {
        const file = files[i];
        
        // 更新进度
        setUploadProgress(prev => ({ ...prev, [file.name]: 0 }));
        
        // 模拟上传进度
        for (let p = 0; p <= 100; p += 20) {
          await new Promise(resolve => setTimeout(resolve, 50));
          setUploadProgress(prev => ({ ...prev, [file.name]: p }));
        }
        
        // 模拟创建照片记录
        const photo: Photo = {
          photo_id: `photo_${Date.now()}_${i}`,
          project_id: projectId,
          file_path: `/uploads/${file.name}`,
          file_size: file.size,
          mime_type: file.type,
          captured_at: new Date().toISOString(),
          station: station ? parseFloat(station) : undefined,
          station_display: stationDisplay || undefined,
          description,
          is_verified: false,
          sync_status: 'pending',
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        };
        
        results.push(photo);
      }
      
      setUploadedPhotos(results);
      setSuccess(`成功上传 ${results.length} 张照片！`);
      setFiles([]);
      setUploadProgress({});
      
    } catch (err) {
      setError(err instanceof Error ? err.message : '上传失败，请重试');
    } finally {
      setUploading(false);
    }
  }, [files, projectId, station, stationDisplay, description]);

  // 批量关联到桩号
  const handleBatchAssign = useCallback(async () => {
    if (uploadedPhotos.length === 0) {
      setError('没有可关联的照片');
      return;
    }

    if (!station || !stationDisplay) {
      setError('请输入桩号信息');
      return;
    }

    try {
      // 模拟批量关联
      await new Promise(resolve => setTimeout(resolve, 300));
      
      setUploadedPhotos(prev => prev.map(photo => ({
        ...photo,
        station: parseFloat(station),
        station_display: stationDisplay,
      })));
      
      setSuccess(`已将 ${uploadedPhotos.length} 张照片关联到桩号 ${stationDisplay}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : '关联失败');
    }
  }, [uploadedPhotos, station, stationDisplay]);

  // 复制照片链接
  const handleCopyLink = useCallback((photo: Photo) => {
    navigator.clipboard.writeText(photo.file_path);
  }, []);

  // 解析桩号显示值
  const parseStationValue = (display: string): number => {
    const match = display.match(/^([Kk])?(\d+)\+(\d{3})$/);
    if (match) {
      return parseInt(match[2]) * 1000 + parseInt(match[3]);
    }
    return parseFloat(display) || 0;
  };

  return (
    <div className="photo-upload-page">
      {/* 顶部导航 */}
      <div className="page-header">
        <button className="btn-back" onClick={() => onNavigate?.('dashboard')}>
          <ArrowLeft size={20} />
          返回
        </button>
        <h1>📷 PC端照片上传</h1>
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

      <div className="content-grid">
        {/* 左侧：上传区域 */}
        <div className="upload-panel">
          <div className="panel-header">
            <h3>选择照片</h3>
            <span className="file-count">{files.length} 个文件</span>
          </div>

          {/* 文件选择区域 */}
          <div 
            className="drop-zone"
            onClick={() => fileInputRef.current?.click()}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              multiple
              onChange={handleFileSelect}
              style={{ display: 'none' }}
            />
            <Upload size={48} />
            <p>点击选择或拖拽照片到这里</p>
            <span>支持 JPG, PNG, HEIC 等格式</span>
          </div>

          {/* 文件列表 */}
          {files.length > 0 && (
            <div className="file-list">
              {files.map((file, index) => (
                <div key={index} className="file-item">
                  <Image size={20} className="file-icon" />
                  <div className="file-info">
                    <span className="file-name">{file.name}</span>
                    <span className="file-size">
                      {(file.size / 1024 / 1024).toFixed(2)} MB
                    </span>
                    {uploadProgress[file.name] !== undefined && (
                      <div className="progress-bar">
                        <div 
                          className="progress-fill"
                          style={{ width: `${uploadProgress[file.name]}%` }}
                        />
                      </div>
                    )}
                  </div>
                  <button
                    className="btn-remove"
                    onClick={() => handleRemoveFile(index)}
                    disabled={uploading}
                  >
                    <X size={16} />
                  </button>
                </div>
              ))}

              <button 
                className="btn-clear"
                onClick={handleClearFiles}
                disabled={uploading}
              >
                <Trash2 size={16} />
                清空列表
              </button>
            </div>
          )}

          {/* 元数据表单 */}
          <div className="metadata-form">
            <h4>照片信息 (可选)</h4>
            
            <div className="form-group">
              <label>项目ID</label>
              <input
                type="text"
                value={projectId}
                onChange={(e) => setProjectId(e.target.value)}
                placeholder="项目ID"
              />
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>桩号</label>
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
                  placeholder="桩号(米)"
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
            </div>

            <div className="form-group">
              <label>描述</label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="照片描述信息"
                rows={2}
              />
            </div>
          </div>

          {/* 上传按钮 */}
          <div className="upload-actions">
            <button
              className="btn-upload"
              onClick={handleUpload}
              disabled={uploading || files.length === 0}
            >
              {uploading ? (
                <>上传中...</>
              ) : (
                <>
                  <Upload size={18} />
                  上传照片 ({files.length})
                </>
              )}
            </button>
          </div>
        </div>

        {/* 右侧：已上传照片 */}
        <div className="preview-panel">
          <div className="panel-header">
            <h3>已上传照片</h3>
            <span className="photo-count">{uploadedPhotos.length} 张</span>
          </div>

          {uploadedPhotos.length === 0 ? (
            <div className="empty-preview">
              <Image size={48} />
              <p>暂无已上传的照片</p>
            </div>
          ) : (
            <>
              {/* 批量操作 */}
              <div className="batch-actions">
                <div className="station-input">
                  <input
                    type="text"
                    value={stationDisplay}
                    onChange={(e) => setStationDisplay(e.target.value)}
                    placeholder="输入桩号"
                  />
                  <button onClick={handleBatchAssign}>
                    <Link size={16} />
                    批量关联
                  </button>
                </div>
              </div>

              {/* 照片网格 */}
              <div className="photo-grid">
                {uploadedPhotos.map((photo) => (
                  <div key={photo.photo_id} className="photo-card">
                    <div className="photo-placeholder">
                      <Image size={32} />
                    </div>
                    <div className="photo-info">
                      <span className="photo-name">
                        {photo.file_path.split('/').pop()}
                      </span>
                      {photo.station_display && (
                        <span className="photo-station">
                          📍 {photo.station_display}
                        </span>
                      )}
                    </div>
                    <div className="photo-actions">
                      <button
                        className="btn-icon"
                        onClick={() => handleCopyLink(photo)}
                        title="复制链接"
                      >
                        <Link size={14} />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      </div>

      <style>{`
        .photo-upload-page {
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

        .content-grid {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 20px;
          flex: 1;
          overflow: hidden;
        }

        .upload-panel,
        .preview-panel {
          display: flex;
          flex-direction: column;
          background: #1a1a2e;
          border-radius: 12px;
          padding: 20px;
          overflow: hidden;
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

        .file-count,
        .photo-count {
          font-size: 12px;
          color: #888;
          background: #252540;
          padding: 4px 10px;
          border-radius: 12px;
        }

        .drop-zone {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          padding: 40px;
          border: 2px dashed #444;
          border-radius: 12px;
          cursor: pointer;
          transition: all 0.2s;
          color: #666;
        }

        .drop-zone:hover {
          border-color: #667eea;
          background: rgba(102, 126, 234, 0.05);
        }

        .drop-zone p {
          margin: 16px 0 8px;
          color: #aaa;
          font-size: 14px;
        }

        .drop-zone span {
          font-size: 12px;
        }

        .file-list {
          margin-top: 16px;
          max-height: 200px;
          overflow-y: auto;
        }

        .file-item {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 10px;
          background: #252540;
          border-radius: 8px;
          margin-bottom: 8px;
        }

        .file-icon {
          color: #667eea;
        }

        .file-info {
          flex: 1;
          min-width: 0;
        }

        .file-name {
          display: block;
          font-size: 13px;
          color: #fff;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }

        .file-size {
          font-size: 11px;
          color: #666;
        }

        .progress-bar {
          height: 4px;
          background: #333;
          border-radius: 2px;
          margin-top: 4px;
        }

        .progress-fill {
          height: 100%;
          background: #00ff88;
          border-radius: 2px;
          transition: width 0.2s;
        }

        .btn-remove {
          padding: 6px;
          background: transparent;
          border: none;
          color: #ff6b6b;
          cursor: pointer;
          border-radius: 4px;
        }

        .btn-remove:hover {
          background: rgba(255, 107, 107, 0.1);
        }

        .btn-clear {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 8px;
          width: 100%;
          padding: 10px;
          background: transparent;
          border: 1px solid #444;
          border-radius: 6px;
          color: #aaa;
          font-size: 13px;
          cursor: pointer;
          margin-top: 8px;
        }

        .btn-clear:hover {
          background: rgba(255, 107, 107, 0.1);
          border-color: #ff6b6b;
          color: #ff6b6b;
        }

        .metadata-form {
          margin-top: 20px;
          padding-top: 20px;
          border-top: 1px solid #333;
        }

        .metadata-form h4 {
          font-size: 14px;
          color: #00ff88;
          margin: 0 0 16px;
        }

        .metadata-form .form-group {
          margin-bottom: 12px;
        }

        .metadata-form label {
          display: block;
          font-size: 12px;
          color: #888;
          margin-bottom: 6px;
        }

        .metadata-form input,
        .metadata-form textarea {
          width: 100%;
          padding: 10px 12px;
          background: #252540;
          border: 1px solid #444;
          border-radius: 6px;
          color: #fff;
          font-size: 13px;
        }

        .metadata-form input:focus,
        .metadata-form textarea:focus {
          outline: none;
          border-color: #667eea;
        }

        .form-row {
          display: flex;
          gap: 12px;
        }

        .form-row .form-group {
          flex: 1;
        }

        .upload-actions {
          margin-top: auto;
          padding-top: 16px;
        }

        .btn-upload {
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

        .btn-upload:hover:not(:disabled) {
          transform: translateY(-2px);
        }

        .btn-upload:disabled {
          opacity: 0.6;
          cursor: not-allowed;
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

        .batch-actions {
          margin-bottom: 16px;
        }

        .station-input {
          display: flex;
          gap: 8px;
        }

        .station-input input {
          flex: 1;
          padding: 8px 12px;
          background: #252540;
          border: 1px solid #444;
          border-radius: 6px;
          color: #fff;
          font-size: 13px;
        }

        .station-input button {
          display: flex;
          align-items: center;
          gap: 6px;
          padding: 8px 16px;
          background: #667eea;
          border: none;
          border-radius: 6px;
          color: #fff;
          font-size: 13px;
          cursor: pointer;
        }

        .photo-grid {
          display: grid;
          grid-template-columns: repeat(2, 1fr);
          gap: 12px;
          overflow-y: auto;
          flex: 1;
        }

        .photo-card {
          background: #252540;
          border-radius: 8px;
          overflow: hidden;
        }

        .photo-placeholder {
          height: 100px;
          display: flex;
          align-items: center;
          justify-content: center;
          background: #1a1a2e;
          color: #444;
        }

        .photo-info {
          padding: 10px;
        }

        .photo-name {
          display: block;
          font-size: 12px;
          color: #fff;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }

        .photo-station {
          display: block;
          font-size: 11px;
          color: #00ff88;
          margin-top: 4px;
        }

        .photo-actions {
          display: flex;
          justify-content: flex-end;
          padding: 0 10px 10px;
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
      `}</style>
    </div>
  );
}
