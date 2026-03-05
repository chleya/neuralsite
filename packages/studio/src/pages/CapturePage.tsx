import { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { photoApi } from '../api/client';
import styles from './CapturePage.module.css';

export default function CapturePage() {
  const navigate = useNavigate();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = () => setPreview(reader.result as string);
      reader.readAsDataURL(file);
    }
  };

  const handleUpload = async () => {
    const file = fileInputRef.current?.files?.[0];
    if (!file) return;

    setUploading(true);
    try {
      await photoApi.upload(file);
      navigate('/photos');
    } catch (error) {
      console.error('Failed to upload:', error);
      alert('上传失败，请重试');
    } finally {
      setUploading(false);
    }
  };

  const handleRetake = () => {
    setPreview(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div className={styles.container}>
      <h1 className={styles.title}>拍照采集</h1>

      <div className={styles.captureArea}>
        {preview ? (
          <div className={styles.preview}>
            <img src={preview} alt="Preview" />
          </div>
        ) : (
          <div className={styles.placeholder} onClick={() => fileInputRef.current?.click()}>
            <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path d="M23 19a2 2 0 01-2 2H3a2 2 0 01-2-2V8a2 2 0 012-2h4l2-3h6l2 3h4a2 2 0 012 2z" />
              <circle cx="12" cy="13" r="4" />
            </svg>
            <p>点击选择照片或拍照</p>
          </div>
        )}
        
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          capture="environment"
          onChange={handleFileSelect}
          className={styles.fileInput}
        />
      </div>

      {preview && (
        <div className={styles.actions}>
          <button className="btn btn-secondary" onClick={handleRetake}>
            重拍
          </button>
          <button className="btn btn-primary" onClick={handleUpload} disabled={uploading}>
            {uploading ? '上传中...' : '确认上传'}
          </button>
        </div>
      )}

      <div className={styles.tips}>
        <h3>拍摄建议</h3>
        <ul>
          <li>确保光线充足</li>
          <li>保持设备稳定</li>
          <li>对焦要清晰</li>
        </ul>
      </div>
    </div>
  );
}
